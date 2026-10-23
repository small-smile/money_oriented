"""
抓取银行类上市公司的年报口径财务数据（东方财富 F10 数据接口，取值来自各期年度报告）。

数据源（datacenter-web.eastmoney.com/api/data/v1/get，reportName 为报表模板）：
    - RPT_F10_FINANCE_BINCOME       银行业利润表（年报期）
    - RPT_F10_FINANCE_BBALANCE      银行业资产负债表（年报期）
    - RPT_F10_FINANCE_BCASHFLOW     银行业现金流量表（年报期）
    - RPT_F10_FINANCE_MAINFINADATA  主要指标（含银行专项：存贷款总额、不良率、
                                    资本充足率、核心一级、一级、NIM/NIS、拨备覆盖率、拨贷比等）
    - RPT_F10_EH_HOLDERS            前十名股东（含报告期内增减）
    - RPT_F10_EH_HOLDERNUM          历年股东户数（股东总数，少数期次含 A/H 拆分）
    - RPT_SHAREBONUS_DET            历年分红实施明细（每 10 股派现等）

纯 H 股上市银行（江西银行 01916.HK、天津银行 01578.HK、哈尔滨银行 06138.HK，均无 A 股上市）
走港股 F10（datacenter.eastmoney.com/securities/api/data/v1/get）+ 年报手工提取覆盖层：
    - RPT_HKF10_FN_MAININDICATOR    港股主要指标（年报 + 中期混排，需自行筛 12-31 行）
      币种陷阱：行内 CURRENCY="HKD"、IS_CNY_CODE=0 是误标 —— 江西银行年报本身以人民币编制，
      接口金额即人民币原值，无需折算（2024 年总资产 573,634,744,000 元 = 年报 573,634.75 百万元）。
      与中国太平（00966.HK，港元编制、接口已折人民币）不同，这里不存在汇率漂移。
      total_share 陷阱：ISSUED_COMMON_SHARES 各年一律回填 6,024,276,901 股，2015—2017 上市前
      实际为 4,678,776,901 股，须用年报值覆盖；DPS_HKD 是快照字段（2015—2024 各行同为 0.0807219），
      不能当逐年股息序列。
      港股 F10 主要指标完全不含银行监管指标（不良率/拨备覆盖率/拨贷比/资本充足率/NIM/NIS/
      贷款总额/员工数/逾期），这些只存在于年报正文，故另设覆盖层（同在 json_file 表，键如下）：
    - data/tables/bank_01916_ar_manual.json   逐年年报手工提取值（列式，一行 = 年报表格一行）
    - data/tables/bank_01578_ar_manual.json   同上（天津银行 2012—2025）
    - data/tables/bank_06138_ar_manual.json   同上（哈尔滨银行 2009—2025，源自 13 份 H 股年报；
      2018 年起 IFRS 9 且未重述比较期，永续债计入其他权益工具、100 亿转股协议存款在客户存款附注内）

输出（data/ 下的 *.json 不落盘，原文存 MySQL json_file 表，键照旧是下列路径）：
    data/raw/em_<reportName>_<code>.json    原始响应（缓存；--refresh 重新拉取）
    data/tables/bank_<code>_annual.json     整理后的逐年序列 + 前十股东 + 分红 + 元信息

用法：
    python data/extract/fetch_bank_financials.py            # 使用缓存（缺失才请求）
    python data/extract/fetch_bank_financials.py --refresh  # 强制重新拉取
    python data/extract/fetch_bank_financials.py 600036     # 只处理指定代码
"""

from __future__ import annotations

import argparse
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from _common import (
    API, API_HK, HEADERS, OUT_DIR, RAW_DIR, ROOT, annual_rows, jsonstore, pick, request_json, request_page,
)
from _common import cached as _cached


def cached(report_name, code, filt, refresh, **kw):
    """银行这几张表结果常超 200 行（如 RPT_F10_EH_HOLDERS count=315），一律整包重取。"""
    return _cached(report_name, code, filt, refresh, full=True, **kw)


