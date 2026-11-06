"""银行详情页图表（/api/company_charts、/api/bank_npl_formation）的数据层：gen_company_charts.build() 的四份输入
（bank_<code>_annual.json、_shareholder_manual.json、_ar_manual.json、_detail_manual.json）从 MySQL 拼回原形状，
build() 照旧现算出图表载荷（配色、文案、派生序列都在 build() 里，不入库）。

还原约定（与 load_to_mysql.py 的拆法一一对应）：
  · annual 同股权页那份（backend/holders_db.holder_table）：年度序列 + 名册 + 户数 + 集中度 + 分红；
  · 手工件只取 source（或户数的 revised_by、分红的 dividend_source）记为该文件的行，页面文案取 data_note；
  · detail 按 DETAIL_PAIR / DETAIL_SINGLE / DETAIL_SERIES 反过来拼：分项按 item_order，年份轴取该主题出现过的年份
    （空格子入库时也写了行），值用 raw_value（原单位）；年份一律写成字符串，整列为 null 的键不出现。
    指标固定的主题在各自宽表里（DETAIL_WIDE_TABLES），先由 _wide_rows 摊回同样的行再拼。
渝农商行（601077）是手工精编件，不走 build()，见 backend/bank.py。"""
import os
import sys
from decimal import Decimal

from backend import db, holders_db, industry_db

_EXTRACT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "extract")
if _EXTRACT_DIR not in sys.path:
    sys.path.insert(0, _EXTRACT_DIR)
import load_to_mysql as schema  # noqa: E402  拆表映射只在载入脚本里写一份
import gen_company_charts as gen  # noqa: E402  图表载荷的拼法只在生成脚本里写一份

# 手工件 top10 的类别键 → 原表里的类别文字（键与 shareholder.holder_category 的 COMMENT 一致）
CATEGORY_LABELS = {"soe": "国有股东", "hk": "境外/H股", "ssf": "社保基金", "ins": "保险资金", "corp": "内资法人", "other": "其他"}


def _entity(code):
    return schema._entity_code(code)


def _notes(company_code, source):
    return {r["topic"]: r["note"] for r in db.query(
        "SELECT topic, note FROM data_note WHERE company_code = %s AND source_file = %s ORDER BY id",
        (company_code, source))}


def annual(code):
    """bank_<code>_annual.json 同形状 + share_capital_events（见 add_share_capital_events）；
    库里没有这家返回 None（build() 遇到会报缺文件）。"""
    d = holders_db.holder_table("bank", code)
    if d is None:
        raise FileNotFoundError("库里没有 bank_%s_annual.json 的数据" % code)
    return add_share_capital_events(d, code)


def add_share_capital_events(d, code):
    """补 share_capital_events：share_capital_year_end 里有变动摘要的年份 {年: {type, items}}，
    build_share_capital 有它才在股本块里输出 events（载入时 items 用「；」拼成一格，这里拆回列表）。
    股权页先读到的 annual 也要补：它和图表载荷共用一份缓存，先到者缺键后到者就跟着缺。"""
    ev = {str(r["fiscal_year"]): {"type": r["change_type"], "items": r["change_summary"].split("；")}
          for r in db.query("SELECT fiscal_year, change_summary, change_type FROM share_capital_year_end"
                            " WHERE company_code = %s AND change_summary IS NOT NULL ORDER BY fiscal_year",
                            (_entity(code),))}
    if ev:
        d["share_capital_events"] = ev
    return d


