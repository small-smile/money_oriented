import os

from backend import jsonstore  # JSON 原文在 MySQL json_file 表；仓库根目录下跑

BASE = "tables"

def load(code, sector):
    return jsonstore.read(os.path.join(BASE, f"{sector}_{code}_annual.json"))

def show(code, sector, name, fields):
    d = load(code, sector)
    ann = d.get("annual", {})
    print(f"\n=== {name} {code} ({sector}) top-keys: {list(d.keys())[:12]}")
    yrs = [str(y) for y in range(2015, 2026)]
    for y in yrs:
        r = ann.get(y)
        if not r:
            continue
        vals = {k: r.get(k) for k in fields if r.get(k) is not None}
        print(y, vals)

# cement: revenue / net profit / cement sales volume (demand proxy)
show("600585", "cement", "海螺水泥", ["operate_income", "netprofit", "ops_sales_cement_wt", "ops_sales_total_wt", "ops_unit_rev", "ops_unit_gross", "ops_gm_pct"])
show("002233", "cement", "塔牌集团", ["operate_income", "netprofit", "ops_sales_cement_wt", "ops_gm_pct"])

# developer: what fields exist?
d = load("600048", "developer")
ann = d.get("annual", {})
print("\n=== 保利发展 600048 (developer) top-keys:", list(d.keys())[:15])
last = ann.get("2024") or ann.get("2023") or {}
print("developer annual field keys (2024/2023):", sorted(last.keys()))
for y in [str(y) for y in range(2018, 2026)]:
    r = ann.get(y)
    if r:
        print(y, {k: r.get(k) for k in ["operate_income", "netprofit", "parent_netprofit"] if r.get(k) is not None})
