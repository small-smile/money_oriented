<template>
  <div class="roa-page">
    <section class="chart-card">
      <div class="chart-head">
        <h2 class="chart-title">中海油（0883.HK）油价 vs 单期 ROA（年化）<span class="sub">布伦特期内均价 × 单期总资产净利率（非累计，年化）· 2001H1–2026Q1</span></h2>
      </div>
      <EChart :option="roaOption" height="70vh" />
    </section>
    <section class="chart-card">
      <div class="chart-head">
        <h2 class="chart-title">中海油（0883.HK）油价 vs 单期 ROE（年化）<span class="sub">布伦特期内均价 × 单期净资产收益率（非累计，年化）· 2001H1–2026Q1</span></h2>
      </div>
      <EChart :option="roeOption" height="70vh" />
    </section>
    <section id="annotations-section">
      <h2>标注事件对照表</h2>
      <table id="annotation-table">
        <thead>
        <tr>
          <th style="width: 16%">时间</th>
          <th style="width: 20%">事件</th>
          <th>说明</th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="(e, i) in EVENTS" :key="i">
          <td class="time">{{ e.time }}</td>
          <td class="event" :style="{ borderLeftColor: e.color, color: e.color }">{{ e.name }}</td>
          <td>{{ e.desc }}</td>
        </tr>
        </tbody>
      </table>
    </section>
  </div>
</template>

<script setup>
import EChart from '../../components/EChart.vue'

// 逐字搬自 dashboard/subject/oil/cnooc_roa_oil.html：DATA/EVENTS/option 与渲染逻辑原样保留，
// 数据为源页内联示意数据（非 /api），数值一律不改；两张图改用 EChart 组件承载（resize/dispose 内置）。
/* 数据口径说明：
 *  p       报告期。2022 前中海油(0883.HK)只披露半年报 → 半年为一期(H1/H2)；
 *          2022 起(A股 600938 上市后)按季度披露 → 季度为一期(Q1..Q4)。
 *  roa     单期 ROA「年化」：单期归母净利 ÷ 期末总资产 × 期数(半年×2 / 季度×4) ×100%
 *  roe     单期 ROE「年化」：单期归母净利 ÷ 期末归母股东权益 × 期数 ×100%
 *  np 单期归母净利(亿元, 人民币)；ta 期末总资产；eq 期末归母股东权益(亿元)
 *  oil     布伦特原油期内均价：该期各月 FRED MCOILBRENTEU 月均价的算术平均(美元/桶)
 *  pt      'H' 半年期 / 'Q' 季度期
 * 单期净利由累计口径在同一财年内逐期相减得到；累计净利/总资产/权益源自东方财富港股数据接口
 * (00883.HK 资产负债表, 单位亿元 RMB)。eq 为期末时点值，直接取用不作差分。
 * 注：2006H1 该接口无中报资产负债表 → eq/roe 缺失(线上连线跨过)。
 * 说明：非累计口径；因半年/季度期长不同，跨 2022 直接比较请用「年化」。
 */
