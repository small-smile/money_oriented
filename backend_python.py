import numpy as np
import pandas as pd
from flask import Flask, jsonify, request, redirect, abort, send_from_directory
from flask_cors import CORS
import os
import json
import re

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

    return {
        "code": 200,
        "data": {
            'candleData': candleData,
            'xAxis': xAxis
        }
    }


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

    return {
        "code": 200,
        "data": {
            "years": years,
            "products": PRODUCTS,
            "regions": regions,
            "region_products": region_products,
            "region_shares": region_shares
        }
    }


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

    return {
        "code": 200,
        "data": {
            "oil":         {"years": oil_years,  "values": oil_vals,  "unit": "千桶/日", "label": "原油总消费量"},
            "population":  {"years": pop_years,  "values": pop_vals,  "unit": "亿人",    "label": "世界人口"},
            "electricity": {"years": elec_years, "values": elec_vals, "unit": "TWh",     "label": "电力发电量"}
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


@app.route("/api/consumption_product")
def api_consumption_product():
    return jsonify(read_consumption_product())


@app.route("/api/consumption_growth")
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


@app.route("/api/petrochina_production")
def api_petrochina_production():
    return jsonify({
        "code": 200,
        "data": _read_company_production_csv("data/tables/petrochina_production.csv")
    })


@app.route("/api/cnooc_production")
def api_cnooc_production():
    return jsonify({
        "code": 200,
        "data": _read_company_production_csv("data/tables/cnooc_production.csv")
    })


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

    return {
        "code": 200,
        "data": {
            "xAxis": years,
            "gold": gold_vals,
            "oil": oil_vals,
            "ratio": ratio_vals
        }
    }


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


@app.route("/api/gold_oil")
def api_gold_oil():
    return jsonify(read_gold_oil())


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


def read_company_charts(code):
    """公司详情页全部图表数据，按银行代码取 data/tables/company_charts_<code>.json。
    数据由 data/extract/ 提取管线从 charts.js 原值程序化抽取，未经手工重录。"""
    if not re.fullmatch(r"[0-9]{5,6}", code):
        return {"code": 400, "msg": f"非法银行代码 {code}", "data": {}}
    path = f"data/tables/company_charts_{code}.json"
    if not os.path.exists(path):
        return {"code": 404, "msg": f"银行 {code} 尚无 company_charts 数据文件", "data": {}}
    with open(path, "r", encoding="utf-8") as f:
        return {"code": 200, "data": json.load(f)}


@app.route("/api/company_charts")
def api_company_charts():
    """参数: code（银行 A 股 6 位代码或 H 股 5 位代码），默认渝农商行 601077"""
    return jsonify(read_company_charts(request.args.get("code", DEFAULT_BANK_CODE)))


def read_tsf():
    """社会融资规模（TSF）宏观数据，独立于任一银行 —— 直接沿用 601077 精编文件里
    已规整好的 tsf-stock 块（months/stock/yoy/flow_total/分项），供行业页 tsf.html 使用。"""
    path = f"data/tables/company_charts_{DEFAULT_BANK_CODE}.json"
    if not os.path.exists(path):
        return {"code": 404, "msg": "社融数据文件不存在", "data": {}}
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    tsf = d.get("tsf-stock")
    if not tsf:
        return {"code": 404, "msg": "社融数据缺失 tsf-stock 键", "data": {}}
    return {"code": 200, "data": tsf}


@app.route("/api/tsf")
def api_tsf():
    return jsonify(read_tsf())


# ── 银行详情页：同一份 HTML 按 bank code 动态下发 ─────────────────────────
# 原来 7 个页面是纯静态文件（file:// 直接打开），银行代码只有浏览器里的 JS 知道；
# 改由本路由渲染后：服务端校验 code、把 window.COMPANY_CODE 和可切换银行清单注入 <head>，
# 首屏就确定是哪家行，导航栏的银行下拉框也不用再在 bank-header.js 里手写名单
# （清单 = data/tables/company_charts_<code>.json 实际存在的那些，加行只需放数据文件）。
# 静态资源仍按原目录结构下发，所以页面里 ../../common/base.css 这类相对路径不用改。
DASHBOARD_DIR = os.path.join(os.path.dirname(__file__), "dashboard")
TABLES_DIR = os.path.join(os.path.dirname(__file__), "data", "tables")
BANK_PAGES = ("index.html", "asset.html", "debt.html", "risk.html",
              "intro.html", "balance-sheet.html", "shareholder.html")
DEFAULT_BANK_CODE = "601077"
# 601077 排最前：它是手工精编（42 个数据键），其余由 gen_company_charts.py 批量生成
# （15~16 个键），缺的图由 charts.js 的 __stub() 贴占位说明。名单外的代码只影响排序。
# 顺序按机构类型分组：国有大行→股份行→城商行→农商行→纯 H 股。list_banks() 只用这个顺序排序，
# bank-header.js 的分组面板（GROUPS）另按 tier 分组展示，两处顺序不必一致但代码集合要对齐。
BANK_ORDER = (
    DEFAULT_BANK_CODE,
    # 国有大行
    "601398", "601288", "601988", "601939", "601328", "601658",
    # 股份行
    "600036", "601166", "600000", "601998", "600016", "000001",
    "600015", "601818", "601916",
    # 城商行
    "601169", "601229", "600919", "002142", "601009", "601838",
    "600926", "601187", "002936", "002948", "601577", "002966",
    "601963", "601665", "601997", "600928", "001227",
    # 农商行（601077 已在最前）
    "601825", "601128", "002958", "600908", "002807", "601860",
    "002839", "601528", "603323",
    # 纯 H 股
    "01578", "01916", "06138",
)


# 上市日期：A+H 两地上市的分别给 A 股（上交所/深交所首日）与 H 股（港交所首日）；
# 仅 A 股的只有 "a"，纯 H 股（01578/01916/06138）只有 "h"。
# 与 bank-header.js 的 BANKS 兜底名单里的 aListDate/hListDate 保持一致（两处都要改）。
LISTING_DATES = {
    # 国有大行（均 A+H）
    "601398": {"a": "2006-10-27", "h": "2006-10-27"},
    "601288": {"a": "2010-07-15", "h": "2010-07-16"},
    "601988": {"a": "2006-07-05", "h": "2006-06-01"},
    "601939": {"a": "2007-09-25", "h": "2005-10-27"},
    "601328": {"a": "2007-05-15", "h": "2005-06-23"},
    "601658": {"a": "2019-12-10", "h": "2016-09-28"},
    # 股份行
    "600036": {"a": "2002-04-09", "h": "2006-09-22"},
    "601166": {"a": "2007-02-05"},
    "600000": {"a": "1999-11-10"},
    "601998": {"a": "2007-04-27", "h": "2007-04-27"},
    "600016": {"a": "2000-12-19", "h": "2009-11-26"},
    "000001": {"a": "1991-04-03"},
    "600015": {"a": "2003-09-12"},
    "601818": {"a": "2010-08-18", "h": "2013-12-20"},
    "601916": {"a": "2019-11-26", "h": "2016-03-30"},
    # 城商行
    "601169": {"a": "2007-09-19"},
    "601229": {"a": "2016-11-16"},
    "600919": {"a": "2016-08-02"},
    "002142": {"a": "2007-07-19"},
    "601009": {"a": "2007-07-19"},
    "601838": {"a": "2018-01-31"},
    "600926": {"a": "2016-10-27"},
    "601187": {"a": "2020-10-27"},
    "002936": {"a": "2018-09-19", "h": "2015-12-23"},
    "002948": {"a": "2019-01-16", "h": "2015-12-03"},
    "601577": {"a": "2018-09-26"},
    "002966": {"a": "2019-08-02"},
    "601963": {"a": "2021-02-05", "h": "2013-11-06"},
    "601665": {"a": "2021-06-18"},
    "601997": {"a": "2016-08-16"},
    "600928": {"a": "2019-03-01"},
    "001227": {"a": "2022-01-17"},
    # 农商行
    "601077": {"a": "2019-10-29", "h": "2010-12-16"},
    "601825": {"a": "2021-08-19"},
    "601128": {"a": "2016-09-30"},
    "002958": {"a": "2019-03-26"},
    "600908": {"a": "2016-09-23"},
    "002807": {"a": "2016-09-02"},
    "601860": {"a": "2019-01-03"},
    "002839": {"a": "2017-01-24"},
    "601528": {"a": "2021-06-25"},
    "603323": {"a": "2016-11-29"},
    # 纯 H 股（仅港交所）
    "01578": {"h": "2016-03-30"},
    "01916": {"h": "2018-06-26"},
    "06138": {"h": "2014-03-31"},
}


def list_banks():
    """可切换银行清单：扫 company_charts_<code>.json，行名取文件里的 _bank 元信息。"""
    found = {}
    for name in sorted(os.listdir(TABLES_DIR)):
        m = re.fullmatch(r"company_charts_([0-9]{5,6})\.json", name)
        if not m:
            continue
        try:
            with open(os.path.join(TABLES_DIR, name), "r", encoding="utf-8") as f:
                b = (json.load(f) or {}).get("_bank") or {}
        except (OSError, ValueError):
            continue          # 半截/损坏的数据文件不该让整页 500
        code = m.group(1)
        ld = LISTING_DATES.get(code, {})
        found[code] = {
            "code": code,
            "name": b.get("shortName") or code,
            "fullName": b.get("fullName") or "",
            "reportYear": b.get("reportYear") or "",
            "tier": b.get("tier") or "",
            "aListDate": ld.get("a", ""),
            "hListDate": ld.get("h", ""),
        }
    ordered = [found.pop(c) for c in BANK_ORDER if c in found]
    return ordered + [found[c] for c in sorted(found)]


def render_bank_page(page, code):
    """读取静态 HTML，在 </head> 前插入本页的银行代码与可切换清单。"""
    with open(os.path.join(DASHBOARD_DIR, "company", "bank", page), "r", encoding="utf-8") as f:
        html = f.read()
    inject = ("<script>/* 由 backend_python.py 动态注入 */\n"
              "window.COMPANY_CODE=%s;window.__BANKS=%s;</script>\n</head>"
              % (json.dumps(code), json.dumps(list_banks(), ensure_ascii=False)))
    return html.replace("</head>", inject, 1)


@app.route("/")
def home_page():
    return redirect("/dashboard/index.html")


@app.route("/dashboard/")
@app.route("/dashboard/<path:sub>")
def dashboard_page(sub="index.html"):
    """dashboard/ 下的看板：银行详情页动态渲染，其余（css/js/其它行业页面）原样下发。"""
    if sub.endswith("/"):
        sub += "index.html"
    parts = sub.split("/")
    if len(parts) == 3 and parts[0] == "company" and parts[1] == "bank" and parts[2] in BANK_PAGES:
        code = request.args.get("code") or DEFAULT_BANK_CODE
        if not re.fullmatch(r"[0-9]{5,6}", code):
            code = DEFAULT_BANK_CODE      # 非法代码退回默认行，不把任意字符串带进页面
        return render_bank_page(parts[2], code)
    return send_from_directory(DASHBOARD_DIR, sub)


@app.route("/bank/<code>/")
@app.route("/bank/<code>/<page>")
def bank_page(code, page="index.html"):
    """短地址 /bank/601288/risk.html：重定向到 /dashboard/... ?code=，
    保持页面 URL 深度不变，页内相对路径的 css/js 才不会 404。"""
    if page not in BANK_PAGES or not re.fullmatch(r"[0-9]{5,6}", code):
        abort(404)
    return redirect("/dashboard/company/bank/%s?code=%s" % (page, code))


@app.route("/api/banks")
def api_banks():
    """导航栏银行下拉框的数据源；有 company_charts 数据文件的行才列出"""
    return jsonify({"code": 200, "data": list_banks()})


def read_bank_npl_formation():
    """全部已有数据行的风控横向对比序列，一次返回，供行业页 npl-formation.html 使用。
    每家 company_charts_<code>.json 取三条可跨行横比的序列：
      · 不良生成率 formation —— scale-dep.formation（配 scale-dep.years，2018 起可比）
      · 净息差 nim / 净利差 nis —— nim-trend.nim / nim-trend.nis（配 nim-trend.years10）
    连同 _bank 元信息按 BANK_ORDER 排序（国有→股份→城商→农商→纯 H）返回。
    各行 years 取自同一提取管线本应一致，仍逐行随数据带出，前端按并集对齐、容忍缺口。
    只要三条序列里任一条有值即纳入（个别行可能只披露息差或只倒推出不良生成）。"""
    banks = []
    seen = set()

    def _has(v):
        return isinstance(v, list) and any(x is not None for x in v)

    def _push(code):
        if code in seen:
            return
        path = os.path.join(TABLES_DIR, f"company_charts_{code}.json")
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                d = json.load(f) or {}
        except (OSError, ValueError):
            return
        sd = d.get("scale-dep") or {}
        nt = d.get("nim-trend") or {}
        fm = sd.get("formation")
        nim = nt.get("nim")
        nis = nt.get("nis")
        if not (_has(fm) or _has(nim) or _has(nis)):
            return                    # 三条全无值的行不进对比图
        b = d.get("_bank") or {}
        seen.add(code)
        banks.append({
            "code": code,
            "name": b.get("shortName") or code,
            "tier": b.get("tier") or "",
            "years": sd.get("years") or [],
            "formation": fm if isinstance(fm, list) else [],
            "years10": nt.get("years10") or [],
            "nim": nim if isinstance(nim, list) else [],
            "nis": nis if isinstance(nis, list) else [],
        })

    for code in BANK_ORDER:
        _push(code)
    for name in sorted(os.listdir(TABLES_DIR)):     # BANK_ORDER 之外的行兜底
        m = re.fullmatch(r"company_charts_([0-9]{5,6})\.json", name)
        if m:
            _push(m.group(1))
    if not banks:
        return {"code": 404, "msg": "尚无 company_charts 数据文件", "data": []}
    return {"code": 200, "data": banks}


@app.route("/api/bank_npl_formation")
def api_bank_npl_formation():
    """全部上市银行历年不良生成率 + 净息差/净利差，一次返回，供跨行对比页使用"""
    return jsonify(read_bank_npl_formation())


# 六家上市险企，数据由 data/extract/fetch_insurer_financials.py 生成：前五家为 A+H 上市、取 A 股年报口径，
# 中国太平（00966）仅在港交所上市，走港股 F10（金额已按年末汇率折人民币）
INSURER_PEERS = ["601318", "601628", "601601", "601336", "601319", "00966"]


# 六家头部央企开发商，数据由 data/extract/fetch_developer_financials.py 生成：
# 前三家 A 股上市（取 A 股年报口径），后三家仅在港交所上市，走港股 F10；
# 港股 F10 金额是年报本位币原值不折算，中海（00688）为港元口径，页面需单独标注
DEVELOPER_PEERS = ["600048", "001979", "000069", "00688", "01109", "00817"]


# 八家水泥企业（地产的上游建材），数据由 data/extract/fetch_cement_financials.py 生成：
# 前五家 A 股上市（海螺 600585、华新 600801 为 A+H，按项目规则取 A 股年报口径），
# 后三家仅在港交所上市走港股 F10（无资产负债表明细，净现金/重资产度等无序列）。
# 注意 000877 天山股份是 03323 中国建材的并表子公司，两条线不是独立样本，不能相加。
CEMENT_PEERS = ["600585", "000877", "600801", "000401", "002233", "03323", "01313", "00743"]


def _cement_ops_manual():
    """经营口径手工层 data/tables/cement_ops_manual.json：逐份年报 PDF 语义读出的
    水泥熟料销量、分产品收入成本、年报直接披露的吨成本/吨售价。财务接口没有这些字段。"""
    path = os.path.join(os.path.dirname(__file__), "data", "tables", "cement_ops_manual.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _cement_unit(amount_mn, sales_wt):
    """百万元 ÷ 万吨 → 元/吨。分子分母任一缺失就返回 None，不做估算。"""
    if amount_mn is None or not sales_wt:
        return None
    return round(amount_mn * 100.0 / sales_wt, 2)


def _cement_ops_year(code, year, r):
    """把某年年报提取值按该公司口径规则归一成 ops_* 字段。分子分母必须同口径，
    各家的选择规则写在 cement_ops_manual.json 的 unit_rule 里，这里是它的实现：
    海螺 2018 年起用自产品行（剔贸易）、华新 2019 年起收入不含熟料故分母换成水泥销量、
    天山 2016 及以前收入含熟料而销量不含（不可直除，吨指标置 None）、
    冀东与塔牌收入是水泥单品故分母用水泥销量、三家港股用水泥熟料合计销量。"""
    y = int(year)
    rev, cost = r.get("rev_cement_mn"), r.get("cost_cement_mn")
    if code == "600585":
        if r.get("rev_self_mn") is not None:
            rev, cost, den = r["rev_self_mn"], r.get("cost_self_mn"), r.get("sales_self_wt")
        else:
            rev, cost, den = r.get("rev_total_mn"), r.get("cost_total_mn"), r.get("sales_total_wt")
    elif code == "600801":
        den = r.get("sales_total_wt") if y <= 2018 else r.get("sales_cement_wt")
    elif code == "000877":
        den = r.get("sales_total_wt") if y >= 2017 else None
    elif code in ("000401", "002233"):
        den = r.get("sales_cement_wt")
    else:
        den = r.get("sales_total_wt")

    unit_rev = _cement_unit(rev, den)
    unit_cost = _cement_unit(cost, den)
    if unit_cost is None:
        # 华润建材科技的分部只有营业额没有成本，退回年报「每吨成本结构图」披露的合计值
        unit_cost = r.get("unit_cost_disclosed") if code == "01313" else None
    unit_gross = None if (unit_rev is None or unit_cost is None) else round(unit_rev - unit_cost, 2)

    # 华润建材科技 2022 年及以前年报以港元呈列，2023 年起改人民币：两段分开成两组字段，
    # 不折算也不拼成一条序列（折算需汇率假设，且年报重列口径与年均汇率不同）
    sfx = "_hkd" if r.get("currency") == "HKD" else ""
    out = {
        "ops_sales_total_wt": r.get("sales_total_wt"),
        "ops_sales_cement_wt": r.get("sales_cement_wt"),
        "ops_sales_clinker_wt": r.get("sales_clinker_wt"),
        "ops_agg_sales_wt": r.get("agg_sales_wt"),
        "ops_concrete_sales_wm3": r.get("concrete_sales_wm3"),
        "ops_sales_base_wt": den,
        "ops_gm_pct": r.get("gm_self_pct") if code == "600585" and r.get("gm_self_pct") is not None else r.get("gm_cement_pct"),
        "ops_unit_cost_disclosed": r.get("unit_cost_disclosed"),
        "ops_unit_price_disclosed": r.get("unit_price_disclosed"),
        "ops_currency": r.get("currency", "CNY"),
        "ops_page": r.get("page"),
        "ops_note": r.get("note"),
    }
    out["ops_unit_rev" + sfx] = unit_rev
    out["ops_unit_cost" + sfx] = unit_cost
    out["ops_unit_gross" + sfx] = unit_gross
    return out


def _merge_cement_ops(code, payload):
    """把经营手工层并进 annual 的每一年（ops_* 前缀），并把该公司的口径说明挂到顶层。
    annual 里原有的接口字段不动，缺该年份记录就补一条只有 ops_* 的年份。"""
    ops = _cement_ops_manual()
    if not ops:
        return payload
    comp = ops.get("companies", {}).get(code)
    if not comp:
        return payload
    annual = payload.setdefault("annual", {})
    for year, r in comp.get("annual", {}).items():
        annual.setdefault(year, {}).update(_cement_ops_year(code, year, r))
    payload["ops_meta"] = {
        "source": ops.get("source"),
        "unit_note": ops.get("unit_note"),
        "caliber_note": ops.get("caliber_note"),
        "currency": comp.get("currency"),
        "years": comp.get("years"),
        "sales_key": comp.get("sales_key"),
        "rev_caliber": comp.get("rev_caliber"),
        "unit_rule": comp.get("unit_rule"),
        "breaks": comp.get("breaks"),
    }
    return payload


# ── 三大运营商（通信）────────────────────────────────────────────────────────

TELECOM_PEERS = ["600941", "601728", "600050"]


def _telecom_ops_manual():
    """经营口径手工层 data/tables/telecom_ops_manual.json：逐份年报原文读出的
    移动/5G/宽带用户数、ARPU、年报口径资本开支、云与产业数字化收入。财务接口没有这些字段。"""
    path = os.path.join(os.path.dirname(__file__), "data", "tables", "telecom_ops_manual.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _telecom_segment_manual():
    """收入构成层 data/tables/telecom_segment_manual.json：年报「营业收入和营业成本」附注里的
    收入分解表，由 data/extract/extract_telecom_segments.py 解析。三家科目体系不同，不可横比同名科目。"""
    path = os.path.join(TABLES_DIR, "telecom_segment_manual.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _telecom_segment_labels(comp):
    """canon 字段 → 年报中文科目名。items 与 canon 是同序生成的两份 dict，按位置对齐即可。
    年份从新到旧遍历，让当前科目体系（联通 2017 年起）排在旧科目（legacy_*）前面。"""
    labels, order = {}, []
    for year in sorted(comp.get("annual") or {}, reverse=True):
        rec = comp["annual"][year]
        for canon, label in zip(rec.get("canon") or {}, rec.get("items") or {}):
            if canon not in labels:
                labels[canon] = label
                order.append(canon)
    return labels, order


def _attach_telecom_segments(code, payload):
    """收入构成挂成顶层 segments 块，不摊进 annual：三家科目集不同、联通 2017 年前后换过一套，
    平铺进年份记录会得到一张到处是空洞的宽表，前端反而要再猜哪些字段属于哪家。"""
    seg = _telecom_segment_manual()
    if not seg:
        return payload
    comp = (seg.get("companies") or {}).get(code)
    if not comp:
        return payload
    labels, order = _telecom_segment_labels(comp)
    payload["segments"] = {
        "source": seg.get("source"),
        "unit_note": seg.get("unit_note"),
        "caliber_note": seg.get("caliber_note"),
        "unit": "亿元",
        "labels": labels,
        "order": order,
        "annual": {y: r.get("canon") or {} for y, r in (comp.get("annual") or {}).items()},
    }
    return payload


def _merge_telecom(code, payload):
    """通信行业的手工层合并入口：经营口径（ops_）+ 年报收入构成（segments）。"""
    return _attach_telecom_segments(code, _merge_telecom_ops(code, payload))


def _merge_telecom_ops(code, payload):
    """把经营手工层并进 annual 的每一年（ops_ 前缀已在手工表里带好），
    并把口径说明挂到顶层 ops_meta。annual 里原有的接口字段不动，
    缺该年份记录（如手工层覆盖到上市前）就补一条只有 ops_* 的年份。"""
    ops = _telecom_ops_manual()
    if not ops:
        return payload
    comp = (ops.get("companies") or {}).get(code)
    if not comp:
        return payload
    annual = payload.setdefault("annual", {})
    for year, rec in (comp.get("annual") or {}).items():
        row = annual.setdefault(year, {})
        for k, v in rec.items():
            row["ops_" + k if not k.startswith("ops_") else k] = v
    payload["ops_meta"] = {
        "source": ops.get("source"),
        "unit_note": ops.get("unit_note"),
        "caliber_note": ops.get("caliber_note"),
        "years": comp.get("years"),
        "report_source": comp.get("report_source"),
        "breaks": comp.get("breaks"),
    }
    return payload


# ── 行业年度数据接口：保险/地产/水泥/通信共用一套读表逻辑 ─────────────────────
# 四个行业的成品表都是 data/tables/<行业>_<code>_annual.json，读法只差四件事：
# 成员清单、代码位数、同业对比要下发哪些字段（顺序即 JSON 里的字段顺序）、
# 有没有经营口径手工层要合并。差异写在下面的 INDUSTRIES 里，逻辑只有一份。
INDUSTRIES = {
    "insurer": {
        "label": "保险公司", "peers_label": "险企", "peers": INSURER_PEERS,
        "code_re": r"[0-9]{5,6}", "script": "fetch_insurer_financials.py", "merge": None,
        "fields": ["name", "source", "unit_note", "caliber_note", "annual"],
    },
    "developer": {
        "label": "开发商", "peers_label": "开发商", "peers": DEVELOPER_PEERS,
        "code_re": r"[0-9]{5,6}", "script": "fetch_developer_financials.py", "merge": None,
        "fields": ["name", "secucode", "group", "currency", "source", "unit_note",
                   "caliber_note", "annual", "dividend_per10"],
    },
    "cement": {
        "label": "水泥企业", "peers_label": "水泥企业", "peers": CEMENT_PEERS,
        "code_re": r"[0-9]{5,6}", "script": "fetch_cement_financials.py",
        "merge": _merge_cement_ops,
        "fields": ["name", "secucode", "group", "currency", "source", "unit_note",
                   "caliber_note", "ops_meta", "annual", "dividend_per10"],
    },
    "telecom": {
        "label": "运营商", "peers_label": "运营商", "peers": TELECOM_PEERS,
        "code_re": r"[0-9]{6}", "script": "fetch_telecom_financials.py",
        "merge": _merge_telecom,
        "fields": ["name", "secucode", "group", "h_code", "h_same_entity", "a_report_from",
                   "currency", "source", "unit_note", "caliber_note", "ops_meta", "segments",
                   "annual", "dividend_per10"],
    },
}

# 这两个字段缺失时给空 dict（前端直接 for-in 遍历），其余缺失给 None
_PEERS_DICT_FIELDS = ("annual", "dividend_per10")


def _read_industry_table(industry, code):
    """读 data/tables/<industry>_<code>_annual.json 并按行业规则合并手工层；文件不存在返回 None。"""
    spec = INDUSTRIES[industry]
    path = os.path.join(TABLES_DIR, f"{industry}_{code}_annual.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    return spec["merge"](code, d) if spec["merge"] else d


def read_industry_annual(industry, code):
    """单家公司历年数据（含该行业的经营口径手工层，如果有）。"""
    spec = INDUSTRIES[industry]
    if not re.fullmatch(spec["code_re"], code):
        return {"code": 400, "msg": f"非法{spec['label']}代码 {code}", "data": {}}
    d = _read_industry_table(industry, code)
    if d is None:
        return {"code": 404, "msg": f"{spec['label']} {code} 尚无年度数据文件", "data": {}}
    return {"code": 200, "data": d}


def read_industry_peers(industry):
    """同业对比用：code → 只带 spec['fields'] 声明的字段；缺数据文件的公司跳过。"""
    spec = INDUSTRIES[industry]
    peers = {}
    for code in spec["peers"]:
        d = _read_industry_table(industry, code)
        if d is None:
            continue
        peers[code] = {k: d.get(k, {} if k in _PEERS_DICT_FIELDS else None) for k in spec["fields"]}
    if not peers:
        return {"code": 404,
                "msg": f"尚无{spec['peers_label']}年度数据文件，请先运行 data/extract/{spec['script']}",
                "data": {}}
    return {"code": 200, "data": peers}


# ── 股权结构：银行/险企/开发商/水泥/运营商共用一套 ─────────────────────────────
# 五个板块的 <板块>_<code>_annual.json 里 holders（接口前十名股东快照）字段结构完全相同，
# 所以股权结构不按板块各写一页，统一由 dashboard/company/shareholder.html 一页读这份 payload，
# 靠 ?industry=&code= 切换。银行表另有 holder_num（逐期股东户数）与 holder_concentration
# （集中度序列）两层，有就下发、页面多画两张图，其余板块自然缺省。
HOLDER_INDUSTRIES = {
    "bank": {"label": "银行", "codes": list(BANK_ORDER)},
    "insurer": {"label": "险企", "codes": INSURER_PEERS},
    "developer": {"label": "开发商", "codes": DEVELOPER_PEERS},
    "cement": {"label": "水泥企业", "codes": CEMENT_PEERS},
    "telecom": {"label": "运营商", "codes": TELECOM_PEERS},
    # 下面两个板块没有 <板块>_<code>_annual.json，股东块整份来自手工层（年报／20-F 原文抽取）
    "tech": {"label": "科技（百度）", "codes": ["09888"]},
    "food": {"label": "食品", "codes": ["605338"]},
}

# 一致行动人（派系）与手工股东块：holders_manual.json 一个文件按 "<板块>:<代码>" 索引。
# 两种用法都在这里：① 只补 factions（telecom 这类 annual 表已有接口股东快照的板块）；
# ② 连 holders 一起给（tech/food 这类没有 annual 表的公司，股东块直接抄年报／20-F 原文）。
HOLDERS_MANUAL_FILE = os.path.join(TABLES_DIR, "holders_manual.json")


def _holders_manual():
    if not os.path.exists(HOLDERS_MANUAL_FILE):
        return {}
    with open(HOLDERS_MANUAL_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _company_charts_holders(code):
    """company_charts_<code>.json 里的 holders 块（年报口径：holders / holderData / factions）。"""
    path = os.path.join(TABLES_DIR, f"company_charts_{code}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return (json.load(f).get("holders")) or None


def _bank_factions(code):
    """银行的一致行动人早就画在年报口径股东页里，派系表就存在 company_charts_<code>.json。
    那份 names 是年报「前十名股东」的长名，与接口快照的名字大体同源、但不保证全部对得上；
    对不上的股东在前端各自成组（normalize 容错），不影响其余派系。"""
    blk = _company_charts_holders(code)
    return (blk or {}).get("factions") or None


def _holder_table(industry, code):
    """只读 annual 表里股权结构要用的那几块，不做手工层合并（股东数据与经营口径无关）。"""
    path = os.path.join(TABLES_DIR, f"{industry}_{code}_annual.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _norm_holder_name(s):
    """比对股东名用的归一化：全角括号/破折号折半角、去空白、砍掉通用公司后缀。
    年报原文与接口名册在这三处系统性不同（年报写「太平人寿保险有限公司－传统－…－022L－CT001 沪」，
    接口写「太平人寿保险有限公司-传统-…-022L-CT001沪」），不折一下没有一个名字能对上。
    银行那 45 份派系表里另有 5 家用的是年报页面上的简称（「渝富资本」「大家人寿-万能」），
    那类差异归一化救不回来，只能靠唯一前缀匹配或干脆不归组。"""
    s = (s or "")
    for a, b in (("（", "("), ("）", ")"), ("－", "-"), ("—", "-"), ("‐", "-"), ("–", "-")):
        s = s.replace(a, b)
    s = re.sub(r"\s+", "", s)
    for tail in ("股份有限公司", "有限责任公司", "有限公司", "公司"):
        if s.endswith(tail) and len(s) > len(tail) + 1:
            return s[: -len(tail)]
    return s


def _resolve_factions(holders, factions):
    """把派系表里的股东名对到名册里的真实名字上；对不上的成员直接丢掉，整组空了就丢整组。
    只认两种命中：归一化后完全相同，或名册里唯一一个以它开头的名字（唯一才算，多个视为对不上）。
    宁可少归一个成员（那家股东在前端自成一组），也不猜——猜错就是把股份记到别人名下。"""
    if not factions or not holders:
        return None
    exact, out = {}, []
    for h in holders:
        exact.setdefault(_norm_holder_name(h.get("name")), h.get("name"))
    for f in factions:
        hit = []
        for n in f.get("names") or []:
            key = _norm_holder_name(n)
            if key in exact:
                hit.append(exact[key])
                continue
            cand = [v for k, v in exact.items() if k.startswith(key)]
            if len(cand) == 1:
                hit.append(cand[0])
        if hit:
            g = dict(f)
            g["names"] = hit
            out.append(g)
    return out or None


def _ring_block_from_charts(code):
    """年报口径的环形图数据块 —— 取 company_charts_<code>.json 的 holders 块。
    bank/shareholder.html（各行业的标准模板）画的就是这一份：holderData 是图上的名字 +
    占总股本比例、已含「其他流通股东」那一块，factions 引用的正是这套名字；
    另一份 holders 带类别与报告期内增减（文字，如「+79.14 万股」「不变」）。
    两份名字 44 家银行完全一致，个别行（渝农商行）图上用简称、表里用另一套简称，
    这时按比例值唯一对上 —— 对不上就只是少两列，不猜。"""
    blk = _company_charts_holders(code)
    if not blk or not blk.get("holderData"):
        return None
    by_name, by_pct = {}, {}
    for h in blk.get("holders") or []:
        by_name[h.get("name")] = h
        by_pct.setdefault(round(float(h.get("pct") or 0), 2), []).append(h)
    out = []
    for x in blk["holderData"]:
        m = by_name.get(x.get("name"))
        if m is None:
            cand = by_pct.get(round(float(x.get("value") or 0), 2)) or []
            m = cand[0] if len(cand) == 1 else None
        out.append({"name": x.get("name"), "value": x.get("value"),
                    "type": (m or {}).get("type") or "",
                    # 年报口径这份增减是文字（「+79.14 万股」），不是股数，原样传给前端
                    "chgText": (m or {}).get("chg") or ""})
    return {"caliber": "占总股本", "holderData": out, "factions": blk.get("factions") or []}


def read_holders(industry, code=None):
    """某板块的成员名单 + 指定公司的股东快照。code 省略时取第一家有股东数据的公司。
    纯 H 股公司（如中国海外发展 00688）接口不返回前十名股东，名单里保留但标 has_holders=false，
    页面把它画成不可点，避免看着像取数遗漏。"""
    spec = HOLDER_INDUSTRIES.get(industry)
    if not spec:
        return {"code": 400, "msg": f"未知板块 {industry}；已支持 {list(HOLDER_INDUSTRIES)}", "data": {}}
    manual = _holders_manual()
    roster, tables = [], {}
    for c in spec["codes"]:
        d = _holder_table(industry, c)
        man = manual.get(f"{industry}:{c}") or {}
        if d is None:
            # 没有 annual 表时，手工层自带 holders 的公司照样进名单（tech/food）
            if not man.get("holders"):
                continue
            d = {}
        rec = dict(d)
        for k in ("name", "secucode", "holders_end_date", "holders", "holder_num", "source", "ring",
                  # 下面三层是照 bank/shareholder.html 那套模板补的历史序列（手工层才有）
                  "holder_concentration", "share_capital", "dividend_per10",
                  # 股本序列中间跨了口径断点（百度 1 拆 80）时，图上要打一条界线
                  "share_capital_break"):
            if man.get(k):
                rec[k] = man[k]
        rec["factions"] = man.get("factions") or (_bank_factions(c) if industry == "bank" else None)
        rec["factions_source"] = man.get("factions_source") or (
            f"银行年报口径股东页的一致行动人表（data/tables/company_charts_{c}.json）"
            if rec["factions"] and industry == "bank" else None)
        rec["caliber_note"] = man.get("caliber_note")
        rec["residual_label"] = man.get("residual_label")
        rec["history_source"] = man.get("history_source")
        # 名册是接口快照还是年报原文，页面要照实说（手工层给了名册的公司在这里写明）
        rec["holders_caliber"] = man.get("holders_caliber")
        rec["history_gaps"] = man.get("history_gaps")
        rec["dividend_unit"] = man.get("dividend_unit")
        tables[c] = rec
        roster.append({"code": c, "name": rec.get("name") or c,
                       "tag": rec.get("tier") or rec.get("group") or man.get("tag") or "",
                       "has_holders": bool(rec.get("holders"))})
    if not roster:
        return {"code": 404, "msg": f"尚无{spec['label']}数据文件", "data": {}}
    if not code:
        code = next((r["code"] for r in roster if r["has_holders"]), roster[0]["code"])
    if code not in tables:
        return {"code": 404, "msg": f"{spec['label']} {code} 尚无年度数据文件", "data": {}}
    d = tables[code]
    return {"code": 200, "data": {
        "industry": industry,
        "label": spec["label"],
        "roster": roster,
        "company": {
            "code": code,
            "name": d.get("name") or code,
            "secucode": d.get("secucode"),
            "tag": d.get("tier") or d.get("group") or next(
                (r["tag"] for r in roster if r["code"] == code), ""),
            "source": d.get("source"),
            "holders_end_date": d.get("holders_end_date"),
            "holders": d.get("holders") or [],
            "holder_num": d.get("holder_num") or None,
            "holder_concentration": d.get("holder_concentration") or None,
            # 历年总股本 [[年, 股数, 变动原因]] 与历年每 10 股分红 [[年, 元]]：
            # bank/shareholder.html 那套模板有这两张图，其余板块的数据在手工层补齐后自然也画得出来
            "share_capital": d.get("share_capital") or None,
            "dividend_per10": d.get("dividend_per10") or None,
            # 股本序列的口径断点 {at, text}：拆股／并股前后基数不可直接比较，图上画界线
            "share_capital_break": d.get("share_capital_break") or None,
            "history_source": d.get("history_source"),
            "holders_caliber": d.get("holders_caliber") or "接口口径的前十名股东快照",
            # 逐年抽取时记下的披露缺口，页面「口径与接口限制」原样列出
            "history_gaps": d.get("history_gaps") or None,
            # 分红图的单位：中国移动的股息以港元宣派，年报不给人民币每股金额，就照港元画
            "dividend_unit": d.get("dividend_unit") or "元",
            # 一致行动人：有派系表才画双层环，没有就只有单层（内外圈同一份数据没意义）
            "factions": _resolve_factions(d.get("holders") or [], d.get("factions")),
            # 环形图的标准数据块（bank/shareholder.html 那套年报口径数据）：银行取 company_charts，
            # 手工层给了 ring 的公司取手工层，都没有时前端拿接口快照 + 分组现拼一份
            "ring": d.get("ring") or (_ring_block_from_charts(code) if industry == "bank" else None),
            "factions_source": d.get("factions_source"),
            # 手工层公司（百度按 20-F beneficial ownership、巴比按年报名册）口径与接口快照不同，
            # 页面把这句原样印出来，不让两套口径混着读
            "caliber_note": d.get("caliber_note"),
            # 环形图里「名册外那一块」的叫法：前十名口径叫「前十名之外」，20-F 口径不是名册前十名
            "residual_label": d.get("residual_label") or "其他股东（前十名之外）",
            # 银行另有一套年报口径的股东页（含一致行动人、按 A 股基数重算），在这里给出入口
            "detail_page": f"/bank/{code}/shareholder.html" if industry == "bank" else None,
        },
    }}


@app.route("/api/insurer_annual")
def api_insurer_annual():
    """参数: code（险企 A 股 6 位代码），默认中国平安 601318"""
    return jsonify(read_industry_annual("insurer", request.args.get("code", "601318")))


@app.route("/api/insurer_peers")
def api_insurer_peers():
    """六家上市险企同业对比数据，一次返回"""
    return jsonify(read_industry_peers("insurer"))


@app.route("/api/developer_annual")
def api_developer_annual():
    """参数: code（开发商 A 股 6 位或 H 股 5 位代码），默认保利发展 600048"""
    return jsonify(read_industry_annual("developer", request.args.get("code", "600048")))


@app.route("/api/developer_peers")
def api_developer_peers():
    """六家头部央企开发商同业对比数据，一次返回"""
    return jsonify(read_industry_peers("developer"))


@app.route("/api/cement_annual")
def api_cement_annual():
    """参数: code（A 股 6 位或 H 股 5 位代码），默认海螺水泥 600585"""
    return jsonify(read_industry_annual("cement", request.args.get("code", "600585")))


@app.route("/api/cement_peers")
def api_cement_peers():
    """八家水泥企业同业对比数据，一次返回"""
    return jsonify(read_industry_peers("cement"))


@app.route("/api/telecom_annual")
def api_telecom_annual():
    """参数: code（A 股 6 位代码），默认中国移动 600941"""
    return jsonify(read_industry_annual("telecom", request.args.get("code", "600941")))


@app.route("/api/telecom_peers")
def api_telecom_peers():
    """三大运营商同业对比数据，一次返回"""
    return jsonify(read_industry_peers("telecom"))


@app.route("/api/holders")
def api_holders():
    """参数: industry（bank/insurer/developer/cement/telecom，默认 bank）、code（省略取首家）
    股权结构页共用接口：返回板块成员名单 + 该公司的前十名股东（银行另带股东户数与集中度）"""
    return jsonify(read_holders(request.args.get("industry", "bank"),
                                request.args.get("code")))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