# 代码 -> (交易所后缀, 简称, 机构类型)
# 机构类型按监管口径分组，供同业对比按组取色/分屏：国有大行 / 股份行 / 城商行 / 农商行
BANKS = {
    # 国有大行（工农中建交邮，前四家即「四大行」）
    "601398": ("SH", "工商银行", "国有大行"),
    "601288": ("SH", "农业银行", "国有大行"),
    "601988": ("SH", "中国银行", "国有大行"),
    "601939": ("SH", "建设银行", "国有大行"),
    "601328": ("SH", "交通银行", "国有大行"),
    "601658": ("SH", "邮储银行", "国有大行"),
    # 股份行（全部9家A股上市）
    "600036": ("SH", "招商银行", "股份行"),
    "601166": ("SH", "兴业银行", "股份行"),
    "600000": ("SH", "浦发银行", "股份行"),
    "601998": ("SH", "中信银行", "股份行"),
    "600016": ("SH", "民生银行", "股份行"),
    "000001": ("SZ", "平安银行", "股份行"),
    "600015": ("SH", "华夏银行", "股份行"),
    "601818": ("SH", "光大银行", "股份行"),
    "601916": ("SH", "浙商银行", "股份行"),
    # 城商行（全部17家A股上市）
    "601169": ("SH", "北京银行", "城商行"),
    "601229": ("SH", "上海银行", "城商行"),
    "600919": ("SH", "江苏银行", "城商行"),
    "002142": ("SZ", "宁波银行", "城商行"),
    "601009": ("SH", "南京银行", "城商行"),
    "601838": ("SH", "成都银行", "城商行"),
    "600926": ("SH", "杭州银行", "城商行"),
    "601187": ("SH", "厦门银行", "城商行"),
    "002936": ("SZ", "郑州银行", "城商行"),
    "002948": ("SZ", "青岛银行", "城商行"),
    "601577": ("SH", "长沙银行", "城商行"),
    "002966": ("SZ", "苏州银行", "城商行"),
    "601963": ("SH", "重庆银行", "城商行"),
    "601665": ("SH", "齐鲁银行", "城商行"),
    "601997": ("SH", "贵阳银行", "城商行"),
    "600928": ("SH", "西安银行", "城商行"),
    "001227": ("SZ", "兰州银行", "城商行"),
    # 农商行（全部10家A股上市）
    "601077": ("SH", "渝农商行", "农商行"),
    "601825": ("SH", "沪农商行", "农商行"),
    "601128": ("SH", "常熟银行", "农商行"),
    "002958": ("SZ", "青农商行", "农商行"),
    "600908": ("SH", "无锡银行", "农商行"),
    "002807": ("SZ", "江阴银行", "农商行"),
    "601860": ("SH", "紫金银行", "农商行"),
    "002839": ("SZ", "张家港行", "农商行"),
    "601528": ("SH", "瑞丰银行", "农商行"),
    "603323": ("SH", "苏农银行", "农商行"),
}

# 纯 H 股上市银行：无 A 股年报，A 股 F10 模板（RPT_F10_FINANCE_B*）查不到，只能走港股 F10
# + 年报手工提取覆盖层。项目规则「A/H 都有时优先取 A 股年报」在这里不适用（本就没有 A 股年报），
# 但输出的 source/caliber_note 必须写明数据来自 H 股年报。
BANKS_HK = {
    "01916": ("HK", "江西银行", "城商行"),
    "01578": ("HK", "天津银行", "城商行"),
    "06138": ("HK", "哈尔滨银行", "城商行"),
}

