#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""一次性辅助脚本：从 20-F 纯文本里截取「股份所有权 / 主要股东」章节正文与脚注，
并记录 .txt 行号（用于 anchors 与脚注语义通读）。表格数值不从这里取（排版错乱）。
输出：data/extract/out/_20f_tables/<year>_sec.txt
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(ROOT, "data", "raw")
OUT = os.path.join(ROOT, "data", "extract", "out", "_20f_tables")

START_PAT = re.compile(r"(E\.\s*Share Ownership|Share Ownership\s*$|A\.\s*Major Shareholders)", re.I)
STOP_PAT = re.compile(r"(Item\s*7\.\s*MAJOR SHAREHOLDERS AND RELATED PARTY|B\.\s*Related Party Transactions|Item\s*8\.\s*FINANCIAL INFORMATION)", re.I)
PROBES = [
    r"calculations in the table below are based on",
    r"beneficial ownership of our",
    r"WVR beneficiaries",
    r"weighted voting rights",
    r"each ADS represent",
    r"ADSs? represent(?:ing|s)?",
    r"Handsome Reward",
    r"irrevocable prox",
    r"Schedule 13[GD]",
    r"Class B ordinary shares",
    r"issued and outstanding as of",
    r"holders of record",
]


def main(years):
    os.makedirs(OUT, exist_ok=True)
    for y in years:
        fp = os.path.join(RAW, "20f_09888_%s.txt" % y)
        if not os.path.exists(fp):
            print(y, "MISSING")
            continue
        lines = open(fp, errors="replace").read().split("\n")
        hits = {}
        for p in PROBES:
            rx = re.compile(p, re.I)
            hits[p] = [i + 1 for i, l in enumerate(lines) if rx.search(l)][:14]
        starts = [i for i, l in enumerate(lines) if START_PAT.search(l.strip())]
        # 章节候选：取最靠后且后面 400 行内出现 beneficial ownership 的
        chosen = []
        for s in starts:
            window = "\n".join(lines[s:s + 400]).lower()
            if "beneficial ownership" in window:
                chosen.append(s)
        # 兜底：直接用 "beneficial ownership of our" 命中行往前 40 行做起点
        if not chosen:
            rx = re.compile(r"beneficial ownership of our", re.I)
            chosen = [max(0, i - 40) for i, l in enumerate(lines) if rx.search(l)]
        with open(os.path.join(OUT, "%s_sec.txt" % y), "w") as f:
            f.write("### FY%s  txt lines=%d\n" % (y, len(lines)))
            f.write("-- probe line numbers --\n")
            for p, v in hits.items():
                f.write("  %-45s %s\n" % (p, v))
            f.write("-- section candidates (start line) --  %s\n" % [c + 1 for c in chosen])
            for s in chosen[-2:]:
                end = min(len(lines), s + 900)
                f.write("\n===== SECTION from txt line %d to %d =====\n" % (s + 1, end))
                for j in range(s, end):
                    t = lines[j].rstrip()
                    st = t.strip()
                    if not st:
                        continue
                    if st == "Table of Contents" or re.fullmatch(r"\d{1,3}", st):
                        continue
                    f.write("%6d| %s\n" % (j + 1, t))
        print(y, "ok", "starts=", [c + 1 for c in chosen])


if __name__ == "__main__":
    yrs = sys.argv[1:] or [str(y) for y in range(2005, 2026)]
    main(yrs)
