#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把 dump_20f_ownership_tables.py 的输出压成精简摘要：
只保留实益拥有权表格网格 + 有数据含量的脚注（丢掉纯 business address 脚注）。
输出：data/extract/out/_20f_tables/digest_<a>_<b>.txt
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "data", "extract", "out", "_20f_tables")

DROP = re.compile(r"^\(\d+\)\s*\|\s*The (business )?address", re.I)
KEEP_HINT = re.compile(r"(Includes|Represents|Percentage|Less than|based on|Schedule 13|voting power|ADS|Class [AB]|proxy|proxies)", re.I)


def digest(year):
    fp = os.path.join(OUT, "%s.txt" % year)
    out = ["#### FY%s" % year]
    keep = False
    for line in open(fp, errors="replace"):
        s = line.rstrip("\n")
        st = s.strip()
        if st.startswith("===== TABLE"):
            out.append(st)
            keep = False
            continue
        if st.startswith("-- preceding text --"):
            keep = "pre"
            continue
        if st.startswith("-- grid --"):
            keep = "grid"
            continue
        if keep == "pre":
            # 只留像章节标题/表引言的行
            if re.search(r"(Share Ownership|beneficial ownership|Major Shareholders|WVR|weighted voting|calculations in the table|following table)", st, re.I):
                out.append("  PRE: " + st[:400])
            continue
        if keep == "grid":
            body = st
            if DROP.match(body):
                continue
            if re.match(r"^\(\d+\)\s*\|", body) or re.match(r"^\*+\s*\|", body) or re.match(r"^†\s*\|", body):
                if not KEEP_HINT.search(body):
                    continue
            out.append("  " + body)
    return "\n".join(out)


if __name__ == "__main__":
    years = sys.argv[1:]
    txt = "\n\n".join(digest(y) for y in years)
    name = "digest_%s_%s.txt" % (years[0], years[-1])
    with open(os.path.join(OUT, name), "w") as f:
        f.write(txt)
    print(os.path.join(OUT, name), len(txt), "chars")