# 港股 F10 主要指标（RPT_HKF10_FN_MAININDICATOR）-> 与 A 股输出字段名对齐，便于同图共用 key。
# 这几家行年报均以人民币编制，接口金额即人民币原值（CURRENCY 写 HKD 是误标），可与 A 股行直接比。
# 只取年报正文摘要表里没有、或与年报口径一致的字段；重叠字段以年报覆盖层为准（见 build_bank_hk）。
HK_MAIN_FIELDS = {
    "interest_ni": "NET_INTEREST_INCOME",
    "fee_ni": "FEE_COMMISSION_INCOME",
    "operate_income": "OPERATE_INCOME",
    "operate_profit": "OPERATE_PROFIT",       # 年报摘要表无此行，只由港股 F10 提供
    "total_profit": "PRETAX_PROFIT",
    "parent_netprofit": "HOLDER_PROFIT",
    "total_assets": "TOTAL_ASSETS",
    "total_liabilities": "TOTAL_LIABILITIES",
    "parent_equity": "TOTAL_PARENT_EQUITY",
    "netcash_operate": "NETCASH_OPERATE",     # 年报摘要表无现金流量行，只由港股 F10 提供
    "netcash_invest": "NETCASH_INVEST",
    "netcash_finance": "NETCASH_FINANCE",
    "op_cf_per_share": "PER_NETCASH_OPERATE",
    "basic_eps": "BASIC_EPS",
    "total_share": "ISSUED_COMMON_SHARES",    # 各年回填当前股数，上市前各年由年报覆盖层纠正
}
# 未采用：*_YOY / *_QOQ（同比口径与年报自算不一致）、PE_TTM/PB_TTM/TOTAL_MARKET_CAP（时点估值，
# 非年报数）、DPS_HKD（快照值，2015—2024 各行同为 0.0807219）、LOAN_DEPOSIT（2025 年 96.61%，
# 与年报存贷比 90.85%（贷款总额 ÷ 吸收存款）对不上，接口口径不明，故存贷比取年报覆盖层值）。

STATEMENTS = {
    "income": "RPT_F10_FINANCE_BINCOME",
    "balance": "RPT_F10_FINANCE_BBALANCE",
    "cashflow": "RPT_F10_FINANCE_BCASHFLOW",
    "main": "RPT_F10_FINANCE_MAINFINADATA",
}

# 从各报表里取用的字段（键 = 输出字段名，值 = 接口字段名）
INCOME_FIELDS = {
    "interest_ni": "INTEREST_NI",
    "fee_ni": "FEE_COMMISSION_NI",
    "operate_income": "OPERATE_INCOME",
    "operate_tax": "OPERATE_TAX_ADD",
    "manage_expense": "BUSINESS_MANAGE_EXPENSE",
    "credit_impairment": "CREDIT_IMPAIRMENT_LOSS",
    "asset_impairment": "ASSET_IMPAIRMENT_LOSS",
    "other_business_cost": "OTHER_BUSINESS_COST",
    "operate_profit": "OPERATE_PROFIT",
    "total_profit": "TOTAL_PROFIT",
    "income_tax": "INCOME_TAX",
    "netprofit": "NETPROFIT",
    "parent_netprofit": "PARENT_NETPROFIT",
    "minority_interest": "MINORITY_INTEREST",
    "basic_eps": "BASIC_EPS",
    "oci": "OTHER_COMPRE_INCOME",
    "opinion_type": "OPINION_TYPE",
}

BALANCE_FIELDS = {
    "total_assets": "TOTAL_ASSETS",
    "loan_advance": "LOAN_ADVANCE",
    "cash_deposit_pbc": "CASH_DEPOSIT_PBC",
    "deposit_interbank": "DEPOSIT_INTERBANK",
    "lend_fund": "LEND_FUND",
    "buy_resale": "BUY_RESALE_FINASSET",
    # 金融投资的组成部分（不同银行披露模板不同，生成脚本按存在的字段组合，避免重复计入）
    "trade_finasset": "TRADE_FINASSET_NOTFVTPL",
    "creditor_invest": "CREDITOR_INVEST",
    "other_creditor_invest": "OTHER_CREDITOR_INVEST",
    "other_equity_invest": "OTHER_EQUITY_INVEST",
    "fvtpl_finasset": "FVTPL_FINASSET",
    "amortize_cost_finasset": "AMORTIZE_COST_FINASSET",
    "fvtoci_finasset": "FVTOCI_FINASSET",
    "total_liabilities": "TOTAL_LIABILITIES",
    "accept_deposit": "ACCEPT_DEPOSIT",
    "loan_pbc": "LOAN_PBC",
    "iofi_deposit": "IOFI_DEPOSIT",
    "borrow_fund": "BORROW_FUND",
    "sell_repo": "SELL_REPO_FINASSET",
    "bond_payable": "BOND_PAYABLE",
    "total_equity": "TOTAL_EQUITY",
    "parent_equity": "TOTAL_PARENT_EQUITY",
    "minority_equity": "MINORITY_EQUITY",
    "share_capital": "SHARE_CAPITAL",
}

