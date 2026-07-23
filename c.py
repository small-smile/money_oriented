import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Line

# 读取 CSV 文件
df = pd.read_csv('y.csv')

# 选择需要分析的数据列，例如 '年月' 和 'GMV'
df['年月'] = pd.to_datetime(df['年月'], format='%Y%m')
df = df.sort_values(by='年月')

# 计算 GMV 的斜率
df['GMV 斜率'] = df['GMV'].diff()

# 创建 Line 图表
line = Line()
line.add_xaxis(df['年月'].dt.strftime('%Y-%m').tolist())
line.add_yaxis("GMV", df['GMV'].tolist(), is_smooth=True)
line.add_yaxis("GMV 斜率", df['GMV 斜率'].tolist(), is_smooth=True)

# 设置全局配置项
line.set_global_opts(
    title_opts=opts.TitleOpts(title="销售曲线及斜率分析"),
    xaxis_opts=opts.AxisOpts(name="年月"),
    yaxis_opts=opts.AxisOpts(name="GMV")
)

# 保存为 HTML 文件
line.render("result.html")

print("图表已生成并保存为 result.html")