"""
拉取黄金年度均价并保存到 data/tables/gold.price.txt
数据源：yfinance GC=F（黄金期货），1970 年起
运行：python fetch_gold.py
"""
import yfinance as yf
import pandas as pd

df = yf.download('GC=F', start='1970-01-01', end='2025-12-31', interval='1mo', auto_adjust=True, progress=False)

if df.empty:
    print("下载失败，可能被限流，稍后重试")
    exit(1)

df.index = pd.to_datetime(df.index)
df['year'] = df.index.year
annual = df.groupby('year')['Close'].mean().reset_index()
annual.columns = ['year', 'close']
annual['close'] = annual['close'].round(2)

annual.to_csv('data/tables/gold.price.txt', sep='\t', index=False)
print(f"保存完成，共 {len(annual)} 条，覆盖 {annual['year'].min()}–{annual['year'].max()}")