CASHFLOW_FIELDS = {
    "netcash_operate": "NETCASH_OPERATE",
    "netcash_invest": "NETCASH_INVEST",
    "netcash_finance": "NETCASH_FINANCE",
}

MAIN_FIELDS = {
    "total_deposits": "TOTALDEPOSITS",          # 存款总额（元）
    "gross_loans": "GROSSLOANS",                # 贷款总额（元）
    "ltd_ratio": "LTDRR",                       # 存贷比 %
    "car": "NEWCAPITALADER",                    # 资本充足率 %
    "cet1": "HXYJBCZL",                         # 核心一级资本充足率 %
    "tier1": "FIRST_ADEQUACY_RATIO",            # 一级资本充足率 %
    "npl_ratio": "NONPERLOAN",                  # 不良贷款率 %
    "provision_coverage": "BLDKBBL",            # 拨备覆盖率 %
    "loan_provision_ratio": "LOAN_PROVISION_RATIO",  # 拨贷比 %
    "nim": "NET_INTEREST_MARGIN",               # 净利息收益率 %
    "nis": "NET_INTEREST_SPREAD",               # 净利差 %
    "roe_weighted": "ROEJQ",                    # 加权平均 ROE %
    "bps": "BPS",                               # 每股净资产
    "eps": "EPSJB",                             # 基本每股收益
    "op_cf_per_share": "MGJYXJJE",              # 每股经营现金流
    "npl_amount": "NON_PERFORMING_LOAN",        # 不良贷款额（元）
    "overdue_loans": "OVERDUE_LOANS",           # 逾期贷款（元）
    "lcr": "LIQUIDITY_COVERAGE_RATIO",          # 流动性覆盖率 %
    "nsfr": "NET_FUNDING_RATIO",                # 净稳定资金比例 %
    "leverage_ratio": "CAPITAL_LEVERAGE_RATIO", # 杠杆率 %
    "staff_num": "STAFF_NUM",                   # 员工人数
    "total_share": "TOTAL_SHARE",               # 总股本
}


def build_holder_num(rows: list[dict]) -> list[list]:
    """逐披露期的股东户数 -> [披露日, 股东总数, A 股股东数, H 股股东数]（升序）。

    口径：HOLDER_TOTAL_NUM 是该期定期报告披露的股东总数（A 股上市公司口径，A+H 行含 H 股
    登记股东）；HOLDER_A_NUM / HOLDER_H_NUM 只有少数期次拆分披露，其余为 None，前端留空断线。
    表里还混着上市首日等非报告期快照（601077 2019-10-29 的 948,725 户），保留——那正是打新
    账户尚未离场的峰值，是户数曲线最有信息量的一个点。
    """
    out: dict[str, list] = {}
    for r in rows:
        date = (r.get("END_DATE") or "")[:10]
        total = r.get("HOLDER_TOTAL_NUM")
        if not date or total is None:
            continue
        out[date] = [date, int(total),
                     int(r["HOLDER_A_NUM"]) if r.get("HOLDER_A_NUM") else None,
                     int(r["HOLDER_H_NUM"]) if r.get("HOLDER_H_NUM") else None]
    return [out[d] for d in sorted(out)]


