#!/usr/bin/env python3
"""本地 SQL 查询引擎：把 data/tables/*_annual.json 装进 DuckDB，供 ad-hoc 取数与交叉核对。

用法：
    python3 data/extract/query_engine.py                      # 打印可查的表与示例
    python3 data/extract/query_engine.py "SELECT ... "        # 跑一条 SQL
    python3 data/extract/query_engine.py -f q.sql             # 跑文件里的 SQL
    python3 data/extract/query_engine.py --db data/tables/query.duckdb "SQL"   # 落盘复用

装好的表：
    annual(kind, code, name, year, metric, value_num, value_txt) —— 长表，一行一个指标年份
    annual_meta(kind, code, name, secucode, tier, source, unit_note, fetched_at, file)
"""
import argparse
import glob
import json
import os
import sys

import duckdb

TABLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tables')

# 文件名前缀 → 行业，annual JSON 只有这三类
KINDS = {'bank_': 'bank', 'insurer_': 'insurer', 'developer_': 'developer'}


def _kind(name):
    for prefix, kind in KINDS.items():
        if name.startswith(prefix):
            return kind
    return 'other'


def _rows():
    """扫描 *_annual.json，产出 (长表行, 元信息行)。"""
    facts, metas = [], []
    for path in sorted(glob.glob(os.path.join(TABLES_DIR, '*_annual.json'))):
        name = os.path.basename(path)
        with open(path, encoding='utf-8') as fh:
            doc = json.load(fh)
        annual = doc.get('annual')
        if not isinstance(annual, dict):
            continue
        kind = _kind(name)
        code, cname = doc.get('code'), doc.get('name')
        metas.append((kind, code, cname, doc.get('secucode'), doc.get('tier'),
                      doc.get('source'), doc.get('unit_note'), doc.get('fetched_at'), name))
        for year, record in annual.items():
            if not isinstance(record, dict):
                continue
            for metric, value in record.items():
                num = value if isinstance(value, (int, float)) and not isinstance(value, bool) else None
                txt = None if num is not None or value is None else json.dumps(value, ensure_ascii=False)
                facts.append((kind, code, cname, int(year), metric, num, txt))
    return facts, metas


def build(db=':memory:'):
    """建库并装数，返回 DuckDB 连接。"""
    con = duckdb.connect(db)
    facts, metas = _rows()
    con.execute('DROP TABLE IF EXISTS annual')
    con.execute('DROP TABLE IF EXISTS annual_meta')
    con.execute("""CREATE TABLE annual(kind VARCHAR, code VARCHAR, name VARCHAR, year INTEGER,
                   metric VARCHAR, value_num DOUBLE, value_txt VARCHAR)""")
    con.execute("""CREATE TABLE annual_meta(kind VARCHAR, code VARCHAR, name VARCHAR,
                   secucode VARCHAR, tier VARCHAR, source VARCHAR, unit_note VARCHAR,
                   fetched_at VARCHAR, file VARCHAR)""")
    con.executemany('INSERT INTO annual VALUES (?,?,?,?,?,?,?)', facts)
    con.executemany('INSERT INTO annual_meta VALUES (?,?,?,?,?,?,?,?,?)', metas)
    return con


def show(sql, rows):
    print(f'-- {sql.strip()}')
    for row in rows:
        print('  ' + ' | '.join('' if v is None else str(v) for v in row))


def main():
    ap = argparse.ArgumentParser(description='DuckDB 本地查询引擎（data/tables/*_annual.json）')
    ap.add_argument('sql', nargs='?', help='要执行的 SQL')
    ap.add_argument('-f', '--file', help='从文件读 SQL')
    ap.add_argument('--db', default=':memory:', help='落盘的 duckdb 文件，缺省内存库')
    args = ap.parse_args()

    con = build(args.db)
    sql = args.sql
    if args.file:
        with open(args.file, encoding='utf-8') as fh:
            sql = fh.read()
    if not sql:
        n_files, = con.execute('SELECT count(*) FROM annual_meta').fetchone()
        n_facts, = con.execute('SELECT count(*) FROM annual').fetchone()
        print(f'装入 {n_files} 份 *_annual.json，{n_facts} 行指标事实。表：annual / annual_meta')
        show('每类几家、年份跨度',
             con.execute("""SELECT kind, count(DISTINCT code) AS n_company,
                            min(year), max(year), count(DISTINCT metric) AS n_metric
                            FROM annual GROUP BY kind ORDER BY kind""").fetchall())
        print('\n示例：')
        print("""  python3 data/extract/query_engine.py "SELECT name, year, value_num FROM annual """
              """WHERE metric='netprofit' AND code='601077' ORDER BY year DESC LIMIT 5" """)
        return

    cur = con.execute(sql)
    cols = [d[0] for d in cur.description] if cur.description else []
    rows = cur.fetchall()
    if cols:
        print(' | '.join(cols))
        print('-+-'.join('-' * len(c) for c in cols))
    for row in rows:
        print(' | '.join('' if v is None else str(v) for v in row))
    print(f'({len(rows)} rows)', file=sys.stderr)


if __name__ == '__main__':
    main()