const DATA = [
/*__DATA__*/
{"p":"2001H1","roa":20.67,"roa_raw":10.33,"np":46.2,"ta":446.9,"eq":308.4,"roe":29.96,"roe_raw":14.98,"oil":26.57,"pt":"H"},
{"p":"2001H2","roa":15.07,"roa_raw":7.54,"np":33.4,"ta":443.2,"eq":333.1,"roe":20.05,"roe_raw":10.03,"oil":22.33,"pt":"H"},
{"p":"2002H1","roa":13.15,"roa_raw":6.58,"np":36.2,"ta":550.2,"eq":359.2,"roe":20.16,"roe_raw":10.08,"oil":23.09,"pt":"H"},
{"p":"2002H2","roa":18.38,"roa_raw":9.19,"np":56.1,"ta":611.0,"eq":405.7,"roe":27.66,"roe_raw":13.83,"oil":26.83,"pt":"H"},
{"p":"2003H1","roa":18.7,"roa_raw":9.35,"np":63.3,"ta":677.3,"eq":442.9,"roe":28.58,"roe_raw":14.29,"oil":28.84,"pt":"H"},
{"p":"2003H2","roa":14.15,"roa_raw":7.08,"np":52.0,"ta":735.0,"eq":467.4,"roe":22.25,"roe_raw":11.13,"oil":28.92,"pt":"H"},
{"p":"2004H1","roa":18.01,"roa_raw":9.01,"np":70.2,"ta":779.3,"eq":511.1,"roe":27.47,"roe_raw":13.74,"oil":33.69,"pt":"H"},
{"p":"2004H2","roa":19.45,"roa_raw":9.72,"np":91.2,"ta":938.0,"eq":564.4,"roe":32.32,"roe_raw":16.16,"oil":42.77,"pt":"H"},
{"p":"2005H1","roa":22.59,"roa_raw":11.3,"np":118.3,"ta":1047.3,"eq":650.6,"roe":36.37,"roe_raw":18.18,"oil":49.66,"pt":"H"},
{"p":"2005H2","roa":23.52,"roa_raw":11.76,"np":134.9,"ta":1147.7,"eq":736.0,"roe":36.66,"roe_raw":18.33,"oil":59.18,"pt":"H"},
{"p":"2006H1","roa":22.14,"roa_raw":11.07,"np":162.8,"ta":1470.3,"eq":null,"roe":null,"roe_raw":null,"oil":65.64,"pt":"H"},
{"p":"2006H2","roa":18.87,"roa_raw":9.43,"np":146.5,"ta":1552.7,"eq":1077.7,"roe":27.19,"roe_raw":13.59,"oil":64.65,"pt":"H"},
{"p":"2007H1","roa":17.5,"roa_raw":8.75,"np":145.5,"ta":1662.6,"eq":1148.8,"roe":25.33,"roe_raw":12.67,"oil":63.17,"pt":"H"},
{"p":"2007H2","roa":18.58,"roa_raw":9.29,"np":167.1,"ta":1797.9,"eq":1343.1,"roe":24.88,"roe_raw":12.44,"oil":81.76,"pt":"H"},
{"p":"2008H1","roa":27.2,"roa_raw":13.6,"np":275.4,"ta":2025.1,"eq":1509.4,"roe":36.49,"roe_raw":18.25,"oil":109.17,"pt":"H"},
{"p":"2008H2","roa":16.29,"roa_raw":8.15,"np":168.3,"ta":2066.7,"eq":1602.4,"roe":21.01,"roe_raw":10.5,"oil":84.53,"pt":"H"},
{"p":"2009H1","roa":11.25,"roa_raw":5.63,"np":124.0,"ta":2203.9,"eq":1647.7,"roe":15.05,"roe_raw":7.53,"oil":51.56,"pt":"H"},
{"p":"2009H2","roa":14.1,"roa_raw":7.05,"np":170.8,"ta":2422.7,"eq":1739.4,"roe":19.64,"roe_raw":9.82,"oil":71.42,"pt":"H"},
{"p":"2010H1","roa":18.33,"roa_raw":9.16,"np":259.9,"ta":2836.3,"eq":1915.0,"roe":27.14,"roe_raw":13.57,"oil":77.38,"pt":"H"},
{"p":"2010H2","roa":17.85,"roa_raw":8.93,"np":284.2,"ta":3184.3,"eq":2157.7,"roe":26.34,"roe_raw":13.17,"oil":81.64,"pt":"H"},
{"p":"2011H1","roa":21.71,"roa_raw":10.86,"np":393.4,"ta":3624.3,"eq":2453.9,"roe":32.06,"roe_raw":16.03,"oil":111.16,"pt":"H"},
{"p":"2011H2","roa":16.09,"roa_raw":8.04,"np":309.1,"ta":3842.6,"eq":2628.6,"roe":23.52,"roe_raw":11.76,"oil":111.37,"pt":"H"},
{"p":"2012H1","roa":15.39,"roa_raw":7.69,"np":318.7,"ta":4142.2,"eq":2842.2,"roe":22.43,"roe_raw":11.21,"oil":113.45,"pt":"H"},
{"p":"2012H2","roa":13.95,"roa_raw":6.98,"np":318.2,"ta":4560.7,"eq":3097.8,"roe":20.54,"roe_raw":10.27,"oil":109.85,"pt":"H"},
{"p":"2013H1","roa":11.19,"roa_raw":5.59,"np":343.8,"ta":6145.7,"eq":3296.2,"roe":20.86,"roe_raw":10.43,"oil":107.54,"pt":"H"},
{"p":"2013H2","roa":7.11,"roa_raw":3.55,"np":220.8,"ta":6214.7,"eq":3416.2,"roe":12.93,"roe_raw":6.46,"oil":109.74,"pt":"H"},
{"p":"2014H1","roa":10.13,"roa_raw":5.07,"np":335.9,"ta":6632.1,"eq":3664.9,"roe":18.33,"roe_raw":9.17,"oil":108.93,"pt":"H"},
{"p":"2014H2","roa":8.03,"roa_raw":4.01,"np":266.1,"ta":6628.6,"eq":3796.1,"roe":14.02,"roe_raw":7.01,"oil":89.11,"pt":"H"},
{"p":"2015H1","roa":4.39,"roa_raw":2.19,"np":147.3,"ta":6718.4,"eq":3829.7,"roe":7.69,"roe_raw":3.85,"oil":57.8,"pt":"H"},
{"p":"2016H1","roa":-2.39,"roa_raw":-1.19,"np":-77.3,"ta":6478.0,"eq":3709.7,"roe":-4.17,"roe_raw":-2.08,"oil":39.61,"pt":"H"},
{"p":"2016H2","roa":2.63,"roa_raw":1.31,"np":83.7,"ta":6376.8,"eq":3823.7,"roe":4.38,"roe_raw":2.19,"oil":47.49,"pt":"H"},
{"p":"2017H1","roa":5.04,"roa_raw":2.52,"np":162.5,"ta":6450.8,"eq":3848.5,"roe":8.44,"roe_raw":4.22,"oil":51.68,"pt":"H"},
{"p":"2017H2","roa":2.73,"roa_raw":1.37,"np":84.3,"ta":6172.2,"eq":3799.8,"roe":4.44,"roe_raw":2.22,"oil":56.82,"pt":"H"},
{"p":"2018H1","roa":7.8,"roa_raw":3.9,"np":254.8,"ta":6529.7,"eq":3959.9,"roe":12.87,"roe_raw":6.43,"oil":70.65,"pt":"H"},
{"p":"2018H2","roa":7.93,"roa_raw":3.96,"np":272.0,"ta":6863.8,"eq":4199.0,"roe":12.96,"roe_raw":6.48,"oil":71.47,"pt":"H"},
{"p":"2019H1","roa":8.41,"roa_raw":4.2,"np":302.9,"ta":7205.4,"eq":4308.7,"roe":14.06,"roe_raw":7.03,"oil":66.05,"pt":"H"},
{"p":"2019H2","roa":8.12,"roa_raw":4.06,"np":307.6,"ta":7577.3,"eq":4481.9,"roe":13.73,"roe_raw":6.86,"oil":62.67,"pt":"H"},
{"p":"2020H1","roa":2.77,"roa_raw":1.38,"np":103.8,"ta":7500.1,"eq":4416.8,"roe":4.7,"roe_raw":2.35,"oil":39.89,"pt":"H"},
{"p":"2020H2","roa":4.04,"roa_raw":2.02,"np":145.7,"ta":7212.8,"eq":4337.1,"roe":6.72,"roe_raw":3.36,"oil":43.63,"pt":"H"},
{"p":"2021H1","roa":8.82,"roa_raw":4.41,"np":333.3,"ta":7560.3,"eq":4568.1,"roe":14.59,"roe_raw":7.3,"oil":64.83,"pt":"H"},
{"p":"2021H2","roa":9.41,"roa_raw":4.7,"np":369.9,"ta":7865.7,"eq":4809.1,"roe":15.38,"roe_raw":7.69,"oil":76.53,"pt":"H"},
{"p":"2022Q1","roa":16.64,"roa_raw":4.16,"np":343.0,"ta":8247.6,"eq":5152.3,"roe":26.63,"roe_raw":6.66,"oil":100.3,"pt":"Q"},
{"p":"2022Q2","roa":16.35,"roa_raw":4.09,"np":375.9,"ta":9198.1,"eq":5486.9,"roe":27.4,"roe_raw":6.85,"oil":113.54,"pt":"Q"},
{"p":"2022Q3","roa":15.78,"roa_raw":3.94,"np":368.8,"ta":9349.6,"eq":5676.7,"roe":25.99,"roe_raw":6.5,"oil":100.71,"pt":"Q"},
{"p":"2022Q4","roa":14.18,"roa_raw":3.54,"np":329.3,"ta":9290.3,"eq":5971.8,"roe":22.06,"roe_raw":5.51,"oil":88.56,"pt":"Q"},
{"p":"2023Q1","roa":13.36,"roa_raw":3.34,"np":321.1,"ta":9611.6,"eq":6257.4,"roe":20.53,"roe_raw":5.13,"oil":81.17,"pt":"Q"},
{"p":"2023Q2","roa":12.67,"roa_raw":3.17,"np":316.5,"ta":9990.7,"eq":6365.4,"roe":19.89,"roe_raw":4.97,"oil":78.32,"pt":"Q"},
{"p":"2023Q3","roa":13.29,"roa_raw":3.32,"np":338.8,"ta":10200.2,"eq":6434.1,"roe":21.06,"roe_raw":5.27,"oil":86.66,"pt":"Q"},
{"p":"2023Q4","roa":10.42,"roa_raw":2.61,"np":262.0,"ta":10056.0,"eq":6665.9,"roe":15.72,"roe_raw":3.93,"oil":83.72,"pt":"Q"},
{"p":"2024Q1","roa":15.06,"roa_raw":3.76,"np":397.2,"ta":10551.8,"eq":7064.8,"roe":22.49,"roe_raw":5.62,"oil":83.0,"pt":"Q"},
{"p":"2024Q2","roa":14.88,"roa_raw":3.72,"np":400.1,"ta":10754.0,"eq":7192.0,"roe":22.25,"roe_raw":5.56,"oil":84.65,"pt":"Q"},
{"p":"2024Q3","roa":13.68,"roa_raw":3.42,"np":369.3,"ta":10793.9,"eq":7188.3,"roe":20.55,"roe_raw":5.14,"oil":79.84,"pt":"Q"},
{"p":"2024Q4","roa":8.06,"roa_raw":2.01,"np":212.8,"ta":10562.8,"eq":7475.5,"roe":11.39,"roe_raw":2.85,"oil":74.61,"pt":"Q"},
{"p":"2025Q1","roa":13.26,"roa_raw":3.32,"np":365.6,"ta":11027.1,"eq":7838.2,"roe":18.66,"roe_raw":4.66,"oil":75.81,"pt":"Q"},
{"p":"2025Q2","roa":11.79,"roa_raw":2.95,"np":329.7,"ta":11189.6,"eq":7864.7,"roe":16.77,"roe_raw":4.19,"oil":68.01,"pt":"Q"},
{"p":"2025Q3","roa":11.52,"roa_raw":2.88,"np":324.4,"ta":11264.7,"eq":7855.6,"roe":16.52,"roe_raw":4.13,"oil":68.97,"pt":"Q"},
{"p":"2025Q4","roa":7.32,"roa_raw":1.83,"np":201.1,"ta":10985.6,"eq":8027.5,"roe":10.02,"roe_raw":2.51,"oil":63.63,"pt":"Q"},
{"p":"2026Q1","roa":13.6,"roa_raw":3.4,"np":391.4,"ta":11515.6,"eq":8371.0,"roe":18.7,"roe_raw":4.68,"oil":80.21,"pt":"Q"}
];

