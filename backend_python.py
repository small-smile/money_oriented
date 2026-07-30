import numpy as np
import pandas as pd
from flask import Flask, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

def read_production():
    path = "data/tables/oil.production.txt"
    xAxis = []
    prodData = []

    # 文件不存在容错
    if not os.path.exists(path):
        return {
            "code": 500,
            "msg": "产量数据文件不存在",
            "data": {
                "xAxis": [],
                "prodData": [],
                "lineProd": []
            }
        }

    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()[1:]
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) < 2:
                    continue
                year, prod = parts[0], parts[1]
                xAxis.append(year)
                prodData.append(int(prod))

    except Exception as e:
        return {
            "code": 500,
            "msg": str(e),
            "data": {
                "xAxis": [],
                "prodData": [],
                "lineProd": []
            }
        }

    return {
        "code": 200,
        "data": {
            "xAxis": xAxis,
            "prodData": prodData,
            "lineProd": [[v, v, v, v] for v in prodData]
        }
    }

def read_price():
    path = "data/tables/oil.price.txt"
    candleData = []
    xAxis = []
    prev_raw = None  # 保存上一期价格

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()[1:]
        for line in lines:
            line = line.strip()
            if not line:
                continue
            year, raw_str, adj = line.split("\t")
            curr_raw = float(raw_str)

            if prev_raw is None:
                # 第一条没有上期数据，开盘=本期
                open_p = curr_raw
            else:
                # 开盘 = 上一周期价格
                open_p = prev_raw

            close_p = curr_raw
            high_p = max(open_p, close_p)
            low_p = min(open_p, close_p)

            candleData.append([open_p, close_p, low_p, high_p])
            xAxis.append(year)

            # 更新上期价格
            prev_raw = curr_raw

    return {
        "code": 200,
        "data": {
            'candleData': candleData,
            'xAxis': xAxis
        }
    }

def read_adj_price():
    path = "data/tables/oil.price.txt"
    candleData = []
    xAxis = []
    prev_raw = None  # 保存上一期价格

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()[1:]
        for line in lines:
            line = line.strip()
            if not line:
                continue
            year, raw_str, adj = line.split("\t")
            curr_raw = float(adj)

            if prev_raw is None:
                # 第一条没有上期数据，开盘=本期
                open_p = curr_raw
            else:
                # 开盘 = 上一周期价格
                open_p = prev_raw

            close_p = curr_raw
            high_p = max(open_p, close_p)
            low_p = min(open_p, close_p)

            candleData.append([open_p, close_p, low_p, high_p])
            xAxis.append(year)

            # 更新上期价格
            prev_raw = curr_raw

    return {
        "code": 200,
        "data": {
            'candleData': candleData,
            'xAxis': xAxis
        }
    }


