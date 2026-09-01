#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""一次性辅助脚本：从本地存档的百度 20-F .htm 里把「股权/实益拥有权」相关 <table>
按列结构 dump 成可读网格，供人工语义核对后手工填写结构化 JSON。

纯文本 (.txt) 的表格排版是错乱的，按列取数必须走 .htm 的 <table>。
输出：data/extract/out/_20f_tables/<year>.txt
"""
import os
import re
import sys

from lxml import html as LH

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(ROOT, "data", "raw")
OUT = os.path.join(ROOT, "data", "extract", "out", "_20f_tables")

NBSP = "\u00a0"

KEY_HINTS = (
    "beneficial", "ordinary shares", "class a", "class b",
    "percentage", "voting", "shareholder", "share ownership",
    "weighted voting", "options", "aggregate",
)


def cell_text(td):
    t = td.text_content()
    t = t.replace(NBSP, " ")
    t = re.sub(r"\s+", " ", t).strip()
    return t


def table_grid(tbl):
    rows = []
    for tr in tbl.xpath(".//tr"):
        cells = [cell_text(c) for c in tr.xpath("./td|./th")]
        # 丢掉全空行
        if any(c for c in cells):
            rows.append(cells)
    return rows


def compact(rows):
    """去掉整列为空的列，便于阅读。"""
    if not rows:
        return rows
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    keep = [i for i in range(width) if any(r[i] for r in rows)]
    return [[r[i] for i in keep] for r in rows]


def score(rows):
    flat = " ".join(" ".join(r) for r in rows).lower()
    s = sum(2 for h in KEY_HINTS if h in flat)
    if "%" in flat:
        s += 2
    # 名字行 + 数字
    if re.search(r"\d{1,3}(,\d{3}){2,}", flat):
        s += 2
    if "li" in flat and ("robin" in flat or "yanhong" in flat):
        s += 6
    if "handsome reward" in flat:
        s += 6
    if "directors and executive officers" in flat:
        s += 6
    return s


def preceding_heading(tbl):
    """向前找最近的若干非空文本块，作为章节锚点。"""
    texts = []
    node = tbl
    for _ in range(400):
        prev = node.getprevious()
        while prev is None:
            node = node.getparent()
            if node is None:
                return list(reversed(texts))
            prev = node.getprevious()
        node = prev
        if not isinstance(prev.tag, str):
            continue
        t = cell_text(prev) if prev.tag != "table" else "[TABLE]"
        if t:
            texts.append(t[:260])
        if len(texts) >= 6:
            break
    return list(reversed(texts))


def is_ownership_table(rows):
    flat = " ".join(" ".join(r) for r in rows).lower()
    if "principal shareholders" in flat:
        return True
    if "wvr beneficiaries" in flat:
        return True
    if "beneficially owned" in flat and "%" in flat:
        return True
    if "directors and executive officers as a group" in flat:
        return True
    return False


def main(years):
    os.makedirs(OUT, exist_ok=True)
    summary = []
    for y in years:
        fp = os.path.join(RAW, "20f_09888_%s.htm" % y)
        if not os.path.exists(fp):
            summary.append((y, "MISSING"))
            continue
        with open(fp, "rb") as f:
            doc = LH.fromstring(f.read())
        tables = doc.xpath("//table")
        grids = {}
        picked_idx = []
        for idx, tbl in enumerate(tables):
            rows = compact(table_grid(tbl))
            grids[idx] = rows
            if len(rows) >= 3 and is_ownership_table(rows):
                picked_idx.append(idx)
        # 把命中表后面紧邻的脚注表也带上（20-F 的每条脚注常自成一张 table）
        marker = re.compile(r"^(\(\d{1,2}\)|\*{1,2}|†|Notes:)$")
        want = set()
        for i in picked_idx:
            want.add(i)
            miss = 0
            for j in range(i + 1, min(i + 30, len(tables))):
                rows = grids[j]
                first = rows[0][0].strip() if rows and rows[0] else ""
                if marker.match(first):
                    want.add(j)
                    miss = 0
                else:
                    miss += 1
                    if miss >= 3:
                        break
        picked = [(i, score(grids[i]), grids[i], preceding_heading(tables[i]))
                  for i in sorted(want) if len(grids[i]) >= 1]
        with open(os.path.join(OUT, "%s.txt" % y), "w") as f:
            f.write("### FY%s  total tables in doc = %d ; candidates = %d\n" % (y, len(tables), len(picked)))
            for idx, sc, rows, head in picked:
                f.write("\n===== TABLE #%d (score %d) =====\n" % (idx, sc))
                f.write("-- preceding text --\n")
                for h in head:
                    f.write("   | %s\n" % h)
                f.write("-- grid --\n")
                for r in rows:
                    f.write("   " + " | ".join(r) + "\n")
        summary.append((y, "tables=%d cand=%d" % (len(tables), len(picked))))
    for y, s in summary:
        print(y, s)


if __name__ == "__main__":
    yrs = sys.argv[1:] or [str(y) for y in range(2005, 2026)]
    main(yrs)
