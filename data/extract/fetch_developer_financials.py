"""
抓取头部央企房地产开发商的年报口径财务数据（东方财富 F10 数据接口，取值来自各期年度报告）。

A 股（通用行业模板，datacenter-web.eastmoney.com/api/data/v1/get）：
    - RPT_F10_FINANCE_GINCOME       利润表（年报期）
    - RPT_F10_FINANCE_GBALANCE      资产负债表（年报期）
    - RPT_F10_FINANCE_GCASHFLOW     现金流量表（年报期）
    - RPT_F10_FINANCE_MAINFINADATA  主要指标（毛利率/ROE/周转/每股/员工数等）
    - RPT_F10_EH_HOLDERS            前十名股东
    - RPT_SHAREBONUS_DET            历年分红实施明细

纯 H 股开发商（无 A 股上市）走港股 F10（datacenter.eastmoney.com/securities/api/data/v1/get）：
    - RPT_HKF10_FN_MAININDICATOR    港股主要指标（年报 + 中期混排，需自行筛 12-31 行）
      币种：接口行内一律写 CURRENCY="HKD"、IS_CNY_CODE=0，这个标记不可信。已逐家用年报
      原文（HKEXnews 年度业绩公告）反查，三家近年披露口径**都是人民币**，接口值即人民币：
        · 中国海外发展 00688：自 2019 年年报起改以**人民币**编制（2018 年及 2018-01-01
          比较数经重列），FY2024 公告「本集团收入为人民币 1,851.5 亿元」、报表栏头「人民币千元」，
          与接口 185,154,027 千一致。2018 年及以前的原始披露是港元，本脚本不再取那些年份的金额。
        · 华润置地 01109：自 2018 年年报起改以**人民币**编制（FY2018 公告把 2017 年
          预售物业已收垫款由港币 142,805,881 千重列为人民币 119,372,967 千）。
        · 中国金茂 00817：自 2016 年年报起改以**人民币**编制（FY2016 公告附注 2.2「呈列货币变更」：
          「于 2016 年 12 月 31 日，本集团将其编制综合财务报表之货币由港元改为人民币」，按 HKAS 21/
          HKAS 8 追溯重列 2015-01-01、2015-12-31 与 FY2015 比较数，收盘汇率 RMB1=HK$1.1936）。
      港股 F10 主要指标不提供资产负债表明细科目，故存货、净负债率、现金短债比、销售回款
      在这三家上仍没有序列；「已售未结」（presale）、已售未结覆盖倍数与剔预资产负债率改由
      HK_PRESALE_THOUSANDS 里硬编码的**年报原文取数**补齐，见该常量的注释。

口径提醒（详见 data/tables/data_sources.txt）：
    - 三道红线是本脚本按公开定义自算，不是年报披露值：
        剔除预收后的资产负债率 =（总负债 − 合同负债 − 预收账款）/（总资产 − 合同负债 − 预收账款）
        净负债率 =（有息负债 − 货币资金）/ 股东权益合计
        现金短债比 = 货币资金 / 短期有息负债
      有息负债取「短期借款 + 一年内到期的非流动负债 + 应付短期债券 + 长期借款 + 应付债券」，
      口径粗于年报：一年内到期的非流动负债里含租赁负债等非有息项，货币资金含预售监管资金与
      其它受限资金，故自算值与年报披露值会有偏差（招商蛇口 2025 年报披露 64.17% /
      72.46% / 1.19，本脚本自算 61.74% / 59.05% / 1.39）。永续债（PERPETUAL_BOND / OTHER_EQUITY_TOOL）
      计在权益里，未从分母剔除，这是净负债率自算值偏低的主因。
    - 2019 年起收入准则把「预收账款」重分类为「合同负债」，早年只有 ADVANCE_RECEIVABLES、
      近年只有 CONTRACT_LIAB，两者相加即可跨年连续（同一年不会重复披露大额）。
    - 华侨城 A 含文旅（主题公园）业务，招商蛇口含物业（招商积余）与园区/邮轮，
      毛利率与周转与纯住宅开发商不同质。

输出：
    data/raw/em_<reportName>_<code>.json         原始响应（缓存；--refresh 重新拉取）
    data/tables/developer_<code>_annual.json     整理后的逐年序列 + 前十股东 + 分红 + 元信息

用法：
    python data/extract/fetch_developer_financials.py            # 使用缓存（缺失才请求）
    python data/extract/fetch_developer_financials.py --refresh  # 强制重新拉取
    python data/extract/fetch_developer_financials.py 600048     # 只处理指定代码
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

# A 股上市的央企开发商：代码 -> (交易所后缀, 简称, 控股集团)
DEVELOPERS = {
    "600048": ("SH", "保利发展", "保利集团"),
    "001979": ("SZ", "招商蛇口", "招商局集团"),
    "000069": ("SZ", "华侨城A", "华侨城集团"),
}

# 纯 H 股上市的央企开发商：无 A 股年报，只能走港股 F10；currency 为**年报记账本位币**，
# 已用年报原文逐家反查（中海 2019 年起、华润 2018 年起、金茂 2016 年起均为人民币）
DEVELOPERS_HK = {
    "00688": ("HK", "中国海外发展", "中国建筑集团", "CNY"),
    "01109": ("HK", "华润置地", "华润集团", "CNY"),
    "00817": ("HK", "中国金茂", "中国中化", "CNY"),
}

STATEMENTS = {
    "income": "RPT_F10_FINANCE_GINCOME",
    "balance": "RPT_F10_FINANCE_GBALANCE",
    "cashflow": "RPT_F10_FINANCE_GCASHFLOW",
    "main": "RPT_F10_FINANCE_MAINFINADATA",
}

INCOME_FIELDS = {
    "total_operate_income": "TOTAL_OPERATE_INCOME",
    "operate_income": "OPERATE_INCOME",
    "operate_cost": "OPERATE_COST",
    "total_operate_cost": "TOTAL_OPERATE_COST",
    "operate_tax": "OPERATE_TAX_ADD",
    "sale_expense": "SALE_EXPENSE",
    "manage_expense": "MANAGE_EXPENSE",
    "finance_expense": "FINANCE_EXPENSE",
    "research_expense": "RESEARCH_EXPENSE",
    "credit_impairment": "CREDIT_IMPAIRMENT_INCOME",   # 新表列为「信用减值损失（负号）」
    "asset_impairment": "ASSET_IMPAIRMENT_INCOME",
    "invest_income": "INVEST_INCOME",
    "invest_joint_income": "INVEST_JOINT_INCOME",      # 对联营合营企业投资收益（表外项目回流）
    "fairvalue_change": "FAIRVALUE_CHANGE_INCOME",
    "other_income": "OTHER_INCOME",
    "operate_profit": "OPERATE_PROFIT",
    "total_profit": "TOTAL_PROFIT",
    "income_tax": "INCOME_TAX",
    "netprofit": "NETPROFIT",
    "parent_netprofit": "PARENT_NETPROFIT",
    "deduct_parent_netprofit": "DEDUCT_PARENT_NETPROFIT",
    "minority_interest": "MINORITY_INTEREST",
    "basic_eps": "BASIC_EPS",
    "opinion_type": "OPINION_TYPE",
}

BALANCE_FIELDS = {
    "monetaryfunds": "MONETARYFUNDS",
    "inventory": "INVENTORY",                          # 开发商的存货 = 在建 + 已完工待售
    "contract_asset": "CONTRACT_ASSET",
    "prepayment": "PREPAYMENT",
    "accounts_rece": "ACCOUNTS_RECE",
    "other_rece": "TOTAL_OTHER_RECE",                  # 其他应收款（含合作方往来，表外风险入口）
    "long_equity_invest": "LONG_EQUITY_INVEST",        # 长期股权投资（合联营即表外项目）
    "invest_realestate": "INVEST_REALESTATE",          # 投资性房地产（持有型资产）
    "fixed_asset": "FIXED_ASSET",
    "useright_asset": "USERIGHT_ASSET",
    "goodwill": "GOODWILL",
    "total_current_assets": "TOTAL_CURRENT_ASSETS",
    "total_assets": "TOTAL_ASSETS",
    "short_loan": "SHORT_LOAN",
    "short_bond_payable": "SHORT_BOND_PAYABLE",
    "note_accounts_payable": "NOTE_ACCOUNTS_PAYABLE",
    "advance_receivables": "ADVANCE_RECEIVABLES",      # 预收账款（2019 年前的售房预收）
    "contract_liab": "CONTRACT_LIAB",                  # 合同负债（2019 年起的售房预收）
    "noncurrent_liab_1year": "NONCURRENT_LIAB_1YEAR",
    "total_current_liab": "TOTAL_CURRENT_LIAB",
    "long_loan": "LONG_LOAN",
    "bond_payable": "BOND_PAYABLE",
    "lease_liab": "LEASE_LIAB",
    "total_noncurrent_liab": "TOTAL_NONCURRENT_LIAB",
    "total_liabilities": "TOTAL_LIABILITIES",
    "perpetual_bond": "PERPETUAL_BOND",                # 权益工具中的永续债
    "other_equity_tool": "OTHER_EQUITY_TOOL",
    "minority_equity": "MINORITY_EQUITY",
    "parent_equity": "TOTAL_PARENT_EQUITY",
    "total_equity": "TOTAL_EQUITY",
    "share_capital": "SHARE_CAPITAL",
    "unassign_profit": "UNASSIGN_RPOFIT",
}

CASHFLOW_FIELDS = {
    "sales_services": "SALES_SERVICES",                # 销售商品收到的现金（回款）
    "netcash_operate": "NETCASH_OPERATE",
    "netcash_invest": "NETCASH_INVEST",
    "netcash_finance": "NETCASH_FINANCE",
    "construct_long_asset": "CONSTRUCT_LONG_ASSET",
    "assign_dividend_profit": "ASSIGN_DIVIDEND_PORFIT",  # 分配股利、利润或偿付利息支付的现金
    "end_cce": "END_CCE",
}

MAIN_FIELDS = {
    "gross_margin": "XSMLL",                     # 销售毛利率 %
    "net_margin": "XSJLL",                       # 销售净利率 %
    "roe_weighted": "ROEJQ",                     # 加权平均 ROE %
    "roe_deduct": "ROEKCJQ",                     # 扣非加权 ROE %
    "roic": "ROIC",                              # 投入资本回报率 %
    "roa": "ZZCJLL",                             # 总资产净利率 %
    "debt_ratio": "ZCFZL",                       # 资产负债率 %
    "equity_multiplier": "QYCS",
    "current_ratio": "LD",                       # 流动比率
    "quick_ratio": "SD",                         # 速动比率
    "inventory_turnover": "CHZZL",               # 存货周转率（次）
    "inventory_days": "CHZZTS",                  # 存货周转天数
    "asset_turnover": "TOAZZL",                  # 总资产周转率
    "ocf_to_revenue": "JYXJLYYSR",               # 经营现金流 / 营业收入
    "eps": "EPSJB",
    "eps_deduct": "EPSKCJB",
    "bps": "BPS",
    "op_cf_per_share": "MGJYXJJE",
    "total_revenue": "TOTALOPERATEREVE",         # 营业总收入（元）
    "main_parent_netprofit": "PARENTNETPROFIT",  # 归母净利润（元）
    "main_total_assets": "TOTAL_ASSETS_PK",
    "main_total_equity": "TOTAL_EQUITY_PK",
    "main_liability": "LIABILITY",
    "staff_num": "STAFF_NUM",
    "total_share": "TOTAL_SHARE",
    "tax_rate": "TAXRATE",                       # 实际税率 %
}

# 港股 F10 主要指标 -> 与 A 股输出字段名对齐，便于同一张图共用 key
HK_MAIN_FIELDS = {
    "total_operate_income": "OPERATE_INCOME",
    "operate_income": "OPERATE_INCOME",
    "gross_profit": "GROSS_PROFIT",
    "gross_margin": "GROSS_PROFIT_RATIO",
    "net_margin": "NET_PROFIT_RATIO",
    "operate_profit": "OPERATE_PROFIT",
    "total_profit": "PRETAX_PROFIT",
    "parent_netprofit": "HOLDER_PROFIT",         # 股东应占溢利
    "total_assets": "TOTAL_ASSETS",
    "total_liabilities": "TOTAL_LIABILITIES",
    "parent_equity": "TOTAL_PARENT_EQUITY",
    "roe_weighted": "ROE_AVG",                   # 平均净资产 ROE，非 A 股「加权平均」算法
    "roa": "ROA",
    "debt_ratio": "DEBT_ASSET_RATIO",
    "equity_multiplier": "EQUITY_MULTIPLIER",
    "current_ratio": "CURRENT_RATIO",
    "eps": "BASIC_EPS",
    "bps": "BPS",
    "op_cf_per_share": "PER_NETCASH_OPERATE",
    "netcash_operate": "NETCASH_OPERATE",
    "netcash_invest": "NETCASH_INVEST",
    "netcash_finance": "NETCASH_FINANCE",
    "end_cce": "END_CASH",
    "dividend_payout": "DIVI_RATIO",             # 派息比率，小数不是 %（中海 2024 为 0.512）
    "total_share": "ISSUED_COMMON_SHARES",
}

# ── 纯 H 股三家的「已售未结蓄水池」：港股 F10 主要指标不含负债明细，逐年从 HKEXnews
# 年度业绩公告（综合财务状况表 / 其他应付款项附注）语义通读后取数，单位为**人民币千元**。
#
# 取数口径与 A 股三家的 presale =「合同负债 + 预收账款」对齐；已重列的年份取**最新重列值**
# （与 annual_rows 取最新修订版一致），括注为取数所依据的那份公告。
# 例外：金茂 2018/2019 取的是**原披露值**（合约负债 46,967,258 / 64,657,028），不是 FY2020 公告
# 因武汉华孜同一控制下合并而重列后的 47,206,477 / 64,873,929 —— 重列后的「预收款项」拆分未单独
# 披露，混用会造成同一年两个口径相加；差额 +239,219 / +216,901 千元（约 0.5%）不影响趋势。
# 只收录金额可与人民币序列同口径比较的年份：中海 2017（2018-01-01 重列列）起、华润 2017（FY2018
# 重列）起、金茂 2015 起；更早年份年报以港币编制、接口值也是港元原值，不入序列。
# 金茂能从 2015 起是因为接口的 2015 年资产负债表数已是 FY2016 年报重列后的人民币值（已核：接口
# 总资产 133,126,399 千 / 总负债 83,777,689 千 = FY2016 年报分部资料的重列 2015 年资产/负债总额，
# 而 FY2015 年报的港币原值为 158,899,671 / —），故 presale 取同一份重列列即口径一致。
# 2014 年接口值同样是重列后人民币（108,884,388 千 ≈ FY2016 三栏式的 2015-01-01 列 108,887,478 千），
# 但那一列只给「其他应付款项和应计款项」合计 11,919,535，未拆出预收款项，故 2014 仍无 presale。
HK_PRESALE_THOUSANDS = {
    # 中国海外发展：科目名 2018 年前为「预售按金」、2018 年为「合同负债」、2019 年起为「预售楼款」
    "00688": {
        "2017": 84358462,    # FY2019 公告 2018-01-01 重列列（原披露港币 77,857,359 千）
        "2018": 81268058,    # FY2019 公告 2018-12-31 重列列（原披露港币 92,984,048 千）
        "2019": 97939167,    # FY2019 公告
        "2020": 121121893,   # FY2020 公告
        "2021": 100455190,   # FY2021 公告
        "2022": 107675933,   # FY2022 公告
        "2023": 108619041,   # FY2023 公告
        "2024": 132542750,   # FY2024 公告
        "2025": 125033296,   # FY2025 公告
    },
    # 华润置地：2017 年前为「预售物业已收垫款」，2018 年起为「合约负债」
    "01109": {
        "2017": 119372967,   # FY2018 公告重列列（原披露港币 142,805,881 千）
        "2018": 193452512,   # FY2020 公告重列列（原披露 192,265,229）
        "2019": 228811678,   # FY2020 公告重列列（原披露 226,719,664）
        "2020": 232584967,   # FY2020 公告
        "2021": 212719073,   # FY2021 公告
        "2022": 225789214,   # FY2023 公告重列列（原披露 2,257.89 亿，重列把 219.8 亿转入应付账款）
        "2023": 267618392,   # FY2023 公告
        "2024": 215504946,   # FY2025 公告经重列列
        "2025": 143567782,   # FY2025 公告
    },
    # 中国金茂：预收不在表面上，藏在「其他应付款项和应计款项」附注里，
    # 取该附注的「合约负债总额 + 预收款项」（2018 年前无合约负债，只有预收款项）
    "00817": {
        "2015": 13846820,            # FY2016 年报附注 30 比较列「（重列）」（原披露港币 16,527,564）
        "2016": 28278803,            # FY2017 公告附注 30：预收款项 28,278,803
        "2017": 38928799,            # FY2017 公告附注 30：预收款项 38,928,799
        "2018": 46967258 + 124153,   # FY2019 公告附注 31 比较列
        "2019": 64657028 + 111303,   # FY2019 公告附注 31
        "2020": 81493761 + 128597,   # FY2021 公告附注 32 比较列
        "2021": 78213782 + 2551602,  # FY2021 公告附注 32
        "2022": 60147539 + 768191,   # FY2022 公告附注 33
        "2023": 55236431 + 153104,   # FY2024 公告附注 33 比较列
        "2024": 52752143 + 2962439,  # FY2025 公告附注 33 比较列
        "2025": 64197801 + 2233323,  # FY2025 公告附注 33
    },
}


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


def ssum(rec: dict, keys: tuple[str, ...]) -> float | None:
    """按 keys 求和；全为空则返回 None（区分「科目本年未披露」与「真的是 0」）。"""
    vals = [rec.get(k) for k in keys]
    got = [v for v in vals if v is not None]
    return sum(got) if got else None


def build_developer(code: str, refresh: bool) -> dict:
    suffix, name, group = DEVELOPERS[code]
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

    # ── 派生指标（三道红线为本脚本自算，非年报披露值，口径见模块 docstring）──
    prev_assets: float | None = None
    for y in years:
        rec = annual[y]
        # 售房预收：2019 年前记在预收账款、2019 年起记在合同负债，相加即跨年连续
        presale = ssum(rec, ("contract_liab", "advance_receivables"))
        rec["presale"] = presale

        ta, tl, te = rec.get("total_assets"), rec.get("total_liabilities"), rec.get("total_equity")
        # ① 剔除预收后的资产负债率（红线 70%）
        if ta and tl is not None and presale is not None and ta - presale:
            rec["adj_debt_ratio"] = round((tl - presale) / (ta - presale) * 100, 4)
        else:
            rec["adj_debt_ratio"] = None

        # 有息负债：短期 = 短期借款 + 一年内到期非流动负债 + 应付短期债券
        short_debt = ssum(rec, ("short_loan", "noncurrent_liab_1year", "short_bond_payable"))
        long_debt = ssum(rec, ("long_loan", "bond_payable"))
        interest_debt = ssum({"s": short_debt, "l": long_debt}, ("s", "l"))
        rec["short_debt"] = short_debt
        rec["long_debt"] = long_debt
        rec["interest_debt"] = interest_debt

        cash = rec.get("monetaryfunds")
        # ② 净负债率（红线 100%）=（有息负债 − 货币资金）/ 股东权益合计
        if interest_debt is not None and cash is not None and te:
            rec["net_gearing"] = round((interest_debt - cash) / te * 100, 4)
        else:
            rec["net_gearing"] = None
        # ③ 现金短债比（红线 1 倍）；货币资金含预售监管资金，实际可动用口径更紧
        rec["cash_short_debt"] = round(cash / short_debt, 4) if cash and short_debt else None
        # 有息负债 ÷ 总资产：看杠杆绝对水平，不受权益里永续债的影响
        rec["interest_debt_ratio"] = round(interest_debt / ta * 100, 4) \
            if interest_debt is not None and ta else None

        # 自算毛利率（营业收入 − 营业成本）：与 main 表 XSMLL 互校
        oi, oc = rec.get("operate_income"), rec.get("operate_cost")
        rec["gross_margin_calc"] = round((oi - oc) / oi * 100, 4) if oi and oc is not None else None

        # 结转蓄水池：合同负债（预收）÷ 当年营业收入，>1 表示已售未结可覆盖一年以上结算
        rec["presale_cover"] = round(presale / oi, 4) if presale and oi else None
        # 存货占总资产：开发商的重资产程度
        inv = rec.get("inventory")
        rec["inventory_ratio"] = round(inv / ta * 100, 4) if inv and ta else None
        # 少数股东损益占净利润：并表少数权益（含明股实债/合作开发）分走的利润比例
        np_, mi = rec.get("netprofit"), rec.get("minority_interest")
        rec["minority_share"] = round(mi / np_ * 100, 4) if np_ and mi is not None else None
        # 销售回款 ÷ 营业收入：现金流质量（开发商回款先于收入确认）
        ss = rec.get("sales_services")
        rec["cash_collect_ratio"] = round(ss / oi, 4) if ss and oi else None

        # 归母 ROA（期初期末总资产均值）
        pnp = rec.get("parent_netprofit")
        if pnp is not None and ta and prev_assets:
            rec["roa_avg"] = round(pnp / ((ta + prev_assets) / 2) * 100, 4)
        else:
            rec["roa_avg"] = None
        prev_assets = ta

        rec["equity_asset_ratio"] = round(te / ta * 100, 4) if te and ta else None

    # 历年分红：按利润分配方案归属的报告年度累加每 10 股派现（含税）
    bonus_payload = cached("RPT_SHAREBONUS_DET", code, filt, refresh,
                           sort_col="PLAN_NOTICE_DATE", page_size=100)
    dividend_per10: dict[str, float] = {}
    for r in (bonus_payload.get("result") or {}).get("data") or []:
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
    year_ends = [d for d in ((r.get("END_DATE") or "")[:10] for r in holder_rows)
                 if d.endswith("-12-31")]
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
        "group": group,
        "currency": "CNY",
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "source": ("东方财富 F10 数据接口（各期 A 股年报合并数）。A 股与 H 股年报都存在的年份"
                   "一律取 A 股年报口径；已核验：保利发展 2024 年营业收入 3,081.44 亿元、"
                   "归母净利润 50.01 亿元，招商蛇口 2024 年营业收入 1,547.28 亿元、"
                   "归母净利润 40.39 亿元，与年报原文一致"),
        "unit_note": "金额字段单位为元；比率字段单位为 %；cash_short_debt / presale_cover / "
                     "cash_collect_ratio 为倍数",
        "caliber_note": ("三道红线（adj_debt_ratio / net_gearing / cash_short_debt）为按公开定义"
                         "自算，不是年报披露值：有息负债取「短期借款 + 一年内到期非流动负债 + "
                         "应付短期债券 + 长期借款 + 应付债券」，其中一年内到期非流动负债含租赁负债等"
                         "非有息项，货币资金含预售监管与其它受限资金，永续债计在权益未从分母剔除，"
                         "故与年报披露值有偏差（招商蛇口 2025 年报披露 64.17% / 72.46% / 1.19，"
                         "本脚本自算 61.74% / 59.05% / 1.39：净负债率偏低源于永续债留在权益分母、"
                         "现金短债比偏高源于货币资金未剔预售监管资金，方向可解释，"
                         "图上以趋势与公司间相对位置为准，不要当披露值引用）。"
                         "presale 为「合同负债 + 预收账款」之和：2019 年起"
                         "收入准则把预收账款重分类为合同负债，相加才能跨年连续。"
                         "华侨城 A 含文旅（主题公园）业务、招商蛇口含物业与园区/邮轮，"
                         "毛利率与存货周转与纯住宅开发商不同质。"
                         "total_equity 含少数股东权益，开发商合作开发普遍，minority_share "
                         "（少数股东损益占比）高说明并表项目权益比例低。"),
        "annual": annual,
        "holders_end_date": latest_end,
        "holders": holders,
        "dividend_per10": dividend_per10,
    }


def build_developer_hk(code: str, refresh: bool) -> dict:
    """纯 H 股开发商：走港股 F10 主要指标，已售未结用 HK_PRESALE_THOUSANDS 的年报原文取数补齐。"""
    suffix, name, group, currency = DEVELOPERS_HK[code]
    secucode = f"{code}.{suffix}"
    filt = f'(SECUCODE="{secucode}")'
    print(f"[fetch] {name} {secucode}（港股 F10，本位币 {currency}）")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = RAW_DIR / f"em_RPT_HKF10_FN_MAININDICATOR_{code}.json"
    if raw_path.exists() and not refresh:
        payload = json.loads(raw_path.read_text(encoding="utf-8"))
    else:
        print("    [http] RPT_HKF10_FN_MAININDICATOR")
        payload = request_json("RPT_HKF10_FN_MAININDICATOR", filt, page_size=200, api=API_HK)
        raw_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    # 接口把中期与年报混排返回，只保留 12-31 行
    annual = {y: pick(row, HK_MAIN_FIELDS) for y, row in annual_rows(payload).items()}

    presale_map = HK_PRESALE_THOUSANDS.get(code, {})
    prev_assets: float | None = None
    for y in sorted(annual):
        rec = annual[y]
        ta, tl = rec.get("total_assets"), rec.get("total_liabilities")
        rec["equity_asset_ratio"] = round((ta - tl) / ta * 100, 4) if ta and tl else None
        pnp = rec.get("parent_netprofit")
        rec["roa_avg"] = round(pnp / ((ta + prev_assets) / 2) * 100, 4) \
            if pnp is not None and ta and prev_assets else None
        prev_assets = ta

        # 已售未结：年报原文硬编码（千元 -> 元，与 A 股一致存元）
        thousands = presale_map.get(y)
        presale = thousands * 1000 if thousands is not None else None
        rec["presale"] = presale
        oi = rec.get("operate_income")
        rec["presale_cover"] = round(presale / oi, 4) if presale and oi else None
        if ta and tl is not None and presale is not None and ta - presale:
            rec["adj_debt_ratio"] = round((tl - presale) / (ta - presale) * 100, 4)
        else:
            rec["adj_debt_ratio"] = None

    return {
        "code": code,
        "secucode": secucode,
        "name": name,
        "group": group,
        "currency": currency,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "source": ("东方财富港股 F10 主要指标接口 RPT_HKF10_FN_MAININDICATOR（各期年报数）；"
                   "已售未结（presale）逐年取自 HKEXnews 年度业绩公告原文。"
                   f"{name} 仅在港交所上市（{secucode}），无 A 股年报，故不适用「A/H 都有时优先取 A 股」"
                   "规则；接口行内一律写 CURRENCY=HKD、IS_CNY_CODE=0，这个标记不可信——已用年报"
                   f"原文反查，本公司近年年报以 {currency} 编制，接口金额即该本位币原值、未做折算"),
        "unit_note": f"金额字段单位为 {currency} 元；比率字段单位为 %；presale_cover 单位为倍",
        "caliber_note": ("已售未结 presale 与 A 股三家口径对齐（合同负债 + 预收账款），但不来自接口："
                         "港股 F10 主要指标不含资产负债表明细科目，故逐年从年度业绩公告的综合财务状况表"
                         "读取——中国海外发展为「预售楼款」（2018 年称合同负债、更早称预售按金），"
                         "华润置地为「合约负债」（2017 年前称预售物业已收垫款），中国金茂不在表面上，"
                         "藏在「其他应付款项和应计款项」附注里，取该附注「合约负债总额 + 预收款项」。"
                         "已重列年份取最新重列值（与本脚本取最新修订版年报一致），唯一例外是金茂 "
                         "2018/2019 取原披露的合约负债（重列后的预收款项拆分未单独披露，混用会让同一年"
                         "两个加数口径不一致，差额约 0.5%）。序列起点为金额可与人民币序列同口径比较的"
                         "年份（中海 2017、华润 2017、金茂 2015：接口的金茂 2015 年资产负债表数已是 FY2016 "
                         "年报重列后的人民币值），更早年份接口值为港元原值、"
                         "折算口径不统一，故不入序列。据此自算 adj_debt_ratio =（总负债 − 已售未结）/"
                         "（总资产 − 已售未结）与 presale_cover = 已售未结 / 营业收入。"
                         "净负债率、现金短债比、存货、销售回款仍缺有息负债与货币资金明细，无序列；"
                         "roe_weighted 取接口 ROE_AVG（平均净资产口径），与 A 股「加权平均 ROE」"
                         "算法不完全一致；接口 *_YOY 同比字段未采集。"
                         "前十大股东与逐年每 10 股派现（A 股 RPT_SHAREBONUS_DET）对港股不适用，"
                         "仅保留派息比率 dividend_payout。"),
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

    codes = args.codes or list(DEVELOPERS) + list(DEVELOPERS_HK)
    unknown = [c for c in codes if c not in DEVELOPERS and c not in DEVELOPERS_HK]
    if unknown:
        raise SystemExit(f"未知代码：{unknown}；已支持 {list(DEVELOPERS) + list(DEVELOPERS_HK)}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for code in codes:
        data = build_developer_hk(code, args.refresh) if code in DEVELOPERS_HK \
            else build_developer(code, args.refresh)
        out = OUT_DIR / f"developer_{code}_annual.json"
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