def read_production_region():
    path = "data/tables/production_region.csv"
    df = pd.read_csv(path)

    # ── 将 CIS 所有成员国合并为 "USSR/CIS"，避免苏联解体前后产量跳跃 ──
    CIS_MEMBERS = {'USSR', 'Russian Federation', 'Azerbaijan', 'Kazakhstan',
                   'Turkmenistan', 'Uzbekistan', 'Other CIS'}
    cis_sum = (df[df['国家'].isin(CIS_MEMBERS)]
               .groupby('年份')['产量(千桶/日)'].sum()
               .reset_index())
    cis_sum['国家'] = 'USSR/CIS'
    cis_sum['洲']  = 'CIS'
    df = pd.concat([df[~df['国家'].isin(CIS_MEMBERS)], cis_sum], ignore_index=True)

    years = sorted(df['年份'].unique().tolist())

    # 按洲汇总
    region_sum = df.groupby(['年份', '洲'])['产量(千桶/日)'].sum().reset_index()
    regions = sorted(df['洲'].unique().tolist())
    region_data = {}
    for r in regions:
        sub = region_sum[region_sum['洲'] == r].sort_values('年份')
        region_data[r] = [round(float(v), 1) for v in sub['产量(千桶/日)'].tolist()]

    # 2024 年产量 Top10 国家
    top10 = df[df['年份'] == 2024].nlargest(10, '产量(千桶/日)')['国家'].tolist()
    country_data = {}
    for c in top10:
        sub = df[df['国家'] == c].sort_values('年份')
        year_map = dict(zip(sub['年份'], sub['产量(千桶/日)']))
        vals = []
        for y in years:
            v = year_map.get(y)
            if v is not None and not (isinstance(v, float) and v != v):
                vals.append(round(float(v), 1))
            else:
                vals.append(None)
        country_data[c] = vals

    # 2024 年各洲饼图数据
    pie_2024 = []
    for r in regions:
        sub = region_sum[(region_sum['洲'] == r) & (region_sum['年份'] == 2024)]
        pie_2024.append({'name': r, 'value': round(float(sub['产量(千桶/日)'].values[0]), 1)})

    # 各国 1965→2024 产量变化（有头有尾才纳入）
    first_year, last_year = years[0], years[-1]
    country_changes = []
    for c in df['国家'].unique():
        sub = df[df['国家'] == c].sort_values('年份')
        year_map = dict(zip(sub['年份'], sub['产量(千桶/日)']))
        v_first = year_map.get(first_year)
        v_last  = year_map.get(last_year)
        if (v_first is not None and v_last is not None
                and not (isinstance(v_first, float) and v_first != v_first)
                and not (isinstance(v_last,  float) and v_last  != v_last)):
            continent = sub['洲'].iloc[0]
            change = round(float(v_last) - float(v_first), 1)
            country_changes.append({
                'country':   c,
                'continent': continent,
                'v_first':   round(float(v_first), 1),
                'v_last':    round(float(v_last),  1),
                'change':    change
            })
    country_changes.sort(key=lambda x: x['change'])

    # 各国 2001 vs 2024 对比，按洲分组
    continents = sorted(df['洲'].unique().tolist())
    country_compare = {}
    for cont in continents:
        sub = df[df['洲'] == cont]
        entries = []
        for c in sorted(sub['国家'].unique()):
            csub = sub[sub['国家'] == c].sort_values('年份')
            ym = dict(zip(csub['年份'], csub['产量(千桶/日)']))
            v2001 = ym.get(2001)
            v2024 = ym.get(2024)
            if v2001 is not None and v2024 is not None:
                entries.append({
                    'country': c,
                    'v2001': round(float(v2001), 1),
                    'v2024': round(float(v2024), 1)
                })
        country_compare[cont] = entries

    # 所有国家逐年数据（用于 demo_3c/3d）
    # 排序：① 增/减（2024 vs 1965 变化方向），② 2024 绝对产量降序
    all_countries = df['国家'].unique().tolist()
    country_all_data = {}
    country_meta = {}   # {country: {continent, v_last, change}}
    for c in all_countries:
        sub = df[df['国家'] == c].sort_values('年份')
        ym = dict(zip(sub['年份'], sub['产量(千桶/日)']))
        vals = []
        for y in years:
            v = ym.get(y)
            vals.append(round(float(v), 1) if v is not None and not (isinstance(v, float) and v != v) else None)
        country_all_data[c] = vals
        v_last  = ym.get(years[-1])
        v_first = ym.get(years[0])
        v_last  = round(float(v_last),  1) if v_last  is not None else 0.0
        v_first = round(float(v_first), 1) if v_first is not None else 0.0
        country_meta[c] = {
            'continent': sub['洲'].iloc[0],
            'v_last': v_last,
            'change': round(v_last - v_first, 1)
        }

    # 排序：先增后减，各组内按 2024 产量降序
    def sort_key(c):
        m = country_meta[c]
        group = 0 if m['change'] >= 0 else 1   # 增加在前
        return (group, -m['v_last'])

    sorted_countries = sorted(all_countries, key=sort_key)

    return {
        "code": 200,
        "data": {
            "years": years,
            "region_data": region_data,
            "top10": top10,
            "country_data": country_data,
            "pie_2024": pie_2024,
            "country_changes": country_changes,
            "country_compare": country_compare,
            "country_all_data": country_all_data,
            "country_meta": country_meta,
            "sorted_countries": sorted_countries
        }
    }


