<template>
  <div class="wrap">
    <div v-if="error" class="cmcc-fail">
      <b>数据未能加载：</b>{{ error }}<br>本页通过 fetch 读取 <code>data/tables/telecom_00941_*.json</code>，需要用本地服务打开（例如在仓库根执行 <code>python3 -m http.server</code> 后访问 <code>/dashboard/company/cmcc/</code>），直接用 file:// 打开会被浏览器拦截。
    </div>

    <div class="page-head">
      <h1>中国移动 · 客户与网络</h1>
      <div class="meta">
        客户数单位：亿户（物联网连接数为亿）· 数据取自公司年报「业务概览－主要运营数据」与官网营运数据页<br>
        连接数的构成变化，是产品更迭在「用户侧」的同一件事
      </div>
      <div class="tags"><span>移动客户</span><span>制式渗透</span><span>宽带</span><span>物联网</span><span>网络与员工</span></div>
    </div>

    <!-- ══════════ 概览 ══════════ -->
    <section id="sec-kpi">
      <h2>最新财年客户概览</h2>
      <p class="sub" id="kpi-sub"></p>
      <div class="kpis" id="main-kpis"></div>
      <div class="note-generic" id="kpi-note"></div>
    </section>

    <!-- ══════════ 移动客户与净增 ══════════ -->
    <section id="sec-subs">
      <h2>移动客户总数与净增</h2>
      <p class="sub">柱：移动客户总数（亿户）· 线：当年净增客户数（万户）。<b>净增在 2015 年后逐级掉档，2024 年起接近零增长</b>——这是「人口红利结束」在报表上的样子</p>
      <div ref="chartSubsEl" class="chart" style="height:440px"></div>
      <div class="note-generic" id="subs-note"></div>
    </section>

    <!-- ══════════ 制式渗透 ══════════ -->
    <section id="sec-tech">
      <h2>网络制式渗透：3G → 4G → 5G</h2>
      <p class="sub">柱：当年最新制式客户数 + 尚未升级的客户（亿户，柱高恒等于移动客户总数）· 实线：最新一代渗透率（%）· 虚线：上一代客户数与 5G 套餐客户数（另一口径）。三代客户的接棒节奏决定了资本开支的节奏</p>
      <div ref="chartTechEl" class="chart" style="height:450px"></div>
      <div class="note-generic" id="tech-note"></div>
    </section>

    <!-- ══════════ 宽带与家庭 ══════════ -->
    <section id="sec-broadband">
      <h2>有线宽带与家庭市场</h2>
      <p class="sub">柱：有线宽带客户数 / 其中家庭宽带 / 千兆宽带（亿户）· 线：家庭客户综合 ARPU（元/户/月）</p>
      <div ref="chartBroadbandEl" class="chart" style="height:440px"></div>
      <div class="note-generic" id="broadband-note"></div>
    </section>
    <!-- ══════════ 物联网与政企 ══════════ -->
    <section id="sec-iot">
      <h2>物联网连接与政企客户</h2>
      <p class="sub">柱：物联网卡连接数（亿）· 线：政企客户数（百万）。<b>连接数早已超过人口</b>——2020 年之后的「连接增长」主要来自物，不是人</p>
      <div ref="chartIotEl" class="chart" style="height:430px"></div>
      <div class="note-generic" id="iot-note"></div>
    </section>

    <!-- ══════════ 网络与人 ══════════ -->
    <section id="sec-network">
      <h2>网络规模与员工</h2>
      <p class="sub">柱：5G 基站数（万站）／对外服务 IDC 标准机架（万架）· 线：员工总数（万人）。缺披露的年份留空，不做插值</p>
      <div ref="chartNetworkEl" class="chart" style="height:430px"></div>
      <div class="note-generic" id="network-note"></div>
    </section>

    <!-- ══════════ 明细表 ══════════ -->
    <section id="sec-table">
      <h2>运营指标明细</h2>
      <p class="sub">「—」表示该年年报未披露此项 · 单位见各行标注</p>
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
      <p class="sub">运营指标的口径变动比财务口径更频繁，下面这几条不知道就会读错趋势</p>
      <ul class="gap-list" id="gaps-list"></ul>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import {
  years, pick, fx, pct, thou, yoyTxt,
  setText, setHTML, renderKpis, renderList, renderRows,
  axisBase, valueAxis, shade, NAVY, GOLD, MUTED, ERA_COLORS, loadCmcc
} from './charts.js'

