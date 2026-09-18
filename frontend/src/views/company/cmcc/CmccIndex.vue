<template>
  <div class="wrap">
    <div v-if="error" class="cmcc-fail">
      <b>数据未能加载：</b>{{ error }}<br>本页通过 fetch 读取 <code>data/tables/telecom_00941_*.json</code>，需要用本地服务打开（例如在仓库根执行 <code>python3 -m http.server</code> 后访问 <code>/dashboard/company/cmcc/</code>），直接用 file:// 打开会被浏览器拦截。
    </div>

    <div class="page-head">
      <h1>中国移动有限公司（941 / 80941 / 600941）· 业绩</h1>
      <div class="meta">
        国际财务报告准则（IFRS）· 人民币百万元／亿元（比率为 %）· 股东应占口径<br>
        覆盖 1997 年在港上市至今 · 2022 年起以 A 股年报为准，之前用港股年报
      </div>
      <div class="tags"><span>营运收入</span><span>主营业务收入</span><span>EBITDA</span><span>资本开支</span><span>股息</span></div>
    </div>

    <!-- ══════════ 最新财年概览 ══════════ -->
    <section id="sec-kpi">
      <h2>最新财年概览</h2>
      <p class="sub" id="kpi-sub"></p>
      <div class="kpis" id="main-kpis"></div>
      <div class="note-generic" id="kpi-note"></div>
    </section>

    <!-- ══════════ 营运收入 ══════════ -->
    <section id="sec-revenue">
      <h2>营运收入与增速</h2>
      <p class="sub">柱：主营业务收入 / 其他业务收入（亿元，堆叠即营运收入）· 线：营运收入同比（%，由相邻年度现算）</p>
      <div ref="chartRevenueEl" class="chart" style="height:440px"></div>
      <div class="note-generic" id="revenue-note"></div>
    </section>

    <!-- ══════════ 利润与利润率 ══════════ -->
    <section id="sec-profit">
      <h2>EBITDA · 股东应占利润 · 利润率</h2>
      <p class="sub">柱：EBITDA / 股东应占利润（亿元）· 线：EBITDA 率 / 股东应占利润率（%）</p>
      <div ref="chartProfitEl" class="chart" style="height:440px"></div>
      <div class="note-generic" id="profit-note"></div>
    </section>

    <!-- ══════════ 成本结构 ══════════ -->
    <section id="sec-cost">
      <h2>营运支出结构</h2>
      <p class="sub">堆叠：各项营运支出占营运收入 %（网络运营及支撑、折旧摊销、雇员薪酬、销售费用、销售产品成本、其他）</p>
      <div ref="chartCostEl" class="chart" style="height:420px"></div>
      <div class="note-generic" id="cost-note"></div>
    </section>
    <!-- ══════════ 资本开支与现金流 ══════════ -->
    <section id="sec-capex">
      <h2>资本开支 · 折旧摊销 · 自由现金流</h2>
      <p class="sub">柱：资本开支（亿元，画为负值）/ 折旧及摊销（亿元）· 线：资本开支占主营业务收入 %</p>
      <div ref="chartCapexEl" class="chart" style="height:440px"></div>
      <div class="note-generic" id="capex-note"></div>
    </section>

    <!-- ══════════ 每股与股息 ══════════ -->
    <section id="sec-dividend">
      <h2>每股基本盈利与股息</h2>
      <p class="sub">柱：每股全年股息（港元）· 线：每股基本盈利（人民币元）与派息率（%）。<b>口径提示：</b>股息以港元计、盈利以人民币计，两者不同币种，比率仅供参考</p>
      <div class="kpis" id="div-kpis"></div>
      <div ref="chartDividendEl" class="chart" style="height:400px"></div>
      <div class="note-generic" id="dividend-note"></div>
    </section>

    <!-- ══════════ 近六年明细 ══════════ -->
    <section id="sec-table">
      <h2>近六年主要指标</h2>
      <p class="sub">单位：人民币百万元（比率为 %，股息为港元）· 括号内为负值 · 数据取自历年年报</p>
      <div style="overflow-x:auto">
        <table>
          <thead><tr id="tbl-head"></tr></thead>
          <tbody id="tbl-body"></tbody>
        </table>
      </div>
    </section>

    <!-- ══════════ 口径与缺口 ══════════ -->
    <section id="sec-gaps">
      <h2>口径提示与披露缺口</h2>
      <p class="sub">本页只用公司年报／官网投资者关系一手数据，以下为读图时必须知道的口径边界</p>
      <ul class="gap-list" id="gaps-list"></ul>
    </section>

  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import {
  years, pick, firstYear, yoy, toYi, yiTxt, yoyTxt, fx, pct, thou,
  setText, setHTML, renderKpis, renderList, renderRows,
  axisBase, valueAxis, gapMark, NAVY, GOLD, ERA_COLORS, loadCmcc
} from './charts.js'

