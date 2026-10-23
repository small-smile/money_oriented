#!/usr/bin/env python3
"""百度长序列财务表：SEC XBRL companyfacts -> data/tables/tech_09888_annual.json。

为什么用 XBRL 而不是逐份 20-F 手抄：companyfacts 是 SEC 按提交件汇总的结构化事实，
与 20-F 正文同源（同一份 XBRL 实例），覆盖 FY2007 起全部年度，比逐份 PDF/HTML 抄数
既全又不会抄错。FY2005–2006 早于 XBRL 强制期，只能从 20-F 正文补（放 manual 表）。

口径：合并报表、人民币元（本脚本转成百万元）；`netIncome` 为归属百度股东的净利润
（us-gaap:NetIncomeLoss，US GAAP 下即 attributable to parent），`netIncomeIncNci`
含少数股东（ProfitLoss）。同一年份在多份 20-F 里可能有重述值，取**最新提交件**的值。

输入 data/raw/sec_companyfacts_09888.json 与输出表都已不落盘：原文存 MySQL json_file 表，
经 backend/jsonstore.py 按原文件路径读写。

用法：./venv/bin/python data/extract/gen_baidu_tables.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from backend import jsonstore  # noqa: E402  JSON 原文在 MySQL json_file 表，按原文件路径取

FACTS = ROOT / "data" / "raw" / "sec_companyfacts_09888.json"
OUT = ROOT / "data" / "tables" / "tech_09888_annual.json"

# 每个指标给一串候选 tag（新旧准则换过标签），按顺序取，后面的只补前面缺的年份
DURATION = {
    "revenue": ["RevenueFromContractWithCustomerExcludingAssessedTax",
                "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet"],
    "adRevenue": ["AdvertisingRevenue"],
    "otherRevenue": ["OtherSalesRevenueNet"],
    "costOfRevenue": ["CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfServices"],
    "operatingIncome": ["OperatingIncomeLoss"],
    "netIncome": ["NetIncomeLoss"],
    "netIncomeIncNci": ["ProfitLoss"],
    "rd": ["ResearchAndDevelopmentExpense"],
    "selling": ["SellingGeneralAndAdministrativeExpense", "GeneralAndAdministrativeExpense"],
    "opCashFlow": ["NetCashProvidedByUsedInOperatingActivities",
                   "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"],
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment"],
    "buyback": ["PaymentsForRepurchaseOfCommonStock"],
    "sbc": ["ShareBasedCompensation"],
    "incomeTax": ["IncomeTaxExpenseBenefit"],
    "interestIncome": ["InvestmentIncomeInterest"],
    "equityMethodPnl": ["IncomeLossFromEquityMethodInvestments"],
    # 减值单列：2025 年的经营亏损主要由长期资产减值造成，不单列就解释不了利润率断崖。
    # 2011–2024 用汇总口径 AssetImpairmentCharges，FY2025 20-F 改用长期资产减值标签
    "assetImpairment": ["AssetImpairmentCharges", "ImpairmentOfLongLivedAssetsHeldForUse"],
    "goodwillImpairment": ["GoodwillImpairmentLoss"],
}
INSTANT = {
    "assets": ["Assets"],
    "liabilities": ["Liabilities"],
    "liabilitiesCurrent": ["LiabilitiesCurrent"],
    "equity": ["StockholdersEquity"],
    "equityIncNci": ["StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
    "minorityInterest": ["MinorityInterest"],
    "cash": ["CashAndCashEquivalentsAtCarryingValue"],
    "shortTermInv": ["ShortTermInvestments", "OtherShortTermInvestments"],
    "goodwill": ["Goodwill"],
    "ppe": ["PropertyPlantAndEquipmentNet"],
    "opLeaseRou": ["OperatingLeaseRightOfUseAsset"],
    # LongTermDebt 是含当期部分的有息负债总额（2015 起披露）；更早年份只有分项票据
    "longTermDebt": ["LongTermDebt", "LongTermDebtNoncurrent", "LongTermNotesPayable"],
    "longTermDebtCurrent": ["LongTermDebtCurrent"],
    "convertibleDebt": ["ConvertibleDebtNoncurrent"],
    "seniorNotes": ["SeniorLongTermNotes"],
}


def load() -> dict:
    return jsonstore.read(FACTS)["facts"]["us-gaap"]


def pick(us: dict, tags: list[str], instant: bool) -> dict[int, float]:
    """{年: 值}。tag 列表按优先级：**后面的 tag 只补前面缺的年份**，
    同一 tag 内同年多条时按 (提交年 fy, accn) 取最新一条，即最新提交件的口径。

    这里必须按 tag 分层合并，不能把所有 tag 的行混在一起比 rank——同一年份不同 tag
    的 fy/accn 会打平，后写入的 tag 就会盖掉首选 tag（曾把 2025 年 longTermDebt
    从 LongTermDebt 的 41,310 覆盖成分项票据的 14,271）。
    """
    out: dict[int, float] = {}
    for tag in tags:
        node = us.get(tag)
        if not node:
            continue
        best: dict[int, tuple] = {}
        for unit, rows in node["units"].items():
            if unit != "CNY":
                continue
            for r in rows:
                st, en = r.get("start"), r.get("end")
                if not en or en[5:7] != "12":
                    continue
                if instant:
                    if st:
                        continue
                    year = int(en[:4])
                elif st and st[5:7] == "01" and en[:4] == st[:4]:
                    year = int(en[:4])
                else:
                    continue
                rank = (r.get("fy") or 0, r.get("accn") or "")
                prev = best.get(year)
                # 同年优先留「更晚提交件」的值；同一提交件内前后重复取后者
                if prev is None or rank >= prev[0]:
                    best[year] = (rank, r["val"])
        for year, v in best.items():
            out.setdefault(year, v[1])
    return dict(sorted(out.items()))


def main() -> int:
    us = load()
    series: dict[str, dict[int, float]] = {}
    for name, tags in DURATION.items():
        series[name] = pick(us, tags, instant=False)
    for name, tags in INSTANT.items():
        series[name] = pick(us, tags, instant=True)

    years = sorted({y for s in series.values() for y in s})
    annual: dict[str, dict] = {}
    for y in years:
        row = {}
        for k, s in series.items():
            if y in s:
                row[k] = round(s[y] / 1e6, 1)          # 元 -> 百万元
        # 派生：毛利率 / 营业利润率 / 净利率 / 研发费用率（分母缺就不算）
        rev = row.get("revenue")
        if rev:
            if "costOfRevenue" in row:
                row["grossMargin"] = round((rev - row["costOfRevenue"]) / rev * 100, 2)
            for k, name in (("operatingIncome", "opMargin"), ("netIncome", "netMargin"),
                            ("rd", "rdRatio")):
                if k in row:
                    row[name] = round(row[k] / rev * 100, 2)
        annual[str(y)] = row

    # 派生：ROE（净利润 / 期初期末平均归母权益）与净现金（现金 + 短期投资 − 有息负债）
    for y in years:
        row, prev = annual[str(y)], annual.get(str(y - 1))
        eq, eq0 = row.get("equity"), (prev or {}).get("equity")
        if row.get("netIncome") is not None and eq:
            base = (eq + eq0) / 2 if eq0 else eq
            row["roe"] = round(row["netIncome"] / base * 100, 2)
        if row.get("cash") is not None:
            row["netCash"] = round(row["cash"] + row.get("shortTermInv", 0)
                                   - row.get("longTermDebt", 0), 1)

    out = {
        "_meta": {
            "company": "百度集团股份有限公司 Baidu, Inc.",
            "codes": {"hk": "09888", "us": "BIDU"},
            "unit": "人民币百万元（比率为 %）",
            "source": "SEC XBRL companyfacts CIK 0001329099（与历年 20-F 同源）",
            "generated_by": "data/extract/gen_baidu_tables.py",
            "note": "同一年份存在重述时取最新提交件口径；FY2005–2006 早于 XBRL 期，见 tech_09888_manual.json",
        },
        "annual": annual,
    }
    jsonstore.write(OUT, out, ensure_ascii=False, indent=1)

    print(f"写入 {OUT.relative_to(ROOT)}  年份 {years[0]}–{years[-1]}（{len(years)}）")
    for k in list(DURATION) + list(INSTANT):
        s = series[k]
        if not s:
            print(f"  {k:16s} 无 CNY 数据")
            continue
        ys = sorted(s)
        gap = [y for y in range(ys[0], ys[-1] + 1) if y not in s]
        print(f"  {k:16s} {ys[0]}–{ys[-1]} 共 {len(ys)}"
              + (f"，缺 {gap}" if gap else "")
              + f"，末年 {s[ys[-1]] / 1e6:,.0f} 百万")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