def build_concentration(holder_rows: list[dict]) -> list[dict]:
    """按报告期汇总第一大 / 前三大 / 前十大股东持股比例（占总股本 %）。

    口径陷阱（都在真实数据里踩到过，改动前先看这几条）：
      · IS_REPORT="0" 的行是事件型快照（如 601077 2022-12-22 过户日只有 4 行），
        算不出前十大合计，整期剔除。
      · HOLDER_RANK 会重复：同一股东被按股份类型拆成两行时共用一个名次
        （601398 名次 [1,1,3..10]、600036 三行同为 10），所以先按股东名称合并比例，
        再取最大 / 前三 / 全部之和，不能直接按名次取。
      · 少数期次接口漏掉了压倒性的第一大股东（已核对：601988 2007-09-30 缺中央汇金
        67.49%，前十大只剩 29.7%，而相邻期为 96%+；601328 2007-09-30 缺 HKSCC 代理人，
        前十大 62.01% vs 前后 72%）。判据不能用"离群值"——601328 2010-06-30 的 67.02%
        是真实的股权结构变化。这里用"前后两期都在、持股 ≥5% 的股东本期整个消失，
        且本期前十大合计比前后两期都低了该股东权重的一半以上"定位缺行期，整期跳过
        （连线断开而不是插值）。后半个条件同时放过了改名期：汇金在 F10 里从"汇金公司"
        改称"中央汇金投资有限责任公司"，按名称比对会误判成"股东消失"，但合计没塌。
    """
    by_date: dict[str, dict[str, float]] = {}
    for r in holder_rows:
        if (r.get("IS_REPORT") or "") != "1":
            continue
        rank = r.get("HOLDER_RANK")
        if rank is None or rank > 10:
            continue
        date = (r.get("END_DATE") or "")[:10]
        name = (r.get("HOLDER_NAME") or "").strip()
        if not date or not name:
            continue
        agg = by_date.setdefault(date, {})
        agg[name] = round(agg.get(name, 0.0) + (r.get("HOLD_NUM_RATIO") or 0.0), 6)

    dates = sorted(by_date)
    # 前十大不齐（不足 10 行 rank≤10）的期次直接不出点，避免合计偏低
    ok = [d for d in dates if len(by_date[d]) and sum(1 for r in holder_rows
          if (r.get("END_DATE") or "")[:10] == d and (r.get("IS_REPORT") or "") == "1"
          and (r.get("HOLDER_RANK") or 99) <= 10) >= 10]

    out: list[dict] = []
    for i, d in enumerate(ok):
        agg = by_date[d]
        prev = by_date.get(ok[i - 1]) if i > 0 else None
        nxt = by_date.get(ok[i + 1]) if i + 1 < len(ok) else None
        if prev and nxt:
            big = {n for n, v in prev.items() if v >= 5} & {n for n, v in nxt.items() if v >= 5}
            gone = big - set(agg)
            if gone:
                weight = max(min(prev[n], nxt[n]) for n in gone)
                near = min(sum(prev.values()), sum(nxt.values()))
                if sum(agg.values()) <= near - weight / 2:
                    continue    # 大股东缺行且合计跟着塌下来 —— 接口丢数据，整期跳过
        vals = sorted(agg.values(), reverse=True)
        top1_name = max(agg, key=lambda n: agg[n])
        # 剔除「香港中央结算」名义持有人后的第一大 / 前三大（占总股本 %）：
        # 香港中央结算（代理人）代持全部 H 股、香港中央结算有限公司代持沪/深股通，
        # 都是名义持有人而非实益股东，剔除后才看得出真正的第一 / 前三大实益股东。
        # 两个账户名称均含「香港中央结算」，用子串判定一并剔除。
        ex = {n: v for n, v in agg.items() if "香港中央结算" not in n}
        rec = {
            "date": d,
            "top1": round(vals[0], 2),
            "top3": round(sum(vals[:3]), 2),
            "top10": round(sum(vals), 2),
            "top1_name": top1_name,
        }
        if ex:
            ex_vals = sorted(ex.values(), reverse=True)
            rec["top1_ex"] = round(ex_vals[0], 2)
            rec["top3_ex"] = round(sum(ex_vals[:3]), 2)
            rec["top1_ex_name"] = max(ex, key=lambda n: ex[n])
        out.append(rec)
    return out