def read_consumption_region():
    path = "data/tables/consumption_region.csv"
    df = pd.read_csv(path)

    # ── 将 CIS 所有成员国合并为 "USSR/CIS"，避免苏联解体前后产量跳跃 ──
    CIS_MEMBERS = {'USSR', 'Russian Federation', 'Azerbaijan', 'Kazakhstan',
                   'Turkmenistan', 'Uzbekistan', 'Other CIS'}
    cis_sum = (df[df['国家'].isin(CIS_MEMBERS)]
               .groupby('年份')['消费量(千桶/日)'].sum()
               .reset_index())
    cis_sum['国家'] = 'USSR/CIS'
    cis_sum['洲']  = 'CIS'
    df = pd.concat([df[~df['国家'].isin(CIS_MEMBERS)], cis_sum], ignore_index=True)

    years = sorted(df['年份'].unique().tolist())

    # 按洲汇总
    region_sum = df.groupby(['年份', '洲'])['消费量(千桶/日)'].sum().reset_index()
    regions = sorted(df['洲'].unique().tolist())
    region_data = {}
    for r in regions:
        sub = region_sum[region_sum['洲'] == r].sort_values('年份')
        region_data[r] = [round(float(v), 1) for v in sub['消费量(千桶/日)'].tolist()]

    # 2024 年产量 Top10 国家
    top10 = df[df['年份'] == 2024].nlargest(10, '消费量(千桶/日)')['国家'].tolist()
    country_data = {}
    for c in top10:
        sub = df[df['国家'] == c].sort_values('年份')
        year_map = dict(zip(sub['年份'], sub['消费量(千桶/日)']))
        vals = []
        for y in years:
            v = year_map.get(y)
            if v is not None and not (isinstance(v, float) and v != v):
                vals.append(round(float(v), 1))
            else:
                vals.append(None)
        country_data[c] = vals

    # 2024 年各洲饼图数据
    pie_2024 = []
    for r in regions:
        sub = region_sum[(region_sum['洲'] == r) & (region_sum['年份'] == 2024)]
        pie_2024.append({'name': r, 'value': round(float(sub['消费量(千桶/日)'].values[0]), 1)})

    # 各国 1965→2024 产量变化（有头有尾才纳入）
    first_year, last_year = years[0], years[-1]
    country_changes = []
    for c in df['国家'].unique():
        sub = df[df['国家'] == c].sort_values('年份')
        year_map = dict(zip(sub['年份'], sub['消费量(千桶/日)']))
        v_first = year_map.get(first_year)
        v_last  = year_map.get(last_year)
        if (v_first is not None and v_last is not None
                and not (isinstance(v_first, float) and v_first != v_first)
                and not (isinstance(v_last,  float) and v_last  != v_last)):
            continent = sub['洲'].iloc[0]
            change = round(float(v_last) - float(v_first), 1)
            country_changes.append({
                'country':   c,
                'continent': continent,
                'v_first':   round(float(v_first), 1),
                'v_last':    round(float(v_last),  1),
                'change':    change
            })
    country_changes.sort(key=lambda x: x['change'])

    # 各国 2001 vs 2024 对比，按洲分组
    continents = sorted(df['洲'].unique().tolist())
    country_compare = {}
    for cont in continents:
        sub = df[df['洲'] == cont]
        entries = []
        for c in sorted(sub['国家'].unique()):
            csub = sub[sub['国家'] == c].sort_values('年份')
            ym = dict(zip(csub['年份'], csub['消费量(千桶/日)']))
            v2001 = ym.get(2001)
            v2024 = ym.get(2024)
            if v2001 is not None and v2024 is not None:
                entries.append({
                    'country': c,
                    'v2001': round(float(v2001), 1),
                    'v2024': round(float(v2024), 1)
                })
        country_compare[cont] = entries

    # 所有国家逐年数据（用于 demo_3c/3d）
    # 排序：① 增/减（2024 vs 1965 变化方向），② 2024 绝对产量降序
    all_countries = df['国家'].unique().tolist()
    country_all_data = {}
    country_meta = {}   # {country: {continent, v_last, change}}
    for c in all_countries:
        sub = df[df['国家'] == c].sort_values('年份')
        ym = dict(zip(sub['年份'], sub['消费量(千桶/日)']))
        vals = []
        for y in years:
            v = ym.get(y)
            vals.append(round(float(v), 1) if v is not None and not (isinstance(v, float) and v != v) else None)
        country_all_data[c] = vals
        v_last  = ym.get(years[-1])
        v_first = ym.get(years[0])
        v_last  = round(float(v_last),  1) if v_last  is not None else 0.0
        v_first = round(float(v_first), 1) if v_first is not None else 0.0
        country_meta[c] = {
            'continent': sub['洲'].iloc[0],
            'v_last': v_last,
            'change': round(v_last - v_first, 1)
        }

    # 排序：先增后减，各组内按 2024 产量降序
    def sort_key(c):
        m = country_meta[c]
        group = 0 if m['change'] >= 0 else 1   # 增加在前
        return (group, -m['v_last'])

    sorted_countries = sorted(all_countries, key=sort_key)

    return {
        "code": 200,
        "data": {
            "years": years,
            "region_data": region_data,
            "top10": top10,
            "country_data": country_data,
            "pie_2024": pie_2024,
            "country_changes": country_changes,
            "country_compare": country_compare,
            "country_all_data": country_all_data,
            "country_meta": country_meta,
            "sorted_countries": sorted_countries
        }
    }


@app.route("/api/production")
def api_prod():
    return jsonify(read_production())


@app.route("/api/price")
def api_price():
    return jsonify(read_price())


@app.route("/api/adj_price")
def api_adj_price():
    return jsonify(read_adj_price())


@app.route("/api/production_region")
def api_production_region():
    return jsonify(read_production_region())


@app.route("/api/consumption_region")
def api_consumption_region():
    return jsonify(read_consumption_region())


