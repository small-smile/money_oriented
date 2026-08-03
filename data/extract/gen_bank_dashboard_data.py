"""
把 data/tables/bank_<code>_annual.json（年报口径原始数据）整理成看板可直接使用的
dashboard/common/bank-data.js（window.BANK_QUANT）。

约定：
    - 金额序列统一换算为「亿元」，三张表明细统一换算为「百万元」（与页面口径一致）
    - 比率保持 %，缺失年份保留 null（页面用 connectNulls 跨接并在脚注说明）
    - 费用类科目在数据里保持正数，另用 neg 标记，由页面渲染成 (x)

用法：
    python data/extract/gen_bank_dashboard_data.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
TABLES = ROOT / "data" / "tables"
OUT = ROOT / "dashboard" / "common" / "bank-data.js"

CODES = ["601077", "600036"]

YI = 1e8        # 元 -> 亿元
MN = 1e6        # 元 -> 百万元


def r(val, div, nd=2):
    return None if val is None else round(val / div, nd)


def ratio(num, den, nd=2):
    if num is None or den in (None, 0):
        return None
    return round(num / den * 100, nd)


def yoy(cur, prev, nd=2):
    if cur is None or prev in (None, 0):
        return None
    return round((cur - prev) / abs(prev) * 100, nd)


def series(annual: dict, years: list[str], key: str, div=None, nd=2):
    out = []
    for y in years:
        v = annual.get(y, {}).get(key)
        out.append(r(v, div, nd) if div else (None if v is None else round(v, nd)))
    return out


def statement_rows(annual: dict, years: list[str]) -> dict:
    """三张表：利润表 / 资产负债表 / 现金流，单位百万元。"""
    def vals(key, div=MN, nd=1):
        return [r(annual.get(y, {}).get(key), div, nd) for y in years]

    def fin_invest(y):
        """金融投资合计：不同银行披露模板不同，按存在的字段组合，避免重复计入。"""
        a = annual.get(y, {})

        def s(*keys):
            parts = [a.get(k) for k in keys if a.get(k) is not None]
            return sum(parts) if parts else None

        if a.get("amortize_cost_finasset") is not None:
            # IFRS9 三分类模板（如招商银行）：交易性(FVTPL) + 债权投资(摊余成本) + FVTOCI
            base = s("fvtpl_finasset", "amortize_cost_finasset")
            fvtoci = a.get("fvtoci_finasset")
            if fvtoci is None:
                fvtoci = s("other_creditor_invest", "other_equity_invest")
            if base is None:
                return fvtoci
            return base + (fvtoci or 0)
        # 债权投资分项模板（如渝农商行）
        return s("trade_finasset", "creditor_invest", "other_creditor_invest", "other_equity_invest")

    income = [
        ("利息净收入", "interest_ni", "plain", False),
        ("手续费及佣金净收入", "fee_ni", "plain", False),
        ("营业收入", "operate_income", "total", False),
        ("税金及附加", "operate_tax", "plain", True),
        ("业务及管理费", "manage_expense", "plain", True),
        ("信用减值损失", "credit_impairment", "plain", True),
        ("其他业务成本", "other_business_cost", "plain", True),
        ("营业利润", "operate_profit", "total", False),
        ("利润总额", "total_profit", "total", False),
        ("所得税费用", "income_tax", "plain", True),
        ("净利润", "netprofit", "total", False),
        ("归属于本行股东的净利润", "parent_netprofit", "plain", False),
        ("少数股东损益", "minority_interest", "plain", False),
    ]
    balance = [
        ("资产总额", "total_assets", "total", False),
        ("客户贷款和垫款（净额）", "loan_advance", "sub", False),
        ("金融投资", "_fin_invest", "sub", False),
        ("存放同业及拆出资金", "_interbank_asset", "sub", False),
        ("现金及存放中央银行款项", "cash_deposit_pbc", "sub", False),
        ("买入返售金融资产", "buy_resale", "sub", False),
        ("负债总额", "total_liabilities", "total", False),
        ("客户存款", "accept_deposit", "sub", False),
        ("同业存放及拆入资金", "_interbank_liab", "sub", False),
        ("卖出回购金融资产", "sell_repo", "sub", False),
        ("向中央银行借款", "loan_pbc", "sub", False),
        ("应付债券", "bond_payable", "sub", False),
        ("权益总额", "total_equity", "total", False),
        ("股本", "share_capital", "sub", False),
        ("归属于本行股东权益", "parent_equity", "sub", False),
        ("少数股东权益", "minority_equity", "sub", False),
    ]
    cashflow = [
        ("经营活动产生的现金流量净额", "netcash_operate", "total", False),
        ("投资活动产生的现金流量净额", "netcash_invest", "plain", False),
        ("筹资活动产生的现金流量净额", "netcash_finance", "plain", False),
    ]

    def derived(key, y):
        if key == "_fin_invest":
            return fin_invest(y)
        if key == "_interbank_asset":
            parts = [annual.get(y, {}).get(k) for k in ("deposit_interbank", "lend_fund")]
            parts = [p for p in parts if p is not None]
            return sum(parts) if parts else None
        if key == "_interbank_liab":
            parts = [annual.get(y, {}).get(k) for k in ("iofi_deposit", "borrow_fund")]
            parts = [p for p in parts if p is not None]
            return sum(parts) if parts else None
        return annual.get(y, {}).get(key)

    def build(spec):
        rows = []
        for label, key, kind, neg in spec:
            v = [r(derived(key, y), MN, 1) for y in years]
            if all(x is None for x in v):
                continue
            rows.append({"label": label, "values": v, "kind": kind, "neg": neg,
                         "yoy": yoy(v[0], v[1]) if len(v) > 1 else None})
        return rows

    latest = years[0]
    total = r(annual.get(latest, {}).get("total_assets"), MN, 1)
    asset_items = [
        ("客户贷款和垫款（净额）", r(annual[latest].get("loan_advance"), MN, 1)),
        ("金融投资", r(fin_invest(latest), MN, 1)),
        ("存放同业及拆出资金", r(derived("_interbank_asset", latest), MN, 1)),
        ("现金及存放中央银行", r(annual[latest].get("cash_deposit_pbc"), MN, 1)),
        ("买入返售金融资产", r(annual[latest].get("buy_resale"), MN, 1)),
    ]
    known = sum(v for _, v in asset_items if v is not None)
    asset_items.append(("其他资产", None if total is None else round(total - known, 1)))

    liab_items = [
        ("客户存款", r(annual[latest].get("accept_deposit"), MN, 1)),
        ("同业存放及拆入", r(derived("_interbank_liab", latest), MN, 1)),
        ("卖出回购", r(annual[latest].get("sell_repo"), MN, 1)),
        ("向中央银行借款", r(annual[latest].get("loan_pbc"), MN, 1)),
        ("应付债券", r(annual[latest].get("bond_payable"), MN, 1)),
    ]
    total_liab = r(annual[latest].get("total_liabilities"), MN, 1)
    known_l = sum(v for _, v in liab_items if v is not None)
    liab_items.append(("其他负债", None if total_liab is None else round(total_liab - known_l, 1)))
    liab_items.append(("归属于本行股东权益", r(annual[latest].get("parent_equity"), MN, 1)))
    liab_items.append(("少数股东权益", r(annual[latest].get("minority_equity"), MN, 1)))

    return {"years": years, "income": build(income),
            "balance": build(balance), "cashflow": build(cashflow),
            "bsStructure": {
                "year": latest, "total": total,
                "assets": [{"name": n, "value": v} for n, v in asset_items if v],
                "claims": [{"name": n, "value": v} for n, v in liab_items if v],
            }}


def build(code: str) -> dict:
    src = json.loads((TABLES / f"bank_{code}_annual.json").read_text(encoding="utf-8"))
    annual = src["annual"]
    years = sorted(annual)
    latest, prev = years[-1], years[-2]
    cur, pre = annual[latest], annual[prev]

    cost_income = [ratio(annual[y].get("manage_expense"), annual[y].get("operate_income"))
                   for y in years]
    # 信贷成本率 = 信用减值损失 / 期初期末平均贷款总额
    credit_cost = []
    for i, y in enumerate(years):
        loss = annual[y].get("credit_impairment")
        cur_loan, prev_loan = annual[y].get("gross_loans"), annual[years[i - 1]].get("gross_loans") if i else None
        avg = None
        if cur_loan is not None and prev_loan is not None:
            avg = (cur_loan + prev_loan) / 2
        elif cur_loan is not None:
            avg = cur_loan
        credit_cost.append(ratio(loss, avg))

    kpi = {
        "year": latest,
        "revenue_yi": r(cur.get("operate_income"), YI),
        "revenue_yoy": yoy(cur.get("operate_income"), pre.get("operate_income")),
        "netprofit_yi": r(cur.get("netprofit"), YI),
        "netprofit_yoy": yoy(cur.get("netprofit"), pre.get("netprofit")),
        "parent_netprofit_yi": r(cur.get("parent_netprofit"), YI),
        "parent_netprofit_yoy": yoy(cur.get("parent_netprofit"), pre.get("parent_netprofit")),
        "roe": cur.get("roe_weighted"),
        "roe_chg": None if None in (cur.get("roe_weighted"), pre.get("roe_weighted"))
                   else round(cur["roe_weighted"] - pre["roe_weighted"], 2),
        "npl": cur.get("npl_ratio"),
        "npl_chg": None if None in (cur.get("npl_ratio"), pre.get("npl_ratio"))
                   else round(cur["npl_ratio"] - pre["npl_ratio"], 2),
        "nim": cur.get("nim"),
        "nim_chg": None if None in (cur.get("nim"), pre.get("nim"))
                   else round(cur["nim"] - pre["nim"], 2),
        "cost_income": cost_income[-1],
        "provision_coverage": cur.get("provision_coverage"),
        "car": cur.get("car"), "cet1": cur.get("cet1"), "tier1": cur.get("tier1"),
        "eps": cur.get("eps"), "bps": cur.get("bps"),
        "staff_num": cur.get("staff_num"),
        "total_share_yi": r(cur.get("total_share"), YI),
        "opinion": cur.get("opinion_type"),
    }

    return {
        "code": code,
        "name": src["name"],
        "fetchedAt": src["fetched_at"],
        "source": src["source"],
        "years": years,
        "revenue": series(annual, years, "operate_income", YI),
        "parentProfit": series(annual, years, "parent_netprofit", YI),
        "assets": series(annual, years, "total_assets", YI),
        "deposit": series(annual, years, "total_deposits", YI),
        "loan": series(annual, years, "gross_loans", YI),
        "npl": series(annual, years, "npl_ratio"),
        "car": series(annual, years, "car"),
        "cet1": series(annual, years, "cet1"),
        "tier1": series(annual, years, "tier1"),
        "nim": series(annual, years, "nim"),
        "nis": series(annual, years, "nis"),
        "provisionCoverage": series(annual, years, "provision_coverage"),
        "loanProvision": series(annual, years, "loan_provision_ratio"),
        "roe": series(annual, years, "roe_weighted"),
        "eps": series(annual, years, "eps"),
        "ltd": series(annual, years, "ltd_ratio"),
        "costIncome": cost_income,
        "creditCost": credit_cost,
        "kpi": kpi,
        "statements": statement_rows(annual, [latest, prev, years[-3]]),
        "holdersEndDate": src["holders_end_date"],
        "holders": src["holders"],
    }


def main() -> None:
    data = {code: build(code) for code in CODES}
    body = json.dumps(data, ensure_ascii=False, indent=1)
    OUT.write_text(
        "/* 自动生成，请勿手工编辑。\n"
        " * 生成脚本：data/extract/gen_bank_dashboard_data.py\n"
        " * 数据源：data/tables/bank_<code>_annual.json（东方财富 F10，取值源自各期年度报告）\n"
        " * 金额序列单位：亿元；三张表单位：百万元；比率单位：%\n"
        " */\n"
        "window.BANK_QUANT = " + body + ";\n",
        encoding="utf-8")
    for code, d in data.items():
        print(f"[gen] {d['name']} {code}: {d['years'][0]}~{d['years'][-1]} "
              f"({len(d['years'])} 年), 股东 {len(d['holders'])} @ {d['holdersEndDate']}")
    print(f"    -> {OUT.relative_to(ROOT)}  ({OUT.stat().st_size/1024:.1f} KB)")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:                          # noqa: BLE001
        print(f"[error] {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
