import numpy as np
import pandas as pd
from flask import Blueprint, jsonify
import os

from backend.shared import success, error

oil_bp = Blueprint("oil", __name__)


def read_production():
    path = "data/tables/oil.production.txt"
    xAxis = []
    prodData = []

    # 文件不存在容错
    if not os.path.exists(path):
        return error("产量数据文件不存在", 500,
                     {"xAxis": [], "prodData": [], "lineProd": []})

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
        return error(str(e), 500,
                     {"xAxis": [], "prodData": [], "lineProd": []})

    return success({
        "xAxis": xAxis,
        "prodData": prodData,
        "lineProd": [[v, v, v, v] for v in prodData]
    })

def _read_oil_candles(col):
    """oil.price.txt（年份 / 原价 / 通胀调整价）→ 年 K 线：开盘取上一年收盘，
    首年开盘=收盘。col=1 取原价、col=2 取通胀调整价，两个接口只差这一列。"""
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
            parts = line.split("\t")
            year = parts[0]
            curr_raw = float(parts[col])

            # 开盘 = 上一周期价格；第一条没有上期数据，开盘=本期
            open_p = curr_raw if prev_raw is None else prev_raw
            close_p = curr_raw
            high_p = max(open_p, close_p)
            low_p = min(open_p, close_p)

            candleData.append([open_p, close_p, low_p, high_p])
            xAxis.append(year)

            # 更新上期价格
            prev_raw = curr_raw

    return success({
        'candleData': candleData,
        'xAxis': xAxis
    })


def read_price():
    return _read_oil_candles(1)


def read_adj_price():
    return _read_oil_candles(2)


def _read_region_csv(path, value_col):
    """production_region.csv / consumption_region.csv 的共用读法：两份表结构一样
    （年份 / 洲 / 国家 + 一列数值），只差数值列名，产量与消费量的聚合、Top10、
    首末年变化、2001 vs 2024 分洲对比、排序规则完全相同，所以只留一份实现。"""
    df = pd.read_csv(path)

    # ── 将 CIS 所有成员国合并为 "USSR/CIS"，避免苏联解体前后数值跳跃 ──
    CIS_MEMBERS = {'USSR', 'Russian Federation', 'Azerbaijan', 'Kazakhstan',
                   'Turkmenistan', 'Uzbekistan', 'Other CIS'}
    cis_sum = (df[df['国家'].isin(CIS_MEMBERS)]
               .groupby('年份')[value_col].sum()
               .reset_index())
    cis_sum['国家'] = 'USSR/CIS'
    cis_sum['洲']  = 'CIS'
    df = pd.concat([df[~df['国家'].isin(CIS_MEMBERS)], cis_sum], ignore_index=True)

    years = sorted(df['年份'].unique().tolist())

    # 按洲汇总
    region_sum = df.groupby(['年份', '洲'])[value_col].sum().reset_index()
    regions = sorted(df['洲'].unique().tolist())
    region_data = {}
    for r in regions:
        sub = region_sum[region_sum['洲'] == r].sort_values('年份')
        region_data[r] = [round(float(v), 1) for v in sub[value_col].tolist()]

    # 2024 年 Top10 国家
    top10 = df[df['年份'] == 2024].nlargest(10, value_col)['国家'].tolist()
    country_data = {}
    for c in top10:
        sub = df[df['国家'] == c].sort_values('年份')
        year_map = dict(zip(sub['年份'], sub[value_col]))
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
        pie_2024.append({'name': r, 'value': round(float(sub[value_col].values[0]), 1)})

    # 各国首末年（1965→2024）变化（有头有尾才纳入）
    first_year, last_year = years[0], years[-1]
    country_changes = []
    for c in df['国家'].unique():
        sub = df[df['国家'] == c].sort_values('年份')
        year_map = dict(zip(sub['年份'], sub[value_col]))
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
            ym = dict(zip(csub['年份'], csub[value_col]))
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
    # 排序：① 增/减（2024 vs 1965 变化方向），② 2024 绝对值降序
    all_countries = df['国家'].unique().tolist()
    country_all_data = {}
    country_meta = {}   # {country: {continent, v_last, change}}
    for c in all_countries:
        sub = df[df['国家'] == c].sort_values('年份')
        ym = dict(zip(sub['年份'], sub[value_col]))
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

    # 排序：先增后减，各组内按 2024 数值降序
    def sort_key(c):
        m = country_meta[c]
        group = 0 if m['change'] >= 0 else 1   # 增加在前
        return (group, -m['v_last'])

    sorted_countries = sorted(all_countries, key=sort_key)

    return success({
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
    })


