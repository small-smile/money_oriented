#!/usr/bin/env python3
"""生成合并后的每公司股东表 data/tables/<板块>_<code>_shareholder.json。

把原先分散在三处、接口每次请求现拼的数据按公司合并落地成一份：
  · <板块>_<code>_annual.json     —— 东方财富接口前十名股东快照（api 口径）
  · company_charts_<code>.json    —— 银行年报口径环形图 / 历年股本 / 历年分红（annual 口径）
  · holders_manual.json           —— 手工层（factions / tech·food 名册 / 历史序列 / ring_alt_meta）
另带一个 sources 块，逐层记下出处（tier + 出处名 + 来源文件），供页面来源标签（SRC_TIER）用。

合并逻辑复用 backend.holders._stitch_rec（接口 read_holders 现拼时用的同一份函数），
所以「读合并表」与「现拼」给出的数据完全一致 —— 接口有这份表就直接读，没有就退回现拼。
上游与产出的 JSON 都不落盘，原文在 MySQL json_file 表，经 backend/jsonstore.py 按原文件路径读写。

用法（本地跑，venv）：
  venv/bin/python data/extract/build_shareholder_tables.py               # 全量（所有板块所有公司）
  venv/bin/python data/extract/build_shareholder_tables.py 601398 09888  # 只跑指定代码
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from backend import jsonstore                                                  # noqa: E402
from backend.holders import HOLDER_INDUSTRIES, SHAREHOLDER_TABLE, _stitch_rec  # noqa: E402
from backend.shared import TABLES_DIR, _holders_manual                         # noqa: E402

META_NOTE = ("合并自 <板块>_<code>_annual.json（接口快照）、company_charts_<code>.json（年报口径）、"
             "holders_manual.json（手工层）三处；sources 记录各层出处。由 build_shareholder_tables.py "
             "生成，请勿手改：改上游数据后重跑本脚本。")


def build(only=None):
    """only 为代码集合时只生成这些代码，否则全量。返回 (已写文件名, 跳过的键)。"""
    manual = _holders_manual()
    written, skipped = [], []
    for industry, spec in HOLDER_INDUSTRIES.items():
        for code in spec["codes"]:
            if only and code not in only:
                continue
            man = manual.get(f"{industry}:{code}") or {}
            rec = _stitch_rec(industry, code, man)
            if rec is None:
                skipped.append(f"{industry}:{code}")   # 既无 annual 表又无手工层 holders
                continue
            rec["_generated"] = {"code": code, "industry": industry,
                                 "generated_by": "data/extract/build_shareholder_tables.py", "note": META_NOTE}
            name = SHAREHOLDER_TABLE.format(industry=industry, code=code)
            jsonstore.write(os.path.join(TABLES_DIR, name), rec, ensure_ascii=False, indent=2)
            written.append(name)
    return written, skipped


if __name__ == "__main__":
    only = set(sys.argv[1:]) or None
    w, s = build(only)
    print(f"wrote {len(w)} shareholder tables to data/tables/")
    for n in w:
        print("  +", n)
    if s:
        print(f"skipped {len(s)} (no annual table & no manual holders): {', '.join(s)}")
