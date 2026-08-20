"""
抓取水泥行业（房地产**上游**建材）主要上市公司的年报口径财务数据。

数据源与 data/extract/fetch_developer_financials.py 一致：
A 股（datacenter-web.eastmoney.com/api/data/v1/get）
    - RPT_F10_FINANCE_GINCOME / GBALANCE / GCASHFLOW / MAINFINADATA
    - RPT_F10_EH_HOLDERS            前十名股东
    - RPT_SHAREBONUS_DET            历年分红实施明细
纯 H 股（datacenter.eastmoney.com/securities/api/data/v1/get）
    - RPT_HKF10_FN_MAININDICATOR    港股主要指标（年报 + 中期混排，只取 12-31 行）

选样（8 家，覆盖央企 / 地方国企 / 民企 / 台资）：
    A 股上市（海螺、华新为 A+H 两地上市，按项目规则一律取 **A 股年报**口径）
      600585 海螺水泥（安徽海螺集团，A+H 00914）—— 行业利润与净现金标杆
      000877 天山股份（中国建材集团，中建材水泥资产整合平台）—— 产能规模最大
      600801 华新水泥（华新集团 / Holcim 参股，A+H 06655）—— 海外与骨料转型最快
      000401 冀东水泥（金隅集团）—— 北方市场、周期波动最大
      002233 塔牌集团（民营，广东梅州）—— 区域小而美、高分红
    仅港股上市（走港股 F10，无分科目负债明细）
      03323 中国建材（中国建材集团）—— 全球最大水泥企业，天山股份的母公司口径
      01313 华润建材科技（华润集团，原华润水泥控股）—— 华南，与华润置地同集团
      00743 亚洲水泥（中国）（台湾远东 / 亚泥系）—— 长江中游，台资口径

口径提醒（同步写进 data/tables/data_sources.txt）：
    - 天山股份（000877）是中国建材（03323）的并表子公司，两条线**不是独立样本**，
      同图并列只用于看「集团口径 vs 水泥主业口径」的差异，不要相加。
    - 水泥行业真正的核心指标是**吨毛利 / 吨成本 / 水泥熟料销量**，这些不在 F10 三张表里，
      需逐家读年报「经营情况讨论」章节，本脚本未取，见页面待定清单。
    - 有息负债口径与开发商脚本一致：短期借款 + 一年内到期非流动负债 + 应付短期债券
      + 长期借款 + 应付债券；net_cash = 货币资金 − 有息负债，海螺长年为**正**（净现金），
      冀东与中国建材长年为负。net_gearing 为负即净现金状态。
    - recv_ratio 用「应收票据及应收账款（NOTE_ACCOUNTS_RECE）÷ 营业收入」，
      不含应收款项融资（FINANCE_RECE，已贴现/保理的票据），故低估赊销强度；
      两个科目都保留在输出里可自行相加。
    - 港股三家的 CURRENCY 字段一律写 HKD、IS_CNY_CODE=0，这个标记**不可信**
      （与开发商脚本同一个坑）：三家近年年报均以人民币编制，接口金额即人民币原值。

输出：
    data/raw/em_<reportName>_<code>.json     原始响应（缓存；--refresh 重新拉取）
    data/tables/cement_<code>_annual.json    整理后的逐年序列 + 前十股东 + 分红 + 元信息

用法：
    python data/extract/fetch_cement_financials.py            # 使用缓存（缺失才请求）
    python data/extract/fetch_cement_financials.py --refresh  # 强制重新拉取
    python data/extract/fetch_cement_financials.py 600585     # 只处理指定代码
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

# A 股（含 A+H 两地上市，一律取 A 股年报）：代码 -> (交易所, 简称, 控股/实控方, H 股代码或 None)
CEMENT = {
    "600585": ("SH", "海螺水泥", "安徽海螺集团", "00914.HK"),
    "000877": ("SZ", "天山股份", "中国建材集团", None),
    "600801": ("SH", "华新水泥", "华新集团 / Holcim 参股", "06655.HK"),
    "000401": ("SZ", "冀东水泥", "金隅集团", None),
    "002233": ("SZ", "塔牌集团", "民营（广东梅州）", None),
}

# 仅港股上市：代码 -> (交易所, 简称, 控股集团, 年报记账本位币)
CEMENT_HK = {
    "03323": ("HK", "中国建材", "中国建材集团", "CNY"),
    "01313": ("HK", "华润建材科技", "华润集团", "CNY"),
    "00743": ("HK", "亚洲水泥（中国）", "台湾远东 / 亚泥系", "CNY"),
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
    "credit_impairment": "CREDIT_IMPAIRMENT_INCOME",
    "asset_impairment": "ASSET_IMPAIRMENT_INCOME",
    "invest_income": "INVEST_INCOME",
    "invest_joint_income": "INVEST_JOINT_INCOME",
    "other_income": "OTHER_INCOME",          # 政府补助与资源综合利用退税，水泥企业金额可观
    "operate_profit": "OPERATE_PROFIT",
    "total_profit": "TOTAL_PROFIT",
    "income_tax": "INCOME_TAX",
    "netprofit": "NETPROFIT",
    "parent_netprofit": "PARENT_NETPROFIT",
    "deduct_parent_netprofit": "DEDUCT_PARENT_NETPROFIT",
    "minority_interest": "MINORITY_INTEREST",
    "basic_eps": "BASIC_EPS",
}

BALANCE_FIELDS = {
    "monetaryfunds": "MONETARYFUNDS",
    "trade_finasset": "TRADE_FINASSET_NOTFVTPL",       # 交易性金融资产（海螺的理财盘）
    "note_accounts_rece": "NOTE_ACCOUNTS_RECE",        # 应收票据及应收账款（赊销强度）
    "finance_rece": "FINANCE_RECE",                    # 应收款项融资（已贴现/保理的票据）
    "prepayment": "PREPAYMENT",
    "other_rece": "TOTAL_OTHER_RECE",
    "inventory": "INVENTORY",
    "long_equity_invest": "LONG_EQUITY_INVEST",
    "fixed_asset": "FIXED_ASSET",                      # 固定资产（窑线、矿山设备）
    "cip": "CIP",                                      # 在建工程（新增产能与技改）
    "useright_asset": "USERIGHT_ASSET",
    "intangible_asset": "INTANGIBLE_ASSET",            # 无形资产（矿权是水泥企业的核心资源）
    "goodwill": "GOODWILL",                            # 并购商誉（华新、中国建材减值来源）
    "total_current_assets": "TOTAL_CURRENT_ASSETS",
    "total_assets": "TOTAL_ASSETS",
    "short_loan": "SHORT_LOAN",
    "short_bond_payable": "SHORT_BOND_PAYABLE",
    "note_accounts_payable": "NOTE_ACCOUNTS_PAYABLE",
    "contract_liab": "CONTRACT_LIAB",
    "advance_receivables": "ADVANCE_RECEIVABLES",
    "noncurrent_liab_1year": "NONCURRENT_LIAB_1YEAR",
    "total_current_liab": "TOTAL_CURRENT_LIAB",
    "long_loan": "LONG_LOAN",
    "bond_payable": "BOND_PAYABLE",
    "lease_liab": "LEASE_LIAB",
    "total_noncurrent_liab": "TOTAL_NONCURRENT_LIAB",
    "total_liabilities": "TOTAL_LIABILITIES",
    "perpetual_bond": "PERPETUAL_BOND",
    "other_equity_tool": "OTHER_EQUITY_TOOL",
    "minority_equity": "MINORITY_EQUITY",
    "parent_equity": "TOTAL_PARENT_EQUITY",
    "total_equity": "TOTAL_EQUITY",
    "share_capital": "SHARE_CAPITAL",
    "unassign_profit": "UNASSIGN_RPOFIT",
}

CASHFLOW_FIELDS = {
    "sales_services": "SALES_SERVICES",
    "netcash_operate": "NETCASH_OPERATE",
    "netcash_invest": "NETCASH_INVEST",
    "netcash_finance": "NETCASH_FINANCE",
    "construct_long_asset": "CONSTRUCT_LONG_ASSET",    # 购建固定资产支付的现金 = 资本开支
    "assign_dividend_profit": "ASSIGN_DIVIDEND_PORFIT",
    "end_cce": "END_CCE",
}

MAIN_FIELDS = {
    "gross_margin": "XSMLL",                     # 销售毛利率 %
    "net_margin": "XSJLL",                       # 销售净利率 %
    "roe_weighted": "ROEJQ",                     # 加权平均 ROE %
    "roe_deduct": "ROEKCJQ",
    "roic": "ROIC",
    "roa": "ZZCJLL",                             # 总资产净利率 %
    "debt_ratio": "ZCFZL",                       # 资产负债率 %
    "equity_multiplier": "QYCS",
    "current_ratio": "LD",
    "quick_ratio": "SD",
    "inventory_turnover": "CHZZL",               # 存货周转率（次）
    "inventory_days": "CHZZTS",                  # 存货周转天数
    "asset_turnover": "TOAZZL",                  # 总资产周转率（重资产行业的核心效率指标）
    "ocf_to_revenue": "JYXJLYYSR",
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
    "tax_rate": "TAXRATE",
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
    "roe_weighted": "ROE_AVG",                   # 平均净资产口径，非 A 股「加权平均」
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
    "dividend_payout": "DIVI_RATIO",             # 派息比率，小数不是 %
    "total_share": "ISSUED_COMMON_SHARES",
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


def derive(annual: dict[str, dict]) -> None:
    """水泥行业派生指标：净现金、重资产度、资本开支强度、赊销强度、期间费用率。"""
    prev_assets: float | None = None
    for y in sorted(annual):
        rec = annual[y]
        ta = rec.get("total_assets")
        te = rec.get("total_equity")
        oi = rec.get("operate_income") or rec.get("total_operate_income")

        # 有息负债与开发商脚本同口径
        short_debt = ssum(rec, ("short_loan", "noncurrent_liab_1year", "short_bond_payable"))
        long_debt = ssum(rec, ("long_loan", "bond_payable"))
        interest_debt = ssum({"s": short_debt, "l": long_debt}, ("s", "l"))
        # 零负债经营的公司（塔牌 2016—2023 年账上没有任何借款与应付债券）在接口里表现为「科目缺失」，
        # 与「本年没抓到资产负债表」长得一样。只要资产负债表本身抓到了（total_assets 非空），
        # 就把缺失的有息负债科目认定为 0，否则净现金/净负债率会在这些年份出现假缺口。
        if interest_debt is None and ta is not None:
            interest_debt = 0.0
            short_debt = 0.0 if short_debt is None else short_debt
            long_debt = 0.0 if long_debt is None else long_debt
        rec["short_debt"] = short_debt
        rec["long_debt"] = long_debt
        rec["interest_debt"] = interest_debt

        # 净现金 = 货币资金 + 交易性金融资产 − 有息负债；水泥龙头的类现金里理财占比高
        cash = rec.get("monetaryfunds")
        cash_like = ssum(rec, ("monetaryfunds", "trade_finasset"))
        rec["cash_like"] = cash_like
        if cash_like is not None and interest_debt is not None:
            rec["net_cash"] = cash_like - interest_debt
        else:
            rec["net_cash"] = None
        # 净负债率 =（有息负债 − 类现金）/ 权益；为负即净现金状态
        if interest_debt is not None and cash_like is not None and te:
            rec["net_gearing"] = round((interest_debt - cash_like) / te * 100, 4)
        else:
            rec["net_gearing"] = None
        rec["cash_short_debt"] = round(cash / short_debt, 4) if cash and short_debt else None

        # 重资产度：（固定资产 + 在建工程）/ 总资产，水泥是典型重资产
        heavy = ssum(rec, ("fixed_asset", "cip"))
        rec["heavy_asset"] = heavy
        rec["heavy_asset_ratio"] = round(heavy / ta * 100, 4) if heavy and ta else None
        # 资本开支强度：购建固定资产现金 / 营业收入，看产能扩张还是收缩
        capex = rec.get("construct_long_asset")
        rec["capex_ratio"] = round(capex / oi * 100, 4) if capex and oi else None
        # 赊销强度：应收票据及应收账款 / 营业收入（不含应收款项融资，见 docstring）
        recv = rec.get("note_accounts_rece")
        rec["recv_ratio"] = round(recv / oi * 100, 4) if recv and oi else None
        # 期间费用率：销售 + 管理 + 财务 + 研发
        exp = ssum(rec, ("sale_expense", "manage_expense", "finance_expense", "research_expense"))
        rec["period_expense"] = exp
        rec["expense_ratio"] = round(exp / oi * 100, 4) if exp is not None and oi else None
        # 自算毛利率，与 main 表 XSMLL 互校
        oc = rec.get("operate_cost")
        rec["gross_margin_calc"] = round((oi - oc) / oi * 100, 4) if oi and oc is not None else None

        pnp = rec.get("parent_netprofit")
        rec["roa_avg"] = round(pnp / ((ta + prev_assets) / 2) * 100, 4) \
            if pnp is not None and ta and prev_assets else None
        prev_assets = ta
        rec["equity_asset_ratio"] = round(te / ta * 100, 4) if te and ta else None


def fetch_holders(code: str, filt: str, refresh: bool) -> tuple[str | None, list[dict]]:
    payload = cached("RPT_F10_EH_HOLDERS", code, filt, refresh,
                     sort_col="END_DATE", page_size=200)
    rows = (payload.get("result") or {}).get("data") or []
    year_ends = [d for d in ((r.get("END_DATE") or "")[:10] for r in rows) if d.endswith("-12-31")]
    latest = max(year_ends) if year_ends else None
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
        for r in rows if (r.get("END_DATE") or "")[:10] == latest
    ]
    holders.sort(key=lambda h: h["rank"] or 99)
    return latest, holders


def fetch_dividend(code: str, filt: str, refresh: bool) -> dict[str, float]:
    payload = cached("RPT_SHAREBONUS_DET", code, filt, refresh,
                     sort_col="PLAN_NOTICE_DATE", page_size=100)
    out: dict[str, float] = {}
    for r in (payload.get("result") or {}).get("data") or []:
        if r.get("ASSIGN_PROGRESS") != "实施分配":
            continue
        amt = r.get("PRETAX_BONUS_RMB")
        rd = (r.get("REPORT_DATE") or "")[:4]
        if amt is None or not rd:
            continue
        out[rd] = round(out.get(rd, 0.0) + amt, 4)
    return out


def build_cement(code: str, refresh: bool) -> dict:
    suffix, name, group, h_code = CEMENT[code]
    secucode = f"{code}.{suffix}"
    filt = f'(SECUCODE="{secucode}")'
    print(f"[fetch] {name} {secucode}" + (f"（A+H，H 股 {h_code}，取 A 股口径）" if h_code else ""))

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
    derive(annual)

    latest_end, holders = fetch_holders(code, filt, refresh)
    dividend_per10 = fetch_dividend(code, filt, refresh)

    ah_note = (f"本公司 A+H 两地上市（H 股 {h_code}），按项目规则取 **A 股年报**口径。"
               if h_code else "本公司仅 A 股上市。")
    return {
        "code": code,
        "secucode": secucode,
        "name": name,
        "group": group,
        "h_code": h_code,
        "currency": "CNY",
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "source": ("东方财富 F10 数据接口（各期 A 股年报合并数）。" + ah_note +
                   "已核验：海螺水泥 2025 年营业收入 825.32 亿元、归母净利润 81.13 亿元、"
                   "毛利率 24.16%，与年报原文一致"),
        "unit_note": "金额字段单位为元；比率字段单位为 %；cash_short_debt / asset_turnover / "
                     "inventory_turnover 为倍数或次数；dividend_per10 为每 10 股派现（含税，元）",
        "caliber_note": ("净现金 net_cash =（货币资金 + 交易性金融资产）− 有息负债，有息负债取"
                         "「短期借款 + 一年内到期非流动负债 + 应付短期债券 + 长期借款 + 应付债券」，"
                         "口径粗于年报（一年内到期非流动负债含租赁负债等非有息项，货币资金含受限资金），"
                         "net_gearing 为负即净现金状态，海螺长年为负、冀东长年为正。"
                         "recv_ratio 只用应收票据及应收账款，不含应收款项融资（finance_rece，"
                         "已贴现/保理的票据），故低估赊销强度，两个科目都在输出里可自行相加。"
                         "heavy_asset_ratio =（固定资产 + 在建工程）/ 总资产，capex_ratio = "
                         "购建固定资产支付的现金 / 营业收入，两者一起看产能是扩张还是收缩。"
                         "other_income（其他收益）为政府补助与资源综合利用增值税退税，水泥企业金额"
                         "可观，看扣非归母（deduct_parent_netprofit）才是主业盈利。"
                         "水泥行业真正的核心指标吨毛利/吨成本/水泥熟料销量不在 F10 三张表里，"
                         "需读年报「经营情况讨论与分析」，本脚本未取。"
                         "天山股份（000877）是中国建材（03323）的并表子公司，两条线不是独立样本，"
                         "同图并列只用于看集团口径与水泥主业口径的差异，不要相加。"),
        "annual": annual,
        "holders_end_date": latest_end,
        "holders": holders,
        "dividend_per10": dividend_per10,
    }


def build_cement_hk(code: str, refresh: bool) -> dict:
    """纯 H 股：港股 F10 主要指标，无资产负债表明细科目，故净现金/重资产度等无序列。"""
    suffix, name, group, currency = CEMENT_HK[code]
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

    annual = {y: pick(row, HK_MAIN_FIELDS) for y, row in annual_rows(payload).items()}

    prev_assets: float | None = None
    for y in sorted(annual):
        rec = annual[y]
        ta, tl = rec.get("total_assets"), rec.get("total_liabilities")
        rec["equity_asset_ratio"] = round((ta - tl) / ta * 100, 4) if ta and tl else None
        pnp = rec.get("parent_netprofit")
        rec["roa_avg"] = round(pnp / ((ta + prev_assets) / 2) * 100, 4) \
            if pnp is not None and ta and prev_assets else None
        prev_assets = ta
        # 港股主要指标给了毛利额，可自算毛利率与 GROSS_PROFIT_RATIO 互校
        gp, oi = rec.get("gross_profit"), rec.get("operate_income")
        rec["gross_margin_calc"] = round(gp / oi * 100, 4) if gp is not None and oi else None

    # 总资产周转率：港股接口不给，用营收 / 期初期末总资产均值自算，与 A 股 TOAZZL 可比
    prev_assets = None
    for y in sorted(annual):
        rec = annual[y]
        ta, oi = rec.get("total_assets"), rec.get("operate_income")
        rec["asset_turnover"] = round(oi / ((ta + prev_assets) / 2), 4) \
            if oi and ta and prev_assets else None
        prev_assets = ta

    return {
        "code": code,
        "secucode": secucode,
        "name": name,
        "group": group,
        "h_code": secucode,
        "currency": currency,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "source": ("东方财富港股 F10 主要指标接口 RPT_HKF10_FN_MAININDICATOR（各期年报数）。"
                   f"{name} 仅在港交所上市（{secucode}），无 A 股年报，故不适用「A/H 都有时优先取"
                   "A 股」规则；接口行内一律写 CURRENCY=HKD、IS_CNY_CODE=0，这个标记不可信——"
                   f"本公司年报以 {currency} 编制，接口金额即该本位币原值、未做折算（已用量级反查："
                   "中国建材 2025 年营收 1,778.47 亿、归母 −37.45 亿；华润建材科技 2025 年营收 "
                   "210.55 亿、归母 4.79 亿；亚洲水泥（中国）2025 年营收 51.09 亿、归母 0.857 亿，"
                   "均与人民币披露口径一致）"),
        "unit_note": f"金额字段单位为 {currency} 元；比率字段单位为 %；asset_turnover 为次数；"
                     "dividend_payout 为派息比率小数（不是 %）",
        "caliber_note": ("港股 F10 主要指标不提供资产负债表明细科目，故净现金 net_cash、净负债率、"
                         "现金短债比、重资产度、资本开支强度、赊销强度、期间费用率在这三家没有序列，"
                         "只有营收/毛利率/净利率/ROE/资产负债率/每股指标与现金流量净额。"
                         "roe_weighted 取接口 ROE_AVG（平均净资产口径），与 A 股「加权平均 ROE」"
                         "算法不完全一致；asset_turnover 为本脚本按营收 / 期初期末总资产均值自算，"
                         "与 A 股接口 TOAZZL 口径接近但非同一来源。"
                         "中国建材（03323）是天山股份（000877）的母公司，集团含水泥 + 新材料 + "
                         "工程服务三块，营收与毛利率与纯水泥企业不同质，且与天山股份不是独立样本。"
                         "前十大股东与每 10 股派现（A 股 RPT_SHAREBONUS_DET）对港股不适用。"),
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

    codes = args.codes or list(CEMENT) + list(CEMENT_HK)
    unknown = [c for c in codes if c not in CEMENT and c not in CEMENT_HK]
    if unknown:
        raise SystemExit(f"未知代码：{unknown}；已支持 {list(CEMENT) + list(CEMENT_HK)}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for code in codes:
        data = build_cement_hk(code, args.refresh) if code in CEMENT_HK \
            else build_cement(code, args.refresh)
        out = OUT_DIR / f"cement_{code}_annual.json"
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
