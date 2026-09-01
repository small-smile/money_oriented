"""
抓取三大电信运营商（互联网板块的**上游**：接入与流量）的年报口径财务数据。

数据源与 data/extract/fetch_cement_financials.py 一致：
A 股（datacenter-web.eastmoney.com/api/data/v1/get）
    - RPT_F10_FINANCE_GINCOME / GBALANCE / GCASHFLOW / MAINFINADATA
    - RPT_F10_EH_HOLDERS            前十名股东
    - RPT_SHAREBONUS_DET            历年分红实施明细
港股（datacenter.eastmoney.com/securities/api/data/v1/get）
    - RPT_HKF10_FN_MAININDICATOR    港股主要指标，只用于交叉核对，不进页面

选样（3 家 A 股主体，均为 A+H）：
    600941 中国移动（H 00941）—— 2022-01 回 A，A 股接口仍带 1999 年起的历史
    601728 中国电信（H 00728）—— 2021-08 回 A
    600050 中国联通（H 00762）—— 2002-10 A 股上市，是三家里 A 股历史最长的

**主体口径提醒（这是本行业最大的坑）**：
    中国移动 600941 与 00941、中国电信 601728 与 00728 都是**同一法人**两地上市，
    A/H 年报是同一套合并报表，按项目规则取 A 股口径即可。
    中国联通不是：A 股 600050 是「中国联合网络通信股份有限公司」（联通 A 股），
    00762.HK 是「中国联通（香港）有限公司」红筹主体，两者是**不同法人**、
    红筹在上、A 股在下的多层持股结构，00762 的合并报表包含 600050 及其少数股东权益，
    两条线不可当作同一公司的 A/H 口径混用，也不可相加。本脚本一律只用 600050。

输出：
    data/raw/em_<reportName>_<code>.json      原始响应（缓存；--refresh 重新拉取）
    data/tables/telecom_<code>_annual.json    整理后的逐年序列 + 前十股东 + 分红 + 元信息

用法：
    python data/extract/fetch_telecom_financials.py            # 使用缓存（缺失才请求）
    python data/extract/fetch_telecom_financials.py --refresh  # 强制重新拉取
    python data/extract/fetch_telecom_financials.py 600941     # 只处理指定代码
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

# 代码 -> (交易所, 简称, 控股方, 港股代码, 港股主体是否同一法人, A 股首份年报年份)
# A 股首份年报年份 = A 股上市后的首个完整会计年度报告：
#   600941 中国移动 2022-01-05 上市 -> 2021 年报为上市后首份 A 股年报
#   601728 中国电信 2021-08-20 上市 -> 2021
#   600050 中国联通 2002-10-09 上市 -> 2002
# 早于该年份的行是接口按发行人上市前历史披露（H 股/招股材料）回填的，口径与 A 股年报不同源，
# 按项目「交易所口径分来源披露」规则打 src=PRE，页面单列 series，不与 A 股年报口径拼成一条线。
TELECOM = {
    "600941": ("SH", "中国移动", "中国移动通信集团", "00941.HK", True, 2021),
    "601728": ("SH", "中国电信", "中国电信集团", "00728.HK", True, 2021),
    "600050": ("SH", "中国联通", "中国联通集团（经联通 BVI 持股）", "00762.HK", False, 2002),
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
    "research_expense": "RESEARCH_EXPENSE",      # 运营商近年研发投入抬升的直接科目
    "credit_impairment": "CREDIT_IMPAIRMENT_INCOME",
    "asset_impairment": "ASSET_IMPAIRMENT_INCOME",
    "invest_income": "INVEST_INCOME",
    "invest_joint_income": "INVEST_JOINT_INCOME",
    "other_income": "OTHER_INCOME",
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
    "trade_finasset": "TRADE_FINASSET_NOTFVTPL",
    "note_accounts_rece": "NOTE_ACCOUNTS_RECE",
    "finance_rece": "FINANCE_RECE",
    "prepayment": "PREPAYMENT",
    "other_rece": "TOTAL_OTHER_RECE",
    "inventory": "INVENTORY",
    "long_equity_invest": "LONG_EQUITY_INVEST",
    "fixed_asset": "FIXED_ASSET",                # 基站/传输网/机楼，运营商最大的一块资产
    "cip": "CIP",                                # 在建工程：当年网络建设进度
    "useright_asset": "USERIGHT_ASSET",          # 租赁铁塔与站址（与中国铁塔的租费相关）
    "intangible_asset": "INTANGIBLE_ASSET",      # 含频谱与软件
    "goodwill": "GOODWILL",
    "total_current_assets": "TOTAL_CURRENT_ASSETS",
    "total_assets": "TOTAL_ASSETS",
    "short_loan": "SHORT_LOAN",
    "short_bond_payable": "SHORT_BOND_PAYABLE",
    "note_accounts_payable": "NOTE_ACCOUNTS_PAYABLE",
    "contract_liab": "CONTRACT_LIAB",            # 预收话费/合同负债，看用户预付沉淀
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
    "construct_long_asset": "CONSTRUCT_LONG_ASSET",   # 购建固定/无形资产现金：资本开支的报表代理
    "depreciation": "ASSET_IMPAIRMENT",               # 现金流量表附注「资产减值准备」，非折旧，仅备查
    "assign_dividend_profit": "ASSIGN_DIVIDEND_PORFIT",
    "end_cce": "END_CCE",
}

MAIN_FIELDS = {
    "gross_margin": "XSMLL",
    "net_margin": "XSJLL",
    "roe_weighted": "ROEJQ",
    "roe_deduct": "ROEKCJQ",
    "roic": "ROIC",
    "roa": "ZZCJLL",
    "debt_ratio": "ZCFZL",
    "equity_multiplier": "QYCS",
    "current_ratio": "LD",
    "quick_ratio": "SD",
    "asset_turnover": "TOAZZL",
    "ocf_to_revenue": "JYXJLYYSR",
    "eps": "EPSJB",
    "eps_deduct": "EPSKCJB",
    "bps": "BPS",
    "op_cf_per_share": "MGJYXJJE",
    "total_revenue": "TOTALOPERATEREVE",
    "main_parent_netprofit": "PARENTNETPROFIT",
    "main_total_assets": "TOTAL_ASSETS_PK",
    "main_total_equity": "TOTAL_EQUITY_PK",
    "main_liability": "LIABILITY",
    "staff_num": "STAFF_NUM",
    "total_share": "TOTAL_SHARE",
    "tax_rate": "TAXRATE",
}

HK_MAIN_FIELDS = {
    "hk_operate_income": "OPERATE_INCOME",
    "hk_parent_netprofit": "HOLDER_PROFIT",
    "hk_total_assets": "TOTAL_ASSETS",
    "hk_parent_equity": "TOTAL_PARENT_EQUITY",
    "hk_eps": "BASIC_EPS",
    "hk_roe": "ROE_AVG",
    "hk_dividend_payout": "DIVI_RATIO",
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


def revenue_of(rec: dict) -> float | None:
    """营业收入：优先营业总收入。
    上市前回填的行里两个字段偶有一个是残值（如中国移动 2011 年 OPERATE_INCOME 只有 244.8 亿、
    而 TOTAL_OPERATE_INCOME 是 5,280.0 亿），两者都有且差一个量级时取大的那个（营业总收入）。"""
    total = rec.get("total_operate_income")
    oi = rec.get("operate_income")
    if total is not None and oi is not None:
        return total if oi < total * 0.5 else oi
    return total if total is not None else oi


def revenue_mismatch(rec: dict) -> bool:
    """两个营业收入字段差一倍以上 —— 该年这一整行的收入侧科目（成本、费用、现金流）
    与所取的收入不同基准，任何以收入为分母的比率都会算出荒谬值
    （中国移动 2011 年因此得出毛利率 −412%、净利率 +515%），故整批作废而不是硬算。"""
    total = rec.get("total_operate_income")
    oi = rec.get("operate_income")
    return total is not None and oi is not None and min(total, oi) < max(total, oi) * 0.5


# 收入口径自相矛盾的年份要作废的字段：分母是营业收入的比率 + 接口自带的利润率 + 现金流代理
RATIO_KEYS_ON_REVENUE = (
    "gross_margin", "gross_margin_calc", "net_margin", "capex_ratio", "expense_ratio",
    "rd_ratio", "ocf_to_revenue", "asset_turnover", "fcf_proxy", "rev_per_staff",
)


def derive(annual: dict[str, dict]) -> None:
    """运营商行业派生指标：资本开支强度、重资产度、净现金、期间费用率、研发强度。"""
    prev_assets: float | None = None
    for y in sorted(annual):
        rec = annual[y]
        ta = rec.get("total_assets")
        te = rec.get("total_equity")
        oi = revenue_of(rec)
        rec["revenue"] = oi              # 页面统一用 revenue，不再各自挑字段

        short_debt = ssum(rec, ("short_loan", "noncurrent_liab_1year", "short_bond_payable"))
        long_debt = ssum(rec, ("long_loan", "bond_payable"))
        interest_debt = ssum({"s": short_debt, "l": long_debt}, ("s", "l"))
        # 三家运营商长年几乎无息负债（移动尤甚），科目缺失即视为 0，否则净现金会出现假缺口
        if interest_debt is None and ta is not None:
            interest_debt = 0.0
            short_debt = 0.0 if short_debt is None else short_debt
            long_debt = 0.0 if long_debt is None else long_debt
        rec["short_debt"] = short_debt
        rec["long_debt"] = long_debt
        rec["interest_debt"] = interest_debt

        cash_like = ssum(rec, ("monetaryfunds", "trade_finasset"))
        rec["cash_like"] = cash_like
        rec["net_cash"] = (cash_like - interest_debt) \
            if cash_like is not None and interest_debt is not None else None
        rec["net_gearing"] = round((interest_debt - cash_like) / te * 100, 4) \
            if interest_debt is not None and cash_like is not None and te else None

        # 重资产度与资本开支强度：运营商是「先砸网络再收月费」的生意，这两条决定自由现金流
        heavy = ssum(rec, ("fixed_asset", "cip"))
        rec["heavy_asset"] = heavy
        rec["heavy_asset_ratio"] = round(heavy / ta * 100, 4) if heavy and ta else None
        capex = rec.get("construct_long_asset")
        rec["capex_ratio"] = round(capex / oi * 100, 4) if capex and oi else None
        # 自由现金流代理 = 经营净现金 − 购建长期资产现金（不扣租赁付现，故偏乐观）
        ocf = rec.get("netcash_operate")
        rec["fcf_proxy"] = (ocf - capex) if ocf is not None and capex is not None else None

        exp = ssum(rec, ("sale_expense", "manage_expense", "finance_expense", "research_expense"))
        rec["period_expense"] = exp
        rec["expense_ratio"] = round(exp / oi * 100, 4) if exp is not None and oi else None
        rd = rec.get("research_expense")
        rec["rd_ratio"] = round(rd / oi * 100, 4) if rd and oi else None
        oc = rec.get("operate_cost")
        rec["gross_margin_calc"] = round((oi - oc) / oi * 100, 4) if oi and oc is not None else None

        pnp = rec.get("parent_netprofit")
        rec["roa_avg"] = round(pnp / ((ta + prev_assets) / 2) * 100, 4) \
            if pnp is not None and ta and prev_assets else None
        prev_assets = ta
        rec["equity_asset_ratio"] = round(te / ta * 100, 4) if te and ta else None
        # 人均营收/人均归母（万元/人）：运营商员工数十万级，人效是国企改革的常用观察口
        staff = rec.get("staff_num")
        rec["rev_per_staff"] = round(oi / staff / 1e4, 4) if oi and staff else None
        rec["np_per_staff"] = round(pnp / staff / 1e4, 4) if pnp and staff else None

        # 收入字段自相矛盾的年份：保留收入与利润的绝对值（量级已核对），
        # 但把以收入为分母的比率与自由现金流代理清空，并留下标记供页面与核对使用
        if revenue_mismatch(rec):
            rec["rev_field_mismatch"] = True
            for k in RATIO_KEYS_ON_REVENUE:
                rec[k] = None


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


def fetch_hk_crosscheck(h_code: str, code: str, refresh: bool) -> dict[str, dict]:
    """港股主要指标，仅留作口径交叉核对（不进图表）。中国联通的 00762 是另一法人，
    这里抓到的数含 A 股少数股东权益，两条线不可混用，见模块 docstring。"""
    filt = f'(SECUCODE="{h_code}")'
    hk = h_code.split(".")[0]
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"em_RPT_HKF10_FN_MAININDICATOR_{hk}.json"
    if path.exists() and not refresh:
        payload = json.loads(path.read_text(encoding="utf-8"))
    else:
        print(f"    [http] RPT_HKF10_FN_MAININDICATOR {h_code}")
        payload = request_json("RPT_HKF10_FN_MAININDICATOR", filt, page_size=200, api=API_HK)
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return {y: pick(row, HK_MAIN_FIELDS) for y, row in annual_rows(payload).items()}


def build(code: str, refresh: bool) -> dict:
    suffix, name, group, h_code, same_entity, a_from = TELECOM[code]
    secucode = f"{code}.{suffix}"
    filt = f'(SECUCODE="{secucode}")'
    print(f"[fetch] {name} {secucode}（H 股 {h_code}，"
          + ("同一法人两地上市" if same_entity else "H 股为另一法人，仅备查") + "）")

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
    # 披露来源标记：A = A 股年报口径（上市后），PRE = 上市前回填（H 股/招股材料口径）
    for y, rec in annual.items():
        rec["src"] = "A" if int(y) >= a_from else "PRE"

    latest_end, holders = fetch_holders(code, filt, refresh)
    dividend_per10 = fetch_dividend(code, filt, refresh)
    hk_check = fetch_hk_crosscheck(h_code, code, refresh)

    entity_note = (
        f"本公司 A+H 两地上市（H 股 {h_code}）、A/H 为同一法人同一套合并报表，"
        "按项目规则取 A 股年报口径。"
        if same_entity else
        "本公司 A 股主体为「中国联合网络通信股份有限公司」（600050）；"
        f"{h_code} 是「中国联通（香港）有限公司」红筹主体，与 600050 **不是同一法人**，"
        "红筹在上、A 股在下的多层持股结构，其合并报表包含 600050 及大额少数股东权益，"
        "两条线不可当作同一公司的 A/H 口径混用、更不可相加。本表只用 600050。"
    )
    return {
        "code": code,
        "secucode": secucode,
        "name": name,
        "group": group,
        "h_code": h_code,
        "h_same_entity": same_entity,
        "a_report_from": a_from,
        "currency": "CNY",
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "source": "东方财富公司数据接口（各期 A 股年报合并数）。" + entity_note,
        "unit_note": "金额字段单位为元；比率字段单位为 %；asset_turnover / equity_multiplier / "
                     "current_ratio 为倍数或次数；rev_per_staff / np_per_staff 为万元/人；"
                     "dividend_per10 为每 10 股派现（含税，元）",
        "caliber_note": (
            f"每年带 src 标记：A = {a_from} 年起的 A 股年报口径（上市后定期报告），"
            "PRE = 上市前年份，由接口按发行人当时的历史披露（H 股年报／招股材料）回填，"
            "两段**不拼成一条序列**（页面分 series 画），且 PRE 段未逐年回原文核对。"
            "revenue 取营业总收入（缺失时退营业收入）；上市前回填行里这两个字段偶有一个是残值，"
            "差一个量级时取大的那个。此时该年整行的收入侧科目与所取收入不同基准，"
            "带 rev_field_mismatch=true 标记，并把以收入为分母的比率（毛利率／净利率／"
            "资本开支强度／费用率／研发强度／资产周转率／人均营收）与 fcf_proxy 一并置空 —— "
            "中国移动 2011 年若硬算会得到毛利率 −412%、净利率 +515%（唯一一处）。"
            "capex_ratio = 购建固定资产、无形资产和其他长期资产支付的现金 / 营业收入，"
            "是资本开支的**报表代理**，与年报「资本开支」披露口径（按预算发生额、含未付款项）"
            "不等，两者都保留：年报口径在 telecom_ops_manual.json 的 ops_capex。"
            "fcf_proxy = 经营活动净现金流 − 购建长期资产现金，未扣租赁付现（运营商租铁塔与站址"
            "的付现记在筹资活动），故系统性偏乐观。"
            "heavy_asset_ratio =（固定资产 + 在建工程）/ 总资产，看网络投资的存量与在途。"
            "研发费用（research_expense）2018 年前多未单列，rd_ratio 早年为空是披露口径而非零投入。"
            "员工数 staff_num 为接口快照，三家均含子公司；rev_per_staff / np_per_staff 由它自算。"
            "中国联通 600050 与 00762.HK 不是同一法人，切勿与红筹口径混比（见 source）。"
        ),
        "annual": annual,
        "hk_crosscheck": hk_check,
        "holders_end_date": latest_end,
        "holders": holders,
        "dividend_per10": dividend_per10,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("codes", nargs="*", default=[], help="股票代码，默认全部")
    ap.add_argument("--refresh", action="store_true", help="忽略缓存重新拉取")
    args = ap.parse_args()

    codes = args.codes or list(TELECOM)
    unknown = [c for c in codes if c not in TELECOM]
    if unknown:
        raise SystemExit(f"未知代码：{unknown}；已支持 {list(TELECOM)}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for code in codes:
        data = build(code, args.refresh)
        out = OUT_DIR / f"telecom_{code}_annual.json"
        out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        yrs = sorted(data["annual"])
        print(f"    -> {out.relative_to(ROOT)}  ({len(yrs)} 年，{yrs[0]}~{yrs[-1]}，"
              f"股东 {len(data['holders'])} 名 @ {data['holders_end_date']}，"
              f"分红 {len(data['dividend_per10'])} 年)")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:                          # noqa: BLE001
        print(f"[error] {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
