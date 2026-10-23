#!/usr/bin/env python3
"""生成本地数据检索索引 data/local_index.md。

本地已抽取的年报文本 (data/raw/annual_<code>_<year>.txt) 与成品表 (data/tables/*.json)
都是可信一手来源, 取数应先查本地。但两个目录合计上千个文件, 靠 ls 很难看出
「哪家、哪些年、有哪些指标」。本脚本扫描这两处, 输出一份按公司组织的索引,
供人和子代理直接检索。成品表 *.json 已不落盘 (原文存 MySQL json_file 表), 经 backend/jsonstore.py
列举与读取; 年报文本照旧扫磁盘。

口径与来源说明仍以 data/tables/data_sources.txt 为准, 本文件只回答「有没有、在哪、覆盖哪些年」。

用法:
    ./venv/bin/python data/extract/gen_local_index.py          # 写 data/local_index.md
    ./venv/bin/python data/extract/gen_local_index.py --stdout  # 只打印不落盘
"""
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.dirname(HERE)
sys.path.insert(0, os.path.dirname(DATA))
from backend import jsonstore  # noqa: E402  JSON 表原文在 MySQL json_file 表, 按原文件路径列举/读取

RAW = os.path.join(DATA, 'raw')
TABLES = os.path.join(DATA, 'tables')
OUT = os.path.join(DATA, 'local_index.md')

# 成品表前缀 -> 板块名
SECTORS = [
    ('bank', '银行'),
    ('insurer', '保险'),
    ('cement', '水泥'),
    ('developer', '房地产'),
    ('telecom', '通信'),
]


def years_span(years):
    """把年份列表压成 '2018-2025 (8)' 或带缺口的 '2015-2017,2019-2025 (10)'。"""
    ys = sorted(int(y) for y in years)
    if not ys:
        return ''
    runs, start, prev = [], ys[0], ys[0]
    for y in ys[1:]:
        if y == prev + 1:
            prev = y
            continue
        runs.append((start, prev))
        start = prev = y
    runs.append((start, prev))
    txt = ','.join(str(a) if a == b else f'{a}-{b}' for a, b in runs)
    return f'{txt} ({len(ys)})'


def scan_raw():
    """data/raw/annual_<code>_<year>[_en|.ocr].{txt,pdf} -> {code: {...}}"""
    pat = re.compile(r'^annual_([0-9]{5,6})_(\d{4})(_en)?(\.ocr)?\.(txt|pdf)$')
    out = defaultdict(lambda: {'txt': set(), 'pdf': set(), 'en': set(), 'ocr': set(), 'bytes': 0})
    if not os.path.isdir(RAW):
        return out
    for fn in os.listdir(RAW):
        m = pat.match(fn)
        if not m:
            continue
        code, year, en, ocr, ext = m.groups()
        rec = out[code]
        if en:
            rec['en'].add(year)
        elif ocr:
            rec['ocr'].add(year)
        else:
            rec[ext].add(year)
        if ext == 'txt':
            rec['bytes'] += os.path.getsize(os.path.join(RAW, fn))
    return out


def load(path):
    try:
        return jsonstore.read(path)
    except Exception:
        return None


def scan_tables():
    """按 <sector>_<code>_<kind>.json 归并成 {(sector, code): {kind: data}}。"""
    recs = defaultdict(dict)
    for fn in jsonstore.listdir(TABLES):
        m = re.match(r'^(bank|insurer|cement|developer|telecom)_([0-9]{5,6})_(\w+)\.json$', fn)
        if m:
            sector, code, kind = m.groups()
            recs[(sector, code)][kind] = load(os.path.join(TABLES, fn))
            continue
        m = re.match(r'^company_charts_([0-9]{5,6})\.json$', fn)
        if m:
            recs[('_charts', m.group(1))]['charts'] = load(os.path.join(TABLES, fn))
    return recs