// 逐字搬自 dashboard/company/cmcc/charts/index.js：所有 ECharts option 与渲染逻辑原样保留，
// 仅把 mount 的容器由 getElementById 改为组件模板 ref，echarts 实例收集到组件内 charts 数组统一
// resize/dispose；取数由 loadCmcc() 用绝对路径 fetch 三表合成 C（字段/合并与原 boot.js 一致）。
const error = ref('')
const chartRevenueEl = ref(null)
const chartProfitEl = ref(null)
const chartCostEl = ref(null)
const chartCapexEl = ref(null)
const chartDividendEl = ref(null)
let charts = []

/* 与原 common.js 的 mount/CHARTS/resize 等价：init + setOption(true)，实例收集入 charts，
   resize 时 resize + 重跑 build（与原页 window.resize 行为一致）。 */
function mount(el, buildOption) {
  if (!el) return null
  const ins = echarts.init(el)
  ins.setOption(buildOption(ins), true)
  charts.push({ ins, build: buildOption })
  return ins
}
function onResize() {
  charts.forEach(c => { c.ins.resize(); c.ins.setOption(c.build(c.ins), true) })
}

onMounted(async () => {
  try {
    const C = await loadCmcc()
    render(C)
    window.addEventListener('resize', onResize)
  } catch (e) {
    error.value = e && e.message ? e.message : String(e)
  }
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  charts.forEach(c => { try { c.ins.dispose() } catch (_) {} })
  charts = []
})