def shareholder_manual(code):
    """bank_<code>_shareholder_manual.json 里 build() 用到的键；库里没有这份手工件返回 None。"""
    file = "bank_%s_shareholder_manual.json" % code
    cc = _entity(code)
    notes = _notes(cc, file)
    div = db.query("SELECT fiscal_year, dividend_per_10_shares FROM financials WHERE company_code = %s"
                   " AND dividend_source = %s ORDER BY fiscal_year", (cc, file))
    counts = db.query("SELECT * FROM shareholder_count WHERE company_code = %s AND (source = %s OR revised_by = %s)"
                      " AND DATE_FORMAT(as_of_date, '%%m-%%d') = '12-31' ORDER BY as_of_date", (cc, file, file))
    if not (notes or div or counts):
        return None
    out = {}
    if div:
        out["dividend"] = {"years": [str(r["fiscal_year"]) for r in div],
                           "per10": [db.number(r["dividend_per_10_shares"]) for r in div]}
    if counts:
        # 手工件里 A/H 两格都空的年份入库时没有落点（不改任何格子），这里也就没有这一行
        out["holderCount"] = [[str(r["as_of_date"].year), db.number(r["a_share_holders"]),
                               db.number(r["h_share_holders"])] for r in counts]
    top = db.query("SELECT * FROM shareholder WHERE company_code = %s AND holder_category IS NOT NULL"
                   " ORDER BY fiscal_year DESC, holder_rank", (cc,))
    if top:
        top = [r for r in top if r["fiscal_year"] == top[0]["fiscal_year"]]
        # 手工件的增减一栏全写「—」（年报口径页不列增减）
        out["top10"] = [[r["holder_short"], round(float(r["ratio"]), 2), "—", CATEGORY_LABELS[r["holder_category"]],
                         r["holder_category"]] for r in top]
    if notes.get("top10Sum"):
        out["top10Sum"] = float(notes["top10Sum"])
    for k in ("holderUnit", "meta", "holdersSub", "dividendSub", "holderNote", "holdersNote", "dividendNote"):
        if notes.get(k):
            out[k] = notes[k]
    return out


def ar_manual(code):
    """bank_<code>_ar_manual.json 里 build() 用到的：港交所口径集中度序列与说明，以及港股年报名册 hk_holders
    （渝农商行 2018：前十大 + SFO ≥5% 的 H 股股东，后者 additional=1）；都没有返回 None。"""
    file = "bank_%s_ar_manual.json" % code
    cc = _entity(code)
    rows = db.query("SELECT * FROM shareholder_concentration WHERE company_code = %s AND source = %s ORDER BY as_of_date",
                    (cc, file))
    notes = _notes(cc, file)
    hk = db.query("SELECT * FROM shareholder WHERE company_code = %s AND source = %s"
                  " ORDER BY is_additional, holder_rank, ratio DESC", (cc, file))
    if not rows and not notes and not hk:
        return None
    out = {"concentrationHist": [[r["as_of_date"].isoformat(), db.number(r["top1_holder_ratio"]),
                                  db.number(r["top3_holders_ratio"]), db.number(r["top10_holders_ratio"]),
                                  {1: "recon", 0: "disc"}.get(r["is_reconstructed"])] for r in rows]}
    if notes.get("concentrationHistNote"):
        out["concentrationHistNote"] = notes["concentrationHistNote"]
    if hk:
        out["hk_holders"] = {"end_date": hk[0]["as_of_date"].isoformat(), "holders": [
            {"rank": r["holder_rank"], "name": r["holder_name"], "short": r["holder_short"], "state": r["holder_nature"],
             "shares_type": r["raw_shares_type"], "ratio": db.number(r["ratio"]),
             "additional": bool(r["is_additional"])} for r in hk]}
    return out


def _v(r):
    return None if r is None else db.number(r["raw_value"])


def _wide_raw(r, col, topic, measure):
    """宽表的统一值换回 detail_manual 的原单位（保留 6 位小数，同 bank_report_detail.raw_value）：
    金额按 amount_raw_unit，高管薪酬按万元，比率与笔数照旧。"""
    v = r[col]
    if v is None:
        return None
    v = Decimal(v)                                       # 笔数列是 INT
    if measure in schema.DETAIL_AMOUNT_MEASURES:
        factor = dict(schema.AMOUNT_UNITS).get(r["amount_raw_unit"])
        if factor is None:
            return None
        v = v / Decimal(factor)
    elif topic == "executive_pay":
        v = v / Decimal(schema.FIXED_UNITS["万元"][1])
    return v.quantize(Decimal("0.000001"))