// 逐字搬自 dashboard/company/cmcc/charts/operation.js：所有 ECharts option 与渲染逻辑原样保留，
// 仅把 mount 的容器由 getElementById 改为组件模板 ref，实例收集到 charts 数组统一 resize/dispose；
// 取数由 loadCmcc() 用绝对路径 fetch 三表合成 C（字段/合并与原 boot.js 一致）。
const error = ref('')
const chartSubsEl = ref(null)
const chartTechEl = ref(null)
const chartBroadbandEl = ref(null)
const chartIotEl = ref(null)
const chartNetworkEl = ref(null)
let charts = []

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
  /* ==== 以下逐字搬自 charts/operation.js ==== */
  var OP = (C.operating && C.operating.annual) || {};
  var AN = (C.annual && C.annual.annual) || {};
  var OMETA = (C.operating && C.operating._meta) || {};

  var Y = years(OP, 'mobileSubs');
  var LAST = Y[Y.length - 1], PREV = Y[Y.length - 2];
  var L = OP[LAST] || {}, P = OP[PREV] || {};

  /* 最新一代制式：5G 有披露就用 5G，否则退到 4G */
  var GEN = years(OP, 'subs5G').length ? { field: 'subs5G', name: '5G 网络客户' }
          : years(OP, 'subs4G').length ? { field: 'subs4G', name: '4G 客户' }
          : null;

  /* ==== 概览 ==== */
  setText('kpi-sub',
    '口径：' + LAST + ' 年末数 · 移动客户数与宽带客户数为公司披露的期末口径 · '
    + (L._reportBasis || OMETA.sourcePrimary || '公司年报「业务概览－主要运营数据」'));
  renderKpis('main-kpis', [
    { label: LAST + ' 移动客户数', value: L.mobileSubs == null ? '—' : fx(L.mobileSubs, 2) + ' 亿户',
      delta: L.netAddSubs == null ? yoyTxt(L.mobileSubs, P.mobileSubs)
                                  : '当年净增 ' + thou(L.netAddSubs) + ' 万户' },
    GEN ? { label: LAST + ' ' + GEN.name,
            value: L[GEN.field] == null ? '—' : fx(L[GEN.field], 2) + ' 亿户',
            delta: (L[GEN.field] != null && L.mobileSubs)
                ? '渗透率 ' + pct(L[GEN.field] / L.mobileSubs * 100) : '' }
        : { label: '制式客户数', value: '—' },
    { label: LAST + ' 有线宽带客户数',
      value: L.broadbandSubs == null ? '—' : fx(L.broadbandSubs, 2) + ' 亿户',
      delta: yoyTxt(L.broadbandSubs, P.broadbandSubs) },
    { label: LAST + ' 物联网卡连接数',
      value: L.iotConnections == null ? '—' : fx(L.iotConnections, 2) + ' 亿',
      delta: yoyTxt(L.iotConnections, P.iotConnections) },
    { label: LAST + ' 移动 ARPU',
      value: L.arpu == null ? '—' : fx(L.arpu, 1) + ' 元/户/月', delta: yoyTxt(L.arpu, P.arpu) },
    { label: LAST + ' 员工总数',
      value: L.employees == null ? '—' : thou(L.employees) + ' 人', delta: yoyTxt(L.employees, P.employees) }
  ]);
  /* ==== 移动客户与净增 ==== */
  mount(chartSubsEl.value, function () {
    var o = axisBase({ x: Y, left: 84, right: 104 });
    o.yAxis = [valueAxis('亿户', { min: 0 }),
               valueAxis('当年净增（万户）', { position: 'right', splitLine: false })];
    o.series = [
      { name: '移动客户总数（亿户）', type: 'bar', barWidth: '56%', itemStyle: { color: NAVY },
        data: pick(OP, Y, 'mobileSubs') },
      { name: '当年净增客户数（万户）', type: 'line', yAxisIndex: 1, symbolSize: 8,
        lineStyle: { width: 3 }, itemStyle: { color: GOLD }, connectNulls: false,
        data: pick(OP, Y, 'netAddSubs') }
    ];
    return o;
  });

  /* ==== 制式渗透 ==== */
  /* 三代客户数不能堆叠——5G 客户同时也是移动客户，堆起来会重复计算。 */
  function genOf(y) {
    var r = OP[y] || {};
    if (r.subs5G != null) return { v: r.subs5G, name: '5G' };
    if (r.subs4G != null) return { v: r.subs4G, name: '4G' };
    if (r.subs3G != null) return { v: r.subs3G, name: '3G' };
    return { v: null, name: null };
  }
  mount(chartTechEl.value, function () {
    var o = axisBase({ x: Y, left: 84, right: 108, top: 56 });
    o.yAxis = [valueAxis('亿户', { min: 0 }),
               valueAxis('最新一代渗透率 %', { position: 'right', splitLine: false, min: 0, max: 100 })];
    o.series = [
      { name: '当年最新制式客户（亿户）', type: 'bar', stack: 't', barWidth: '58%',
        itemStyle: { color: '#c0392b' },
        data: Y.map(function (y) { return genOf(y).v; }) },
      { name: '尚未升级到最新制式（亿户）', type: 'bar', stack: 't',
        itemStyle: { color: shade(NAVY, 0.55) },
        data: Y.map(function (y) {
            var r = OP[y], g = genOf(y).v;
            if (r.mobileSubs == null) return null;
            return +Math.max(0, r.mobileSubs - (g || 0)).toFixed(2);
        }) },
      { name: '最新一代渗透率（%）', type: 'line', yAxisIndex: 1, symbolSize: 7,
        lineStyle: { width: 3 }, itemStyle: { color: GOLD }, connectNulls: false,
        data: Y.map(function (y) {
            var r = OP[y], g = genOf(y).v;
            if (!r.mobileSubs || g == null) return null;
            return +(g / r.mobileSubs * 100).toFixed(1);
        }) },
      { name: '3G 客户（亿户）', type: 'line', symbolSize: 6,
        lineStyle: { width: 2.5, type: 'dotted' }, itemStyle: { color: MUTED },
        connectNulls: false, data: pick(OP, Y, 'subs3G') },
      { name: '4G 客户（亿户）', type: 'line', symbolSize: 6,
        lineStyle: { width: 2.5, type: 'dashed' }, itemStyle: { color: ERA_COLORS.data },
        connectNulls: false, data: pick(OP, Y, 'subs4G') },
      { name: '5G 套餐客户（亿户，另一口径）', type: 'line', symbolSize: 6,
        lineStyle: { width: 2, type: 'dashed' }, itemStyle: { color: '#e67e22' },
        connectNulls: false, data: pick(OP, Y, 'subs5GPackage') }
    ];
    o.legend.type = 'scroll';
    return o;
  });
  /* ==== 宽带与家庭 ==== */
  mount(chartBroadbandEl.value, function () {
    var xs = Object.keys(OP).filter(function (y) {
        return OP[y] && (OP[y].broadbandSubs != null || OP[y].homeArpu != null);
    }).sort();
    var o = axisBase({ x: xs, left: 84, right: 108, top: 56 });
    o.yAxis = [valueAxis('亿户', { min: 0 }),
               valueAxis('元/户/月', { position: 'right', splitLine: false, min: 0 })];
    o.series = [
      { name: '有线宽带客户数（亿户）', type: 'bar', barWidth: '26%',
        itemStyle: { color: ERA_COLORS.broadband }, data: pick(OP, xs, 'broadbandSubs') },
      { name: '其中家庭宽带（亿户）', type: 'bar', barWidth: '26%',
        itemStyle: { color: shade(ERA_COLORS.broadband, 0.4) }, data: pick(OP, xs, 'homeBroadbandSubs') },
      { name: '千兆宽带（亿户）', type: 'bar', barWidth: '26%',
        itemStyle: { color: GOLD }, data: pick(OP, xs, 'gigabitSubs') },
      { name: '家庭客户综合 ARPU（元/户/月）', type: 'line', yAxisIndex: 1, symbolSize: 8,
        lineStyle: { width: 3 }, itemStyle: { color: NAVY }, connectNulls: false,
        data: pick(OP, xs, 'homeArpu') }
    ];
    o.legend.type = 'scroll';
    return o;
  });

  /* ==== 物联网与政企 ==== */
  mount(chartIotEl.value, function () {
    var xs = Object.keys(OP).filter(function (y) {
        return OP[y] && (OP[y].iotConnections != null || OP[y].govEntSubs != null);
    }).sort();
    var o = axisBase({ x: xs, left: 84, right: 108 });
    o.yAxis = [valueAxis('亿（连接）', { min: 0 }),
               valueAxis('百万（政企客户）', { position: 'right', splitLine: false, min: 0 })];
    o.series = [
      { name: '物联网卡连接数（亿）', type: 'bar', barWidth: '54%',
        itemStyle: { color: ERA_COLORS.appInfo }, data: pick(OP, xs, 'iotConnections') },
      { name: '政企客户数（百万）', type: 'line', yAxisIndex: 1, symbolSize: 8,
        lineStyle: { width: 3 }, itemStyle: { color: NAVY }, connectNulls: false,
        data: pick(OP, xs, 'govEntSubs') },
      { name: '移动客户数（亿户，参照线）', type: 'line', symbolSize: 6,
        lineStyle: { width: 2, type: 'dashed' }, itemStyle: { color: MUTED }, connectNulls: false,
        data: pick(OP, xs, 'mobileSubs') }
    ];
    o.legend.type = 'scroll';
    return o;
  });

  /* ==== 网络与员工 ==== */
  mount(chartNetworkEl.value, function () {
    var xs = Object.keys(OP).filter(function (y) {
        return OP[y] && (OP[y].base5G != null || OP[y].idcRacks != null || OP[y].employees != null);
    }).sort();
    var o = axisBase({ x: xs, left: 84, right: 108, top: 56 });
    o.yAxis = [valueAxis('万（站 / 架）', { min: 0 }),
               valueAxis('万人', { position: 'right', splitLine: false, min: 0 })];
    o.series = [
      { name: '5G 基站数（万站）', type: 'bar', barWidth: '30%', itemStyle: { color: '#c0392b' },
        data: pick(OP, xs, 'base5G') },
      { name: '对外服务 IDC 标准机架（万架）', type: 'bar', barWidth: '30%',
        itemStyle: { color: ERA_COLORS.appInfo }, data: pick(OP, xs, 'idcRacks') },
      { name: '员工总数（万人）', type: 'line', yAxisIndex: 1, symbolSize: 8, lineStyle: { width: 3 },
        itemStyle: { color: NAVY }, connectNulls: false,
        data: xs.map(function (y) {
            var v = OP[y].employees;
            return v == null ? null : +(v / 10000).toFixed(1);
        }) }
    ];
    o.legend.type = 'scroll';
    return o;
  });
  /* ==== 明细表 ==== */
  (function () {
    var TY = Y.slice(-12);
    setHTML('tbl-head', '<th>指标</th>' + TY.map(function (y) { return '<th>' + y + '</th>'; }).join(''));
    var ROWS = [
        { label: '移动客户数（亿户）', field: 'mobileSubs', dec: 2, total: true },
        { label: '　当年净增（万户）', field: 'netAddSubs', dec: 0, sub: true },
        { label: '　3G 客户（亿户）', field: 'subs3G', dec: 2, sub: true },
        { label: '　4G 客户（亿户）', field: 'subs4G', dec: 2, sub: true },
        { label: '　5G 网络客户（亿户）', field: 'subs5G', dec: 2, sub: true },
        { label: '　5G 套餐客户（亿户）', field: 'subs5GPackage', dec: 2, sub: true },
        { label: 'MOU（分钟/户/月）', field: 'mou', dec: 0 },
        { label: 'DOU（GB/户/月）', field: 'dou', dec: 1 },
        { label: '移动 ARPU（元/户/月）', field: 'arpu', dec: 1 },
        { label: '有线宽带客户数（亿户）', field: 'broadbandSubs', dec: 2, total: true },
        { label: '　其中家庭宽带（亿户）', field: 'homeBroadbandSubs', dec: 2, sub: true },
        { label: '　千兆宽带（亿户）', field: 'gigabitSubs', dec: 2, sub: true },
        { label: '家庭客户综合 ARPU（元/户/月）', field: 'homeArpu', dec: 1 },
        { label: '政企客户数（百万）', field: 'govEntSubs', dec: 2 },
        { label: '物联网卡连接数（亿）', field: 'iotConnections', dec: 2 },
        { label: '5G 基站数（万站）', field: 'base5G', dec: 1 },
        { label: '员工总数（人）', field: 'employees' }
    ];
    renderRows('tbl-body', ROWS.map(function (r) {
        return {
            _th: true,
            _cls: r.total ? 'row-total' : (r.sub ? 'row-sub' : ''),
            cells: [r.label].concat(TY.map(function (y) {
                var v = OP[y] ? OP[y][r.field] : null;
                if (v == null) return '—';
                return r.dec !== undefined ? fx(v, r.dec) : thou(v);
            }))
        };
    }));
  })();

  /* ==== 说明文字 ==== */
  (function () {
    var naY = years(OP, 'netAddSubs');
    var iotY = years(OP, 'iotConnections');

    setHTML('kpi-note',
        '<b>客户数这条线在 ' + LAST + ' 年已经基本走平。</b>'
        + (naY.length >= 3
            ? '净增客户数从 ' + naY[0] + ' 年的 ' + thou(OP[naY[0]].netAddSubs) + ' 万户，到 '
              + naY[naY.length - 1] + ' 年的 ' + thou(OP[naY[naY.length - 1]].netAddSubs) + ' 万户；'
            : '')
        + '在移动客户已超过 10 亿户、渗透率接近饱和之后，'
        + '「连接数」的增量主要来自物联网与宽带，而不是手机用户——这也是收入结构必须换代的直接原因。');

    setHTML('subs-note',
        '柱子是存量、线是增量。<b>存量看起来一直在涨，但增量早就掉了一个数量级</b>：'
        + '存量图的斜率变化不明显，增量线的落差才是真实的经营压力。'
        + (OMETA.definitions && OMETA.definitions.subsBasis ? '口径：' + OMETA.definitions.subsBasis : ''));

    setHTML('tech-note',
        '柱子只分「当年最新制式」与「尚未升级」两层，<b>柱高恒等于当年移动客户总数</b>——'
        + '不把 3G/4G/5G 三代堆在一起，因为 5G 客户同时也是移动客户，堆叠会重复计算。'
        + '「最新制式」逐年取该年披露过的最高制式（3G→4G→5G），所以 2001 年至今每年都有柱子，'
        + '不会因为某一代还没出现而出现空档；换代的加速度就体现在深色部分吃满柱子的速度上。'
        + '<b>橙色虚线是「5G 套餐客户」，与红柱的「5G 网络客户」是两个口径</b>，'
        + '2021–2023 年两者同时披露、相差 1.8 至 3.3 亿户；'
        + '把 2023 的套餐口径直接接到 2024 的网络口径上，会读出一次并不存在的负增长。'
        + (OMETA.definitions && OMETA.definitions.gen5GBasis
            ? '<b>口径提示：</b>' + OMETA.definitions.gen5GBasis : ''));

    setHTML('broadband-note',
        '宽带是产品更迭里「接棒流量」的那一环：<b>它的 ARPU 比移动 ARPU 更稳</b>，'
        + '因为家庭宽带是按户订阅、迁移成本高。千兆宽带与 FTTR 是同一批客户里的升级，'
        + '不是新增客户——看渗透而不是看总数。'
        + (OMETA.definitions && OMETA.definitions.broadbandBasis
            ? '<b>口径提示：</b>' + OMETA.definitions.broadbandBasis : ''));

    setHTML('iot-note',
        (iotY.length
            ? '物联网连接数从 ' + iotY[0] + ' 年的 ' + fx(OP[iotY[0]].iotConnections, 2) + ' 亿涨到 '
              + iotY[iotY.length - 1] + ' 年的 ' + fx(OP[iotY[iotY.length - 1]].iotConnections, 2) + ' 亿，'
              + '<b>已经是移动客户数的 '
              + (L.iotConnections && L.mobileSubs ? fx(L.iotConnections / L.mobileSubs, 1) : '—')
              + ' 倍。</b>'
            : '')
        + '但要注意：物联网卡的单卡 ARPU 远低于手机用户，连接数的增长与收入的增长不是同一个量级——'
        + '这是读运营商「连接数」时最容易被误导的地方。');

    setHTML('network-note',
        '网络规模与员工放在一起看：<b>每一轮制式换代都是先加基站、再加机架，人却基本不加</b>。'
        + '缺披露的年份留空不插值（早年年报未披露 5G/IDC 这类指标是自然的，因为业务还不存在）。');

    /* 口径缺口 */
    var FIELDS = [
        ['mobileSubs', '移动客户数'], ['netAddSubs', '净增客户数'],
        ['subs3G', '3G 客户数'], ['subs4G', '4G 客户数'],
        ['subs5G', '5G 网络客户数'], ['subs5GPackage', '5G 套餐客户数'],
        ['mou', 'MOU'], ['dou', 'DOU'], ['arpu', '移动 ARPU'],
        ['broadbandSubs', '有线宽带客户数'], ['homeArpu', '家庭客户综合 ARPU'],
        ['govEntSubs', '政企客户数'], ['iotConnections', '物联网卡连接数'],
        ['base5G', '5G 基站数'], ['idcRacks', 'IDC 标准机架'], ['employees', '员工总数']
    ];
    var allY = Object.keys(OP).sort();
    var items = FIELDS.map(function (p) {
        var ys = years(OP, p[0]);
        if (!ys.length) return '<b>' + p[1] + '</b>：数据源中无任何年份披露。';
        var missing = allY.filter(function (y) {
            return +y > +ys[0] && +y < +ys[ys.length - 1] && OP[y][p[0]] == null;
        });
        return '<b>' + p[1] + '</b>：披露 ' + ys[0] + '–' + ys[ys.length - 1] + '（' + ys.length + ' 年）'
            + (missing.length ? '，区间内缺 ' + missing.join('、') : '') + '。';
    });
    if (OMETA.gaps) {
        Object.keys(OMETA.gaps).forEach(function (k) { items.push('<b>' + k + '</b>：' + OMETA.gaps[k]); });
    }
    if (OMETA.definitions) {
        Object.keys(OMETA.definitions).forEach(function (k) {
            items.push('<b>' + k + '</b>：' + OMETA.definitions[k]);
        });
    }
    renderList('gaps-list', items);
  })();
}
</script>

<!-- 静态骨架逐字取自 company/page.css 与源页 <head> 内联 .note-generic/.gap-list；base.css 已全局引入不重复。 -->
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
.chart { width: 100%; height: 428px; }   /* 各图容器内联 height 覆盖此默认值 */
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px,1fr)); gap: 12px; margin-bottom: 16px; }
.note-generic {
    margin: 10px 0 0; padding: 12px 16px; background: #f6f7f9;
    border-left: 4px solid #b7b1c4; border-radius: 6px;
    font-size: 18px; color: #555; line-height: 1.75;
}
.gap-list { margin: 6px 0 0 18px; font-size: 18px; color: #555; line-height: 1.8; }
</style>

<!-- 动态节点（renderKpis/renderRows/renderList 用 innerHTML 注入，无 data-v）：非 scoped，.wrap 前缀收敛作用域；
     取值逐字取自 company/page.css 与源页内联 .gap-list b。 -->
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

