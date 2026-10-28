"""保险/地产/水泥/通信的年度数据与经营口径手工层：从 MySQL 结构化表拼回接口原来的 JSON 形状。

字段映射与载入时是同一份——data/extract/load_to_mysql.py 与 industry_columns.py 的 (SQL 列名, JSON 字段名[, 倍数])
清单反过来用，所以接口照旧按成品表的字段名（多为东财命名）下发，前端不用改。还原时的约定：
  · annual 每年给出该行业登记过的全部字段，库里为 NULL 的写 null（页面一律按 null/undefined 判缺）；
  · 同义字段（main_total_assets、total_revenue、basic_eps、电信的 revenue）与同一列的值一并给出；
  · 只有分红或股东户数、没有任何财务值的年份不进 annual（原表 annual 里本来就没有这些年）；
  · 比率列库里存 4 位小数，原文更长的小数在这里是截到 4 位后的值；
  · holders / holders_end_date 不再下发：行业页不读，股权页走 /api/holders。"""
import os
import sys

from backend import db

_EXTRACT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "extract")
if _EXTRACT_DIR not in sys.path:
    sys.path.insert(0, _EXTRACT_DIR)
import load_to_mysql as schema  # noqa: E402  映射清单只在载入脚本里写一份

_ROW_SKIP = set(schema.YEAR_LEVEL_KEYS)        # 原表挂在顶层、按年份组织的字段，不放进每年记录


def _one(sql, args):
    rows = db.query(sql, args)
    return rows[0] if rows else None


def _secucode(company_code):
    """sh.600585 → 600585.SH（成品表的 secucode 写法）。"""
    market, code = company_code.split(".", 1)
    return "%s.%s" % (code, market.upper())


def _fetched_at(v):
    return v.strftime("%Y-%m-%d %H:%M UTC") if v else None


def _value(v, scale=1):
    return None if v is None else db.number(float(v) / scale)


def _industry_specs(industry, file):
    """<行业>_financials 的 (列, 字段, 倍数) 清单：行业映射按文件覆盖改写后，再补上覆盖新增的列（银行是 bank_financials 那份）。"""
    over = schema.FILE_COLUMN_OVERRIDES.get(file, {})
    base = schema.BANK_COLS if industry == "bank" else schema.INDUSTRY_COLS.get(industry, [])
    return [over.get(t[1], t) for t in base] + [t for t in over.values() if t not in base]


def read_annual_table(industry, code):
    """data/tables/<industry>_<code>_annual.json 的同形状数据；该文件没载入过（库里没有）返回 None。"""
    file = "%s_%s_annual.json" % (industry, code)
    meta = _one("SELECT * FROM financials_meta WHERE source_file = %s", (file,))
    if meta is None:
        return None
    cc = meta["company_code"]
    co = _one("SELECT * FROM company WHERE company_code = %s", (cc,)) or {}
    fin = {r["fiscal_year"]: r for r in db.query("SELECT * FROM financials WHERE company_code = %s", (cc,))}
    ind = {r["fiscal_year"]: r for r in db.query(
        "SELECT * FROM `%s_financials` WHERE company_code = %%s" % industry, (cc,))}
    num_specs = _industry_specs(industry, file)
    text_specs = schema.INDUSTRY_TEXT_COLS.get(industry, [])
    flag_specs = schema.INDUSTRY_FLAG_COLS.get(industry, [])
    aliases = {a: c for a, (c, scale) in {**schema.FIELD_ALIASES["*"], **schema.FIELD_ALIASES.get(industry, {})}.items()
               if scale == 1}                  # 倍数不为 1 的同义字段只出现在港股/20-F 序列，那些文件不走本接口

    annual, year_level, hk = {}, {}, {}
    for y in sorted(set(fin) | set(ind)):
        f, i = fin.get(y) or {}, ind.get(y) or {}
        row = {j: _value(f.get(c)) for c, j in schema.FIN_NUM_COLS}
        row.update({j: f.get(c) for c, j in schema.AUDIT_COLS})
        for t in num_specs:
            if row.get(t[1]) is None:
                row[t[1]] = _value(i.get(t[0]), t[2] if len(t) > 2 else 1)
        row.update({j: i.get(c) for c, j in text_specs})
        row.update({j: None if i.get(c) is None else bool(i[c]) for c, j in flag_specs})
        for alias, canon in aliases.items():
            row[alias] = row.get(canon)
        if industry == "telecom":                                 # 同 fetch_telecom_financials.revenue_of：两个收入字段差一个量级时取营业总收入
            total, oi = row.get("total_operate_income"), row.get("operate_income")
            row["revenue"] = (total if oi < total * 0.5 else oi) if total is not None and oi is not None else \
                (total if total is not None else oi)
        for k in [k for k in row if k in _ROW_SKIP]:             # fx_rate_used 等挪回顶层
            v = row.pop(k)
            if v is not None:
                year_level.setdefault(k, {})[str(y)] = v
        for k in [k for k in row if k.startswith("hk_")]:        # 港股年报交叉核对挪回顶层 hk_crosscheck
            v = row.pop(k)
            if v is not None:
                hk.setdefault(str(y), {})[k] = v
        if "mixLayers" in row and row["mixLayers"] is not None:
            row["mixLayers"] = row["mixLayers"].split(",")
        if any(v is not None for v in row.values()):
            annual[str(y)] = row

    out = {
        "code": code, "secucode": _secucode(cc), "name": co.get("short_name"), "group": co.get("group_name"),
        "h_code": "%s.HK" % co["h_code"] if co.get("h_code") else None,
        "h_same_entity": None if co.get("same_entity") is None else bool(co["same_entity"]),
        "a_report_from": meta.get("a_share_report_from"), "currency": meta.get("currency"),
        "fetched_at": _fetched_at(meta.get("fetched_at")), "source": meta.get("source"),
        "unit_note": meta.get("unit_note"), "caliber_note": meta.get("caliber_note"),
        "fx_note": meta.get("exchange_rate_note"), "annual": annual,
        "dividend_per10": {str(y): db.number(r["dividend_per_10_shares"]) for y, r in sorted(fin.items())
                           if r.get("dividend_per_10_shares") is not None},
    }
    out.update(year_level)
    if hk:
        out["hk_crosscheck"] = hk
    return out