def _read_reserves_csv(path, oil_col, price_col):
    """通用储量 CSV 读取：三列拆分 + 实现油价 + 布伦特"""
    df = pd.read_csv(path)
    records = []
    for _, row in df.iterrows():
        def _f(col):
            v = row.get(col)
            if v is None or (isinstance(v, float) and pd.isna(v)):
                return None
            try:
                return float(v)
            except (TypeError, ValueError):
                return None
        records.append({
            "year":     int(row["年份"]),
            "oil":      _f(oil_col),
            "gas":      _f("天然气(十亿立方英尺)"),
            "combined": _f("油气合计(百万桶油当量)"),
            "realized": _f(price_col),
            "brent":    _f("布伦特现货价(美元/桶)"),
            "note":     str(row.get("备注", ""))
        })
    return records


def read_petrochina_reserves():
    return {
        "code": 200,
        "data": _read_reserves_csv(
            "data/tables/petrochina_reserves.csv",
            oil_col="原油凝析油(百万桶)",
            price_col="中石油实现油价(美元/桶)"
        )
    }


def read_cnooc_reserves():
    return {
        "code": 200,
        "data": _read_reserves_csv(
            "data/tables/cnooc_reserves.csv",
            oil_col="石油液体(百万桶)",
            price_col="中海油实现油价(美元/桶)"
        )
    }


@app.route("/api/petrochina_reserves")
def api_petrochina_reserves():
    return jsonify(read_petrochina_reserves())


@app.route("/api/cnooc_reserves")
def api_cnooc_reserves():
    return jsonify(read_cnooc_reserves())


def _read_oil_years_usd():
    """读取 oil.price.txt，返回 (年份列表, {年份: 名义美元价})，作为对齐用的规范 x 轴"""
    path = "data/tables/oil.price.txt"
    years = []
    usd = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f.readlines()[1:]:
            line = line.strip()
            if not line:
                continue
            year, raw_str, adj = line.split("\t")
            years.append(year)
            usd[year] = float(raw_str)
    return years, usd


def read_gold_ratio():
    """油价以黄金计价：每桶原油 = 多少盎司黄金 (oil_usd / gold_usd_per_oz)。
    黄金数据从 1970 起，之前的年份返回 None。"""
    years, oil_usd = _read_oil_years_usd()
    gold = {}
    with open("data/tables/gold.price.txt", "r", encoding="utf-8") as f:
        for line in f.readlines()[1:]:
            line = line.strip()
            if not line:
                continue
            y, close = line.split("\t")
            gold[y] = float(close)
    values = []
    for y in years:
        g = gold.get(y)
        values.append(round(oil_usd[y] / g, 4) if g and g > 0 else None)
    return {"code": 200, "data": {"xAxis": years, "values": values}}


def read_population():
    """世界人口 (亿)，对齐到油价年份。数据从 1960 起 (World Bank SP.POP.TOTL)。"""
    years, _ = _read_oil_years_usd()
    pop = {}
    with open("data/tables/world_population.txt", "r", encoding="utf-8") as f:
        for line in f.readlines()[1:]:
            line = line.strip()
            if not line:
                continue
            y, v = line.split("\t")
            pop[y] = float(v)
    values = [pop.get(y) for y in years]
    return {"code": 200, "data": {"xAxis": years, "values": values}}


def read_bank_financials(stock_code):
    """读取银行财务数据（tab分隔txt文件）"""
    code_name = stock_code.replace('.', '_')
    FILE_MAP = {
        'sh_601288': 'abc_financials.txt',
    }
    filename = FILE_MAP.get(code_name, f'{code_name}_financials.txt')
    path = os.path.join(os.path.dirname(__file__), 'data', 'tables', filename)
    if not os.path.exists(path):
        return None
    records = []
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()[1:]
        for line in lines:
            line = line.strip()
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) < 3:
                continue
            year, revenue, net_profit = parts[0], parts[1], parts[2]
            try:
                records.append({
                    'year': year,
                    'revenue': float(revenue) * 1e8,
                    'net_profit': float(net_profit) * 1e8
                })
            except (ValueError, TypeError):
                continue
    return records if records else None


@app.route("/api/gold_ratio")
def api_gold_ratio():
    return jsonify(read_gold_ratio())


@app.route("/api/population")
def api_population():
    return jsonify(read_population())


@app.route("/api/bank_financials")
def api_bank_financials():
    """获取银行财务数据 - 参数: code (如 sh.601288)"""
    stock_code = request.args.get('code', 'sh.601288')
    data = read_bank_financials(stock_code)
    if data is None:
        return jsonify({"code": 500, "msg": "财务数据文件不存在"})
    return jsonify({"code": 200, "data": data})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
