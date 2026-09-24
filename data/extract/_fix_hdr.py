#!/usr/bin/env python
"""临时件：把 tables/*.sql 首行的「拆自 data/sql/schema.sql · 段 X」改成「· 段 X」（用完即删）。"""
import os, re, glob

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "data", "sql", "tables")
pat = re.compile(r"（拆自 data/sql/schema\.sql · 段 (.*)）")

n = 0
for path in sorted(glob.glob(os.path.join(OUT, "*.sql"))):
    lines = open(path, encoding="utf-8").read().splitlines()
    new0 = pat.sub(r"· 段 \1", lines[0]).rstrip()
    if new0 != lines[0]:
        lines[0] = new0
        open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
        n += 1
print(f"fixed={n}")