const COLOR_OIL = '#c94a4a';   // 油价（红）
const COLOR_ROA = '#2a7ab5';   // ROA（蓝）
const COLOR_ROE = '#7b4fb0';   // ROE（紫）
const labels = DATA.map(d => d.p);
const oil = DATA.map(d => d.oil);
const firstQ = DATA.findIndex(d => d.pt === 'Q');   // 季报口径起点 (2022Q1)
// 事件标注：非油价驱动的拐点（琥珀=运营事件 / 青=海外收购）
const EVENTS = [
    {
        p: '2011H2',
        name: '蓬莱19-3停产',
        color: '#c2820e',
        time: '2011.6 起',
        desc: '2011.6 渤海蓬莱19-3溢油，9月起被责令全面停产；渤海核心产区减产，油价仍在 $111 高位，单期归母净利却环比 393→309 亿元、ROA 从 21.7% 掉到 16.1%。'
    },
    {
        p: '2011H2',
        name: '收购 OPTI（油砂）',
        color: '#2f8f83',
        time: '2011.11',
        line: false,   // 与蓬莱同落 2011H2，图上只保留一条线，本条仅进对照表
        desc: '约 21 亿美元收购加拿大 OPTI，拿到 Long Lake 油砂 35% 权益——为切入非常规重油、补储量。收购＋高资本开支推高总资产（分母），与蓬莱停产叠加压低 2011H2 ROA。'
    },
    {
        p: '2013H1',
        name: '收购 Nexen',
        color: '#2f8f83',
        time: '2013.2',
        desc: '约 151 亿美元完成收购加拿大 Nexen（中企当时最大海外并购），为换取探明储量与油砂/深水/北海资产及全球布局。总资产单期从 4561→6146 亿元（+35%），分母骤增把 ROA 从 14.0% 拉到 11.2%；并入多为高成本资产，2014 起油价下行时回撤被放大。'
    }
];
const evOf = p => EVENTS.filter(e => e.p === p);
/*__SCRIPT__*/
// 每张图：指标线（左轴）+ 油价线（右轴）；左右两轴段数相同，使 0 落在同一条网格线
const CHARTS = [
    {
        dom: 'chart-roa', field: 'roa', color: COLOR_ROA,
        seriesName: '单期 ROA（年化）', axisName: 'ROA (%)',
        leftMin: -5, leftMax: 30, leftInterval: 5,
        oilMin: -20, oilMax: 120, oilInterval: 20,
        extra: d => `期末总资产：<b>${d.ta.toLocaleString()}</b> 亿元`
    },
    {
        dom: 'chart-roe', field: 'roe', color: COLOR_ROE,
        seriesName: '单期 ROE（年化）', axisName: 'ROE (%)',
        leftMin: -10, leftMax: 40, leftInterval: 10,
        oilMin: -30, oilMax: 120, oilInterval: 30,
        extra: d => `期末归母权益：<b>${d.eq == null ? '—' : d.eq.toLocaleString()}</b> 亿元`
    }
];