def read_production_region():
    return _read_region_csv("data/tables/production_region.csv", '产量(千桶/日)')


def read_consumption_region():
    return _read_region_csv("data/tables/consumption_region.csv", '消费量(千桶/日)')


def read_consumption_product():
    """分产品消费量（汽油/柴油/航空煤油/石脑油 + 总计），EI Regional Consumption。

    四个细分品种源表只有 1980 起，总计有 1965 起 —— 年轴统一用细分品种的跨度，
    否则 1965-1979 会留出一段只有总计的空白。
    """
    df = pd.read_csv("data/tables/consumption_product.csv")
    PRODUCTS = ["汽油", "柴油", "航空煤油", "石脑油"]

    sub = df[df['产品'].isin(PRODUCTS)]
    years = sorted(sub['年份'].unique().tolist())
    regions = sorted(df['地区'].unique().tolist())

    def series_for(region, product):
        s = df[(df['地区'] == region) & (df['产品'] == product)]
        ym = dict(zip(s['年份'], s['消费量(千桶/日)']))
        out = []
        for y in years:
            v = ym.get(y)
            out.append(round(float(v), 1) if v is not None and not (isinstance(v, float) and v != v) else None)
        return out

    region_products = {}
    for r in regions:
        region_products[r] = {p: series_for(r, p) for p in PRODUCTS}
        region_products[r]['总计'] = series_for(r, '总计')

    # 各品种占同区域石油总消费的比例（%），用于底部占比视图
    region_shares = {}
    for r in regions:
        total = region_products[r]['总计']
        region_shares[r] = {
            p: [None if (v is None or total[i] in (None, 0)) else round(v / total[i] * 100, 2)
                for i, v in enumerate(region_products[r][p])]
            for p in PRODUCTS
        }

    return success({
        "years": years,
        "products": PRODUCTS,
        "regions": regions,
        "region_products": region_products,
        "region_shares": region_shares
    })


