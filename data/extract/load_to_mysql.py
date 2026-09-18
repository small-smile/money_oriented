#!/usr/bin/env python
"""把 data/tables 下的 JSON 成品表载入 data/sql/schema.sql 定义的 MySQL 表。

用法：
  # 只解析并打印各表将写入的行数，不连接数据库（无需任何驱动）：
  ./venv/bin/python data/extract/load_to_mysql.py --dry-run

  # 真实入库（需先 pip install pymysql；--init 先执行 schema.sql 建表）：
  ./venv/bin/python data/extract/load_to_mysql.py \
      --host 127.0.0.1 --port 3306 --user root --password *** --db money --init

财务走混合模型：跨行业公共列进 financial_common，其余指标进 financial_metric 长表 + metric 维度。
本轮只收 JSON 派生表（oil/宏观 CSV 未纳入）。*_shareholder*.json 原始手工件较异构，
股权数据统一从 holders_manual.json 取。
"""
import os
import re
import json
import glob
import argparse

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TABLES = os.path.join(ROOT, "data", "tables")
SCHEMA = os.path.join(ROOT, "data", "sql", "schema.sql")

INDUSTRIES = ["bank", "insurer", "developer", "cement", "telecom", "tech", "food"]

# financial_common 宽表的列（与 schema.sql 一致）；其余 annual 指标进 financial_metric 长表
COMMON_COLS = ["operate_income", "operate_profit", "total_profit", "netprofit", "parent_netprofit",
               "total_assets", "total_liabilities", "total_equity", "parent_equity", "share_capital",
               "eps", "bps", "roe_weighted", "net_margin", "op_cf_per_share"]
CONSUMED = set(COMMON_COLS) | {"basic_eps"}   # basic_eps 作为 eps 的回退，一并视为已消费

YEAR = re.compile(r"^(19|20)\d{2}$")


