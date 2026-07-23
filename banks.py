import akshare as ak

# 获取A股实时行情
stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()

# 筛选名称包含“银行”的股票
bank_stocks = stock_zh_a_spot_em_df[stock_zh_a_spot_em_df['名称'].str.contains('银行')]

# 输出到 CSV 文件
bank_stocks.to_csv("银行股票.csv", index=False, encoding="utf-8-sig")  # utf-8-sig 可以避免 Excel 打开中文乱码

print("已保存到 银行股票.csv")