// 事件竖线 + 徽标（两张图共用；季报口径起点单独一条灰线）
function eventMarkLine() {
    return {
        silent: true, symbol: 'none',
        lineStyle: { color: '#aaa', type: 'dashed', width: 1.5 },
        label: { formatter: '季报口径起', fontSize: 16, color: '#888', position: 'insideEndTop' },
        data: [{ xAxis: firstQ }].concat(EVENTS.filter(e => e.line !== false).map(e => ({
            xAxis: DATA.findIndex(d => d.p === e.p),
            lineStyle: { color: e.color, type: 'dashed', width: 2 },
            label: {
                show: true, formatter: e.name,
                fontSize: 16, fontWeight: 'bold', color: '#fff',
                backgroundColor: e.color, padding: [4, 8], borderRadius: 4,
                rotate: 0, position: 'insideEndTop', distance: 4
            }
        })))
    };
}
function buildOption(cfg) {
    return {
        backgroundColor: '#ffffff',
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'cross', lineStyle: { width: 2 } },
            textStyle: { fontSize: 18 },
            position: (point, params, dom, rect, size) => {
                const [x] = point;
                const tw = size.contentSize[0], vw = size.viewSize[0];
                return [x + 16 + tw > vw ? x - tw - 16 : x + 16, 16];
            },
            formatter: params => {
                const d = DATA[params[0].dataIndex];
                const per = d.pt === 'Q' ? '季度' : '半年';
                const evs = evOf(d.p);
                const val = d[cfg.field];
                return `<b>${d.p}</b>（${per}期）<br>
                    <span style="color:${COLOR_OIL}">■</span> 布伦特期内均价：<b>${d.oil}</b> 美元/桶<br>
                    <span style="color:${cfg.color}">■</span> ${cfg.seriesName}：<b>${val == null ? '—' : val}</b> %<br>
                    单期归母净利：<b>${d.np.toLocaleString()}</b> 亿元<br>
                    ${cfg.extra(d)}`
                    + evs.map(ev => `<br><span style="color:${ev.color}">▲ ${ev.name}</span>：<span style="color:#555;white-space:normal;display:inline-block;max-width:360px;vertical-align:top">${ev.desc}</span>`).join('');
            }
        },
        legend: { data: [cfg.seriesName, '布伦特油价'], top: 4, textStyle: { fontSize: 18, color: '#333' } },
        grid: { left: 60, right: 72, top: 44, bottom: 56 },
        xAxis: {
            type: 'category', data: labels, boundaryGap: false,
            axisLabel: {
                color: '#555', fontSize: 17, interval: 0, rotate: 55,
                formatter: v => (/H1$|Q1$/.test(v) ? v.slice(0, 4) : '')
            },
            axisLine: { lineStyle: { color: '#bbb' } }
        },
        yAxis: [
            {
                type: 'value', name: cfg.axisName, min: cfg.leftMin, max: cfg.leftMax, interval: cfg.leftInterval,
                nameTextStyle: { fontSize: 18, color: cfg.color, align: 'right' },
                axisLabel: { color: '#555', fontSize: 18, formatter: '{value}%' },
                splitLine: { lineStyle: { color: '#e8e8e8' } }
            },
            {
                // 与左轴段数相同 → 两轴 0 对齐；油价不为负，隐藏负值格标签
                type: 'value', name: '美元/桶', min: cfg.oilMin, max: cfg.oilMax, interval: cfg.oilInterval,
                nameTextStyle: { fontSize: 18, color: COLOR_OIL, align: 'right' },
                axisLabel: { color: '#555', fontSize: 18, formatter: v => (v < 0 ? '' : v) },
                splitLine: { show: false }
            }
        ],
        series: [
            {
                name: cfg.seriesName, type: 'line', yAxisIndex: 0, data: DATA.map(d => d[cfg.field]),
                smooth: false, symbol: 'circle', symbolSize: 6, connectNulls: true,
                lineStyle: { color: cfg.color, width: 3 }, itemStyle: { color: cfg.color },
                areaStyle: { color: cfg.color + '14' },
                markLine: eventMarkLine()
            },
            {
                name: '布伦特油价', type: 'line', yAxisIndex: 1, data: oil,
                smooth: false, symbol: 'circle', symbolSize: 6,
                lineStyle: { color: COLOR_OIL, width: 3 }, itemStyle: { color: COLOR_OIL }
            }
        ]
    };
}
// 两张图的 option 在 setup 期即可算出（数据为静态内联）；容器 resize/dispose 交给 EChart 组件。
const roaOption = buildOption(CHARTS[0])
const roeOption = buildOption(CHARTS[1])
</script>