def bank_field_catalog(recs):
    """从任一 bank annual 表里取 annual 的字段名, 作为可查指标清单。"""
    fields, det_keys = set(), set()
    for (sector, _code), kinds in recs.items():
        if sector != 'bank':
            continue
        ann = kinds.get('annual')
        if ann and isinstance(ann.get('annual'), dict):
            for row in ann['annual'].values():
                fields.update(row.keys())
        det = kinds.get('detail_manual')
        if det:
            det_keys.update(k for k in det if not k.startswith('_'))
    return sorted(fields), sorted(det_keys)


KIND_LABEL = {
    'ar_manual': '年报覆盖层',
    'shareholder_manual': '股东手工表',
    'detail_manual': '详情页手工表',
}


def company_rows(sector, recs, raw):
    rows = []
    for (sec, code), kinds in sorted(recs.items(), key=lambda kv: kv[0][1]):
        if sec != sector:
            continue
        ann = kinds.get('annual') or {}
        name = ann.get('name') or '?'
        tag = ann.get('tier') or ann.get('group') or ''
        cur = ann.get('currency')
        if cur and cur != 'CNY':
            tag = f'{tag} {cur}'.strip()
        yrs = years_span((ann.get('annual') or {}).keys())
        det = kinds.get('detail_manual')
        det_n = len([k for k in det if not k.startswith('_')]) if det else 0
        extra = [KIND_LABEL[k] for k in ('ar_manual', 'shareholder_manual') if k in kinds]
        if recs.get(('_charts', code)):
            extra.append('详情页图表')
        r = raw.get(code, {})
        raw_txt = years_span(r.get('txt', ()))
        note = []
        if r.get('en'):
            note.append('英文版 ' + years_span(r['en']))
        if r.get('ocr'):
            note.append('OCR ' + years_span(r['ocr']))
        rows.append({
            'code': code, 'name': name, 'tag': tag, 'annual': yrs,
            'det_n': det_n, 'extra': extra, 'raw': raw_txt, 'note': note,
        })
    return rows


def fmt_rows(rows):
    out = []
    for r in rows:
        head = f"- **{r['code']}** {r['name']}"
        if r['tag']:
            head += f" [{r['tag']}]"
        out.append(head)
        bits = [f"annual {r['annual']}" if r['annual'] else 'annual 无']
        if r['det_n']:
            bits.append(f"detail_manual {r['det_n']} 键")
        bits += r['extra']
        out.append('  - 成品表: ' + '; '.join(bits))
        if r['raw']:
            line = f"  - 年报文本: raw/annual_{r['code']}_<年>.txt {r['raw']}"
            if r['note']:
                line += '; ' + '; '.join(r['note'])
            out.append(line)
    return out


HEADER = """# 本地数据检索索引 (data/)

**本地已抽取的年报是可信一手来源。取任何公司财务数据, 先查本地, 本地没有再去交易所/官网。**
`data/raw/annual_<code>_<year>.txt` 是交易所或公司官网年报 PDF 经 `pdftotext -layout`
抽出的原文, 与 `data/tables/*.json` 里由它汇总的数值同源, 不需要回交易所重新覆核;
只有本地确实缺该公司/该年份/该指标时才去外部抓取。

本文件由 `data/extract/gen_local_index.py` 生成, 回答「有没有、在哪、覆盖哪些年」。
**口径、单位、来源与历次陷阱记在 `data/tables/data_sources.txt`, 引用数值前读那份。**

## 怎么查

1. 看下面的公司清单确认代码与年份覆盖。
2. 要连续年度指标 -> `data/tables/<板块>_<code>_annual.json` 的 `annual["2025"]["nim"]` 这类路径。
3. 要年报里的明细表 (期限结构/五级分类/分部/员工/迁徙率等) -> `bank_<code>_detail_manual.json`,
   键名见文末清单, 每个键的口径写在同文件 `_notes` 里。
4. 表里没有的指标 -> 直接读 `data/raw/annual_<code>_<year>.txt`, 按章节语义通读, 不要 grep 单词。
5. A+H 两地都有年报时优先 A 股; 纯 H 股公司才用 H 股年报 (`_notes` 会注明)。
"""