def _num(v):
    """把 12,345 / 3.4% / '' / '-' 之类清成 float 或 None。"""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return v
    s = str(v).replace(",", "").replace("%", "").strip()
    if s in ("", "-", "—", "N/A", "null", "None"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _txt(v):
    if v is None:
        return None
    s = str(v).strip()
    return s or None


# 每张表的插入列（顺序即 add() 时元组的顺序）；带 AUTO_INCREMENT id 的表这里不列 id。
COLUMNS = {
    "company": ("code", "short_name", "full_name", "industry", "a_code", "h_code",
                "us_code", "tier", "same_entity", "note"),
    "company_source": ("company_code", "source_line"),
    "data_gap": ("company_code", "item", "why"),
    "metric": ("metric_code", "domain", "label", "unit", "note"),
    "financial_meta": ("company_code", "secucode", "currency", "group_name", "source",
                       "unit_note", "caliber_note", "fetched_at"),
    "financial_common": ("company_code", "fiscal_year", *COMMON_COLS),
    "financial_metric": ("company_code", "fiscal_year", "metric_code", "value"),
    "dividend_per10": ("company_code", "fiscal_year", "per10", "unit"),
    "segment_annual": ("company_code", "fiscal_year", "segment", "metric_code", "value"),
    "shareholder_top10": ("company_code", "as_of_date", "rank", "holder_name", "hold_num",
                          "ratio", "chg", "state", "shares_type", "total_shares", "pledged"),
    "holder_count": ("company_code", "as_of_date", "holder_num", "avg_hold"),
    "holder_concentration": ("company_code", "as_of_date", "top1", "top3", "top10",
                             "top1_ex", "top3_ex", "top1_name", "top1_ex_name"),
    "share_capital_history": ("company_code", "fiscal_year", "shares", "change_reason"),
    "tsf_pboc": ("kind", "period_month", "series_key", "value"),
}
# 插入顺序：company 先建（外键父表），factions 在 shareholder 之后单独插（要拿 AUTO_INCREMENT id）
INSERT_ORDER = ["company", "company_source", "data_gap", "metric", "financial_meta",
                "financial_common", "financial_metric", "dividend_per10", "segment_annual",
                "shareholder_top10", "holder_count", "holder_concentration",
                "share_capital_history", "tsf_pboc"]


class Loader:
    def __init__(self):
        self.rows = {t: [] for t in COLUMNS}
        self.companies = {}       # code -> company 行元组（去重）
        self.metric_seen = set()
        self.factions = []        # {company_code,title,color,basis,members:[str]}

    def add(self, table, row):
        self.rows[table].append(row)

    def ensure_company(self, code, industry="", name=None):
        if code and code not in self.companies:
            self.companies[code] = (code, name or code, None, industry,
                                    None, None, None, None, 1, None)
        return code

    def set_company(self, e):     # 权威公司行来自 company_codes.json
        self.companies[e["key"]] = (
            e["key"], e.get("short") or e["key"], e.get("full"), e.get("industry") or "",
            e.get("a_code"), e.get("h_code"), e.get("us_code"), e.get("tier"),
            1 if e.get("same_entity", True) else 0, e.get("note"))

    def add_metric(self, code, domain):
        if (code, domain) not in self.metric_seen:
            self.metric_seen.add((code, domain))
            self.add("metric", (code, domain, None, None, None))

    def counts(self):
        c = {t: len(r) for t, r in self.rows.items()}
        c["company"] = len(self.companies)
        c["holder_faction"] = len(self.factions)
        c["holder_faction_member"] = sum(len(f["members"]) for f in self.factions)
        return c


def _load_json(name):
    p = os.path.join(TABLES, name)
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def load_company(L):
    d = _load_json("company_codes.json")
    for e in d.get("entities", []) or []:
        L.set_company(e)
        for s in e.get("sources") or []:
            L.add("company_source", (e["key"], str(s)[:512]))
    for g in d.get("gaps", []) or []:
        L.add("data_gap", (None, _txt(g.get("item")) or "", _txt(g.get("why"))))


def _common_values(row):
    vals = [_num(row.get(c)) for c in COMMON_COLS]
    if vals[COMMON_COLS.index("eps")] is None:      # eps 缺则回退 basic_eps
        vals[COMMON_COLS.index("eps")] = _num(row.get("basic_eps"))
    return vals


def load_annual(L):
    for industry in INDUSTRIES:
        for path in sorted(glob.glob(os.path.join(TABLES, "%s_*_annual.json" % industry))):
            d = json.load(open(path, encoding="utf-8"))
            code = _txt(d.get("code")) or re.search(r"_(\w+)_annual", os.path.basename(path)).group(1)
            L.ensure_company(code, industry, _txt(d.get("name")))
            L.add("financial_meta", (code, _txt(d.get("secucode")), _txt(d.get("currency")),
                  _txt(d.get("group")), _txt(d.get("source")), _txt(d.get("unit_note")),
                  _txt(d.get("caliber_note")), _txt(d.get("fetched_at"))))
            for year, row in (d.get("annual") or {}).items():
                if not (YEAR.match(str(year)) and isinstance(row, dict)):
                    continue
                yr = int(year)
                cv = _common_values(row)
                if any(v is not None for v in cv):
                    L.add("financial_common", (code, yr, *cv))
                for k, v in row.items():
                    if k in CONSUMED:
                        continue
                    val = _num(v)
                    if val is not None:
                        L.add("financial_metric", (code, yr, k, val))
                        L.add_metric(k, industry)
            for year, val in (d.get("dividend_per10") or {}).items():
                v = _num(val)
                if YEAR.match(str(year)) and v is not None:
                    L.add("dividend_per10", (code, int(year), v, "元"))
            end = _txt(d.get("holders_end_date"))
            for h in d.get("holders") or []:
                L.add("shareholder_top10", (code, end, h.get("rank"), _txt(h.get("name")),
                      _num(h.get("hold_num")), _num(h.get("ratio")), _txt(h.get("change")),
                      _txt(h.get("state")), _txt(h.get("shares_type")),
                      _num(h.get("total_shares")), _num(h.get("pledged"))))
            _load_segments(L, code, d.get("segments"))


def _load_segments(L, code, seg):
    """telecom 等的分部数据，尽力识别 {年:{分部:值}} 或 {分部:{年:值}} 两种形态。"""
    if not isinstance(seg, dict) or not seg:
        return
    top_years = all(YEAR.match(str(k)) for k in seg)
    for k1, sub in seg.items():
        if not isinstance(sub, dict):
            continue
        for k2, v in sub.items():
            year, segment = (k1, k2) if top_years else (k2, k1)
            val = _num(v)
            if YEAR.match(str(year)) and val is not None:
                L.add("segment_annual", (code, int(year), str(segment)[:64], "revenue", val))


def load_holders_manual(L):
    d = _load_json("holders_manual.json")
    for key, e in d.items():
        if ":" not in key or not isinstance(e, dict):
            continue
        industry, code = key.split(":", 1)
        L.ensure_company(code, industry, _txt(e.get("name")))
        end = _txt(e.get("holders_end_date"))
        for h in e.get("holders") or []:
            L.add("shareholder_top10", (code, end, h.get("rank"), _txt(h.get("name")),
                  _num(h.get("hold_num")), _num(h.get("ratio")), _txt(h.get("change")),
                  _txt(h.get("state")), _txt(h.get("shares_type")),
                  _num(h.get("total_shares")), _num(h.get("pledged"))))
        for fac in e.get("factions") or []:
            L.factions.append({"company_code": code, "title": _txt(fac.get("title")) or "",
                               "color": _txt(fac.get("color")), "basis": _txt(fac.get("basis")),
                               "members": [str(n) for n in (fac.get("names") or [])]})
        for r in e.get("holder_num") or []:
            if isinstance(r, list) and r and _txt(r[0]):
                L.add("holder_count", (code, r[0], _num(r[1]) if len(r) > 1 else None,
                                       _num(r[2]) if len(r) > 2 else None))
        for r in e.get("holder_concentration") or []:
            if isinstance(r, dict) and _txt(r.get("date")):
                L.add("holder_concentration", (code, r["date"], _num(r.get("top1")),
                      _num(r.get("top3")), _num(r.get("top10")), _num(r.get("top1_ex")),
                      _num(r.get("top3_ex")), _txt(r.get("top1_name")), _txt(r.get("top1_ex_name"))))
        for r in e.get("share_capital") or []:
            if isinstance(r, list) and r and YEAR.match(str(r[0])):
                L.add("share_capital_history", (code, int(r[0]), _num(r[1]) if len(r) > 1 else None,
                                                _txt(r[2]) if len(r) > 2 else None))
        unit = _txt(e.get("dividend_unit")) or "元"
        for r in e.get("dividend_per10") or []:
            if isinstance(r, list) and len(r) >= 2 and YEAR.match(str(r[0])) and _num(r[1]) is not None:
                L.add("dividend_per10", (code, int(r[0]), _num(r[1]), unit))


def load_telecom_segments(L):
    """telecom_segment_manual.json：companies[code].annual[year].canon = {分部:值}，
    用 canon 的规范键；剔除 total/合计（那是营业收入，另在 financial_common 里）。"""
    path = os.path.join(TABLES, "telecom_segment_manual.json")
    if not os.path.exists(path):
        return
    d = json.load(open(path, encoding="utf-8"))
    for code, c in (d.get("companies") or {}).items():
        L.ensure_company(code, "telecom", _txt(c.get("name")))
        for year, blk in (c.get("annual") or {}).items():
            segs = (blk or {}).get("canon") or (blk or {}).get("items") or {}
            if not (YEAR.match(str(year)) and isinstance(segs, dict)):
                continue
            for seg, v in segs.items():
                val = _num(v)
                if seg not in ("total", "合计") and val is not None:
                    L.add("segment_annual", (code, int(year), str(seg)[:64], "revenue", val))


def load_tsf(L):
    for kind, name in (("stock", "tsf_pboc_stock.json"), ("flow", "tsf_pboc_flow.json")):
        path = os.path.join(TABLES, name)
        if not os.path.exists(path):
            continue
        d = json.load(open(path, encoding="utf-8"))
        recs = d.get("data") if isinstance(d, dict) else None
        if isinstance(recs, list):                    # [{month, <series>:值, ...}]（实际形态）
            for rec in recs:
                if not isinstance(rec, dict):
                    continue
                m = _txt(rec.get("month") or rec.get("date"))
                if not m:
                    continue
                for k, v in rec.items():
                    if k in ("month", "date"):
                        continue
                    val = _num(v)
                    if val is not None:
                        L.add("tsf_pboc", (kind, m[:7], str(k)[:32], val))
        elif isinstance(d, dict) and isinstance(d.get("months"), list):
            months = d["months"]
            for k, arr in d.items():
                if k == "months" or not isinstance(arr, list):
                    continue
                for m, v in zip(months, arr):
                    val = _num(v)
                    if _txt(m) and val is not None:
                        L.add("tsf_pboc", (kind, str(m)[:7], str(k)[:32], val))
        elif isinstance(d, dict):
            for m, sub in d.items():
                if isinstance(sub, dict):
                    for k, v in sub.items():
                        val = _num(v)
                        if val is not None:
                            L.add("tsf_pboc", (kind, str(m)[:7], str(k)[:32], val))


# 有自然主键/唯一键的表，入库前按键去重（多来源可能给出同一行），保留首次出现。
KEY_COLS = {
    "company_source": ("company_code", "source_line"),
    "financial_meta": ("company_code",),
    "financial_common": ("company_code", "fiscal_year"),
    "financial_metric": ("company_code", "fiscal_year", "metric_code"),
    "dividend_per10": ("company_code", "fiscal_year"),
    "segment_annual": ("company_code", "fiscal_year", "segment", "metric_code"),
    "shareholder_top10": ("company_code", "as_of_date", "shares_type", "rank"),
    "holder_count": ("company_code", "as_of_date"),
    "holder_concentration": ("company_code", "as_of_date"),
    "share_capital_history": ("company_code", "fiscal_year"),
    "tsf_pboc": ("kind", "period_month", "series_key"),
}


def dedupe(L):
    for t, keys in KEY_COLS.items():
        idx = [COLUMNS[t].index(k) for k in keys]
        seen, out = set(), []
        for row in L.rows[t]:
            kk = tuple(row[i] for i in idx)
            if kk not in seen:
                seen.add(kk)
                out.append(row)
        L.rows[t] = out


def _run_schema(cur):
    cur.execute("SET FOREIGN_KEY_CHECKS=0")
    for stmt in open(SCHEMA, encoding="utf-8").read().split(";"):
        code_lines = [ln for ln in stmt.splitlines()
                      if ln.strip() and not ln.strip().startswith("--")]
        if code_lines:
            cur.execute(stmt)
    cur.execute("SET FOREIGN_KEY_CHECKS=1")


def main():
    ap = argparse.ArgumentParser(description="载入 data/tables JSON → MySQL（见文件头用法）")
    ap.add_argument("--dry-run", action="store_true", help="只解析并打印各表行数，不连库")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=3306)
    ap.add_argument("--user", default="root")
    ap.add_argument("--password", default=os.environ.get("MYSQL_PWD", ""))
    ap.add_argument("--db", default="money")
    ap.add_argument("--init", action="store_true", help="入库前先执行 schema.sql 建表")
    a = ap.parse_args()

    L = Loader()
    load_company(L)
    load_annual(L)
    load_holders_manual(L)
    load_tsf(L)
    load_telecom_segments(L)
    L.rows["company"] = list(L.companies.values())
    dedupe(L)

    counts = L.counts()
    order = INSERT_ORDER + ["holder_faction", "holder_faction_member"]
    for t in order:
        print("  %-24s %8d" % (t, counts.get(t, 0)))
    print("  %-24s %8d" % ("(合计)", sum(counts[t] for t in order)))

    if a.dry_run:
        print("dry-run：未连接数据库、未写入。")
        return

    import pymysql
    conn = pymysql.connect(host=a.host, port=a.port, user=a.user,
                           password=a.password, database=a.db, charset="utf8mb4")
    try:
        cur = conn.cursor()
        if a.init:
            _run_schema(cur)
        for t in INSERT_ORDER:
            rows = L.rows[t]
            if not rows:
                continue
            cols = ",".join("`%s`" % c for c in COLUMNS[t])
            ph = ",".join(["%s"] * len(COLUMNS[t]))
            cur.executemany("INSERT INTO `%s` (%s) VALUES (%s)" % (t, cols, ph), rows)
        for f in L.factions:                 # 要拿 AUTO_INCREMENT id 再插成员
            cur.execute("INSERT INTO holder_faction (company_code,title,color,basis) "
                        "VALUES (%s,%s,%s,%s)",
                        (f["company_code"], f["title"], f["color"], f["basis"]))
            if f["members"]:
                cur.executemany("INSERT INTO holder_faction_member "
                                "(faction_id,holder_name,alias_of) VALUES (%s,%s,%s)",
                                [(cur.lastrowid, m, None) for m in f["members"]])
        conn.commit()
        print("入库完成。")
    finally:
        conn.close()


if __name__ == "__main__":
    main()