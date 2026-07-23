import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Line
from pyecharts.commons.utils import JsCode

# 读取CSV文件
df = pd.read_csv('y.csv')

# 数据预处理
# 确保数值列没有异常值
df['POS(箱)'] = pd.to_numeric(df['POS(箱)'], errors='coerce')
df['GMV'] = pd.to_numeric(df['GMV'], errors='coerce')

# 按年月聚合数据，计算总销售额和总销量
monthly_data = df.groupby('年月').agg({
    'GMV': 'sum',
    'POS(箱)': 'sum'
}).reset_index()

# 将年月转换为字符串类型以便正确排序
monthly_data['年月'] = monthly_data['年月'].astype(str)
monthly_data = monthly_data.sort_values('年月')

# 计算同比增长率
monthly_data['GMV同比增长'] = monthly_data['GMV'].pct_change() * 100

# 创建折线图
line = (
    Line(init_opts=opts.InitOpts(width='1200px', height='600px'))
    .add_xaxis(monthly_data['年月'].tolist())
    .add_yaxis(
        "总销售额(GMV)",
        monthly_data['GMV'].round(2).tolist(),
        yaxis_index=0,
        label_opts=opts.LabelOpts(is_show=False),
        linestyle_opts=opts.LineStyleOpts(width=3),
        itemstyle_opts=opts.ItemStyleOpts(color="#5470C6")
    )
    .add_yaxis(
        "同比增长率(%)",
        monthly_data['GMV同比增长'].round(2).tolist(),
        yaxis_index=1,
        label_opts=opts.LabelOpts(is_show=False),
        linestyle_opts=opts.LineStyleOpts(width=3, type_="dashed"),
        itemstyle_opts=opts.ItemStyleOpts(color="#91CC75")
    )
    .extend_axis(
        yaxis=opts.AxisOpts(
            name="同比增长率(%)",
            type_="value",
            min_=min(monthly_data['GMV同比增长'].min() - 10, -50),
            max_=max(monthly_data['GMV同比增长'].max() + 10, 50),
            position="right",
            axisline_opts=opts.AxisLineOpts(
                linestyle_opts=opts.LineStyleOpts(color="#91CC75")
            ),
            axislabel_opts=opts.LabelOpts(formatter="{value}%"),
        )
    )
    .set_global_opts(
        title_opts=opts.TitleOpts(
            title="公司整体销售趋势分析",
            subtitle="销售额(GMV)及同比增长率变化"
        ),
        tooltip_opts=opts.TooltipOpts(
            trigger="axis",
            axis_pointer_type="cross",
            formatter=JsCode("""
                function(params) {
                    let result = params[0].name + '<br/>';
                    for (let i = 0; i < params.length; i++) {
                        if (params[i].seriesName === '总销售额(GMV)') {
                            result += params[i].seriesName + ': ' + params[i].value.toLocaleString() + '元<br/>';
                        } else {
                            result += params[i].seriesName + ': ' + params[i].value.toFixed(2) + '%<br/>';
                        }
                    }
                    return result;
                }
            """)
        ),
        xaxis_opts=opts.AxisOpts(
            type_="category",
            axislabel_opts=opts.LabelOpts(rotate=45)
        ),
        yaxis_opts=opts.AxisOpts(
            name="销售额(元)",
            type_="value",
            min_=0,
            axislabel_opts=opts.LabelOpts(
                formatter=JsCode("function(value){return value.toLocaleString();}")
            )
        ),
        datazoom_opts=opts.DataZoomOpts(
            is_show=True,
            type_="inside",
            range_start=0,
            range_end=100
        ),
        legend_opts=opts.LegendOpts(pos_top="10%", pos_left="center")
    )
)

# 添加趋势线注释
latest_growth = monthly_data['GMV同比增长'].iloc[-1]
if latest_growth > 0:
    trend = "增长"
    color = "green"
else:
    trend = "萎缩"
    color = "red"

line.set_global_opts(
    title_opts=opts.TitleOpts(
        title=f"公司整体销售趋势分析 - 当前趋势: {trend}",
        subtitle=f"最近月份同比增长率: {latest_growth:.2f}%",
        title_textstyle_opts=opts.TextStyleOpts(color=color, font_size=20)
    )
)

# 渲染图表到HTML文件
line.render("result.html")

# 输出分析结论
print("分析结果已保存到 result.html")
print(f"\n销售趋势分析结论:")
print(f"1. 数据时间范围: {monthly_data['年月'].min()} 至 {monthly_data['年月'].max()}")
print(f"2. 总销售额变化: {monthly_data['GMV'].iloc[0]:.2f}元 → {monthly_data['GMV'].iloc[-1]:.2f}元")
print(f"3. 最近月份同比增长率: {latest_growth:.2f}%")
print(f"4. 整体趋势: 公司销售正在{'增长' if latest_growth > 0 else '萎缩'}")