FOOTER_TMPL = """
## `<板块>_<code>_annual.json` 可查字段

顶层: `code / secucode / name / tier|group / fetched_at / source / unit_note / annual /
holders / holder_num / holder_concentration / dividend_per10`。金额单位元, 比率单位 %。
`annual` 以年份字符串为键, 每年一个 dict, 字段:

{fields}

注意 `share_capital` / `total_share` 在多数行是最新值向历年回填, 不能用来看历年股本变动。

## `bank_<code>_detail_manual.json` 键

{det_keys}

各键的年份范围、期末/日均口径、单位都写在同文件的 `_notes` 里, 读值前先读 `_notes`。
"""


def sector_manual_lines(sector):
    """板块级手工层（不按公司分文件的 <板块>_*_manual.json，如 telecom_ops_manual.json、
    telecom_segment_manual.json）：列出文件名与每家覆盖的年份，否则这两层在索引里查不到。"""
    out = []
    for fn in jsonstore.listdir(TABLES):
        if not re.fullmatch(rf'{sector}_[a-z_]+_manual\.json', fn):
            continue                      # 按公司分的手工表（含 6 位代码）已在公司行里列出
        d = load(os.path.join(TABLES, fn)) or {}
        comps = d.get('companies') or {}
        if not comps:
            continue
        bits = [f"{c.get('name') or code} {years_span((c.get('annual') or {}).keys())}"
                for code, c in sorted(comps.items())]
        out.append(f'- 板块手工层 `{fn}`: ' + '; '.join(bits))
    return out


def build():
    raw = scan_raw()
    recs = scan_tables()
    lines = [HEADER]
    covered = set()
    for sector, label in SECTORS:
        rows = company_rows(sector, recs, raw)
        if not rows:
            continue
        covered.update(r['code'] for r in rows)
        lines.append(f'\n## {label} ({len(rows)} 家) — `{sector}_<code>_*.json`\n')
        lines.extend(fmt_rows(rows))
        man = sector_manual_lines(sector)
        if man:
            lines.append('')
            lines.extend(man)

    orphan = sorted(set(raw) - covered)
    if orphan:
        lines.append('\n## 只有年报文本、没有成品表的代码\n')
        lines.append('没有对应的 `*_annual.json`, 需要时直接读文本 '
                     '(可能是同一家公司的另一上市地, 也可能是尚未入库的公司):\n')
        for code in orphan:
            r = raw[code]
            bits = [years_span(r['txt'])] if r['txt'] else []
            if r['en']:
                bits.append('英文版 ' + years_span(r['en']))
            if r['ocr']:
                bits.append('OCR ' + years_span(r['ocr']))
            lines.append(f"- **{code}**: raw/annual_{code}_<年>.txt " + '; '.join(bits))

    fields, det_keys = bank_field_catalog(recs)
    lines.append(FOOTER_TMPL.format(
        fields='`' + '` / `'.join(fields) + '`',
        det_keys='`' + '` / `'.join(det_keys) + '`',
    ))
    n_txt = sum(len(r['txt']) for r in raw.values())
    mb = sum(r['bytes'] for r in raw.values()) / 1024 / 1024
    lines.append(f'\n---\n共 {len(raw)} 个代码、{n_txt} 份年报文本 ({mb:.0f} MB)。'
                 f'新增公司或年份后重跑 `python3 data/extract/gen_local_index.py`。\n')
    return '\n'.join(lines)


if __name__ == '__main__':
    text = build()
    if '--stdout' in sys.argv:
        print(text)
    else:
        with open(OUT, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f'wrote {OUT} ({len(text)} chars)')
