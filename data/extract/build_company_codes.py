"""生成 data/tables/company_codes.json —— 代码 ↔ 公司实体的映射（A 股与 H 股映射到同一家）。

为什么要这张表：股权结构页只有一份，靠 ?code= 取数，而同一家公司在两地有两个代码
（渝农商行 A 股 601077 / H 股 03618）。有了这张表，给任一代码都能落到同一家公司的数据上，
页面也能把「A 股 xxx · H 股 xxx」照实印出来。

数据来源一律本地（不联网）：
  · 银行：data/tables/company_charts_<code>.json 的 _bank 块（aCode / hCode / fullName /
    shortName / tier）—— 44 家生成件 + 601077 手工精编件都有这一块；
  · 其余板块：dashboard/industry/<行业>/overview.html 的「A/H 股概览」表、
    data/tables/<板块>_<code>_annual.json 的 name / secucode / source。

关键约定：
  · **same_entity=false 的不当作同一家**。中国联通 A 股 600050（中国联合网络通信股份有限公司）
    与红筹 00762 不是同一法人，给 00762 不会解析到 600050，接口会直接说明原因。
  · 纯 H 股公司 a_code=null；仅 A 股公司 h_code=null；不凭常识补代码，本地没出处就留 null。
  · key 为实体唯一键：有 A 股用 A 股代码，纯 H 股用 H 股代码 —— 与 HOLDER_INDUSTRIES 里
    登记的代码保持一致，后端据此判断这条映射服务哪个板块。

用法：venv/bin/python data/extract/build_company_codes.py [来源草稿.json]
默认读 data/extract/out/company_codes_draft.json（逐条带 sources 的调查底稿，逐家在本地
数据表与页面里核对过），校验后写入 data/tables/company_codes.json。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TABLES = os.path.join(os.path.dirname(HERE), "tables")
OUT = os.path.join(TABLES, "company_codes.json")
DRAFT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out",
                                                           "company_codes_draft.json")

FIELDS = ("key", "short", "full", "industry", "a_code", "h_code", "us_code",
          "tier", "same_entity", "note", "sources")


def norm_code(c):
    """H 股代码统一补零到 5 位（年报封面写 941 / 3618，项目里一律 00941 / 03618）。"""
    if not c:
        return None
    c = str(c).strip()
    return c.zfill(5) if c.isdigit() and len(c) < 5 else c


def main():
    with open(DRAFT, encoding="utf-8") as f:
        draft = json.load(f)
    ents, seen = [], {}
    for e in draft["entities"]:
        rec = {k: e.get(k) for k in FIELDS}
        rec["a_code"] = (str(rec["a_code"]).strip() or None) if rec["a_code"] else None
        rec["h_code"] = norm_code(rec["h_code"])
        rec["key"] = str(rec["key"]).strip()
        assert rec["key"], e
        assert rec["a_code"] or rec["h_code"], f"{rec['key']} 两地代码全空"
        assert rec["key"] in (rec["a_code"], rec["h_code"], rec["us_code"]), \
            f"{rec['key']} 不是自己的任一代码"
        # 一个代码只能指向一家公司（撞号的必须在草稿里就分清，如 002233 塔牌 vs 02233 西部水泥）
        for c in (rec["a_code"], rec["h_code"], rec["us_code"]):
            if not c:
                continue
            assert c not in seen or seen[c] == rec["key"], \
                f"代码 {c} 同时指向 {seen[c]} 与 {rec['key']}"
            seen[c] = rec["key"]
        ents.append(rec)
    ents.sort(key=lambda r: (r["industry"], r["key"]))
    out = {
        "_meta": {
            "generated_by": "data/extract/build_company_codes.py",
            "consumed_by": "backend_python.py::_resolve_company_code → /api/holders → "
                           "dashboard/company/bank/shareholder.html",
            "note": "key 为实体唯一键（有 A 股用 A 股代码，纯 H 股用 H 股代码）；"
                    "a_code / h_code / us_code 是同一家公司在三地的代码，"
                    "same_entity=false 表示两地主体不是同一法人（中国联通 A 股 vs 红筹），"
                    "这类不做代码互换。每条的 sources 记着本地出处，不联网、不凭常识补代码。",
        },
        "entities": ents,
        "gaps": draft.get("gaps") or [],
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    ah = [e for e in ents if e["a_code"] and e["h_code"]]
    print("written", OUT)
    print(f"  实体 {len(ents)} 家；A+H 双代码 {len(ah)} 家；"
          f"纯 H 股 {sum(1 for e in ents if not e['a_code'])} 家；"
          f"仅 A 股 {sum(1 for e in ents if not e['h_code'])} 家")
    for e in ents:
        if e["same_entity"] is not True:
            print(f"  [特例] {e['key']} {e['short']}: same_entity={e['same_entity']} — {e['note'][:60]}")


if __name__ == "__main__":
    main()