def _wide_rows(cc, file):
    """指标固定主题的宽表（schema.DETAIL_WIDE_TABLES）摊回 bank_report_detail 的行形状，detail() 照旧按行拼。
    每行 columns_missing_in_source 里的列在这一年不出行（原表这一年没有这一格，整列都没有的拼回后该键为 null，
    只缺部分年份的不进它的年份轴）；其余列照出，空值也出。"""
    out = []
    for topic, (table, cols) in schema.DETAIL_WIDE_TABLES.items():
        got = db.query("SELECT * FROM %s WHERE company_code = %%s AND source_file = %%s ORDER BY fiscal_year" % table,
                       (cc, file))
        order = schema.detail_item_order(topic)
        pay = topic == "executive_pay"
        for (item, measure), col in cols.items():
            for r in got:
                if col in (r["columns_missing_in_source"] or "").split(","):
                    continue
                out.append({"topic": topic, "fiscal_year": r["fiscal_year"], "period_label": r.get("period_label"),
                            "item_name": (r[measure.replace("_pay", "_name")] or "") if pay else item,
                            "item_order": None if pay else order[(item, measure)], "measure": measure,
                            "raw_value": _wide_raw(r, col, topic, measure)})
    return out


def _detail_marks(notes, key):
    """data_note 里 <键>.marks.<序号>.<字段> → [{字段: 原文}]（按序号）。"""
    marks = {}
    for topic, note in notes.items():
        parts = topic.split(".")
        if len(parts) == 4 and parts[0] == key and parts[1] == "marks" and parts[2].isdigit():
            marks.setdefault(int(parts[2]), {})[parts[3]] = note
    return [marks[i] for i in sorted(marks)]


def detail(code):
    """bank_<code>_detail_manual.json 同形状（build() 只取不以 _ 开头的键与 _notes）；库里没有这份返回 None。"""
    file = "bank_%s_detail_manual.json" % code
    cc = _entity(code)
    rows = list(db.query("SELECT * FROM bank_report_detail WHERE company_code = %s AND source_file = %s"
                         " ORDER BY topic, item_order, fiscal_year", (cc, file))) + _wide_rows(cc, file)
    notes = _notes(cc, file)
    if not rows and not notes:
        return None
    by_topic = {}
    for r in rows:
        by_topic.setdefault(r["topic"], []).append(r)
    out = {}

    def cell(rs, year, measure, item=None, order=None):
        for r in rs:
            if r["fiscal_year"] == year and r["measure"] == measure and (item is None or r["item_name"] == item) \
                    and (order is None or r["item_order"] == order):
                return r
        return None

    for key, (topic, items_key, value_keys, _) in schema.DETAIL_PAIR.items():
        rs = by_topic.get(topic)
        if not rs:
            continue
        items = []
        for r in sorted(rs, key=lambda x: x["item_order"] or 0):
            if r["item_name"] not in items:
                items.append(r["item_name"])
        sec = {items_key: items}
        years = sorted({r["fiscal_year"] for r in rs})
        for vk, (year, measure) in value_keys.items():
            y = year or years[-1]
            got = [r for r in rs if r["fiscal_year"] == y and r["measure"] == measure]
            sec[vk] = [_v(cell(got, y, measure, item)) for item in items] if got else None
        out[key] = sec
    for key, (topic, items, measure, _) in schema.DETAIL_SINGLE.items():
        rs = sorted(by_topic.get(topic) or [], key=lambda x: x["item_order"] or 0)
        if not rs:
            continue
        if isinstance(items, list):
            out[key] = {"vals": [_v(next((r for r in rs if r["item_name"] == i), None)) for i in items]}
        elif items == "buckets":
            out[key] = {"buckets": [r["item_name"] for r in rs], "vals": [_v(r) for r in rs]}
        else:
            out[key] = {items: [{"name": r["item_name"], "value": _v(r)} for r in rs]}
    for key, (topic, series) in schema.DETAIL_SERIES.items():
        rs = by_topic.get(topic)
        if not rs:
            continue
        sec, names = {}, {}
        axes = {}
        labels = {r["fiscal_year"]: r["period_label"] for r in rs if r["period_label"]}   # 「2024 年末」这类原写法
        for i, (sk, spec) in enumerate(series.items(), 1):
            got = [r for r in rs if r["item_order"] == i and r["measure"] == spec[1]]
            axes.setdefault(spec[3] if len(spec) > 3 else "years", set()).update(r["fiscal_year"] for r in got)
        for axis, ys in axes.items():
            sec[axis] = [labels.get(y) or str(y) for y in sorted(ys)]
        for i, (sk, spec) in enumerate(series.items(), 1):
            got = [r for r in rs if r["item_order"] == i and r["measure"] == spec[1]]
            if not got:
                sec[sk] = None                    # 原表这一列整列为 null（入库时不写行）
                continue
            ys = sorted(axes[spec[3] if len(spec) > 3 else "years"])
            sec[sk] = [_v(cell(got, y, spec[1])) for y in ys]
            if got[0]["item_name"] != spec[0]:
                names[sk] = got[0]["item_name"]
        if names:
            sec["names"] = names
        if key == "loantrend":
            # 公司/零售贷款余额与不良余额进库时放在 bank_financials（元），这里按 loantrend 的年份轴换回亿元
            loans = {r["fiscal_year"]: r for r in db.query(
                "SELECT fiscal_year, corporate_loans, retail_loans, corporate_non_performing_loans,"
                " retail_non_performing_loans FROM bank_financials WHERE company_code = %s", (cc,))}
            for col, jk in schema.LOAN_STRUCTURE_COLS:
                vals = [loans.get(int(str(y)[:4]), {}).get(col) for y in sec["years"]]
                sec[jk] = [None if v is None else db.number(round(float(v) / 1e8, 6)) for v in vals]
        marks = _detail_marks(notes, key)
        if marks:
            sec["marks"] = marks
        out[key] = sec
    pay = by_topic.get("executive_pay")
    if pay:
        years = sorted({r["fiscal_year"] for r in pay})
        sec = {"years": [str(y) for y in years]}
        for role in ("chairman", "president"):
            got = [cell(pay, y, role + "_pay") for y in years]
            sec[role + "Names"] = [(r["item_name"] or None) if r else None for r in got]
            sec[role + "Pay"] = [_v(r) for r in got]
        marks = _detail_marks(notes, "chairman-pay")
        if marks:
            sec["marks"] = marks
        out["chairman-pay"] = sec
    bonds = db.query("SELECT * FROM bank_bond_issue WHERE company_code = %s AND source_file = %s ORDER BY bond_order",
                     (cc, file))
    if bonds and "bondpay" in out:
        out["bondpay"]["bonds"] = [{"name": b["bond_name"], "issueDate": b["issue_date"], "tenor": b["tenor"],
                                    "coupon": db.number(b["coupon_rate"]), "amount": db.number(b["issue_amount"]),
                                    "maturity": b["maturity"], "status": b["status"]} for b in bonds]
    dn = {k: v for k, v in notes.items() if not k.startswith("_source") and ".marks." not in k}
    if dn:
        out["_notes"] = dn
    return out


