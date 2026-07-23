import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Line, Kline
from pyecharts.commons.utils import JsCode
from pyecharts.globals import ThemeType

# 1. 读取产量文件
df_prod = pd.read_csv(
    "data/tables/oil.production.txt",
    sep="\t",
    skiprows=1,
    names=["year", "output"]
)
# 2. 读取油价文件
df_price = pd.read_csv(
    "data/tables/oil.price.txt",
    sep=r"\s+",
    skiprows=1,
    names=["year", "real_price", "price_2024"],
    encoding="utf-8"
)

# 合并数据
df = pd.merge( df_price, df_prod,on="year", how="left")
df = df.sort_values("year")

x_data = df["year"].tolist()
y_output = df["output"].tolist()
y_price = df["price_2024"].tolist()

# 构建左侧Y轴：产量折线图
line = (
    Line(init_opts=opts.InitOpts(width="1400px", height="700px", theme=ThemeType.MACARONS))
    .add_xaxis(x_data)
    .add_yaxis(
        series_name="石油产量",
        y_axis=y_output,
        yaxis_index=0,
        is_smooth=True,
    )
    # 开启底部滑块缩放+滚轮缩放+拖拽平移
    .add_js_funcs("""
        chart_1.setOption({
            dataZoom: [
                {type: 'inside'},
                {type: 'slider', bottom: 10}
            ]
        })
    """)
    .set_global_opts(
        title_opts=opts.TitleOpts(title="石油产量与油价K线对比"),
        tooltip_opts=opts.TooltipOpts(trigger="axis"),
        xaxis_opts=opts.AxisOpts(name="年份"),
        yaxis_opts=opts.AxisOpts(name="产量", position="left"),
        legend_opts=opts.LegendOpts(pos_left="center"),
    )
)

# 构建右侧Y轴：油价K线图（标准蜡烛K线）
# 构造K线需要 [open, close, low, high]
kline_data = []
for p in y_price:
    o = p * 0.95
    c = p
    l = p * 0.9
    h = p * 1.05
    kline_data.append([o, c, l, h])

k = (
    Kline()
    .add_xaxis(x_data)
    .add_yaxis(
        series_name="油价K线(2024折算)",
        y_axis=kline_data,
        yaxis_index=1,
    )
)

# 双图组合，共用X轴，双Y轴独立刻度
overlap_chart = line.overlap(k)
# 配置第二个Y轴（右侧）
overlap_chart.add_js_funcs(JsCode("""
chart_1.setOption({
  yAxis: [
    {axisLabel: {formatter: '{value}'}, name: '产量'},
    {axisLabel: {formatter: '{value} USD'}, name: '油价', position: 'right', splitLine: {show: false}}
  ]
})
"""))

# 生成html文件，双击打开
overlap_chart.render("oil_kline_chart.html")
print("图表已生成：oil_kline_chart.html")