def _read_two_col_txt(path):
    """读取 year<TAB>value 两列 txt（跳过表头），返回 {int(year): float(value)}。"""
    out = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f.readlines()[1:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            try:
                out[int(parts[0])] = float(parts[1])
            except (ValueError, TypeError):
                continue
    return out


def read_consumption_growth():
    """全球原油总消费量长期趋势 + 人口 / 电力发电量对比。

    - 原油: consumption_region.csv 各国按年求和 (千桶/日), 1965-2024
    - 人口: world_population.txt (亿), World Bank, 1960-2025
    - 电力: electricity_generation.txt (TWh), EI Total World, 1985-2024

    三条序列各自年份跨度不同，一并返回，回归线与指数化对比由前端计算。
    """
    df = pd.read_csv("data/tables/consumption_region.csv")
    oil_sum = df.groupby("年份")["消费量(千桶/日)"].sum().sort_index()
    oil_years = [int(y) for y in oil_sum.index.tolist()]
    oil_vals = [round(float(v), 1) for v in oil_sum.tolist()]

    pop = _read_two_col_txt("data/tables/world_population.txt")
    pop_years = sorted(pop.keys())
    pop_vals = [round(pop[y], 2) for y in pop_years]

    elec = _read_two_col_txt("data/tables/electricity_generation.txt")
    elec_years = sorted(elec.keys())
    elec_vals = [round(elec[y], 1) for y in elec_years]

    return success({
        "oil":         {"years": oil_years,  "values": oil_vals,  "unit": "千桶/日", "label": "原油总消费量"},
        "population":  {"years": pop_years,  "values": pop_vals,  "unit": "亿人",    "label": "世界人口"},
        "electricity": {"years": elec_years, "values": elec_vals, "unit": "TWh",     "label": "电力发电量"}
    })


@oil_bp.route("/production")
def api_prod():
    return jsonify(read_production())


@oil_bp.route("/price")
def api_price():
    return jsonify(read_price())


@oil_bp.route("/adj_price")
def api_adj_price():
    return jsonify(read_adj_price())


@oil_bp.route("/production_region")
def api_production_region():
    return jsonify(read_production_region())


@oil_bp.route("/consumption_region")
def api_consumption_region():
    return jsonify(read_consumption_region())


@oil_bp.route("/consumption_product")
def api_consumption_product():
    return jsonify(read_consumption_product())


@oil_bp.route("/consumption_growth")
def api_consumption_growth():
    return jsonify(read_consumption_growth())


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
    return success(_read_reserves_csv(
        "data/tables/petrochina_reserves.csv",
        oil_col="原油凝析油(百万桶)",
        price_col="中石油实现油价(美元/桶)"
    ))


def read_cnooc_reserves():
    return success(_read_reserves_csv(
        "data/tables/cnooc_reserves.csv",
        oil_col="石油液体(百万桶)",
        price_col="中海油实现油价(美元/桶)"
    ))


@oil_bp.route("/petrochina_reserves")
def api_petrochina_reserves():
    return jsonify(read_petrochina_reserves())


@oil_bp.route("/cnooc_reserves")
def api_cnooc_reserves():
    return jsonify(read_cnooc_reserves())


def _read_company_production_csv(path):
    """通用公司产量 CSV 读取：年份 + 原油/天然气/油气合计"""
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
            "oil":      _f("原油产量(百万桶)"),
            "gas":      _f("天然气产量(十亿立方英尺)"),
            "combined": _f("油气合计产量(百万桶油当量)"),
            "note":     str(row.get("备注", ""))
        })
    return records


@oil_bp.route("/petrochina_production")
def api_petrochina_production():
    return jsonify(success(
        _read_company_production_csv("data/tables/petrochina_production.csv")))


@oil_bp.route("/cnooc_production")
def api_cnooc_production():
    return jsonify(success(
        _read_company_production_csv("data/tables/cnooc_production.csv")))


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
    return success({"xAxis": years, "values": values})


def read_gold_oil():
    """1970 年起的黄金价 (USD/oz)、原油名义价 (USD/bbl) 与金油比 (每盎司黄金可换桶数)。
    只取两个序列都有数据的年份 (黄金 1970 起, 原油序列到 2024)。"""
    _, oil_usd = _read_oil_years_usd()
    gold = {}
    with open("data/tables/gold.price.txt", "r", encoding="utf-8") as f:
        for line in f.readlines()[1:]:
            line = line.strip()
            if not line:
                continue
            y, close = line.split("\t")
            gold[y] = float(close)

    years = sorted(y for y in oil_usd if y in gold and int(y) >= 1970)
    gold_vals, oil_vals, ratio_vals = [], [], []
    for y in years:
        g, o = gold[y], oil_usd[y]
        gold_vals.append(g)
        oil_vals.append(o)
        ratio_vals.append(round(g / o, 2) if o > 0 else None)

    return success({
        "xAxis": years,
        "gold": gold_vals,
        "oil": oil_vals,
        "ratio": ratio_vals
    })


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
    return success({"xAxis": years, "values": values})


@oil_bp.route("/gold_ratio")
def api_gold_ratio():
    return jsonify(read_gold_ratio())


@oil_bp.route("/gold_oil")
def api_gold_oil():
    return jsonify(read_gold_oil())


@oil_bp.route("/population")
def api_population():
    return jsonify(read_population())