def _social_financing():
    """社融宏观块：同 /api/social-financing 那份（社融表与原 601077 精编块逐字节一致）。"""
    from backend import bank          # bank 也要用本模块，按需导入免得互相导入时绕圈
    r = bank.read_social_financing()
    return r["data"] if r.get("code") == 200 else None


def charts(code, cache=None, skip=()):
    """company_charts_<code>.json 同形状：库里拼回 build() 的输入、由 gen_company_charts.build() 现算；
    库里没有这家银行的年度序列返回 None。cache 是 {代码: annual} —— 一次请求里要拼多家（跨行对比、股权页名单）时
    传同一个 dict，对标行（农行/招行/邮储）的年度序列只拼一次。skip 里列的输入（manual / ar_manual / detail /
    social_financing）当作没有：只要其中几块的调用方（股权页只取环形图/股本/分红，跨行对比只取息差与不良生成）用它省掉大块查询。"""
    if not db.query("SELECT 1 FROM financials_meta WHERE source_file = %s", ("bank_%s_annual.json" % code,)):
        return None
    cache = {} if cache is None else cache

    def cached_annual(c):
        if c not in cache:
            cache[c] = annual(c)
        return cache[c]

    inputs = {"annual": cached_annual, "manual": shareholder_manual, "ar_manual": ar_manual,
              "detail": detail, "social_financing": _social_financing}
    inputs.update({k: (lambda *_: None) for k in skip})
    return gen.build(code, inputs)