def _notes(company_code, source_file):
    """data_note 里某份文件（某家公司）的说明 {键: 原文}；company_code 为 None 取整份文件通用的。"""
    rows = db.query("SELECT topic, note FROM data_note WHERE source_file = %s AND company_code "
                    + ("IS NULL" if company_code is None else "= %s") + " ORDER BY id",
                    (source_file,) if company_code is None else (source_file, company_code))
    return {r["topic"]: r["note"] for r in rows}


def _operating_rows(table, company_code, specs, text_specs, flag_specs=()):
    """<行业>_operating 某家的逐年记录，按载入映射还原成手工层原字段（每列取清单里第一个字段名，空值不写）。"""
    first = {}
    for t in specs:
        first.setdefault(t[0], t)
    out = {}
    for r in db.query("SELECT * FROM `%s` WHERE company_code = %%s ORDER BY fiscal_year" % table, (company_code,)):
        rec = {t[1]: _value(r[c], t[2] if len(t) > 2 else 1) for c, t in first.items() if r.get(c) is not None}
        rec.update({j: r[c] for c, j in text_specs if r.get(c) is not None})
        rec.update({j: bool(r[c]) for c, j in flag_specs if r.get(c) is not None})
        out[str(r["fiscal_year"])] = rec
    return out


def cement_ops_manual():
    """cement_ops_manual.json 同形状：{source, unit_note, caliber_note, companies: {代码: {name, currency, years, …, annual}}}。"""
    file = "cement_ops_manual.json"
    out = dict(_notes(None, file))
    companies = {}
    for r in db.query("SELECT DISTINCT o.company_code, c.short_name, c.a_code, c.h_code FROM cement_operating o"
                      " JOIN company c ON c.company_code = o.company_code"):
        notes = _notes(r["company_code"], file)
        companies[r["a_code"] or r["h_code"]] = {
            "name": r["short_name"], "currency": notes.get("currency"), "years": notes.get("years"),
            "sales_key": notes.get("sales_key"), "rev_caliber": notes.get("rev_caliber"),
            "unit_rule": notes.get("unit_rule"), "breaks": notes.get("breaks"),
            "annual": _operating_rows("cement_operating", r["company_code"], schema.CEMENT_OPERATING_COLS,
                                      schema.CEMENT_OPERATING_TEXT_COLS)}
        for rec in companies[r["a_code"] or r["h_code"]]["annual"].values():
            if str(rec.get("page", "")).isdigit():             # 单页页码原表是数字，多页是「14,15,16」这样的文本
                rec["page"] = int(rec["page"])
    out["companies"] = companies
    return out if companies else None


def telecom_ops_manual():
    """telecom_ops_manual.json 同形状（三家 A 股年报口径；中国移动港股序列 hk.00941 不在这层）。"""
    file = "telecom_ops_manual.json"
    out = dict(_notes(None, file))
    text_specs = [(c, j) for c, j in schema.TELECOM_OPERATING_TEXT_COLS if j in ("cloud_name", "dx_name", "approx", "src")]
    companies = {}
    for r in db.query("SELECT DISTINCT n.company_code, c.short_name, c.a_code FROM data_note n"
                      " JOIN company c ON c.company_code = n.company_code WHERE n.source_file = %s", (file,)):
        notes = _notes(r["company_code"], file)
        annual = _operating_rows("telecom_operating", r["company_code"], schema.TELECOM_OPERATING_COLS, text_specs)
        for rec in annual.values():
            if "approx" in rec:
                rec["approx"] = rec["approx"].split(",")
        companies[r["a_code"]] = {"name": r["short_name"], "years": notes.get("years"),
                                  "report_source": notes.get("report_source"),
                                  "breaks": (notes.get("breaks") or "").split("\n") if notes.get("breaks") else None,
                                  "annual": annual}
    out["companies"] = companies
    return out if companies else None


def telecom_segment_manual():
    """telecom_segment_manual.json 同形状：companies[代码].annual[年] = {items: {原文科目: 亿元}, canon: {分部编码: 亿元}}。"""
    file = "telecom_segment_manual.json"
    out = dict(_notes(None, file))
    companies = {}
    for r in db.query("SELECT s.*, c.a_code, c.short_name FROM segment_revenue s"
                      " JOIN company c ON c.company_code = s.company_code ORDER BY s.company_code, s.fiscal_year, s.line_order"):
        comp = companies.setdefault(r["a_code"], {"name": r["short_name"], "annual": {}})
        rec = comp["annual"].setdefault(str(r["fiscal_year"]), {"items": {}, "canon": {}})
        rec["canon"][r["segment_code"]] = db.number(r["revenue"])
        rec["items"][r["raw_item_name"] or r["segment_code"]] = db.number(r["revenue"])
    out["companies"] = companies
    return out if companies else None
