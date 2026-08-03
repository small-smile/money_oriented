import requests
import pandas as pd
import time
import os

print(10)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
}

# USD 美元每盎司
url = "https://fsapi-china.gold.org/api/goldprice/v11/chart/price/usd/oz"
res = requests.get(url, headers=headers)
data = res.json()
print(data)
# 时间戳转日期，提取年份，按年取均价
rows = data["chartData"]["USD"]
records = []
for item in rows:
    date_str = time.strftime("%Y-%m-%d", time.localtime(item[0] / 1000))
    records.append({"date": date_str, "price": item[1]})

df = pd.DataFrame(records)
df["year"] = df["date"].str[:4].astype(int)
annual = df.groupby("year")["price"].mean().round(2).reset_index()
annual.columns = ["year", "close"]

print(annual)
out_path = os.path.join(os.path.dirname(__file__), "../../data/tables/gold.price.txt")
annual.to_csv(out_path, sep="\t", index=False)
print(f"保存完成，共 {len(annual)} 条，覆盖 {annual['year'].min()}–{annual['year'].max()}")
print(annual)
