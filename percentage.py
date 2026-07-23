import plotly.graph_objects as go

year = [1960,1970,1980,1990,2000,2010,2020]

top3 = [28,34,39,43,49,54,59]
others = [72,66,61,57,51,46,41]

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=year,
    y=top3,
    stackgroup='one',
    name='Top 3',
    mode='lines'
))

fig.add_trace(go.Scatter(
    x=year,
    y=others,
    stackgroup='one',
    name='Others',
    mode='lines'
))

fig.update_layout(
    template="plotly_white",
    title="Share of Global Oil Production",
    yaxis=dict(
        title="Share (%)",
        range=[0,100]
    ),
    hovermode="x unified",
    width=1000,
    height=550
)

fig.show()