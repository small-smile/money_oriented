import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Kline
from pyecharts.globals import ThemeType

# ===================== 1. 读取数据 =====================
# 读取产量
df_prod = pd.read_csv(
    "data/tables/oil.production.txt",
    sep="\t",
    skiprows=1,
    names=["Year", "production"]
)
df_prod["Year"] = df_prod["Year"].astype(int)

# 读取价格
df_price = pd.read_csv(
    "data/tables/oil.price.txt",
    sep="\t",
    skiprows=1,
    names=["Year", "real_price", "price_2024"]
)
df_price["Year"] = df_price["Year"].astype(int)

# 合并并按年份升序
df = pd.merge(df_price, df_prod, on="Year", how="left")
df = df.sort_values("Year").reset_index(drop=True)

# ===================== 2. 构造第一组K线：历史真实价格 =====================
# close=当年，open=前一年close
df["close_r"] = df["real_price"]
df["open_r"] = df["close_r"].shift(1)
df["high_r"] = df[["open_r", "close_r"]].max(axis=1)
df["low_r"]  = df[["open_r", "close_r"]].min(axis=1)

# ===================== 3. 构造第二组K线：2024换算价格 =====================
df["close_24"] = df["price_2024"]
df["open_24"] = df["close_24"].shift(1)
df["high_24"] = df[["open_24", "close_24"]].max(axis=1)
df["low_24"]  = df[["open_24", "close_24"]].min(axis=1)

# 剔除首行无open数据
df = df.dropna(subset=["open_r", "open_24"]).reset_index(drop=True)

# x轴年份列表
x_axis = df["Year"].astype(str).tolist()

# Pyecharts Kline 数据格式：[[open, close, low, high], ...]
data_real = []    # 真实价格K线数据
data_2024 = []    # 2024换算价K线数据
for _, row in df.iterrows():
    data_real.append([row["open_r"], row["close_r"], row["low_r"], row["high_r"]])
    data_2024.append([row["open_24"], row["close_24"], row["low_24"], row["high_24"]])

# ===================== 4. 绘制双K线图表 =====================
kline_chart = (
    Kline(init_opts=opts.InitOpts(
        theme=ThemeType.MACARONS,
        width="1400px",
        height="700px"
    ))
    .add_xaxis(x_axis)
    # 第一条K线：历史真实价格
    .add_yaxis(
        "历史真实原油价格",
        data_real,
        itemstyle_opts=opts.ItemStyleOpts(
            color="#ef232a",     # 上涨红
            border_color="#ef232a",
            color0="#14b82a",    # 下跌绿
            border_color0="#14b82a"
        )
    )
    # 第二条K线：2024等价换算价格
    .add_yaxis(
        "2024年等价换算价格",
        data_2024,
        itemstyle_opts=opts.ItemStyleOpts(
            color="#ff7f0e",
            border_color="#ff7f0e",
            color0="#00868b",
            border_color0="#00868b"
        )
    )
    .set_global_opts(
        title_opts=opts.TitleOpts(title="原油年度双K线对比图", subtitle="Open=上一年价格 | Close=当年价格"),
        xaxis_opts=opts.AxisOpts(name="年份"),
        yaxis_opts=opts.AxisOpts(name="价格"),
        legend_opts=opts.LegendOpts(pos_left="center", pos_top="bottom"),
        tooltip_opts=opts.TooltipOpts(trigger="axis"),
        datazoom_opts=[
            opts.DataZoomOpts(type_="slider", orient="horizontal"),
            opts.DataZoomOpts(type_="inside")
        ]
    )
)

# 生成html文件并自动打开
kline_chart.render("oil_double_kline.html")
print("图表已生成：oil_double_kline.html")