function render(C) {
  /* ==== 以下逐字搬自 charts/index.js ==== */
  var AN = (C.annual && C.annual.annual) || {};
  var META = (C.annual && C.annual._meta) || {};
  /* 有营运收入的年份即为本页 x 轴；缺披露的字段在图上留 null，不插值 */
  var Y = years(AN, 'totalRevenue');
  var LAST = Y[Y.length - 1], PREV = Y[Y.length - 2];
  var L = AN[LAST] || {}, P = AN[PREV] || {};

  /* ==== 最新财年概览 ==== */
  setText('kpi-sub',
    '口径：' + LAST + ' 财年 · 营运收入 = 主营业务收入 + 其他业务收入（其他业务主要为手机等终端销售）'
    + ' · 数据来源 ' + (L._reportBasis || META.sourcePrimary || '公司年报'));
  renderKpis('main-kpis', [
    { label: LAST + ' 营运收入', value: yiTxt(L.totalRevenue), delta: yoyTxt(L.totalRevenue, P.totalRevenue) },
    { label: LAST + ' 主营业务收入', value: yiTxt(L.serviceRevenue), delta: yoyTxt(L.serviceRevenue, P.serviceRevenue) },
    { label: LAST + ' EBITDA', value: yiTxt(L.ebitda), delta: yoyTxt(L.ebitda, P.ebitda) },
    { label: LAST + ' 股东应占利润', value: yiTxt(L.netProfit), delta: yoyTxt(L.netProfit, P.netProfit) },
    { label: LAST + ' 资本开支', value: yiTxt(L.capex), delta: yoyTxt(L.capex, P.capex) },
    { label: LAST + ' 每股全年股息', value: L.dividendTotal === null || L.dividendTotal === undefined
        ? '—' : fx(L.dividendTotal, 2) + ' 港元', delta: yoyTxt(L.dividendTotal, P.dividendTotal) }
  ]);

  /* ==== 营运收入：主营 + 其他堆叠，线为营运收入同比 ==== */
  mount(chartRevenueEl.value, function () {
    var o = axisBase({ x: Y, left: 84, right: 96 });
    o.yAxis = [valueAxis('亿元', { min: 0 }),
               valueAxis('营运收入同比 %', { position: 'right', splitLine: false })];
    o.series = [
      { name: '主营业务收入（亿元）', type: 'bar', stack: 'r', barWidth: '58%',
        itemStyle: { color: NAVY }, data: pick(AN, Y, 'serviceRevenue', toYi) },
      { name: '其他业务收入（亿元）', type: 'bar', stack: 'r',
        itemStyle: { color: ERA_COLORS.other }, data: pick(AN, Y, 'otherRevenue', toYi) },
      { name: '营运收入同比（%）', type: 'line', yAxisIndex: 1, symbolSize: 7, lineStyle: { width: 3 },
        itemStyle: { color: GOLD }, connectNulls: false,
        data: Y.map(function (y, i) { return i === 0 ? null : yoy(AN[y].totalRevenue, AN[Y[i - 1]].totalRevenue); }),
        markArea: (function () {
            /* 主营/其他两分法从哪年起才有披露：之前只有营运收入一个总数，
               柱子会只剩一层，用灰带说明这是口径问题不是业务问题 */
            var f = firstYear(AN, 'serviceRevenue');
            if (!f || f === Y[0]) return undefined;
            return gapMark(Y, Y[0], String(+f - 1), '此前只披露营运收入总额，未分主营／其他');
        })() }
    ];
    return o;
  });

  /* ==== EBITDA / 净利润 / 两条率 ==== */
  mount(chartProfitEl.value, function () {
    var o = axisBase({ x: Y, left: 84, right: 96 });
    o.yAxis = [valueAxis('亿元', { min: 0 }),
               valueAxis('率 %', { position: 'right', splitLine: false, min: 0 })];
    var ebitdaMargin = Y.map(function (y) {
        var r = AN[y];
        if (r.ebitda === null || r.ebitda === undefined || !r.totalRevenue) return null;
        return +(r.ebitda / r.totalRevenue * 100).toFixed(1);
    });
    var netMargin = Y.map(function (y) {
        var r = AN[y];
        if (r.netProfit === null || r.netProfit === undefined || !r.totalRevenue) return null;
        return +(r.netProfit / r.totalRevenue * 100).toFixed(1);
    });
    o.series = [
      { name: 'EBITDA（亿元）', type: 'bar', barWidth: '30%', itemStyle: { color: NAVY },
        data: pick(AN, Y, 'ebitda', toYi) },
      { name: '股东应占利润（亿元）', type: 'bar', barWidth: '30%', itemStyle: { color: '#2980b9' },
        data: pick(AN, Y, 'netProfit', toYi) },
      { name: 'EBITDA 率（%，本页按营运收入现算）', type: 'line', yAxisIndex: 1, symbolSize: 7,
        lineStyle: { width: 3 }, itemStyle: { color: GOLD }, data: ebitdaMargin },
      { name: '股东应占利润率（%）', type: 'line', yAxisIndex: 1, symbolSize: 7,
        lineStyle: { width: 3, type: 'dashed' }, itemStyle: { color: '#c0392b' }, data: netMargin }
    ];
    return o;
  });
  /* ==== 营运支出结构：各项占营运收入 % ==== */
  var OPEX_ITEMS = [
    { field: 'networkOpex',    name: '网络运营及支撑成本', color: NAVY },
    { field: 'depreciation',   name: '折旧及摊销',         color: '#2980b9' },
    { field: 'staffCost',      name: '雇员薪酬及相关成本', color: '#16a085' },
    { field: 'sellingExpense', name: '销售费用',           color: GOLD },
    { field: 'productCost',    name: '销售产品成本',       color: '#8e44ad' },
    { field: 'otherOpex',      name: '其他营运支出',       color: '#b0bac5' }
  ];
  mount(chartCostEl.value, function () {
    /* 支出明细只有近年才逐项披露，x 轴收窄到有网络成本的年份，避免左侧一大片空柱 */
    var OY = years(AN, 'networkOpex');
    var o = axisBase({ x: OY, left: 84, right: 96 });
    o.yAxis = [valueAxis('占营运收入 %', { min: 0 }),
               valueAxis('营运利润率 %', { position: 'right', splitLine: false, min: 0 })];
    o.series = OPEX_ITEMS.map(function (it, i) {
        return {
            name: it.name, type: 'bar', stack: 'c', barWidth: i === 0 ? '58%' : undefined,
            itemStyle: { color: it.color },
            data: OY.map(function (y) {
                var r = AN[y];
                if (r[it.field] === null || r[it.field] === undefined || !r.totalRevenue) return null;
                return +(r[it.field] / r.totalRevenue * 100).toFixed(1);
            })
        };
    });
    o.series.push({
        name: '营运利润率（%）', type: 'line', yAxisIndex: 1, symbolSize: 7, lineStyle: { width: 3 },
        itemStyle: { color: '#c0392b' },
        data: OY.map(function (y) {
            var r = AN[y];
            if (r.opProfit === null || r.opProfit === undefined || !r.totalRevenue) return null;
            return +(r.opProfit / r.totalRevenue * 100).toFixed(1);
        })
    });
    return o;
  });

  /* ==== 资本开支 · 折旧 · 自由现金流 ==== */
  mount(chartCapexEl.value, function () {
    var o = axisBase({ x: Y, left: 88, right: 104 });
    o.yAxis = [valueAxis('亿元'),
               valueAxis('资本开支占主营业务收入 %', { position: 'right', splitLine: false })];
    o.series = [
      { name: '资本开支（亿元，画为负值）', type: 'bar', barWidth: '30%', itemStyle: { color: '#c0392b' },
        data: Y.map(function (y) {
            var v = AN[y].capex;
            return v === null || v === undefined ? null : -toYi(v);
        }) },
      { name: '折旧及摊销（亿元）', type: 'bar', barWidth: '30%', itemStyle: { color: '#2980b9' },
        data: pick(AN, Y, 'depreciation', toYi) },
      { name: '自由现金流（亿元）', type: 'line', symbolSize: 7, lineStyle: { width: 3 },
        itemStyle: { color: '#16a085' }, data: pick(AN, Y, 'fcf', toYi) },
      { name: '资本开支占主营业务收入（%）', type: 'line', yAxisIndex: 1, symbolSize: 7,
        lineStyle: { width: 3, type: 'dashed' }, itemStyle: { color: GOLD },
        data: Y.map(function (y) {
            var r = AN[y];
            if (r.capex === null || r.capex === undefined || !r.serviceRevenue) return null;
            return +(r.capex / r.serviceRevenue * 100).toFixed(1);
        }) }
    ];
    return o;
  });
  /* ==== 每股盈利与股息 ==== */
  mount(chartDividendEl.value, function () {
    var o = axisBase({ x: Y, left: 84, right: 104 });
    o.yAxis = [valueAxis('每股金额', { min: 0 }),
               valueAxis('派息率 %', { position: 'right', splitLine: false, min: 0 })];
    o.series = [
      { name: '每股全年股息（港元）', type: 'bar', barWidth: '52%', itemStyle: { color: GOLD },
        data: pick(AN, Y, 'dividendTotal') },
      { name: '每股基本盈利（人民币元）', type: 'line', symbolSize: 7, lineStyle: { width: 3 },
        itemStyle: { color: NAVY }, data: pick(AN, Y, 'eps') },
      { name: '派息率（%）', type: 'line', yAxisIndex: 1, symbolSize: 7,
        lineStyle: { width: 3, type: 'dashed' }, itemStyle: { color: '#c0392b' },
        data: pick(AN, Y, 'payoutRatio') }
    ];
    return o;
  });

  /* ==== 股息 KPI ==== */
  (function () {
    var DY = years(AN, 'dividendTotal');
    if (!DY.length) return;
    var first = AN[DY[0]], last = AN[DY[DY.length - 1]];
    renderKpis('div-kpis', [
        { label: '有股息披露的年份', value: DY[0] + '–' + DY[DY.length - 1] + '（' + DY.length + ' 年）' },
        { label: DY[DY.length - 1] + ' 每股全年股息', value: fx(last.dividendTotal, 2) + ' 港元',
          delta: DY[0] + ' 为 ' + fx(first.dividendTotal, 2) + ' 港元' },
        { label: DY[DY.length - 1] + ' 派息率',
          value: last.payoutRatio === null || last.payoutRatio === undefined ? '—' : pct(last.payoutRatio, 0) }
    ]);
  })();

  /* ==== 近六年明细表 ==== */
  (function () {
    var TY = Y.slice(-6);
    setHTML('tbl-head', '<th>指标</th>' + TY.map(function (y) { return '<th>' + y + '</th>'; }).join(''));
    var ROWS = [
        { label: '营运收入', field: 'totalRevenue', total: true },
        { label: '　主营业务收入', field: 'serviceRevenue', sub: true },
        { label: '　其他业务收入', field: 'otherRevenue', sub: true },
        { label: '营运支出', field: 'opexTotal' },
        { label: '营运利润', field: 'opProfit' },
        { label: 'EBITDA', field: 'ebitda' },
        { label: '股东应占利润', field: 'netProfit', total: true },
        { label: '资本开支', field: 'capex' },
        { label: '经营活动现金流净额', field: 'ocf' },
        { label: '自由现金流', field: 'fcf' },
        { label: '每股基本盈利（人民币元）', field: 'eps', dec: 2 },
        { label: '每股全年股息（港元）', field: 'dividendTotal', dec: 2 },
        { label: '派息率（%）', field: 'payoutRatio', dec: 0 }
    ];
    renderRows('tbl-body', ROWS.map(function (r) {
        return {
            _th: true,
            _cls: r.total ? 'row-total' : (r.sub ? 'row-sub' : ''),
            cells: [r.label].concat(TY.map(function (y) {
                var v = AN[y] ? AN[y][r.field] : null;
                if (v === null || v === undefined) return '—';
                if (r.dec !== undefined) return fx(v, r.dec);
                return v < 0 ? '(' + thou(-v) + ')' : thou(v);
            }))
        };
    }));
  })();
  /* ==== 说明文字：全部由数据现算，改数不用改文案 ==== */
  (function () {
    var f = AN[Y[0]];
    setHTML('kpi-note',
        '<b>这家公司的报表从 ' + Y[0] + ' 年的 ' + yiTxt(f.totalRevenue) + ' 营运收入长到 '
        + LAST + ' 年的 ' + yiTxt(L.totalRevenue) + '，'
        + (Y.length > 1 ? '合计 ' + (+LAST - +Y[0]) + ' 年、年化 '
            + fx((Math.pow(L.totalRevenue / f.totalRevenue, 1 / (+LAST - +Y[0])) - 1) * 100, 1) + '%。</b>' : '</b>')
        + '增长的形状值得注意：前十几年靠客户数扩张，近十年营运收入增速已降到个位数，'
        + '真正在变的是<b>收入里面的产品构成</b>——那部分放在「产品更迭」页。');

    setHTML('revenue-note',
        '柱子分两层：深蓝是主营业务收入（通信/算力/智能服务），灰色是其他业务收入（主要为手机等终端销售）。'
        + '终端销售毛利很薄，把它和主营混在一起看会低估主业的利润率——这也是公司自己在年报里'
        + '始终把两者分开呈报的原因。' + LAST + ' 年其他业务收入 ' + yiTxt(L.otherRevenue)
        + '，占营运收入 ' + (L.otherRevenue && L.totalRevenue ? pct(L.otherRevenue / L.totalRevenue * 100) : '—') + '。');

    setHTML('profit-note',
        '<b>EBITDA 率与净利率的差额几乎全部是折旧摊销</b>——运营商是重资产生意，'
        + '每一轮制式换代（3G/4G/5G）都先砸资本开支、再用十年折旧摊回来。'
        + LAST + ' 年 EBITDA ' + yiTxt(L.ebitda) + '、股东应占利润 ' + yiTxt(L.netProfit)
        + '，两者之差 ' + (L.ebitda != null && L.netProfit != null ? yiTxt(L.ebitda - L.netProfit) : '—')
        + '，主要由折旧及摊销 ' + yiTxt(L.depreciation) + ' 与税项构成。'
        + '<b>口径提示：</b>本页 EBITDA 率按营运收入现算，公司年报部分年份改用「EBITDA / 主营业务收入」口径列示，'
        + '两者分母不同、数值会差 3–5 个百分点，跨年引用时务必看清分母。');

    setHTML('cost-note',
        '这张图只画到有逐项披露的年份为止。<b>销售产品成本（终端）这一层是「非主业」的重量</b>，'
        + '它涨的时候营运收入也涨，但几乎不带利润；真正决定利润率的是网络运营及支撑成本与折旧摊销两层。');

    setHTML('capex-note',
        '资本开支画成负值是为了和折旧摊销上下对照：<b>当资本开支的绝对额低于折旧摊销时，'
        + '意味着这一轮网络投资已经过了峰值</b>，账面开始"收回"前几年的投入。'
        + (L.capex != null && L.depreciation != null
            ? LAST + ' 年资本开支 ' + yiTxt(L.capex) + '、折旧及摊销 ' + yiTxt(L.depreciation) + '。'
            : ''));

    setHTML('dividend-note',
        '<b>币种不同请注意：</b>每股盈利以人民币计、每股股息以港元派发，图上两者同轴只是为了看趋势，'
        + '直接相除得不到真实派息率——派息率一栏用的是公司年报自己披露的口径。');

    /* 口径缺口：由数据里各字段的实际覆盖区间现算，不手写年份 */
    var GAP_FIELDS = [
        ['serviceRevenue', '主营业务收入'],
        ['opexTotal', '营运支出总额'],
        ['networkOpex', '营运支出逐项明细'],
        ['fcf', '自由现金流'],
        ['payoutRatio', '派息率'],
        ['capex', '资本开支']
    ];
    var items = GAP_FIELDS.map(function (p) {
        var ys = years(AN, p[0]);
        if (!ys.length) return '<b>' + p[1] + '</b>：本页数据源中无任何年份披露。';
        var missing = Y.filter(function (y) {
            return +y >= +ys[0] && +y <= +ys[ys.length - 1] && (AN[y][p[0]] === null || AN[y][p[0]] === undefined);
        });
        return '<b>' + p[1] + '</b>：覆盖 ' + ys[0] + '–' + ys[ys.length - 1] + '（共 ' + ys.length + ' 年）'
            + (+ys[0] > +Y[0] ? '，' + Y[0] + '–' + (+ys[0] - 1) + ' 未披露' : '')
            + (missing.length ? '，区间内缺 ' + missing.join('、') : '') + '。';
    });
    if (META.gaps) {
        Object.keys(META.gaps).forEach(function (k) {
            items.push('<b>' + k + '</b>：' + META.gaps[k]);
        });
    }
    items.push('<b>来源与优先级</b>：' + (META.sourcePriority
        || '2022–2025 年以 A 股年报为准，1997–2021 年用港股年报；官网投资者关系页仅用于交叉核对。'));
    renderList('gaps-list', items);
  })();
}
</script>

