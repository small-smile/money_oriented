import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

# ============================================
# 1. 读取 Excel（请修改为您的文件路径和字段名）
# ============================================
# df = pd.read_excel('your_file.xlsx')
# df['日期'] = pd.to_datetime(df['日期'])

# ============================================
# 2. 模拟数据（替换为实际数据后删除此段）
# ============================================
np.random.seed(42)
dates = pd.date_range(start='2023-01-01', periods=90, freq='D')

df = pd.DataFrame({
    '日期': dates,
    '油价_定值': np.cumsum(np.random.randn(90) * 0.5) + 80,  # 2024年定值美元
    '油价_当年': np.cumsum(np.random.randn(90) * 0.5) + 75,  # 当年美元
    '产量': np.cumsum(np.random.randn(90) * 0.1) + 12,  # 百万桶/日
})


# ============================================
# 3. 生成 K线 OHLC 数据（对每个指标各做一套）
# ============================================
def make_ohlc(df, price_col):
    """把单列价格转为年/月/周K线的OHLC"""
    ohlc = df.set_index('日期')[price_col].resample('W').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last'
    }).dropna().reset_index()
    return ohlc


# 油价（2024定值）
ohlc_ding = make_ohlc(df, '油价_定值')
# 油价（当年价格）
ohlc_nian = make_ohlc(df, '油价_当年')

# 产量（折线图，不是K线）
prod_weekly = df.set_index('日期')['产量'].resample('W').mean().reset_index()

# ============================================
# 4. 创建图表（4个Y轴）
# ============================================
fig = make_subplots(specs=[[{"secondary_y": True}]])

# --- 油价 K线1：2024定值（左Y轴1） ---
fig.add_trace(go.Candlestick(
    x=ohlc_ding['日期'],
    open=ohlc_ding['open'],
    high=ohlc_ding['high'],
    low=ohlc_ding['low'],
    close=ohlc_ding['close'],
    name='油价（2024定值）',
    increasing_line_color='#FF4444',
    decreasing_line_color='#00CC66',
    yaxis='y',
    hovertemplate='<b>%{x|%Y-%m-%d}</b><br>开: %{open:.2f}<br>高: %{high:.2f}<br>低: %{low:.2f}<br>收: %{close:.2f}<extra></extra>'
), secondary_y=False)

# --- 油价 K线2：当年价格（左Y轴2） ---
fig.add_trace(go.Candlestick(
    x=ohlc_nian['日期'],
    open=ohlc_nian['open'],
    high=ohlc_nian['high'],
    low=ohlc_nian['low'],
    close=ohlc_nian['close'],
    name='油价（当年价格）',
    increasing_line_color='#CC0000',
    decreasing_line_color='#00994D',
    yaxis='y2',
    hovertemplate='<b>%{x|%Y-%m-%d}</b><br>开: %{open:.2f}<br>高: %{high:.2f}<br>低: %{low:.2f}<br>收: %{close:.2f}<extra></extra>'
))

# --- 产量折线（右Y轴1） ---
fig.add_trace(go.Scatter(
    x=prod_weekly['日期'], y=prod_weekly['产量'],
    mode='lines', name='产量（百万桶/日）',
    line=dict(color='#4ECDC4', width=2),
    yaxis='y3',
    hovertemplate='%{x|%Y-%m-%d}<br>产量: %{y:.2f} 百万桶/日<extra></extra>'
))

# ============================================
# 5. 设置4个Y轴
# ============================================
fig.update_layout(
    title='石油数据综合走势图<br><sup>🖱️ 滚轮缩放 | ✋ 拖动平移 | 🔒 Y轴锁定 | ✅ Y轴自适应</sup>',
    hovermode='x unified',
    template='plotly_white',
    legend=dict(x=0.01, y=0.99),
    dragmode='pan',  # 🔑 拖动=平移

    xaxis=dict(
        title='日期',
        rangeslider=dict(visible=True),
        type='date',
        fixedrange=False
    ),

    # 左Y轴1：油价（2024定值）
    yaxis=dict(
        title='<span style="color:#FF4444">油价 2024定值（美元/桶）</span>',
        tickfont=dict(color='#FF4444'),
        side='left', position=0.00,
        autorange=True, constrain='domain', fixedrange=True
    ),
    # 左Y轴2：油价（当年价格）
    yaxis2=dict(
        title='<span style="color:#CC0000">油价 当年（美元/桶）</span>',
        tickfont=dict(color='#CC0000'),
        side='left', position=0.06,
        anchor='free', overlaying='y',
        autorange=True, constrain='domain', fixedrange=True
    ),
    # 右Y轴1：产量
    yaxis3=dict(
        title='<span style="color:#4ECDC4">产量（百万桶/日）</span>',
        tickfont=dict(color='#4ECDC4'),
        side='right', position=1.00,
        anchor='free', overlaying='y',
        autorange=True, constrain='domain', fixedrange=True
    )
)

fig.update_xaxes(
    rangeselector=dict(
        buttons=list([
            dict(count=7, label='1周', step='day', stepmode='backward'),
            dict(count=1, label='1月', step='month', stepmode='backward'),
            dict(count=3, label='3月', step='month', stepmode='backward'),
            dict(step='all', label='全部')
        ])
    )
)

fig.show(config={'scrollZoom': True, 'displayModeBar': False, 'displaylogo': False})