<style scoped>
.roa-page {
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    font-family: Arial, "Microsoft YaHei", sans-serif;
}
.chart-card { width: 100%; max-width: 1800px; margin: 0 auto; flex-shrink: 0; }
.chart-head { display: flex; align-items: baseline; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.chart-box { width: 100%; height: 70vh; }

/* === 底部标注表（参照 price_history.html） === */
#annotations-section {
    width: 100%; max-width: 1800px; margin: 0 auto;
    background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px 24px;
}
#annotations-section h2 { margin: 0 0 16px; font-size: 20px; color: #111827; font-weight: bold; }
#annotation-table { width: 100%; border-collapse: collapse; font-size: 18px; color: #1f2937; }
#annotation-table th {
    background: #f3f4f6; padding: 10px 12px; text-align: left; font-weight: 600;
    font-size: 18px; color: #4b5563; border-bottom: 2px solid #d1d5db; white-space: nowrap;
}
#annotation-table td { padding: 12px; border-bottom: 1px solid #e5e7eb; vertical-align: top; line-height: 1.7; }
#annotation-table tr:hover td { background: #fafafa; }
#annotation-table td.time { font-family: "SF Mono", Consolas, monospace; white-space: nowrap; color: #4b5563; }
#annotation-table td.event { border-left: 4px solid transparent; font-weight: 600; padding-left: 12px; white-space: nowrap; }
#annotation-table td:last-child { font-size: 20px; }
</style>

