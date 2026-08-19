"""
抓取保险类上市公司的年报口径财务数据（东方财富 F10 数据接口，取值来自各期年度报告）。

数据源（datacenter-web.eastmoney.com/api/data/v1/get，reportName 为报表模板）：
    - RPT_F10_FINANCE_IINCOME       保险业利润表（年报期）
    - RPT_F10_FINANCE_IBALANCE      保险业资产负债表（年报期）
    - RPT_F10_FINANCE_ICASHFLOW     保险业现金流量表（年报期）
    - RPT_F10_FINANCE_MAINFINADATA  主要指标（含保险专项：已赚保费、综合/净投资收益率、
                                    偿付能力充足率、寿险退保率、新业务价值及其利润率等）
    - RPT_F10_EH_HOLDERS            前十名股东（含报告期内增减）
    - RPT_SHAREBONUS_DET            历年分红实施明细（每 10 股派现等）

纯 H 股险企（中国太平 00966.HK，无 A 股上市）走港股 F10（datacenter.eastmoney.com/securities/api/data/v1/get）：
    - RPT_HKF10_FN_MAININDICATOR    港股主要指标（年报 + 中期混排，需自行筛 12-31 行）
      币种陷阱：行内 CURRENCY="HKD"、IS_CNY_CODE=0，但金额已按当年年末汇率折成人民币 ——
      2025 年隐含 0.90322（年报 270.59 亿港元 → 接口 244.40 亿元）、2024 年 0.92600
      （84.32 → 78.08；总资产 17,343.42 → 16,060.7），与年末 CNY/HKD 中间价吻合，
      因此可与五家 A 股险企的人民币金额同图比较；但同比字段 *_YOY 是按港元原值算的（2025 年
      +220.93% 对应港元口径），与折算后金额自算的同比不等，不要引用。
      不提供净/总投资收益率、偿付能力充足率、新业务价值、退保率与投资资产明细科目。
      RPT_HKF10_FN_INCOME / _BALANCE 为 STD_ITEM_CODE 长表（每个科目一行）需 pivot，科目与 A 股模板
      不对应，暂未采用；_CASHFLOW 与保险专版（_INCOME_INSU/_BALANCE_INSU）接口不存在（code 9501）。
      DPS_HKD 是快照字段（2000—2024 年逐行同为 1.58），不可当逐年股息序列。
      已核验（2026-08-19，对照 2025 年度业绩公告与 2025 中期公告原文）：2025 年保险服务收入
      1,122.67 亿港元、股东应占溢利 270.59 亿港元、EPS 7.251 港元、平均净资产 ROE 27.30%，
      2024 年股东应占溢利 84.32 亿港元、总资产 17,343.42 亿港元、普通股股东应占权益 711.09 亿港元，
      折算后与接口 earned_premium / parent_netprofit / eps / roe_weighted / total_assets / bps 一致。

口径断点（画图/解读时必须标注，详见 data/tables/data_sources.txt）：
    - 2023 年起执行 IFRS17 新保险合同准则 + IFRS9 新金融工具准则：退保金、赔付支出、
      提取保险责任准备金、手续费及佣金支出、分保相关科目在 2022 年止；
      「保险合同负债」未进入本模板的资产负债表字段，2023 年起负债只能看 TOTAL_LIABILITIES。
    - 2022 年（中国人寿含 2023 年）是接口的新旧准则混排年：合计项与每股指标已被后一年年报的
      重述可比数覆盖（operate_income / earned_premium / parent_netprofit / total_assets /
      eps / roe_weighted），而同一行的明细科目仍是当年旧准则原披露值
      （surrender_value 退保金、compensate_expense 赔付支出、fee_commission_expense
      手续费及佣金支出、policy_bonus_expense 保单红利、insurance_contract_reserve 保险合同准备金），
      main_earned_premium（MAINFINADATA 的已赚保费）与 bps 也停留在原披露值
      —— 同一年度内两种口径并存，"收入-支出=营业利润"只在重述侧成立。
      已用中国平安核实：2022 年报原披露营业收入 1,110,568 百万元、已赚保费 742,418、
      归母净利润 83,774、EPS 4.80、加权 ROE 10.1%、每股净资产 46.97；
      接口的 operate_income 880,355 / earned_premium 525,981 / parent_netprofit 111,008 /
      eps 6.36 / roe_weighted 13.2 出自《基于新保险合同准则编制的 2022 年财务信息》
      (2023-07-19) 的重述数，而 main_earned_premium 742,418、bps 46.97、退保金 54,102、
      赔付支出 282,122、手续费及佣金支出 70,354 与 2022 年报原文一致。
      同期 extract_insurance_reserve=78,000,000 也不是年报的「提取保险责任准备金」262,301 百万元，
      而是紧邻一行的「提取保费准备金」(78) 百万元，不可当准备金提取额使用。
    - 2018 年起金融资产三分类：可供出售/持有至到期被债权投资、其他债权投资、其他权益投资替代。
    - 偿付能力充足率 2016 年切换偿二代、2022 年切换偿二代二期，前后不可直接比较。
    - 中国平安合并平安银行，资产负债表出现吸收存款/发放贷款，总资产与 ROA 不宜与纯保险公司直接对比。

已核验（2026-08-18，对照 data/raw/annual_<code>_2025.txt，按章节语义通读而非 grep）：
    五家 2025 年度的营业收入/保险服务收入/归母净利润/总资产/股东权益合计/综合偿付能力充足率/
    净与总投资收益率/新业务价值/新业务价值率/加权 ROE/EPS/BPS/员工数/总股本/退保率共 84 项，
    与 A 股年报原文逐项一致，无数值偏差；中国人保 nbv_rate 为空经确认系年报确未披露价值率。

输出：
    data/raw/em_<reportName>_<code>.json       原始响应（缓存；--refresh 重新拉取）
    data/tables/insurer_<code>_annual.json     整理后的逐年序列 + 前十股东 + 分红 + 元信息

用法：
    python data/extract/fetch_insurer_financials.py            # 使用缓存（缺失才请求）
    python data/extract/fetch_insurer_financials.py --refresh  # 强制重新拉取
    python data/extract/fetch_insurer_financials.py 601318     # 只处理指定代码
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "tables"

API = "https://datacenter-web.eastmoney.com/api/data/v1/get"
API_HK = "https://datacenter.eastmoney.com/securities/api/data/v1/get"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Referer": "https://data.eastmoney.com/",
    "Accept-Encoding": "identity",
}

# 代码 -> (交易所后缀, 简称)；A+H 两地上市公司统一取 A 股年报口径
INSURERS = {
    "601318": ("SH", "中国平安"),
    "601628": ("SH", "中国人寿"),
    "601601": ("SH", "中国太保"),
    "601336": ("SH", "新华保险"),
    "601319": ("SH", "中国人保"),
}

# 纯 H 股上市险企：无 A 股年报，只能走港股 F10（RPT_HKF10_*）；年报以港元编制，
# 但接口返回的金额已按各年年末汇率折成人民币（见 HK_MAIN_FIELDS 上方的币种陷阱说明）
INSURERS_HK = {
    "00966": ("HK", "中国太平"),
}

STATEMENTS = {
    "income": "RPT_F10_FINANCE_IINCOME",
    "balance": "RPT_F10_FINANCE_IBALANCE",
    "cashflow": "RPT_F10_FINANCE_ICASHFLOW",
    "main": "RPT_F10_FINANCE_MAINFINADATA",
}

# 从各报表里取用的字段（键 = 输出字段名，值 = 接口字段名）
INCOME_FIELDS = {
    "operate_income": "OPERATE_INCOME",
    "earned_premium": "EARNED_PREMIUM",              # 已赚保费 / 保险服务收入（2023 起）
    "reinsure_income": "REINSURE_INCOME",            # 分保费收入
    "bank_interest_ni": "BANK_INTEREST_NI",          # 银行业务利息净收入（平安）
    "uninsurance_cni": "UNINSURANCE_CNI",            # 非保险业务手续费及佣金净收入
    "invest_income": "INVEST_INCOME",
    "invest_joint_income": "INVEST_JOINT_INCOME",    # 对联营合营企业投资收益
    "fairvalue_change": "FAIRVALUE_CHANGE",
    "exchange_income": "EXCHANGE_INCOME",
    "other_business_income": "OTHER_BUSINESS_INCOME",
    "operate_expense": "OPERATE_EXPENSE",
    "surrender_value": "SURRENDER_VALUE",            # 退保金（2022 年止）
    "compensate_expense": "COMPENSATE_EXPENSE",      # 赔付支出（2022 年止）
    "extract_insurance_reserve": "EXTRACT_INSURANCE_RESERVE",  # 提取保险责任准备金（2022 年止）
    "policy_bonus_expense": "POLICY_BONUS_EXPENSE",  # 保单红利支出
    "reinsure_expense": "REINSURE_EXPENSE",          # 分保费用
    "fee_commission_expense": "FEE_COMMISSION_EXPENSE",  # 手续费及佣金支出（2022 年止）
    "manage_expense": "BUSINESS_MANAGE_EXPENSE",
    "interest_expense": "INTEREST_EXPENSE",
    "other_business_cost": "OTHER_BUSINESS_COST",
    "credit_impairment": "CREDIT_IMPAIRMENT_LOSS",
    "asset_impairment": "ASSET_IMPAIRMENT_LOSS",
    "operate_tax": "OPERATE_TAX_ADD",
    "operate_profit": "OPERATE_PROFIT",
    "total_profit": "TOTAL_PROFIT",
    "income_tax": "INCOME_TAX",
    "netprofit": "NETPROFIT",
    "parent_netprofit": "PARENT_NETPROFIT",
    "deduct_parent_netprofit": "DEDUCT_PARENT_NETPROFIT",
    "minority_interest": "MINORITY_INTEREST",
    "basic_eps": "BASIC_EPS",
    "other_compre_income": "OTHER_COMPRE_INCOME",
    "total_compre_income": "TOTAL_COMPRE_INCOME",
    "opinion_type": "OPINION_TYPE",
}

BALANCE_FIELDS = {
    "total_assets": "TOTAL_ASSETS",
    "monetaryfunds": "MONETARYFUNDS",
    "time_deposit": "TIME_DEPOSIT",
    "buy_resale": "BUY_RESALE_FINASSET",
    # 金融资产：2018 年起为三分类，之前为可供出售 / 持有至到期 / 交易性
    "trade_finasset": "TRADE_FINASSET_NOTFVTPL",
    "creditor_invest": "CREDITOR_INVEST",
    "other_creditor_invest": "OTHER_CREDITOR_INVEST",
    "other_equity_invest": "OTHER_EQUITY_INVEST",
    "fvtpl_finasset": "FVTPL_FINASSET",
    "fvtoci_finasset": "FVTOCI_FINASSET",
    "amortize_cost_finasset": "AMORTIZE_COST_FINASSET",
    "available_sale_finasset": "AVAILABLE_SALE_FINASSET",
    "hold_maturity_invest": "HOLD_MATURITY_INVEST",
    "creditor_plan_invest": "CREDITOR_PLAN_INVEST",  # 债权计划投资
    "long_equity_invest": "LONG_EQUITY_INVEST",
    "invest_realestate": "INVEST_REALESTATE",
    "insured_pledge_loan": "INSURED_PLEDGE_LOAN",    # 保户质押贷款
    "premium_rece": "PREMIUM_RECE",                  # 应收保费（2022 年止）
    "reinsure_rece": "REINSURE_RECE",
    "ind_acc_asset": "IND_ACC_ASSET",                # 独立账户资产
    "fixed_asset": "FIXED_ASSET",
    "defer_tax_asset": "DEFER_TAX_ASSET",
    "accept_deposit": "ACCEPT_DEPOSIT",              # 吸收存款（平安合并平安银行）
    "loan_advance": "LOAN_ADVANCE",                  # 发放贷款（同上）
    "total_liabilities": "TOTAL_LIABILITIES",
    "insurance_contract_reserve": "INSURANCE_CONTRACT_RESERVE",  # 保险合同准备金（2022 年止）
    "uc_reserve": "UC_RESERVE",                      # 未到期责任准备金
    "ud_reserve": "UD_RESERVE",                      # 未决赔款准备金
    "ld_reserve": "LD_RESERVE",                      # 寿险责任准备金
    "hd_reserve": "HD_RESERVE",                      # 长期健康险责任准备金
    "insured_deposit_invest": "INSURED_DEPOSIT_INVEST",  # 保户储金及投资款
    "sell_repo": "SELL_REPO_FINASSET",
    "bond_payable": "BOND_PAYABLE",
    "subbond_payable": "SUBBOND_PAYABLE",
    "ind_acc_liab": "IND_ACC_LIAB",
    "total_equity": "TOTAL_EQUITY",
    "parent_equity": "TOTAL_PARENT_EQUITY",
    "minority_equity": "MINORITY_EQUITY",
    "share_capital": "SHARE_CAPITAL",
    "general_risk_reserve": "GENERAL_RISK_RESERVE",
    "unassign_profit": "UNASSIGN_RPOFIT",
    "balance_oci": "OTHER_COMPRE_INCOME",            # 资产负债表其他综合收益（累计额）
}

CASHFLOW_FIELDS = {
    "receive_premium_cash": "RECEIVE_ORIGIC_PREMIUM",  # 收到原保险合同保费现金
    "pay_compensate_cash": "PAY_ORIGIC_COMPENSATE",    # 支付原保险合同赔付款项
    "netcash_operate": "NETCASH_OPERATE",
    "netcash_invest": "NETCASH_INVEST",
    "netcash_finance": "NETCASH_FINANCE",
}

MAIN_FIELDS = {
    "main_earned_premium": "EARNED_PREMIUM",     # 主要指标口径的已赚保费（元）
    "total_roi": "TOTAL_ROI",                    # 总（综合）投资收益率 %
    "net_roi": "NET_ROI",                        # 净投资收益率 %
    "solvency_ar": "SOLVENCY_AR",                # 偿付能力充足率 %
    "surrender_rate_life": "SURRENDER_RATE_LIFE",  # 寿险退保率 %
    "nbv_life": "NBV_LIFE",                      # 寿险新业务价值（元）
    "nbv_rate": "NBV_RATE",                      # 新业务价值率 %
    "roe_weighted": "ROEJQ",                     # 加权平均 ROE %
    "roa": "ZZCJLL",                             # 总资产净利率 %
    "net_margin": "XSJLL",                       # 销售净利率 %
    "debt_ratio": "ZCFZL",                       # 资产负债率 %
    "equity_multiplier": "QYCS",                 # 权益乘数
    "bps": "BPS",                                # 每股净资产
    "eps": "EPSJB",                              # 基本每股收益
    "op_cf_per_share": "MGJYXJJE",               # 每股经营现金流
    "total_revenue": "TOTALOPERATEREVE",         # 营业总收入（元）
    "main_parent_netprofit": "PARENTNETPROFIT",  # 归母净利润（元）
    "main_total_assets": "TOTAL_ASSETS_PK",      # 总资产（元）
    "main_total_equity": "TOTAL_EQUITY_PK",      # 股东权益（元）
    "main_liability": "LIABILITY",               # 总负债（元）
    "staff_num": "STAFF_NUM",                    # 员工人数
    "total_share": "TOTAL_SHARE",                # 总股本
}

# 港股 F10 主要指标（RPT_HKF10_FN_MAININDICATOR）-> 与 A 股输出字段名对齐，便于同一张图共用 key。
# 币种陷阱：行内 CURRENCY 写 "HKD"、IS_CNY_CODE 写 0，但金额其实已按当年年末汇率折成人民币
# （2025 年隐含 0.90322、2024 年 0.92600，与年末 CNY/HKD 中间价一致，已用年报原文反推核验），
# 所以可以直接与五家 A 股险企的人民币金额同图比较；而 *_YOY 同比字段是按港元原值算的，不要用。
# 港股 F10 的利润表/资产负债表（RPT_HKF10_FN_INCOME/BALANCE）是 STD_ITEM_CODE 长表，
# 需逐项 pivot 且科目名与 A 股模板不对应，暂不取；现金流量表与保险专版报表接口不存在（code 9501）。
HK_MAIN_FIELDS = {
    "operate_income": "OPERATE_INCOME",
    "earned_premium": "PREMIUM_INCOME",      # 2023 起为 IFRS17 保险服务收入，此前为接口保费收入口径
    "operate_profit": "OPERATE_PROFIT",
    "total_profit": "PRETAX_PROFIT",
    "parent_netprofit": "HOLDER_PROFIT",     # 股东应占溢利
    "total_assets": "TOTAL_ASSETS",
    "total_liabilities": "TOTAL_LIABILITIES",
    "roe_weighted": "ROE_AVG",               # 港股 F10 为平均净资产 ROE，非 A 股「加权平均」算法
    "roa": "ROA",
    "net_margin": "NET_PROFIT_RATIO",
    "debt_ratio": "DEBT_ASSET_RATIO",
    "equity_multiplier": "EQUITY_MULTIPLIER",
    "eps": "BASIC_EPS",
    "bps": "BPS",                            # 对得上「普通股股东应占权益 ÷ 已发行股数」
    "op_cf_per_share": "PER_NETCASH_OPERATE",
    "netcash_operate": "NETCASH_OPERATE",
    "netcash_invest": "NETCASH_INVEST",
    "netcash_finance": "NETCASH_FINANCE",
    "total_share": "ISSUED_COMMON_SHARES",
}
# 未采用：TOTAL_PARENT_EQUITY（2024 年折回港元为 870.7 亿，与年报「普通股股东应占权益」711.09 亿、
# 「总权益」1,223 亿都对不上，口径不明）；DPS_HKD（快照值，2000—2024 年逐行同为 1.58）。


def request_json(report_name: str, filt: str, sort_col: str = "REPORT_DATE",
                 page_size: int = 200, retries: int = 3, timeout: int = 60,
                 api: str = API) -> dict:
    url = "%s?reportName=%s&columns=ALL&filter=%s&sortColumns=%s&sortTypes=-1&pageSize=%d" % (
        api, report_name, urllib.parse.quote(filt), sort_col, page_size)
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            if not payload.get("success", True) and payload.get("result") is None:
                raise RuntimeError(payload.get("message") or "empty result")
            return payload
        except Exception as e:                      # noqa: BLE001 - 统一重试
            last_err = e
            wait = 2 ** attempt
            print(f"    [retry {attempt}/{retries}] {e}; sleep {wait}s", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"{report_name} failed after {retries} attempts: {last_err}")


def cached(report_name: str, code: str, filt: str, refresh: bool, **kw) -> dict:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"em_{report_name}_{code}.json"
    if path.exists() and not refresh:
        return json.loads(path.read_text(encoding="utf-8"))
    print(f"    [http] {report_name}")
    payload = request_json(report_name, filt, **kw)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return payload


def annual_rows(payload: dict) -> dict[str, dict]:
    """按年份聚合年报期（REPORT_DATE 为 12-31）的行。"""
    out: dict[str, dict] = {}
    for row in (payload.get("result") or {}).get("data") or []:
        rd = (row.get("REPORT_DATE") or "")[:10]
        if not rd.endswith("-12-31"):
            continue
        out.setdefault(rd[:4], row)     # 接口按日期降序，首条为最新修订版
    return out


def pick(row: dict, mapping: dict[str, str]) -> dict:
    return {k: row.get(v) for k, v in mapping.items()}

def build_insurer(code: str, refresh: bool) -> dict:
    suffix, name = INSURERS[code]
    secucode = f"{code}.{suffix}"
    filt = f'(SECUCODE="{secucode}")'
    print(f"[fetch] {name} {secucode}")

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

    # ── 派生指标 ──
    prev_assets: float | None = None
    for y in years:
        rec = annual[y]
        # 综合与净投资收益率之差：正值多来自浮盈/已实现价差，负值多为公允价值损失
        tr, nr = rec.get("total_roi"), rec.get("net_roi")
        rec["roi_spread"] = round(tr - nr, 4) if tr is not None and nr is not None else None

        # 投资资产合计：按当年披露存在的分类科目相加，避免新旧准则重复计入
        legacy = [rec.get(k) for k in ("available_sale_finasset", "hold_maturity_invest")]
        new_cls = [rec.get(k) for k in ("creditor_invest", "other_creditor_invest",
                                        "other_equity_invest")]
        parts = [rec.get("trade_finasset"), rec.get("fvtpl_finasset"),
                 rec.get("fvtoci_finasset"), rec.get("amortize_cost_finasset"),
                 rec.get("time_deposit"), rec.get("long_equity_invest"),
                 rec.get("invest_realestate")]
        parts += new_cls if any(v for v in new_cls) else legacy
        vals = [v for v in parts if v]
        rec["invest_asset_total"] = sum(vals) if vals else None

        # 归母 ROA（期初期末总资产均值），平安含银行业务不宜与纯保险公司横比
        pnp, ta = rec.get("parent_netprofit"), rec.get("total_assets")
        if pnp is not None and ta and prev_assets:
            rec["roa_avg"] = round(pnp / ((ta + prev_assets) / 2) * 100, 4)
        else:
            rec["roa_avg"] = None
        prev_assets = ta

        # 权益资产比：股东权益合计 ÷ 总资产（= 1 − 资产负债率 = 1/权益乘数），衡量财务杠杆。
        # total_equity 含少数股东权益（非归母口径）；平安含平安银行，分母被银行资产抬高。
        te = rec.get("total_equity")
        rec["equity_asset_ratio"] = round(te / ta * 100, 4) if te and ta else None

    # 历年分红：按利润分配方案归属的报告年度（REPORT_DATE 年份）累加每 10 股派现（含税），
    # 同一年度可能有中期 + 末期两条记录，按年度合计。
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

    return {
        "code": code,
        "secucode": secucode,
        "name": name,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "source": ("东方财富 F10 数据接口（各期 A 股年报合并数）。2025 年度已逐项对照五家 A 股年报"
                   "原文核验：营业收入/保险服务收入/归母净利润/总资产/股东权益/偿付能力/投资收益率/"
                   "新业务价值/ROE/EPS/BPS/员工数/总股本/退保率全部一致；2022 年（中国人寿含 2023 年）"
                   "接口为新旧准则混排行，不可直接同比，详见 data/tables/data_sources.txt"),
        "unit_note": "金额字段单位为元；比率字段单位为 %",
        "caliber_note": ("2023 年起执行 IFRS17 + IFRS9：退保金/赔付支出/提取保险责任准备金/"
                         "手续费及佣金支出/保险合同准备金等科目在 2022 年止；"
                         "偿付能力充足率 2016 年切偿二代、2022 年切偿二代二期，前后不可比。"
                         "2022 年是混排年：营业收入/保险服务收入/归母净利润/总资产/EPS/加权 ROE "
                         "已是后一年年报的新准则重述值，而同一行的退保金/赔付支出/"
                         "手续费及佣金支出/保险合同准备金以及 main_earned_premium（已赚保费）/BPS "
                         "仍是旧准则原披露值。字段名沿用接口命名，earned_premium 在 2022 年起"
                         "实为「保险服务收入」；total_equity 含少数股东权益（中国人保归母仅占 74%），"
                         "solvency_ar 主体不一（平安/太保/人保为集团，新华为寿险本级），"
                         "nbv_rate 口径不一（平安按标准保费、国寿仅个险渠道、人保不披露）"),
        "annual": annual,
        "holders_end_date": latest_end,
        "holders": holders,
        "dividend_per10": dividend_per10,
    }


def build_insurer_hk(code: str, refresh: bool) -> dict:
    """纯 H 股险企（中国太平 00966.HK）：走港股 F10 主要指标，金额已折人民币。"""
    suffix, name = INSURERS_HK[code]
    secucode = f"{code}.{suffix}"
    filt = f'(SECUCODE="{secucode}")'
    print(f"[fetch] {name} {secucode}（港股 F10，金额已按年末汇率折人民币）")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = RAW_DIR / f"em_RPT_HKF10_FN_MAININDICATOR_{code}.json"
    if raw_path.exists() and not refresh:
        payload = json.loads(raw_path.read_text(encoding="utf-8"))
    else:
        print("    [http] RPT_HKF10_FN_MAININDICATOR")
        payload = request_json("RPT_HKF10_FN_MAININDICATOR", filt, page_size=200, api=API_HK)
        raw_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    # 接口把中期与年报混在一起返回（DATE_TYPE_CODE 作为查询参数无效），只保留 12-31 行
    rows = annual_rows(payload)
    annual = {y: pick(row, HK_MAIN_FIELDS) for y, row in rows.items()}

    # 权益资产比：港股 F10 未采集股东权益，用（总资产 − 总负债）÷ 总资产 反推全口径权益占比，
    # 与五家 A 股「total_equity ÷ total_assets」同义（total_equity = 总资产 − 总负债）。
    for rec in annual.values():
        ta, tl = rec.get("total_assets"), rec.get("total_liabilities")
        rec["equity_asset_ratio"] = round((ta - tl) / ta * 100, 4) if ta and tl else None

    return {
        "code": code,
        "secucode": secucode,
        "name": name,
        "currency": "CNY",
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "source": ("东方财富港股 F10 主要指标接口 RPT_HKF10_FN_MAININDICATOR（各期年报数）。"
                   "中国太平仅在港交所上市（00966.HK），无 A 股年报，因此不适用「A/H 都有时优先取 A 股」"
                   "的取数规则；年报本身以港元编制，接口返回的金额已按各年年末汇率折成人民币"
                   "（行内 CURRENCY 写 HKD、IS_CNY_CODE 写 0 是误标，2025 年隐含 0.90322、2024 年 0.92600，"
                   "已用 2025 年报业绩公告原文反推核验）"),
        "unit_note": "金额字段单位为人民币元（接口按当年年末汇率由港元折算）；比率字段单位为 %",
        "caliber_note": ("金额已折成人民币，可与五家 A 股险企同图直接比大小；但每年用各自年末汇率折算，"
                         "太平自身的同比含汇率漂移，利润按期末价而非平均价折算。"
                         "2023 年起同步执行 IFRS17 + IFRS9，接口 2022 年行已是重述可比数："
                         "营业收入 2021 年 2,582.5→2022 年 1,081.0 亿元、保险服务收入 2,146.6→972.8 亿元，"
                         "落差是换口径不是业务下滑。"
                         "港股 F10 主要指标不提供净/总投资收益率、综合偿付能力充足率、寿险新业务价值、"
                         "寿险退保率与投资资产明细科目，这些图上没有太平序列；"
                         "roe_weighted 取接口 ROE_AVG（平均净资产口径），与 A 股「加权平均 ROE」算法不完全一致。"
                         "中国太平是控股集团，偿付能力按太平人寿/太平财险等境内子公司分别披露，集团层面无单一指标。"
                         "接口 *_YOY 同比字段是按港元原值算的（2025 年 +220.93% 为港元口径），与折算后金额"
                         "自算的同比不等，故未采集；DPS_HKD 字段为快照值（2000—2024 年各行同为 1.58），"
                         "不能当逐年股息序列用，亦未采集。"),
        "annual": annual,
        "holders_end_date": None,
        "holders": [],
        "dividend_per10": {},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("codes", nargs="*", default=[], help="股票代码，默认全部")
    ap.add_argument("--refresh", action="store_true", help="忽略缓存重新拉取")
    args = ap.parse_args()

    codes = args.codes or list(INSURERS) + list(INSURERS_HK)
    unknown = [c for c in codes if c not in INSURERS and c not in INSURERS_HK]
    if unknown:
        raise SystemExit(f"未知代码：{unknown}；已支持 {list(INSURERS) + list(INSURERS_HK)}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for code in codes:
        data = build_insurer_hk(code, args.refresh) if code in INSURERS_HK \
            else build_insurer(code, args.refresh)
        out = OUT_DIR / f"insurer_{code}_annual.json"
        out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        yrs = sorted(data["annual"])
        print(f"    -> {out.relative_to(ROOT)}  ({len(yrs)} 年，{yrs[0]}~{yrs[-1]}，"
              f"股东 {len(data['holders'])} 名 @ {data['holders_end_date']})")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:                          # noqa: BLE001
        print(f"[error] {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)