<!-- 静态骨架（模板里带 data-v 的容器/标题/说明框）逐字取自 company/page.css 与源页 <head> 内联
     .note-generic/.gap-list；base.css 已全局引入（reset/body/.chart-title/#loading 等），此处不重复。 -->
<style scoped>
.cmcc-fail {
    max-width: 900px; margin: 80px auto; padding: 20px 24px;
    background: #fff5f5; border-left: 4px solid #c0392b; border-radius: 8px;
    font: 18px/1.8 -apple-system, "Microsoft YaHei", sans-serif; color: #7b241c;
}
.wrap { max-width: var(--content-w, 1200px); margin: 0 auto; padding: 24px 24px 60px; }
.page-head { text-align: center; margin-bottom: 8px; }
.page-head h1 { font-size: 29px; color: #1f2937; margin-bottom: 6px; }
.page-head .meta { color: #6b7280; font-size: 18px; line-height: 1.7; }
.page-head .tags { margin-top: 8px; display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; }
.page-head .tags span {
    background: #dde8f3; color: #10243e; border-radius: 12px;
    padding: 3px 12px; font-size: 18px; font-weight: 500;
}
section { background: #fff; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.06);
          padding: 20px 22px; margin-top: 22px; scroll-margin-top: 116px; }
section > h2 {
    font-size: 22px; color: #1f2937; margin-bottom: 4px;
    border-left: 4px solid #10243e; padding-left: 10px;
}
section > .sub { color: #6b7280; font-size: 18px; margin: 0 0 14px 14px; }
.chart { width: 100%; height: 428px; }   /* 380 × 1.125；各图容器内联 height 覆盖此默认值 */
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px,1fr)); gap: 12px; margin-bottom: 16px; }
.note-generic {
    margin: 10px 0 0; padding: 12px 16px; background: #f6f7f9;
    border-left: 4px solid #b7b1c4; border-radius: 6px;
    font-size: 18px; color: #555; line-height: 1.75;
}
.gap-list { margin: 6px 0 0 18px; font-size: 18px; color: #555; line-height: 1.8; }
</style>

<!-- 动态节点（renderKpis/renderRows/renderList 用 innerHTML 注入，拿不到 scoped 的 data-v）：
     必须非 scoped 才能命中。用 .wrap 作前缀把作用域收在本页容器内，避免 th/td/.kpi 等通用选择器
     泄漏到全站；取值逐字取自 company/page.css 与源页内联 .gap-list b。 -->
<style>
.wrap .kpi { background: #f3f6fa; border: 1px solid #dde8f3; border-radius: 8px; padding: 12px 14px; }
.wrap .kpi .label { font-size: 18px; color: #7f8c8d; }
.wrap .kpi .value { font-size: 25px; font-weight: 700; color: #10243e; margin-top: 4px; }
.wrap .kpi .delta { font-size: 18px; margin-top: 2px; }
.wrap table { width: 100%; border-collapse: collapse; font-size: 18px; }
.wrap th, .wrap td { padding: 8px 10px; text-align: right; border-bottom: 1px solid #eee; }
.wrap th:first-child, .wrap td:first-child { text-align: left; }
.wrap thead th { background: #eef2f7; color: #10243e; font-weight: 600; border-bottom: 2px solid #c9a24a; }
.wrap tbody tr:hover { background: #f3f6fa; }
.wrap .row-total td { font-weight: 700; background: #f6f8fb; border-top: 2px solid #c9a24a; }
.wrap .row-sub td:first-child { padding-left: 26px; color: #555; font-weight: 400; }
.wrap .gap-list b { color: #10243e; }
</style>


