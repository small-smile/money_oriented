import pandas as pd
import numpy as np
from pyecharts import options as opts
from pyecharts.charts import Line
from sklearn.linear_model import LinearRegression
from datetime import datetime

# 读取CSV文件
df = pd.read_csv('y.csv')

# 数据预处理
# 确保日期格式正确并排序
df['年月'] = df['年月'].astype(str)
df['日期'] = pd.to_datetime(df['年月'], format='%Y%m')
df = df.sort_values('日期')

# 按年月分组计算总销售额
sales_by_month = df.groupby('日期')['POS(箱)'].sum().reset_index()
sales_by_month['月份'] = sales_by_month['日期'].dt.strftime('%Y-%m')

# 准备线性回归数据
X = np.arange(len(sales_by_month)).reshape(-1, 1)
y = sales_by_month['POS(箱)'].values.reshape(-1, 1)

# 计算线性回归（斜率）
model = LinearRegression()
model.fit(X, y)
slope = model.coef_[0][0]
intercept = model.intercept_[0]

# 生成趋势线数据
trend_line = model.predict(X)

# 创建折线图
line_chart = (
    Line(init_opts=opts.InitOpts(width="1200px", height="600px"))
    .add_xaxis(sales_by_month['月份'].tolist())
    .add_yaxis(
        "销售数量(POS箱)",
        sales_by_month['POS(箱)'].round(2).tolist(),
        is_smooth=True,
        label_opts=opts.LabelOpts(is_show=False),
        linestyle_opts=opts.LineStyleOpts(width=3),
    )
    .add_yaxis(
        "趋势线",
        [round(val[0], 2) for val in trend_line],
        linestyle_opts=opts.LineStyleOpts(width=2, type_="dashed"),
        label_opts=opts.LabelOpts(is_show=False),
    )
    .set_global_opts(
        title_opts=opts.TitleOpts(
            title=f"销售曲线分析 (斜率: {slope:.4f})",
            subtitle="基于POS(箱)数据的销售趋势分析",
        ),
        tooltip_opts=opts.TooltipOpts(trigger="axis"),
        xaxis_opts=opts.AxisOpts(
            type_="category",
            name="月份",
            axislabel_opts=opts.LabelOpts(rotate=45),
        ),
        yaxis_opts=opts.AxisOpts(
            type_="value",
            name="销售数量(POS箱)",
            axistick_opts=opts.AxisTickOpts(is_show=True),
            splitline_opts=opts.SplitLineOpts(is_show=True),
        ),
        datazoom_opts=opts.DataZoomOpts(),
    )
)

# 添加斜率注释
line_chart.set_series_opts(
    markpoint_opts=opts.MarkPointOpts(
        data=[
            opts.MarkPointItem(type_="max", name="最大值"),
            opts.MarkPointItem(type_="min", name="最小值"),
        ]
    )
)

# 保存为HTML文件
line_chart.render("result.html")

# 打印斜率信息
print(f"销售曲线的斜率: {slope:.6f}")
if slope > 0:
    print("趋势分析: 销售呈上升趋势")
elif slope < 0:
    print("趋势分析: 销售呈下降趋势")
else:
    print("趋势分析: 销售保持平稳")

print("可视化图表已保存为 result.html")