from backend import industry_db

# 八家水泥企业（地产的上游建材），数据由 data/extract/fetch_cement_financials.py 生成：
# 前五家 A 股上市（海螺 600585、华新 600801 为 A+H，按项目规则取 A 股年报口径），
# 后三家仅在港交所上市走港股 F10（无资产负债表明细，净现金/重资产度等无序列）。
# 注意 000877 天山股份是 03323 中国建材的并表子公司，两条线不是独立样本，不能相加。
CEMENT_PEERS = ["600585", "000877", "600801", "000401", "002233", "03323", "01313", "00743"]


def _cement_ops_manual():
    """经营口径手工层（逐份年报 PDF 语义读出的水泥熟料销量、分产品收入成本、年报直接披露的吨成本/吨售价，
    财务接口没有这些字段）：读 MySQL cement_operating 与 data_note，形状同 cement_ops_manual.json。"""
    return industry_db.cement_ops_manual()


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
