import pandas as pd
import os, subprocess
import plotly.graph_objects as go

xlsx_path = "/home/gem/workspace/attachments/EI-Stats-Review-ALL-data.xlsx"
d = "/home/gem/workspace/.ark/output/Oil_Gold_Charts_20260715"
os.makedirs(d, exist_ok=True)

# --- Oil Prices ---
df_p = pd.read_excel(xlsx_path, sheet_name="Oil crude prices since 1861", header=None)
p = df_p.iloc[4:, :3].copy()
p.columns = ['Year', 'Nominal', 'Real_2024']
p = p[p['Year'].apply(lambda x: isinstance(x, (int, float)) and pd.notna(x))]
p['Year'] = p['Year'].astype(int)
p = p[(p['Year'] >= 1950) & (p['Year'] <= 2024)]

# --- Reserves ---
df_r = pd.read_excel(xlsx_path, sheet_name="Oil - Proved reserves history", header=None)
for i in range(len(df_r)):
    if str(df_r.iloc[i, 0]).strip().lower() == 'total world': break
ry = df_r.iloc[4, 1:42].tolist()
rv = df_r.iloc[i, 1:42].tolist()
res = [(int(y), float(v)) for y, v in zip(ry, rv) if pd.notna(y) and pd.notna(v)]
res_y = [x[0] for x in res];
res_v = [x[1] for x in res]

# --- Production ---
df_pd = pd.read_excel(xlsx_path, sheet_name="Oil Production - barrels", header=None)
for i in range(len(df_pd)):
    if 'total world' in str(df_pd.iloc[i, 0]).lower():
        py = df_pd.iloc[2, 1:61].tolist()
        pv = df_pd.iloc[i, 1:61].tolist()
        break
prod = [(int(y), float(v)) for y, v in zip(py, pv) if pd.notna(y) and pd.notna(v)]
prod_y = [x[0] for x in prod];
prod_v = [x[1] for x in prod]

# --- Gold ---
gv = [35] * 5 + [35] * 4 + [39, 41, 36, 41, 58, 97, 159, 161, 125, 148, 193, 307,
                            608, 460, 376, 423, 360, 318, 368, 446, 437, 381,
                            383, 362, 344, 360, 384, 384, 388, 331, 294, 279,
                            279, 271, 310, 364, 409, 445, 604, 697, 872, 973,
                            1225, 1569, 1670, 1411, 1266, 1161, 1249, 1258, 1269, 1392,
                            1770, 1800, 1801, 1943, 2388]
gy = list(range(1960, 2025))

p_nom = dict(zip(p['Year'], p['Nominal']))
p_real = dict(zip(p['Year'], p['Real_2024']))
prod_d = dict(zip(prod_y, prod_v))
res_d = dict(zip(res_y, res_v))
gold_d = dict(zip(gy, gv))

rows = []
for y in range(1960, 2025):
    rows.append({'Year': y, 'Oil_Nominal': p_nom.get(y), 'Oil_Real': p_real.get(y),
                 'Gold': gold_d.get(y), 'Production': prod_d.get(y), 'Reserves': res_d.get(y)})
df = pd.DataFrame(rows)

cols = ['Oil_Nominal', 'Oil_Real', 'Gold', 'Production', 'Reserves']
base = df[df['Year'] == 2000][cols].iloc[0]
for c in cols:
    df[f'{c}_Idx'] = df[c] / base[c] * 100

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df['Year'], y=df['Oil_Nominal_Idx'], mode='lines',
    name='Oil Price (nominal)',
    line=dict(color='#1f77b4', width=2),
    customdata=df[['Oil_Nominal']].values,
    hovertemplate='<b>%{fullData.name}</b><br>Year: %{x}<br>Index: %{y:.1f}<br>Actual: $%{customdata[0]:.2f}/bbl<extra></extra>'
))
fig.add_trace(go.Scatter(
    x=df['Year'], y=df['Oil_Real_Idx'], mode='lines',
    name='Oil Price (2024$ adj.)',
    line=dict(color='#ff7f0e', width=2),
    customdata=df[['Oil_Real']].values,
    hovertemplate='<b>%{fullData.name}</b><br>Year: %{x}<br>Index: %{y:.1f}<br>Actual: $%{customdata[0]:.2f}/bbl<extra></extra>'
))
fig.add_trace(go.Scatter(
    x=df['Year'], y=df['Gold_Idx'], mode='lines+markers',
    name='Gold Price',
    line=dict(color='#d62728', width=2.5), marker=dict(size=3),
    customdata=df[['Gold']].values,
    hovertemplate='<b>%{fullData.name}</b><br>Year: %{x}<br>Index: %{y:.1f}<br>Actual: $%{customdata[0]:,.0f}/oz<extra></extra>'
))
fig.add_trace(go.Scatter(
    x=df['Year'], y=df['Production_Idx'], mode='lines',
    name='Oil Production',
    line=dict(color='#2ca02c', width=2),
    customdata=df[['Production']].values,
    hovertemplate='<b>%{fullData.name}</b><br>Year: %{x}<br>Index: %{y:.1f}<br>Actual: %{customdata[0]:,.0f} bbl/d<extra></extra>'
))
fig.add_trace(go.Scatter(
    x=df['Year'], y=df['Reserves_Idx'], mode='lines+markers',
    name='Proved Reserves',
    line=dict(color='#9467bd', width=2.5, dash='dash'), marker=dict(size=4),
    customdata=df[['Reserves']].values,
    hovertemplate='<b>%{fullData.name}</b><br>Year: %{x}<br>Index: %{y:.1f}<br>Actual: %{customdata[0]:,.1f} billion bbl<extra></extra>'
))

