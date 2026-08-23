"""把 data/tables/bank_<code>_annual.json（+ 可选的 bank_<code>_shareholder_manual.json 手工年报覆盖层）
整理成银行详情页 7 个页面直接消费的 data/tables/company_charts_<code>.json。

背景：详情页（dashboard/company/bank/*.html）统一从 /api/company_charts?code=<code> 取一份大 JSON，
charts.js 按 key 渲染各图。601077 那份是手工精编的（41 个 key，含大量只有年报正文才有的明细），
本脚本只负责生成「能从 F10 年度数据推导出来的」那部分 key，其余 key 缺失时页面显示
「该行暂无此项数据」占位（charts.js 的 stub 逻辑）。

约定：
    - 金额：perf/scale-dep 用亿元；creditamount/bs-trend/bs 用百万元（与 601077 口径一致）
    - 比率：%，缺失年份保留 null
    - 不良生成率统一自 2018 年起（早年口径不可比，见 MEMORY 中的 2018 基准）
    - A+H 两地上市优先采用 A 股年报口径（手工覆盖层里的股东户数/前十大/分红即 A 股年报）

用法：
    python data/extract/gen_company_charts.py            # 生成 CODES 全部
    python data/extract/gen_company_charts.py 600036     # 只生成指定行
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
TABLES = ROOT / "data" / "tables"

YI = 1e8        # 元 -> 亿元
MN = 1e6        # 元 -> 百万元

# 生成范围：全部 42 家 A 股上市银行 + 2 家纯 H 股行。601077（渝农商行）为手工精编，
# 不在此列、不要覆盖（main() 里也硬跳过）。缺 annual.json 的代码由 main() 优雅跳过。
CODES = [
    # 国有大行
    "601398", "601288", "601988", "601939", "601328", "601658",
    # 股份行
    "600036", "601166", "600000", "601998", "600016", "000001",
    "600015", "601818", "601916",
    # 城商行
    "601169", "601229", "600919", "002142", "601009", "601838",
    "600926", "601187", "002936", "002948", "601577", "002966",
    "601963", "601665", "601997", "600928", "001227",
    # 农商行（601077 手工精编，不在此列）
    "601825", "601128", "002958", "600908", "002807", "601860",
    "002839", "601528", "603323",
    # 纯 H 股
    "01578", "01916", "06138",
]

# 银行名录：shortName 取自 annual 里的 name，这里只补全称与 H 股代码
BANKS = {
    "601077": {"fullName": "重庆农村商业银行", "hCode": "03618"},
    # 国有大行
    "601398": {"fullName": "中国工商银行股份有限公司", "hCode": "01398"},
    "601288": {"fullName": "中国农业银行股份有限公司", "hCode": "01288"},
    "601988": {"fullName": "中国银行股份有限公司", "hCode": "03988"},
    "601939": {"fullName": "中国建设银行股份有限公司", "hCode": "00939"},
    "601328": {"fullName": "交通银行股份有限公司", "hCode": "03328"},
    "601658": {"fullName": "中国邮政储蓄银行股份有限公司", "hCode": "01658"},
    # 股份行
    "600036": {"fullName": "招商银行股份有限公司", "hCode": "03968"},
    "601166": {"fullName": "兴业银行股份有限公司", "hCode": ""},
    "600000": {"fullName": "上海浦东发展银行股份有限公司", "hCode": ""},
    "601998": {"fullName": "中信银行股份有限公司", "hCode": "00998"},
    "600016": {"fullName": "中国民生银行股份有限公司", "hCode": "01988"},
    "000001": {"fullName": "平安银行股份有限公司", "hCode": ""},
    "600015": {"fullName": "华夏银行股份有限公司", "hCode": ""},
    "601818": {"fullName": "中国光大银行股份有限公司", "hCode": "06818"},
    "601916": {"fullName": "浙商银行股份有限公司", "hCode": "02016"},
    # 城商行
    "601169": {"fullName": "北京银行股份有限公司", "hCode": ""},
    "601229": {"fullName": "上海银行股份有限公司", "hCode": ""},
    "600919": {"fullName": "江苏银行股份有限公司", "hCode": ""},
    "002142": {"fullName": "宁波银行股份有限公司", "hCode": ""},
    "601009": {"fullName": "南京银行股份有限公司", "hCode": ""},
    "601838": {"fullName": "成都银行股份有限公司", "hCode": ""},
    "600926": {"fullName": "杭州银行股份有限公司", "hCode": ""},
    "601187": {"fullName": "厦门银行股份有限公司", "hCode": ""},
    "002936": {"fullName": "郑州银行股份有限公司", "hCode": "06196"},
    "002948": {"fullName": "青岛银行股份有限公司", "hCode": "03866"},
    "601577": {"fullName": "长沙银行股份有限公司", "hCode": ""},
    "002966": {"fullName": "苏州银行股份有限公司", "hCode": ""},
    "601963": {"fullName": "重庆银行股份有限公司", "hCode": "01963"},
    "601665": {"fullName": "齐鲁银行股份有限公司", "hCode": ""},
    "601997": {"fullName": "贵阳银行股份有限公司", "hCode": ""},
    "600928": {"fullName": "西安银行股份有限公司", "hCode": ""},
    "001227": {"fullName": "兰州银行股份有限公司", "hCode": ""},
    # 农商行
    "601825": {"fullName": "上海农村商业银行股份有限公司", "hCode": ""},
    "601128": {"fullName": "江苏常熟农村商业银行股份有限公司", "hCode": ""},
    "002958": {"fullName": "青岛农村商业银行股份有限公司", "hCode": ""},
    "600908": {"fullName": "无锡农村商业银行股份有限公司", "hCode": ""},
    "002807": {"fullName": "江苏江阴农村商业银行股份有限公司", "hCode": ""},
    "601860": {"fullName": "江苏紫金农村商业银行股份有限公司", "hCode": ""},
    "002839": {"fullName": "江苏张家港农村商业银行股份有限公司", "hCode": ""},
    "601528": {"fullName": "浙江绍兴瑞丰农村商业银行股份有限公司", "hCode": ""},
    "603323": {"fullName": "江苏苏州农村商业银行股份有限公司", "hCode": ""},
}

# 对标行后缀 -> 代码（与 charts.js 里 nplAbc/nplCmb/nplPsb 等字段名对应）
PEERS = [("Abc", "601288"), ("Cmb", "600036"), ("Psb", "601658")]
# 对标行代码 -> 简称（风控页图表标题按本行 + 对标行拼接，剔除自己）
PEER_NAMES = {"601288": "农业银行", "600036": "招商银行", "601658": "邮储银行"}

START_PERF = "2009"    # 营收/利润/ROE 起点（与 601077 的 17 年窗口一致）
START_MAIN = "2010"    # 规模/资产质量/息差等主序列起点
START_PROV = "2013"    # 拨备覆盖率/拨贷比起点
NEW_STD = "2018"       # 新金融工具准则（信用减值损失）起点


def r(v, div=1.0, nd=2):
    return None if v is None else round(v / div, nd)


def ratio(num, den, nd=2):
    if num is None or den in (None, 0):
        return None
    return round(num / den * 100, nd)


_CACHE: dict[str, dict] = {}


def load_annual(code: str) -> dict:
    """读 bank_<code>_annual.json（带缓存，对标行会被反复用到）。"""
    if code not in _CACHE:
        _CACHE[code] = json.loads((TABLES / f"bank_{code}_annual.json").read_text(encoding="utf-8"))
    return _CACHE[code]


def load_manual(code: str) -> dict | None:
    """读手工年报覆盖层（股东户数/前十大/分红/文案），没有就返回 None。"""
    p = TABLES / f"bank_{code}_shareholder_manual.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def load_ar_manual(code: str) -> dict | None:
    """读逐年年报手工提取层 bank_<code>_ar_manual.json（纯 H 股行的数据底稿，
    港交所 H 股年报逐年读出来的值）。这里只取它的港交所口径集中度序列——
    该文件的财务序列本来是 fetch_bank_financials.py 的输入，不在本脚本里消费。"""
    p = TABLES / f"bank_{code}_ar_manual.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def load_detail(code: str) -> dict | None:
    """读风控/负债/简介等专属明细键的年报覆盖层（迁徙率/重定价/期限/五级分类/员工构成/
    高管薪酬/分部/行业投向/存款成本/贷款结构/公允价值层级/现金流等，均需语义读年报 PDF）。
    顶层键即 charts.js 消费的图表数据键（migrate/repricing/maturity/nim/5tier/cf/... ），
    另可带 `_notes`（DOM id -> 文案）在页面上补充本行专属说明。没有该文件就返回 None。"""
    p = TABLES / f"bank_{code}_detail_manual.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def ser(annual: dict, years: list[str], key: str, div=None, nd=2) -> list:
    out = []
    for y in years:
        v = annual.get(y, {}).get(key)
        out.append(r(v, div, nd) if div else (None if v is None else round(v, nd)))
    return out


def ser_ratio(annual: dict, years: list[str], num_key: str, den_key: str, nd=2) -> list:
    return [ratio(annual.get(y, {}).get(num_key), annual.get(y, {}).get(den_key), nd) for y in years]


def ser_formation(annual: dict, years: list[str]) -> list:
    """不良生成率：统一自 2018 年起取用（早年口径不可比）。"""
    return [r(annual.get(y, {}).get("npl_formation_rate")) if y >= NEW_STD else None for y in years]


def ser_cost_income(annual: dict, years: list[str]) -> list:
    """成本收入比：A 股行用「业务及管理费 ÷ 营业收入」自算；纯 H 股行的覆盖层无业务及管理费
    （营业支出含税金及附加，不能替代），退回年报披露的成本收入比。"""
    out = []
    for y in years:
        a = annual.get(y, {})
        v = ratio(a.get("manage_expense"), a.get("operate_income"))
        out.append(v if v is not None else r(a.get("cost_income_ratio")))
    return out


def ser_imp(annual: dict, years: list[str], new: bool) -> list:
    """信用/资产减值损失占营收比：2018 前后分属旧/新准则两条线。"""
    key = "credit_impairment" if new else "asset_impairment"
    out = []
    for y in years:
        if (y >= NEW_STD) != new:
            out.append(None)
            continue
        out.append(ratio(annual.get(y, {}).get(key), annual.get(y, {}).get("operate_income")))
    return out


# ────────────────────────── 资产负债结构（最新年，百万元） ──────────────────────────

def fin_invest(a: dict):
    """金融投资合计：披露模板不同，按存在的字段组合，避免重复计入（同 gen_bank_dashboard_data.py）。"""
    def s(*keys):
        parts = [a.get(k) for k in keys if a.get(k) is not None]
        return sum(parts) if parts else None

    if a.get("amortize_cost_finasset") is not None:
        base = s("fvtpl_finasset", "amortize_cost_finasset")
        fvtoci = a.get("fvtoci_finasset")
        if fvtoci is None:
            fvtoci = s("other_creditor_invest", "other_equity_invest")
        if base is None:
            return fvtoci
        return base + (fvtoci or 0)
    return s("trade_finasset", "creditor_invest", "other_creditor_invest", "other_equity_invest")


def _sum(a: dict, *keys):
    parts = [a.get(k) for k in keys if a.get(k) is not None]
    return sum(parts) if parts else None


def build_bs(a: dict) -> dict:
    """最新年资产/权益结构饼图：明细取已披露科目，差额归入「其他资产/其他负债」。"""
    total = r(a.get("total_assets"), MN, 1)
    assets = [
        ("客户贷款和垫款（净额）", r(a.get("loan_advance"), MN, 1)),
        ("金融投资", r(fin_invest(a), MN, 1)),
        ("存放同业及拆出资金", r(_sum(a, "deposit_interbank", "lend_fund"), MN, 1)),
        ("现金及存放中央银行", r(a.get("cash_deposit_pbc"), MN, 1)),
        ("买入返售金融资产", r(a.get("buy_resale"), MN, 1)),
    ]
    known = sum(v for _, v in assets if v is not None)
    if total is not None:
        assets.append(("其他资产", round(total - known, 1)))

    claims = [
        ("客户存款", r(a.get("accept_deposit"), MN, 1)),
        ("同业存放及拆入", r(_sum(a, "iofi_deposit", "borrow_fund"), MN, 1)),
        ("卖出回购", r(a.get("sell_repo"), MN, 1)),
        ("向中央银行借款", r(a.get("loan_pbc"), MN, 1)),
        ("应付债券", r(a.get("bond_payable"), MN, 1)),
    ]
    total_liab = r(a.get("total_liabilities"), MN, 1)
    known_l = sum(v for _, v in claims if v is not None)
    if total_liab is not None:
        claims.append(("其他负债", round(total_liab - known_l, 1)))
    claims.append(("归属于本行股东权益", r(a.get("parent_equity"), MN, 1)))
    claims.append(("少数股东权益", r(a.get("minority_equity"), MN, 1)))

    return {"assets": [{"name": n, "value": v} for n, v in assets if v],
            "claims": [{"name": n, "value": v} for n, v in claims if v]}


# ────────────────────────── 股东结构 ──────────────────────────

CAT = {
    "soe":   {"title": "国有股东",     "color": "#c0392b"},
    "hk":    {"title": "境外 / H 股",  "color": "#16a085"},
    "ssf":   {"title": "社保基金",     "color": "#f1c40f"},
    "ins":   {"title": "保险资金",     "color": "#2980b9"},
    "corp":  {"title": "内资法人",     "color": "#e67e22"},
    "other": {"title": "其他",         "color": "#6c3483"},
    "float": {"title": "其他流通股东", "color": "#95a5a6"},
}

# 无手工覆盖层时，按股东名称关键词归类（页面脚注会注明归类为自动推导）
KEYWORDS = [
    (("社会保障", "社保"), "ssf"),
    (("人寿", "保险", "养老", "太平洋财险"), "ins"),
    (("香港中央结算", "沪股通", "深股通", "H股", "汇丰", "渣打", "澳新"), "hk"),
    (("汇金", "财政部", "证券金融", "烟草", "国有资产", "国资", "投资集团", "控股集团"), "soe"),
]


def classify(name: str) -> str:
    for words, key in KEYWORDS:
        if any(w in name for w in words):
            return key
    return "corp"


def build_holders(top10: list, top10_sum: float) -> dict:
    """top10 行 [name, pct, chg, typeLabel, catKey] -> charts.js 的 holders 载荷。"""
    holder_data = [{"name": h[0], "value": h[1], "itemStyle": {"color": CAT[h[4]]["color"]}} for h in top10]
    float_pct = round(100 - top10_sum, 2)
    holder_data.append({"name": "其他流通股东", "value": float_pct,
                        "itemStyle": {"color": CAT["float"]["color"]}})

    holders = [{"name": h[0], "pct": h[1], "chg": h[2], "type": h[3]} for h in top10]
    holders.append({"name": "其他流通股东", "pct": float_pct, "chg": "—", "type": "流通股"})

    order, grp = [], {}
    for h in top10:
        k = h[4]
        if k not in grp:
            grp[k] = {"title": CAT[k]["title"], "color": CAT[k]["color"], "names": []}
            order.append(k)
        grp[k]["names"].append(h[0])
    grp["float"] = {"title": CAT["float"]["title"], "color": CAT["float"]["color"],
                    "names": ["其他流通股东"]}
    order.append("float")

    return {"holders": holders, "holderData": holder_data,
            "factions": [grp[k] for k in order],
            "centerText": "前十大\n%.2f%%" % top10_sum}


def top10_from_annual(src: dict) -> tuple[list, float]:
    """没有手工覆盖层时，用 F10 的十大股东（annual.holders）拼一份，性质按名称关键词推导。"""
    rows = []
    for h in sorted(src.get("holders") or [], key=lambda x: x.get("rank") or 99):
        name, pct = h.get("name"), h.get("ratio")
        if not name or pct is None:
            continue
        cat = classify(name)
        label = CAT[cat]["title"] + ("（%s）" % h["shares_type"] if h.get("shares_type") else "")
        rows.append([name, round(pct, 2), h.get("change") or "—", label, cat])
    return rows, round(sum(x[1] for x in rows), 2)


# 第一大股东名称在图例/tooltip 里要短。F10 里同一个股东跨年有多种写法
# （汇金公司 / 中央汇金投资有限责任公司、财政部 / 中华人民共和国财政部(财政部)），一并归一。
HOLDER_ALIAS = [
    ("香港中央结算(代理人)", "香港中央结算（代理人）"),
    ("香港中央结算", "香港中央结算（沪股通）"),
    ("中央汇金", "中央汇金"),
    ("汇金公司", "中央汇金"),
    ("财政部", "财政部"),
    ("財政部", "财政部"),
    ("全国社会保障基金", "社保基金会"),
]
SUFFIX = ("股份有限公司", "有限责任公司", "有限公司", "集团公司")


def short_holder(name: str) -> str:
    n = (name or "").strip()
    for kw, short in HOLDER_ALIAS:
        if kw in n:
            return short
    for suf in SUFFIX:
        if n.endswith(suf):
            n = n[: -len(suf)]
            break
    return n if len(n) <= 14 else n[:13] + "…"


def build_concentration(src: dict, is_ah: bool) -> dict | None:
    """holder_concentration（fetch 脚本按报告期算好的）-> 集中度图载荷。

    raw 每行 5 列 [报告期, 第一大, 前三大, 前十大, 其他流通股东]，与 601077 精编文件同构；
    第一大股东名称逐期不同（改名 / 换人），单独走并行数组 top1Names，不塞进 raw 当第 6 列。
    剔除「香港中央结算」名义持有人后的第一大 / 前三大另走并行数组 top1Ex / top3Ex / top1ExNames，
    只有含 HKSCC 的报告期才与原值不同，charts.js 据此决定是否画「剔除香港中央结算」线。

    仅 A+H 两地上市行（is_ah，本行有 H 股代码）才输出剔除口径：H 股由「香港中央结算（代理人）」
    名义代持、是这些行名义第一大的成因，剔除后才看得出真实实益股东。纯 A 股行即便前十大里有
    「香港中央结算有限公司」（沪深股通北向名义持有人，如兴业 601166 / 瑞丰 601528），也按 A 股
    定期报告如实披露、不做剔除——沪深股通持股占比小、并非名义第一大，剔除反而失真（milestone
    「A 或 H 单独上市披露前十大原值，A+H 才从 A 披露剔除香港中央结算/香港代理人」）。
    """
    conc = src.get("holder_concentration") or []
    if len(conc) < 4:                       # 少于 4 期画不出趋势，宁可显示占位
        return None
    out = {
        "raw": [[c["date"], c["top1"], c["top3"], c["top10"], round(100 - c["top10"], 2)]
                for c in conc],
        "top1Names": [short_holder(c["top1_name"]) for c in conc],
    }
    if is_ah:
        out["top1Ex"] = [c.get("top1_ex") for c in conc]
        out["top3Ex"] = [c.get("top3_ex") for c in conc]
        out["top1ExNames"] = [short_holder(c["top1_ex_name"]) if c.get("top1_ex_name") else ""
                              for c in conc]
    return out


def build_share_capital(annual: dict, years: list[str]) -> dict | None:
    """历年总股本（亿股）。取资产负债表「股本」科目——面值 1 元，元金额即股数。

    total_share（ISSUED_COMMON_SHARES）是今天的快照回填到所有年份，不能用来看历年变动。
    缺失/为 0 的年份整年剔除（农行 2002–2006、建行 2003 的 share_capital 为空），
    页面脚注里点名，不做插值。
    """
    ys, shares, gaps = [], [], []
    for y in years:
        v = annual.get(y, {}).get("share_capital")
        if not v:
            gaps.append(y)
            continue
        ys.append(y)
        shares.append(round(v / YI, 2))
    if len(ys) < 3:
        return None
    return {"years": ys, "shares": shares, "gaps": gaps}


def build_invest(annual: dict, years: list[str]) -> dict | None:
    """金融投资按 IFRS9 三分类拆分（亿元）：摊余成本(AC) / 其他债权投资(FVOCI债) /
    其他权益工具(FVOCI股) / 交易性金融资产(FVTPL)。

    只在 2018 年新准则起有意义（早年为「持有至到期/可供出售/交易性」旧四分类，不可比），
    故 years8 取 NEW_STD 起。字段名两套模板：招行/工行系用 amortize_cost_finasset + fvtpl_finasset；
    邮储/城商行系用 creditor_invest（债权投资）+ trade_finasset（交易性金融资产），此处一并兜底。
    至少要 3 个年份且当年有摊余成本科目才画，否则整 key 缺失走占位。
    """
    ys = [y for y in years if y >= NEW_STD]
    # AC（摊余成本/债权投资）：两套模板字段名不同
    ac = [r(annual.get(y, {}).get("amortize_cost_finasset")
            if annual.get(y, {}).get("amortize_cost_finasset") is not None
            else annual.get(y, {}).get("creditor_invest"), YI, 1) for y in ys]
    fvociEq = ser(annual, ys, "other_equity_invest", YI, 1)
    # FVOCI 债权：招行/渝农商行拆了 other_creditor_invest；国有大行只报合计 fvtoci_finasset，
    # 拆不出债/股时用合计口径回填到「债权」这一档（权益档通常极小），页面脚注注明。
    fvociDebt = []
    for y in ys:
        a = annual.get(y, {})
        v = a.get("other_creditor_invest")
        if v is None:
            fv = a.get("fvtoci_finasset")
            v = None if fv is None else (fv - (a.get("other_equity_invest") or 0))
        fvociDebt.append(r(v, YI, 1))
    fvtpl = [r(annual.get(y, {}).get("fvtpl_finasset")
              if annual.get(y, {}).get("fvtpl_finasset") is not None
              else annual.get(y, {}).get("trade_finasset"), YI, 1) for y in ys]
    if len([v for v in ac if v is not None]) < 3:
        return None
    return {"years8": ys, "ac": ac, "fvociDebt": fvociDebt, "fvociEq": fvociEq, "fvtpl": fvtpl}



# ────────────────────────── 生成文案（覆盖页面上的渝农商行静态文案） ──────────────────────────

def dividend_cards(name: str, annual: dict, div: dict) -> str | None:
    """分红卡片：最近年度每 10 股派现 -> 现金分红总额（亿元）与分红率，再给近五年累计。

    现金分红 = 每 10 股派现 ÷ 10 × 当年末总股本；分红率 = 现金分红 ÷ 归母净利润。
    注意口径：总股本用当年末数，若当年有增发/转股，与实际派现基数会有出入，故文案里写"约"。
    """
    years, per10 = div.get("years9") or [], div.get("per10") or []
    pairs = [(y, p) for y, p in zip(years, per10) if p]
    if not pairs:
        return None

    def amount(y, p):
        sc = annual.get(y, {}).get("share_capital")
        return None if not sc else p / 10 * sc / YI

    ly, lp = pairs[-1]
    li = ["%s 年度每 10 股派现：<b>%.4f 元</b>（含税）" % (ly, lp)]
    amt = amount(ly, lp)
    if amt:
        li.append("对应现金分红约 <b>%.0f 亿元</b>" % amt)
        np_ = annual.get(ly, {}).get("parent_netprofit")
        if np_:
            li.append("分红率（占归母净利润）约 <b>%.1f%%</b>" % (amt * YI / np_ * 100))
    five = [(y, p) for y, p in pairs if y >= str(int(ly) - 4)]
    cum = [amount(y, p) for y, p in five]
    if all(cum) and len(five) > 1:
        li.append("近 %d 年（%s–%s）累计分红约 <b>%.0f 亿元</b>" %
                  (len(five), five[0][0], ly, sum(cum)))
    return ('<div class="card2"><h3>%s %s 年度分红</h3><ul>%s</ul></div>'
            % (name, ly, "".join("<li>%s</li>" % x for x in li)))


def share_capital_note(name: str, sc: dict) -> str:
    span = "%s–%s" % (sc["years"][0], sc["years"][-1])
    chg = [(sc["years"][i], round(sc["shares"][i] - sc["shares"][i - 1], 2))
           for i in range(1, len(sc["years"])) if abs(sc["shares"][i] - sc["shares"][i - 1]) >= 0.01]
    body = ("%s %s 年总股本由 <b>%.2f 亿股</b>增至 <b>%.2f 亿股</b>，其间 <b>%d 个年份</b>发生变动："
            % (name, span, sc["shares"][0], sc["shares"][-1], len(chg)))
    body += "、".join("%s 年 %+.2f 亿股" % (y, d) for y, d in chg) + "。"
    body += ("数据来源：东方财富 F10 银行业资产负债表「股本」科目（面值 1 元，元金额即股数），"
             "取各年度年报期。<b>本图只给出股本数量的变动，未区分 IPO / 定向增发 / 配股 / "
             "转增股本等成因</b>——成因需读当年年报「股本变动及股东情况」章节，尚未逐年录入。")
    if sc.get("gaps"):
        body += " 缺口年份（接口未提供股本科目，已整年剔除，非零值）：%s。" % "、".join(sc["gaps"])
    return body


def concentration_note(name: str, conc: dict | None, hist: dict | None = None) -> str:
    """集中度三张柱图的脚注。

    conc = A 股定期报告口径（F10 按报告期汇总），hist = 港交所 H 股年报口径（手工逐年读年报）。
    两者在页面上是两个 series 单独披露，脚注也分段写清各自的来源与口径处理。
    """
    h_rows = (hist or {}).get("raw") or []
    if conc is None:                      # 纯 H 股行（天津/江西银行）：只有港交所口径
        return h_only_concentration_note(name, h_rows, (hist or {}).get("note") or "")
    raw, names = conc["raw"], conc["top1Names"]
    top10 = [r[3] for r in raw]
    lo, hi = min(top10), max(top10)
    lo_d, hi_d = raw[top10.index(lo)][0], raw[top10.index(hi)][0]
    extra = ""
    if h_rows:
        extra = ("另有 <b>%s–%s</b> 年共 %d 个年度取自本行 <b>H 股年报</b>（港交所披露口径），"
                 "在图上作为<b>单独一个 series</b>（浅色柱、图例「港交所披露」）披露——"
                 "两地披露的股东表范围不同（H 股年报里香港中央结算（代理人）名义持有全部 H 股），"
                 "不与 A 股口径合成一条序列。"
                 % (str(h_rows[0][0])[:4], str(h_rows[-1][0])[:4], len(h_rows)))
    return ("%s 共 <b>%d 个报告期</b>（%s ~ %s）的前十大股东合计占比在 <b>%.2f%%</b>（%s）"
            "~ <b>%.2f%%</b>（%s）之间；期末第一大股东为 <b>%s</b>（%.2f%%）。%s"
            "图上<b>每年只画一根柱</b>——取该年最后一个已披露报告期（一年里季报/中报多为同一批"
            "股东的重复值，全画只会更密而不更有信息），三个口径（第一大/前三大/前十大）各占一张图，"
            "纵轴按各自数据取整、不从 0 起，绝对水平看柱顶数值。"
            "「其他流通股东」= 100%% − 前十大合计，与前十大严格镜像，只在 tooltip 里给出。"
            "数据来源：东方财富 F10「前十名股东」接口，按各报告期（年报/中报/季报）披露的"
            "前十大股东持股比例汇总计算（占总股本）。口径处理："
            "① 事件型快照（过户日等非报告期，只列受影响的几名股东）整期剔除；"
            "② 同一股东被按股份类型拆成多行时先按名称合并再排序，不按接口名次；"
            "③ 个别期次接口漏掉了压倒性的第一大股东（如中央汇金、HKSCC 代理人），"
            "表现为合计突然塌陷，这类期次整期剔除、该年缺柱，不做插值。"
            % (name, len(raw), raw[0][0], raw[-1][0], lo, lo_d, hi, hi_d,
               names[-1], raw[-1][1], extra))


def h_only_concentration_note(name: str, h_rows: list, hist_note: str = "") -> str:
    """纯 H 股行的集中度脚注：数据全部来自港交所披露的 H 股年报，口径与 A 股定期报告不同。

    hist_note 为该行手工 overlay 里的 concentrationHistNote（逐年重构口径的具体交代），
    追加在通用口径说明之后——各行 H 股具名股东的去重方式、缺口年份都不一样。
    """
    t10 = [r[3] for r in h_rows if r[3] is not None]
    span = "%s ~ %s" % (h_rows[0][0], h_rows[-1][0])
    head = "%s 共 <b>%d 个年度</b>（%s）" % (name, len(h_rows), span)
    if t10:
        lo, hi = min(t10), max(t10)
        lo_d = next(r[0] for r in h_rows if r[3] == lo)
        hi_d = next(r[0] for r in h_rows if r[3] == hi)
        head += ("的前十大股东合计占比在 <b>%.2f%%</b>（%s）~ <b>%.2f%%</b>（%s）之间。"
                 % (lo, lo_d, hi, hi_d))
    else:
        head += "只披露到 5% 以上主要股东，前十大合计无从计算。"
    return (head +
            "本行<b>只在港交所上市</b>，数据全部逐年取自 <b>H 股年报</b>"
            "「股本变动及股东情况 / 主要股东权益」章节，与 A 股定期报告的「前十名股东」"
            "不是同一张表，故图例单列<b>「港交所披露（H 股年报口径）」</b>一项、单独披露。"
            "图上<b>每年只画一根柱</b>（年报期末口径），三个口径（第一大/前三大/前十大）各占一张图，"
            "纵轴按各自数据取整、不从 0 起，绝对水平看柱顶数值。"
            "「其他流通股东」= 100% − 前十大合计，与前十大严格镜像，只在 tooltip 里给出。"
            "口径处理：① 年报只单列「内资股前十大股东」的年份，按「内资股前十大（占总股本）"
            "＋ SFO 主要股东表里<b>具名披露的 H 股实益持有人</b>」合并排序取前十<b>重构</b>"
            "（柱身红色虚线框标出）；具名 H 股股东按年报附注的控制链去重，"
            "实益拥有人／受控法团／配偶／信托受托人指向同一批股份时只算一次；"
            "② 重构口径与年报自己披露的合并前十大表<b>对齐</b>——同样<b>不含</b>"
            "香港中央结算（代理人）名下其余 H 股散户（该账户是名义持有人而非实益股东）；"
            "③ 年报只披露到 5% 以上主要股东、凑不满前十名的年份，前十大合计留空缺柱，不做插值。"
            + (" 柱身红色虚线框的年份为重构口径（该年年报未直接披露含 H 股的合并前十大表）。"
               if any(str(r[-1]) == "recon" for r in h_rows) else "")
            + ((" " + hist_note) if hist_note else ""))


def holder_count_note(name: str, hc: dict) -> str:
    raw = hc["raw"]
    tot = [r[1] for r in raw if r[1] is not None]
    if not tot:      # 手工年报覆盖层只给 A/H 拆分、不给合计（如天津银行只有 H 股登记股东数）
        tot = [v for r in raw for v in r[2:] if v is not None] or [0]
    return ("%s 共 <b>%d 个披露期</b>（%s ~ %s）的股东户数：由 %s 户到 %s 户，"
            "区间最高 %s 户、最低 %s 户。A 股 / H 股拆分仅部分期次披露，未拆分的期次留空断线。"
            "数据来源：东方财富 F10「股东户数」接口（取值源自各期定期报告「股东情况」章节）；"
            "非报告期的快照（如 A 股上市首日）一并保留——那正是打新账户尚未离场的峰值。"
            % (name, len(raw), raw[0][0], raw[-1][0],
               f"{tot[0]:,}", f"{tot[-1]:,}", f"{max(tot):,}", f"{min(tot):,}"))


def page_meta(code: str, hcode: str, assets: float | None, latest: str) -> str:
    """页头副标题：页面写死的是渝农商行的代码/董监高，各行至少要换成自己的代码与规模。

    董事长/行长不在 F10 财务接口里（要读年报「公司治理」章节），故生成版只给可核对的三项：
    两地代码、最新年末总资产、金额单位。手工覆盖层给了 meta 的行仍以覆盖层为准。
    """
    bits = []
    if len(code) == 6:
        bits.append("A 股 %s（%s）" % (code, "上交所" if code[0] == "6" else "深交所"))
    if hcode:
        bits.append("H 股 %s（港交所）" % hcode)
    if assets:
        bits.append("%s 年末总资产 %s" % (latest, "%.2f 万亿元" % (assets / 1e12) if assets >= 1e12
                                        else "%.0f 亿元" % (assets / YI)))
    bits.append("单位：人民币百万元（另标注除外）")
    return " · ".join(bits)


def holders_sub(hc: dict | None, top10_sum: float | None, latest: str) -> str | None:
    """「股东及股东变动」小节副标题：期末股东户数（能拆 A/H 就拆）+ 前十大合计。

    页面上写死的是渝农商行的 116,634 户，这段有 id 但内容非图表，必须逐行替换；
    两项都拿不到时返回 None，由 .yns-only 门控整段隐藏，不让别的行显示渝农商行的数字。
    """
    bits = []
    if hc and hc.get("raw"):
        date, tot, a, h = (hc["raw"][-1] + [None] * 4)[:4]
        split = [x for x in (None if a is None else "A 股 %s 户" % f"{a:,}",
                             None if h is None else "H 股 %s 户" % f"{h:,}") if x]
        if tot is not None:
            bits.append("%s 股东总数 %s 户%s"
                        % (date, f"{tot:,}", "（%s）" % "、".join(split) if split else ""))
        elif split:
            bits.append("%s 股东户数：%s" % (date, "、".join(split)))
    if top10_sum:
        bits.append("%s 年报前十名股东合计持股 %.2f%%" % (latest, top10_sum))
    return " · ".join(bits) or None


def dividend_sub(div: dict | None) -> str | None:
    """「分红与股东回报」小节副标题：把渝农商行的上市日/年份区间换成本行的实际披露区间。"""
    years = (div or {}).get("years9") or []
    if not years:
        return None
    return ("来源：东方财富 F10「分红送配」逐年度利润分配方案 · %s–%s 年度每 10 股派现（含税）"
            "，同一年度多次派发（中期 + 末期）按年度合计" % (years[0], years[-1]))


# ────────────────────────── 主体 ──────────────────────────

def build(code: str) -> dict:
    src = load_annual(code)
    annual = src["annual"]
    manual = load_manual(code)
    all_years = sorted(annual)
    latest = all_years[-1]
    y_perf = [y for y in all_years if y >= START_PERF]
    years = [y for y in all_years if y >= START_MAIN]
    y_prov = [y for y in all_years if y >= START_PROV]
    y_staff = [y for y in years if annual[y].get("staff_num")]
    meta = BANKS.get(code, {})

    def roe_calc(y):
        """简单 ROE = 归母净利 / 平均归母权益（年报未披露加权 ROE 的年份用它兜底）。"""
        if annual[y].get("roe_weighted") is not None:
            return None
        i = all_years.index(y)
        cur = annual[y].get("parent_equity")
        prev = annual[all_years[i - 1]].get("parent_equity") if i else None
        den = (cur + prev) / 2 if None not in (cur, prev) else cur
        return ratio(annual[y].get("parent_netprofit"), den)

    scale = {
        "years": years,
        "deposit": ser(annual, years, "total_deposits", YI),
        "loan": ser(annual, years, "gross_loans", YI),
        "npl": ser(annual, years, "npl_ratio"),
        "car": ser(annual, years, "car"),
        "cet1": ser(annual, years, "cet1"),
        "overdue": ser_ratio(annual, years, "overdue_loans", "gross_loans"),
        "overdueAmt": ser(annual, years, "overdue_loans", YI),
        "nplAmt": ser(annual, years, "npl_amount", YI),
        "writeoffRate": ser_ratio(annual, years, "net_charge_off", "gross_loans"),
        "formation": ser_formation(annual, years),
    }
    equity_asset = {"years": years, "yrcb": ser(annual, years, "equity_asset_ratio")}
    nim = {
        "years10": years,
        "nim": ser(annual, years, "nim"),
        "nis": ser(annual, years, "nis"),
        "nonInt": [ratio(None if annual[y].get("operate_income") is None or annual[y].get("interest_ni") is None
                         else annual[y]["operate_income"] - annual[y]["interest_ni"],
                         annual[y].get("operate_income")) for y in years],
        "costIncome": ser_cost_income(annual, years),
        "yearsCC": years,
        "impOld": ser_imp(annual, years, new=False),
        "impNew": ser_imp(annual, years, new=True),
        "years13": y_prov,
        "provCov13": ser(annual, y_prov, "provision_coverage"),
        "provRatio": ser(annual, y_prov, "loan_provision_ratio"),
    }

    # 对标行序列（自己就是某个对标行时跳过该行，charts.js 会自动收起空系列）
    for suf, pcode in PEERS:
        if pcode == code:
            continue
        pa = load_annual(pcode)["annual"]
        scale["npl" + suf] = ser(pa, years, "npl_ratio")
        scale["overdue" + suf] = ser_ratio(pa, years, "overdue_loans", "gross_loans")
        scale["writeoffRate" + suf] = ser_ratio(pa, years, "net_charge_off", "gross_loans")
        scale["formation" + suf] = ser_formation(pa, years)
        equity_asset[suf.lower()] = ser(pa, years, "equity_asset_ratio")

    out = {
        "_bank": {
            "code": code,
            "shortName": src["name"],
            "fullName": meta.get("fullName", src["name"]),
            "aCode": code if len(code) == 6 else "",
            "hCode": meta.get("hCode", ""),
            "reportYear": latest,
            "tier": src.get("tier", ""),
        },
        "perf": {
            "years": y_perf,
            "revenue": ser(annual, y_perf, "operate_income", YI),
            "profit": ser(annual, y_perf, "parent_netprofit", YI),
        },
        "roe": {
            "years": y_perf,
            "roeCalc": [roe_calc(y) for y in y_perf],
            "roeOld": [annual[y].get("roe_weighted") if y < NEW_STD else None for y in y_perf],
            "roeNew": [annual[y].get("roe_weighted") if y >= NEW_STD else None for y in y_perf],
        },
        "pershare": {
            "years16": years,
            "eps": ser(annual, years, "eps"),
            "bvps": ser(annual, years, "bps"),
        },
        "scale-dep": scale,
        "nim-trend": nim,
        "creditamount": {
            "years16": years,
            "impAmt": [r(annual[y].get("credit_impairment") if annual[y].get("credit_impairment") is not None
                         else annual[y].get("asset_impairment"), MN, 1) for y in years],
            "totalAssetsY": ser(annual, years, "total_assets", MN, 1),
        },
        "bs-trend": {
            "years": years,
            "assets": ser(annual, years, "total_assets", MN, 1),
            "liab": ser(annual, years, "total_liabilities", MN, 1),
            "equity": ser(annual, years, "total_equity", MN, 1),
        },
        "bs": build_bs(annual[latest]),
        "staff": {
            "years15": y_staff,
            "staff": [annual[y]["staff_num"] for y in y_staff],
            "perOI": [r(annual[y].get("operate_income"), annual[y]["staff_num"] * 1e4, 1) for y in y_staff],
            "perNP": [r(annual[y].get("parent_netprofit"), annual[y]["staff_num"] * 1e4, 1) for y in y_staff],
        },
        "equity-asset": equity_asset,
    }

    # 其他综合收益（亿元）：income 表 OTHER_COMPRE_INCOME，2010 起（早年披露稀疏，全空则不出）
    oci = ser(annual, years, "oci", YI, 2)
    if len([v for v in oci if v is not None]) >= 3:
        out["oci"] = {"years16": years, "oci": oci}

    # 金融投资 IFRS9 三分类（亿元，2018 起）：摊余成本/FVOCI债/FVOCI股/FVTPL
    inv = build_invest(annual, years)
    if inv:
        out["invest"] = inv

    # 分红：优先用手工覆盖层（A 股年报「利润分配方案」全历史），否则用 F10 的 dividend_per10
    if manual and manual.get("dividend"):
        out["dividend-per10"] = manual["dividend"]
    else:
        dy = sorted(src.get("dividend_per10") or {})
        if dy:
            out["dividend-per10"] = {"years9": dy, "per10": [src["dividend_per10"][y] for y in dy]}

    # 股东户数：手工年报覆盖层优先（A 股年报口径），否则用 F10 的历年股东户数
    if manual and manual.get("holderCount"):
        out["holder-count"] = {
            "raw": [[row[0], None, row[1], row[2]] for row in manual["holderCount"]],
            "unit": manual.get("holderUnit", "hu"),
        }
    elif src.get("holder_num"):
        raw = src["holder_num"]
        out["holder-count"] = {
            "raw": raw,
            "unit": "wan" if max(r[1] for r in raw) >= 1e5 else "hu",
        }

    # 历年持股集中度 / 总股本变动：全部由 F10 年度数据推导，各行都有
    conc = build_concentration(src, bool(meta.get("hCode")))
    if conc:
        out["holder-concentration"] = conc
    # 港交所（H 股年报）口径的集中度单独一份载荷、页面上单独一个 series 披露：
    # F10「前十名股东」只覆盖 A 股定期报告期，纯 H 股行（天津/江西银行）与 A+H 行上市前的年份
    # 只能从港股年报「股本变动及股东情况」逐年读出，口径与 A 股披露不同，不能并成一条序列。
    # 纯 H 股行没有 shareholder_manual 覆盖层，这份序列写在 ar_manual 年报底稿里。
    hsrc = manual if (manual and manual.get("concentrationHist")) else (load_ar_manual(code) or {})
    if hsrc.get("concentrationHist"):
        out["holder-concentration-hist"] = {
            "raw": hsrc["concentrationHist"],
            "note": hsrc.get("concentrationHistNote", ""),
        }
    sc = build_share_capital(annual, all_years)
    if sc:
        out["share-capital"] = sc

    # 十大股东：手工覆盖层优先（A 股年报口径 + 人工派系归类），否则退回 F10 十大股东
    top10_sum = None
    if manual and manual.get("top10"):
        out["holders"] = build_holders(manual["top10"], manual["top10Sum"])
        top10_sum = manual["top10Sum"]
    else:
        rows, s = top10_from_annual(src)
        if rows:
            out["holders"] = build_holders(rows, s)
            top10_sum = s

    notes = {}
    if manual:
        for key, dom in (("meta", "page-meta"), ("holdersSub", "holders-sub"),
                         ("dividendSub", "dividend-sub"), ("holderNote", "note-holder-count-g"),
                         ("holdersNote", "note-holders-g"), ("dividendNote", "note-dividend-g")):
            if manual.get(key):
                notes[dom] = manual[key]
    elif out.get("holders"):
        notes["note-holders-g"] = ("十大股东取自东方财富 F10「%s 十大股东」（源自 %s 年年度报告），"
                                  "派系配色按股东名称关键词自动归类，仅供示意。"
                                  % (src["name"], latest))

    name = src["name"]
    # 页面上这几处静态文案/标题写的是渝农商行的具体数字，换行后必须整段替换（charts.js 里
    # 没被覆盖的 .yns-only 元素会整块隐藏，所以这里给不出文案的图位就只剩标题隐藏 + 图占位）
    if out.get("dividend-per10"):
        cards = dividend_cards(name, annual, out["dividend-per10"])
        if cards:
            notes["dividend-cards"] = cards
    if sc:
        notes["share-capital-title"] = "历年总股本变动（%s–%s · 亿股）" % (sc["years"][0], sc["years"][-1])
        notes["note-share-capital-g"] = share_capital_note(name, sc)
    hist = out.get("holder-concentration-hist")
    if conc or hist:
        # 三张柱图的小节副标题与各图标题：页面静态文案写的是渝农商行（含 2010–2017 重构口径、
        # 香港中央结算代理人），别的行必须整段替换，否则 .yns-only 会把标题整块隐藏。
        # 副标题按本行实际有哪几个披露来源拼：港交所（H 股年报）与 A 股定期报告在图上分开画。
        a_rows = conc["raw"] if conc else []
        h_rows = (hist or {}).get("raw") or []
        conc_years = sorted({str(r[0])[:4] for r in list(h_rows) + list(a_rows)})
        srcs = []
        if h_rows and a_rows:
            srcs.append("浅色柱 = %s–%s <b>港交所披露</b>（H 股年报口径）"
                        % (str(h_rows[0][0])[:4], str(h_rows[-1][0])[:4]))
            srcs.append("深色柱 = %s–%s <b>A 股定期报告披露</b>"
                        % (str(a_rows[0][0])[:4], str(a_rows[-1][0])[:4]))
        elif h_rows:                        # 纯 H 股行：只有一个来源，不用浅深色对比的说法
            srcs.append("全部取自 <b>港交所披露</b>的 H 股年报「股本变动及股东情况」（口径见下方说明）")
        else:
            srcs.append("取自 <b>A 股定期报告</b>披露的「前十名股东」（东方财富 F10 按报告期汇总）")
        last_d = (a_rows or h_rows)[-1][0]
        tail = "" if str(last_d)[5:] == "12-31" else f"（最新一根为 {last_d} 当期）"
        head = "每年一根柱（年末口径，最新年份取最近报告期）" if tail else "每年一根柱（年末口径）"
        notes["conc-sub"] = (f"{head}· {conc_years[0]}–"
                             f"{conc_years[-1]} 共 {len(conc_years)} 年{tail} · "
                             + ("按披露来源分开画：" if len(srcs) > 1 else "") + "；".join(srcs))
        t1_tail = (f" · 最新一期为{conc['top1Names'][-1]}" if conc else
                   " · 第一大为内资股股东；H 股按年报具名披露的实益持有人参与排序，"
                   "不含香港中央结算（代理人）名下的散户余额")
        notes["conc-title-top1"] = f"第一大股东持股比例（占总股本 %{t1_tail}）"
        notes["conc-title-top3"] = "前三大股东合计（占总股本 %）"
        notes["conc-title-top10"] = "前十大股东合计（占总股本 %）"
        notes["note-holder-concentration-g"] = concentration_note(name, conc, hist)
    if out.get("holder-count") and not (manual and manual.get("holderNote")):
        notes["note-holder-count-g"] = holder_count_note(name, out["holder-count"])

    # 风控页 7 处含行名的图表标题：601077 静态 HTML 已写死本行名，本脚本给其他行按本行简称重拼
    # （标题元素带 id 且是 .yns-only，charts.js 只在 _notes 里给了文案时才显示，否则整块隐藏）
    peers4 = " vs ".join(nm for pc, nm in PEER_NAMES.items() if pc != code)
    if peers4:
        vs4 = f"{name} vs {peers4}"
        notes["ct-npl"] = f"不良贷款率（%） · {vs4}"
        notes["ct-overdue"] = f"逾期贷款率（%） · {vs4}"
        notes["ct-npl-amt"] = f"不良贷款总额（亿元）"
        notes["ct-overdue-amt"] = f"逾期贷款总额（亿元）"
        notes["ct-npl-formation"] = f"不良生成率（%） · {vs4}"
        notes["ct-writeoff-rate"] = f"核销率（%） · {vs4}"
        notes["ct-equity-asset"] = f"权益资产比（%） · {vs4}"
    notes["ct-migrate-self"] = f"关注/次级/可疑类迁徙率（{name}）"
    notes["ct-migrate-normal"] = (f"正常类迁徙率 · {name} vs 农业银行"
                                  if code != "601288" else f"正常类迁徙率（{name}）")

    notes["holders-title-a"] = ("%s 年报（%s）· 前十大股东占总股本"
                                % ("A 股" if len(code) == 6 else "H 股", latest))
    # 两处小节副标题：手工覆盖层里给了就用它，没给就按本行数据现拼（页面静态文案是渝农商行的户数）
    if "holders-sub" not in notes:
        v = holders_sub(out.get("holder-count"), top10_sum, latest)
        if v:
            notes["holders-sub"] = v
    if "dividend-sub" not in notes:
        v = dividend_sub(out.get("dividend-per10"))
        if v:
            notes["dividend-sub"] = v
    if "page-meta" not in notes:
        notes["page-meta"] = page_meta(code, meta.get("hCode", ""),
                                       annual[latest].get("total_assets"), latest)
    if notes:
        out["_notes"] = notes

    # 专属明细键覆盖层：语义读年报得到的迁徙率/重定价/期限/五级分类/分部/行业投向/员工构成/
    # 高管薪酬/存款成本/贷款结构/公允价值层级/现金流等，直接并入 out（顶层键即图表数据键）。
    # charts.js 里这些图位默认按 .yns-only 隐藏，只有 out 里出现对应键（及标题 _notes）才显示。
    detail = load_detail(code)
    if detail:
        dnotes = detail.pop("_notes", None)
        for k, v in detail.items():
            if not k.startswith("_"):
                out[k] = v
        if dnotes:
            out.setdefault("_notes", {}).update(dnotes)

    # 社融为宏观口径，各行共用同一份（直接沿用 601077 精编文件里的那份）
    ref = json.loads((TABLES / "company_charts_601077.json").read_text(encoding="utf-8"))
    if "tsf-stock" in ref:
        out["tsf-stock"] = ref["tsf-stock"]
    return out


def main(argv: list[str]) -> None:
    codes = argv or CODES
    for code in codes:
        if code == "601077":
            print("[skip] 601077 为手工精编文件，不由本脚本生成")
            continue
        if not (TABLES / f"bank_{code}_annual.json").exists():
            print(f"[skip] {code}: 缺 bank_{code}_annual.json（fetch 未成功或未拉取），跳过")
            continue
        data = build(code)
        path = TABLES / f"company_charts_{code}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        keys = [k for k in data if not k.startswith("_")]
        print(f"[gen] {data['_bank']['shortName']} {code}: {len(keys)} key, "
              f"{data['perf']['years'][0]}~{data['_bank']['reportYear']}, "
              f"{path.stat().st_size / 1024:.1f} KB -> {path.relative_to(ROOT)}")


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except Exception as e:                          # noqa: BLE001
        print(f"[error] {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
