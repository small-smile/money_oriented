from pyecharts import options as opts
from pyecharts.charts import Candlestick
import os
import webbrowser

def read_oil_price(filepath: str) -> dict:
    """读取油价txt，跳过表头，返回 {年份:2024折算价格}"""
    price_dict = {}
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"文件不存在：{filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()[1:]  # 跳过表头第一行
        for line in lines:
            line = line.strip()
            if not line:
                continue
            year_str, _, price_2024 = line.split("\t")
            year = int(year_str)
            price_dict[year] = float(price_2024)
    return price_dict

def build_candlestick_data(price_dict: dict):
    """
    构造K线数据
    open = 上一年价格
    close = 当年价格
    high = max(open, close)
    low = min(open, close)
    返回：x轴年份列表, K线二维数组
    """
    sorted_years = sorted(price_dict.keys())
    x_data = []
    k_data = []

    for idx, year in enumerate(sorted_years):
        close = price_dict[year]
        if idx == 0:
            # 第一条无昨日数据，开盘=收盘
            open_p = close
        else:
            prev_year = sorted_years[idx - 1]
            open_p = price_dict[prev_year]

        high = max(open_p, close)
        low = min(open_p, close)

        x_data.append(str(year))
        k_data.append([open_p, close, low, high])
    return x_data, k_data

if __name__ == "__main__":
    # 文件路径
    price_path = "data/tables/oil.price.txt"
    # 读取数据
    price_data = read_oil_price(price_path)
    x_axis, candle_series = build_candlestick_data(price_data)

    # 初始化K线图
    candle_chart = (
        Candlestick(init_opts=opts.InitOpts(width="1400px", height="750px"))
        .add_xaxis(xaxis_data=x_axis)
        .add_yaxis(
            series_name="原油价格K线(open=上年价,close=当年折算2024价)",
            yaxis_data=candle_series,
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="原油历史价格K线图"),
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=45)),
            yaxis_opts=opts.AxisOpts(scale=True),  # Y轴自适应缩放
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            datazoom_opts=[opts.DataZoomOpts(type_="slider", orient="horizontal")],
        )
    )

    # 生成html文件
    out_html = "oil_candlestick.html"
    candle_chart.render(out_html)
    print(f"图表已生成：{os.path.abspath(out_html)}")
    # 自动用默认浏览器打开
    webbrowser.open(out_html)