def build_bank(code: str, refresh: bool) -> dict:
    suffix, name, tier = BANKS[code]
    secucode = f"{code}.{suffix}"
    filt = f'(SECUCODE="{secucode}")'
    print(f"[fetch] {name} {secucode} ({tier})")

    payloads = {key: cached(rn, code, filt, refresh) for key, rn in STATEMENTS.items()}
    rows = {key: annual_rows(p) for key, p in payloads.items()}

    years = sorted(set().union(*[set(r) for r in rows.values()]))
    annual: dict[str, dict] = {}
    for y in years:
        rec: dict = {}
        for key, fields in (("income", INCOME_FIELDS), ("balance", BALANCE_FIELDS),
                            ("cashflow", CASHFLOW_FIELDS), ("main", MAIN_FIELDS)):
            row = rows[key].get(y)
            if row:
                rec.update(pick(row, fields))
        annual[y] = rec

    # ── 派生指标：贷款减值准备余额、核销净额、不良生成额/率 ──
    # 减值损失科目回退：工行等个别行 2018–2022 的减值在 F10 模板里仍挂「资产减值损失」，
    # 「信用减值损失」要到 2023 才出现（口径无差异，纯模板映射差异）。这类行（首个
    # 信用减值年份晚于 2019）在 2018 起的年份缺失时回退取资产减值损失；
    # 首个信用减值年份在 2017–2019 的行不回退——它们 2018/2019 的资产减值损失是旧准则
    # 数值，拆不出贷款部分，回退会破坏不良生成率自 2018 年起可比的基准。
    credit_years = [y for y in years if annual[y].get("credit_impairment") is not None]
    allow_asset_fallback = bool(credit_years) and min(credit_years) > "2019"

    prev_allowance: float | None = None
    prev_npl: float | None = None
    prev_gross: float | None = None
    for y in years:
        rec = annual[y]
        npl = rec.get("npl_amount")
        pc = rec.get("provision_coverage")
        gl = rec.get("gross_loans")
        lpr = rec.get("loan_provision_ratio")
        ci = rec.get("credit_impairment")
        if ci is None and allow_asset_fallback and y >= "2018":
            ci = rec.get("asset_impairment")

        # 贷款减值准备余额 = 不良余额 × 拨备覆盖率 / 100（优先）或 贷款总额 × 拨贷比 / 100
        if npl and pc:
            allowance = npl * pc / 100
        elif gl and lpr:
            allowance = gl * lpr / 100
        else:
            allowance = None
        rec["loan_loss_allowance"] = allowance

        # 核销净额 = 期初准备 + 本期计提 − 期末准备
        if prev_allowance is not None and allowance is not None and ci is not None:
            rec["net_charge_off"] = prev_allowance + ci - allowance
        else:
            rec["net_charge_off"] = None

        # 不良生成额 = 期末不良 − 期初不良 + 核销净额
        nco = rec["net_charge_off"]
        if npl is not None and prev_npl is not None and nco is not None:
            rec["npl_formation"] = npl - prev_npl + nco
        else:
            rec["npl_formation"] = None

        # 不良生成率 = 不良生成额 / 期初贷款总额 × 100（%）
        formation = rec["npl_formation"]
        if formation is not None and prev_gross and prev_gross > 0:
            rec["npl_formation_rate"] = round(formation / prev_gross * 100, 4)
        else:
            rec["npl_formation_rate"] = None

        # 权益资产比：股东权益合计 ÷ 总资产（= 1 − 资产负债率 = 1/权益乘数），衡量财务杠杆。
        # total_equity 含少数股东权益（非归母口径），与保险五家 A 股口径一致。
        te, ta = rec.get("total_equity"), rec.get("total_assets")
        rec["equity_asset_ratio"] = round(te / ta * 100, 4) if te and ta else None

        prev_allowance = allowance
        prev_npl = npl
        prev_gross = gl

    # 历年分红：按利润分配方案归属的报告年度（REPORT_DATE 年份）累加每 10 股派现（含税），
    # 同一年度可能有中期 + 末期两条记录（如 2025 起），按年度合计。
    bonus_payload = cached("RPT_SHAREBONUS_DET", code, filt, refresh,
                           sort_col="PLAN_NOTICE_DATE", page_size=100)
    bonus_rows = (bonus_payload.get("result") or {}).get("data") or []
    dividend_per10: dict[str, float] = {}
    for r in bonus_rows:
        if r.get("ASSIGN_PROGRESS") != "实施分配":
            continue
        amt = r.get("PRETAX_BONUS_RMB")
        rd = (r.get("REPORT_DATE") or "")[:4]
        if amt is None or not rd:
            continue
        dividend_per10[rd] = round(dividend_per10.get(rd, 0.0) + amt, 4)

    holders_payload = cached("RPT_F10_EH_HOLDERS", code, filt, refresh,
                             sort_col="END_DATE", page_size=200)
    holder_rows = (holders_payload.get("result") or {}).get("data") or []
    # 取最近一个年报期（12-31）的前十大股东，与页面「年报口径」一致
    year_ends = [d for d in ((r.get("END_DATE") or "")[:10] for r in holder_rows) if d.endswith("-12-31")]
    latest_end = max(year_ends) if year_ends else None
    holders = [
        {
            "rank": r.get("HOLDER_RANK"),
            "name": r.get("HOLDER_NAME"),
            "hold_num": r.get("HOLD_NUM"),
            "ratio": r.get("HOLD_NUM_RATIO"),
            "change": r.get("HOLD_NUM_CHANGE"),
            "state": r.get("HOLDER_STATE_NEW") or r.get("HOLDER_STATE"),
            "shares_type": r.get("SHARES_TYPE"),
            "total_shares": r.get("TOTAL_SHARES_NUM"),
        }
        for r in holder_rows if (r.get("END_DATE") or "")[:10] == latest_end
    ]
    holders.sort(key=lambda h: h["rank"] or 99)

    # 历年股东户数（F10 只给股东总数，A/H 拆分多数期次为空）
    holdernum_payload = cached("RPT_F10_EH_HOLDERNUM", code, filt, refresh,
                               sort_col="END_DATE", page_size=200)
    holder_num = build_holder_num((holdernum_payload.get("result") or {}).get("data") or [])

    return {
        "code": code,
        "secucode": secucode,
        "name": name,
        "tier": tier,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "source": "东方财富公司数据接口（取值源自各期年度报告，合并口径）",
        "unit_note": "金额字段单位为元；比率字段单位为 %",
        "annual": annual,
        "holders_end_date": latest_end,
        "holders": holders,
        # 逐报告期的持股集中度（第一大/前三大/前十大），供股东页集中度图使用
        "holder_concentration": build_concentration(holder_rows),
        # 逐披露期的股东户数，供股东页股东户数图使用（无手工年报覆盖层的行走这份）
        "holder_num": holder_num,
        "dividend_per10": dividend_per10,
    }