fig.add_hline(y=100, line=dict(color='gray', width=1, dash='dot'), opacity=0.4,
              annotation_text='2000 baseline')

latest = df[df['Year'] == 2024].iloc[0]
annotations = [
    dict(x=2024, y=latest['Oil_Nominal_Idx'], text=f" {latest['Oil_Nominal']:.0f}$",
         xanchor='left', font=dict(size=10, color='#1f77b4'), showarrow=False),
    dict(x=2024, y=latest['Oil_Real_Idx'], text=f" {latest['Oil_Real']:.0f}$",
         xanchor='left', font=dict(size=10, color='#ff7f0e'), showarrow=False),
    dict(x=2024, y=latest['Gold_Idx'], text=f" ${latest['Gold']:,.0f}",
         xanchor='left', font=dict(size=10, color='#d62728'), showarrow=False),
    dict(x=2024, y=latest['Production_Idx'], text=f" {latest['Production']:,.0f}",
         xanchor='left', font=dict(size=10, color='#2ca02c'), showarrow=False),
    dict(x=2024, y=latest['Reserves_Idx'], text=f" {latest['Reserves']:.0f}B",
         xanchor='left', font=dict(size=10, color='#9467bd'), showarrow=False),
]

fig.update_layout(
    title=dict(text='Oil & Gold: 相对趋势对比 (2000年 = 100)', font=dict(size=20)),
    hovermode='x unified',
    hoverlabel=dict(namelength=-1, font=dict(size=12)),
    template='plotly_white',
    height=650, width=1300,
    dragmode='zoom',
    xaxis=dict(title='Year', range=[1958, 2035],
               rangeslider=dict(visible=True, thickness=0.08),
               rangeselector=dict(
                   buttons=[
                       dict(count=5, label='5Y', step='year', stepmode='todate'),
                       dict(count=10, label='10Y', step='year', stepmode='todate'),
                       dict(count=20, label='20Y', step='year', stepmode='todate'),
                       dict(step='all', label='All')],
                   x=0.5, xanchor='center', y=1.05)),
    yaxis=dict(title='Index (2000 = 100)', autorange=True,
               tickfont=dict(size=11), rangemode='nonnegative'),
    legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.95)',
                bordercolor='#ccc', borderwidth=1, font=dict(size=12),
                itemclick='toggle', itemdoubleclick='toggleothers'),
    margin=dict(l=80, r=40, t=80, b=80),
    updatemenus=[
        dict(
            type='buttons',
            showactive=False,
            x=1.0, y=1.0, xanchor='right',
            font=dict(size=11),
            buttons=[
                dict(label='Y轴自适应',
                     method='relayout',
                     args=[{'yaxis.autorange': True}]),
                dict(label='Y轴固定范围',
                     method='relayout',
                     args=[{'yaxis.autorange': False, 'yaxis.range': [0, 1200]}])
            ]
        )
    ],
    annotations=[
                    dict(text='💡 点击图例隐藏/显示曲线 | 拖拽缩放后 Y 轴自动适配当前范围 | 右上角可切换「Y轴自适应」模式',
                         xref='paper', yref='paper', x=0.01, y=-0.08,
                         showarrow=False, font=dict(size=12, color='#888'))
                ] + annotations
)

html_path = os.path.join(d, "oil_gold_indexed.html")
config = {'scrollZoom': True, 'displaylogo': False}
fig.write_html(html_path, config=config)
print(f"Saved: {html_path}")

r = subprocess.run(["dodo_cli", "bos", "upload", "--short-url", "--no-ath", html_path],
                   capture_output=True, text=True)
print(r.stdout.strip())
if r.stderr: print("ERR:", r.stderr.strip())
