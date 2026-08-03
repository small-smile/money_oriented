"""
抓取银行类上市公司的年报口径财务数据（东方财富 F10 数据接口，取值来自各期年度报告）。

数据源（datacenter-web.eastmoney.com/api/data/v1/get，reportName 为报表模板）：
    - RPT_F10_FINANCE_BINCOME       银行业利润表（年报期）
    - RPT_F10_FINANCE_BBALANCE      银行业资产负债表（年报期）
    - RPT_F10_FINANCE_BCASHFLOW     银行业现金流量表（年报期）
    - RPT_F10_FINANCE_MAINFINADATA  主要指标（含银行专项：存贷款总额、不良率、
                                    资本充足率、核心一级、一级、NIM/NIS、拨备覆盖率、拨贷比等）
    - RPT_F10_EH_HOLDERS            前十名股东（含报告期内增减）

输出：
    data/raw/em_<reportName>_<code>.json    原始响应（缓存；--refresh 重新拉取）
    data/tables/bank_<code>_annual.json     整理后的逐年序列 + 前十股东 + 元信息

用法：
    python extract/fetch_bank_financials.py            # 使用缓存（缺失才请求）
    python extract/fetch_bank_financials.py --refresh  # 强制重新拉取
    python extract/fetch_bank_financials.py 600036     # 只处理指定代码
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

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "tables"

API = "https://datacenter-web.eastmoney.com/api/data/v1/get"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Referer": "https://data.eastmoney.com/",
    "Accept-Encoding": "identity",
}

# 代码 -> (交易所后缀, 简称)
BANKS = {
    "601077": ("SH", "渝农商行"),
    "600036": ("SH", "招商银行"),
}

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


def request_json(report_name: str, filt: str, sort_col: str = "REPORT_DATE",
                 page_size: int = 200, retries: int = 3, timeout: int = 60) -> dict:
    url = "%s?reportName=%s&columns=ALL&filter=%s&sortColumns=%s&sortTypes=-1&pageSize=%d" % (
        API, report_name, urllib.parse.quote(filt), sort_col, page_size)
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
    """按年份聚合年报期（REPORT_DATE 为 12-31 且 REPORT_TYPE 含「年报」）的行。"""
    out: dict[str, dict] = {}
    for row in (payload.get("result") or {}).get("data") or []:
        rd = (row.get("REPORT_DATE") or "")[:10]
        if not rd.endswith("-12-31"):
            continue
        out.setdefault(rd[:4], row)     # 接口按日期降序，首条为最新修订版
    return out


def pick(row: dict, mapping: dict[str, str]) -> dict:
    return {k: row.get(v) for k, v in mapping.items()}


def build_bank(code: str, refresh: bool) -> dict:
    suffix, name = BANKS[code]
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
        "source": "东方财富 F10 数据接口（取值源自各期年度报告，合并口径）",
        "unit_note": "金额字段单位为元；比率字段单位为 %",
        "annual": annual,
        "holders_end_date": latest_end,
        "holders": holders,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("codes", nargs="*", default=[], help="股票代码，默认全部")
    ap.add_argument("--refresh", action="store_true", help="忽略缓存重新拉取")
    args = ap.parse_args()

    codes = args.codes or list(BANKS)
    unknown = [c for c in codes if c not in BANKS]
    if unknown:
        raise SystemExit(f"未知代码：{unknown}；已支持 {list(BANKS)}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for code in codes:
        data = build_bank(code, args.refresh)
        out = OUT_DIR / f"bank_{code}_annual.json"
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