def load_ar_manual(code: str) -> dict:
    """读取年报手工提取覆盖层，把列式 series 摊平成 {年份: {字段: 值}}，金额由百万元换成元。"""
    path = OUT_DIR / f"bank_{code}_ar_manual.json"
    doc = jsonstore.read(path)
    if doc is None:
        raise FileNotFoundError(f"json_file 表里没有 {jsonstore.key(path)}")
    years, series = doc["years"], doc["series"]
    amount = set(doc["amount_fields"])
    annual: dict[str, dict] = {y: {} for y in years}
    for field, values in series.items():
        if len(values) != len(years):
            raise RuntimeError(f"{path.name}: series[{field}] 长度 {len(values)} ≠ years {len(years)}")
        for y, v in zip(years, values):
            if v is None:
                continue
            annual[y][field] = round(v * 1e6, 2) if field in amount else v
    return {"doc": doc, "annual": annual}


def build_bank_hk(code: str, refresh: bool) -> dict:
    """纯 H 股上市银行（江西银行 01916.HK、天津银行 01578.HK、哈尔滨银行 06138.HK）：港股 F10 主要指标 + 年报手工提取覆盖层。"""
    suffix, name, tier = BANKS_HK[code]
    secucode = f"{code}.{suffix}"
    filt = f'(SECURITY_CODE="{code}")'
    print(f"[fetch] {name} {secucode} ({tier})（港股 F10 + 年报覆盖层，金额为人民币原值）")

    payload = cached("RPT_HKF10_FN_MAININDICATOR", code, filt, refresh, api=API_HK)
    # 接口把中期/三季与年报混排（DATE_TYPE_CODE 作查询参数无效），annual_rows 只留 12-31 行
    annual = {y: pick(row, HK_MAIN_FIELDS) for y, row in annual_rows(payload).items()}

    # 年报值优先覆盖接口值：重叠字段（总资产/负债/归母权益/利息净收入…）以年报原文为准，
    # 且能纠正 total_share 在上市前各年被回填成当前股数的问题。
    manual = load_ar_manual(code)
    for y, rec in manual["annual"].items():
        annual.setdefault(y, {}).update(rec)

    for y in sorted(annual):
        rec = annual[y]
        # 减值科目跨年换名（资产减值损失 / 信用减值损失）由覆盖层给出，缺的一侧补 None 占位
        rec.setdefault("credit_impairment", None)
        rec.setdefault("asset_impairment", None)
        tp, np_, pnp = rec.get("total_profit"), rec.get("netprofit"), rec.get("parent_netprofit")
        rec["income_tax"] = round(tp - np_, 2) if tp is not None and np_ is not None else None
        rec["minority_interest"] = round(np_ - pnp, 2) if np_ is not None and pnp is not None else None

    # ── 派生指标：核销净额、不良生成额/率 ──
    # 与 19 家 A 股行的关键差别：核销取年报「贷款减值准备变动表」实测值（核销 + 转出），
    # 不用「期初准备 + 计提 − 期末准备」反推，因此不受 F10 减值科目含非贷款资产的偏差影响。
    prev_npl: float | None = None
    prev_gross: float | None = None
    for y in sorted(annual):
        rec = annual[y]
        npl, gross = rec.get("npl_amount"), rec.get("gross_loans")
        wo, to = rec.get("write_off"), rec.get("transfer_out")
        rec["net_charge_off"] = round(wo + (to or 0), 2) if wo is not None else None

        nco = rec["net_charge_off"]
        if npl is not None and prev_npl is not None and nco is not None:
            rec["npl_formation"] = round(npl - prev_npl + nco, 2)
        else:
            rec["npl_formation"] = None

        formation = rec["npl_formation"]
        if formation is not None and prev_gross:
            rec["npl_formation_rate"] = round(formation / prev_gross * 100, 4)
        else:
            rec["npl_formation_rate"] = None

        # 权益资产比：港股 F10/年报覆盖层只给归母权益，用（总资产 − 总负债）÷ 总资产
        # 反推全口径权益占比，与 19 家 A 股行「total_equity ÷ total_assets」同义。
        ta, tl = rec.get("total_assets"), rec.get("total_liabilities")
        rec["equity_asset_ratio"] = round((ta - tl) / ta * 100, 4) if ta and tl else None

        prev_npl, prev_gross = npl, gross

    doc = manual["doc"]
    return {
        "code": code,
        "secucode": secucode,
        "name": name,
        "tier": tier,
        "currency": "CNY",
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "source": ("① 东方财富港股公司数据接口（主要指标） RPT_HKF10_FN_MAININDICATOR（各期年报数）提供"
                   "现金流量、营业利润、每股经营现金流；② 其余字段（含全部银行监管指标）取自"
                   f"{name}历年 H 股年度报告原文，见 data/tables/bank_{code}_ar_manual.json。"
                   f"{name}仅在港交所上市（{secucode}），无 A 股年报，因此不适用"
                   "「A/H 都有时优先取 A 股年报」的取数规则——本行序列全部为 H 股年报来源。"),
        "unit_note": "金额字段单位为元；比率字段单位为 %（ltd_ratio 为小数，与 A 股各行一致）",
        # 各行口径说明写在自己的 bank_<code>_ar_manual.json 里，跟数据同源同版本
        "caliber_note": doc.get("caliber_note"),
        "annual": annual,
        "holders_end_date": doc.get("holders_end_date"),
        "holders": doc.get("holders", []),
        "holders_note": doc.get("holders_note"),
        "holder_count": doc.get("holder_count"),
        "dividend_per10": doc.get("dividend_per10", {}),
        "dividend_note": doc.get("dividend_note"),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("codes", nargs="*", default=[], help="股票代码，默认全部")
    ap.add_argument("--refresh", action="store_true", help="忽略缓存重新拉取")
    args = ap.parse_args()

    codes = args.codes or list(BANKS) + list(BANKS_HK)
    unknown = [c for c in codes if c not in BANKS and c not in BANKS_HK]
    if unknown:
        raise SystemExit(f"未知代码：{unknown}；已支持 {list(BANKS) + list(BANKS_HK)}")

    for code in codes:
        data = build_bank_hk(code, args.refresh) if code in BANKS_HK \
            else build_bank(code, args.refresh)
        out = OUT_DIR / f"bank_{code}_annual.json"
        jsonstore.write(out, data, ensure_ascii=False, indent=1)
        yrs = sorted(data["annual"])
        print(f"    -> {out.relative_to(ROOT)}  ({len(yrs)} 年，{yrs[0]}~{yrs[-1]}，"
              f"股东 {len(data['holders'])} 名 @ {data['holders_end_date']})")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:                          # noqa: BLE001
        print(f"[error] {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
