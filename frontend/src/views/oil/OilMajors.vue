<template>
  <div class="oil-majors">
    <LoadingNote v-if="loading" />
    <div v-if="error" id="error-msg" style="display:block">加载失败：{{ error }}（请确保 Flask 后端已启动）</div>
    <section class="chart-card" id="card-ptr" v-show="ready">
      <h2 class="chart-title">中石油证实原油储量瀑布图<span class="sub">深色 = 保留　浅色 = 增加　灰色斜线 = 减少 | 单位：百万桶</span></h2>
      <div ref="chartPtrEl" id="chart-ptr" class="chart-box"></div>
    </section>
    <section class="chart-card" id="card-cnc" v-show="ready">
      <h2 class="chart-title">中海油证实原油储量瀑布图<span class="sub">深色 = 保留　浅色 = 增加　灰色斜线 = 减少 | 单位：百万桶</span></h2>
      <div ref="chartCncEl" id="chart-cnc" class="chart-box"></div>
    </section>
    <section class="chart-card" id="card-compare" v-show="ready">
      <h2 class="chart-title">中石油 vs 中海油 证实原油储量对比（2000-2024）<span class="sub">数据来源：两家公司历年年报（SEC 标准）| 单位：百万桶</span></h2>
      <div ref="chartCompareEl" id="chart-compare" class="chart-box"></div>
    </section>
    <section class="chart-card" id="card-prod" v-show="ready">
      <h2 class="chart-title">中石油 vs 中海油 历年原油及液体产量<span class="sub">含原油、凝析油等石油液体 | 数据来源：两家公司历年年报 | 单位：百万桶</span></h2>
      <div ref="chartProdEl" id="chart-prod" class="chart-box"></div>
    </section>
  </div>
</template>

<script setup>
import LoadingNote from '../../components/LoadingNote.vue'
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { apiGet } from '../../api'
import { useChartPool } from '../../composables/useCharts'

// 逐字搬自 dashboard/subject/oil/china_oil_majors.html：4 张图的 option 与渲染逻辑原样保留，
// 仅取数改走统一 apiGet、容器改用组件 ref、resize/dispose 归拢到组件生命周期。图与数据一律不变。
const loading = ref(true)
const error = ref('')
const ready = ref(false)
const chartPtrEl = ref(null)
const chartCncEl = ref(null)
const chartCompareEl = ref(null)
const chartProdEl = ref(null)
const { charts } = useChartPool()

onMounted(async () => {
  try {
    // 源页 Promise.all 顺序：petrochina_reserves / cnooc_reserves / petrochina_production / cnooc_production
    const [ptr, cnc, ptrProd, cncProd] = await Promise.all([
      apiGet('/api/petrochina_reserves'),
      apiGet('/api/cnooc_reserves'),
      apiGet('/api/petrochina_production'),
      apiGet('/api/cnooc_production'),
    ])
    loading.value = false
    ready.value = true
    await nextTick()
    charts.push(renderWaterfall(chartPtrEl.value, '中石油', ptr, { base: '#c94a4a', gain: '#e88a8a', label: '#a03030' }))
    charts.push(renderWaterfall(chartCncEl.value, '中海油', cnc, { base: '#2a7ab5', gain: '#4fc3f7', label: '#1565c0' }))
    charts.push(renderCompare(chartCompareEl.value, ptr, cnc))
    charts.push(renderProduction(chartProdEl.value, ptrProd, cncProd))
  } catch (e) {
    loading.value = false
    error.value = e.message || String(e)
  }
})

/* ────── 通用瀑布图 ────── */
function renderWaterfall(el, company, data, colors) {
  const years = data.map(d => d.year);
  const oil   = data.map(d => d.oil);

  // 斜线纹理
  const patternCanvas = document.createElement('canvas');
  patternCanvas.width = 10; patternCanvas.height = 10;
  const pCtx = patternCanvas.getContext('2d');
  pCtx.fillStyle = '#f0f0f0'; pCtx.fillRect(0, 0, 10, 10);
  pCtx.strokeStyle = '#999'; pCtx.lineWidth = 1.5;
  pCtx.beginPath(); pCtx.moveTo(0, 10); pCtx.lineTo(10, 0); pCtx.stroke();
  pCtx.beginPath(); pCtx.moveTo(-2, 2);  pCtx.lineTo(2, -2);  pCtx.stroke();
  pCtx.beginPath(); pCtx.moveTo(8, 12);  pCtx.lineTo(12, 8);  pCtx.stroke();
  const stripeImg = new Image();
  stripeImg.src = patternCanvas.toDataURL();
  const stripePattern = { image: stripeImg, repeat: 'repeat' };

  const COLOR_BASE = colors.base;
  const COLOR_GAIN = colors.gain;

  const baseData = [], gainData = [], lossData = [];
  oil.forEach((v, i) => {
    if (v == null) { baseData.push(null); gainData.push(null); lossData.push(null); return; }
    const prev = i > 0 ? oil[i - 1] : null;
    if (prev == null) { baseData.push(v); gainData.push(0); lossData.push(0); }
    else {
      baseData.push(Math.min(prev, v));
      gainData.push(Math.max(0, v - prev));
      lossData.push(Math.max(0, prev - v));
    }
  });

  const chart = echarts.init(el);
  chart.setOption({
    backgroundColor: '#ffffff',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      textStyle: { fontSize: 18 },
      position: (point, params, dom, rect, size) => {
        const [x] = point;
        const tw = size.contentSize[0];
        const vw = size.viewSize[0];
        return [x + 16 + tw > vw ? x - tw - 16 : x + 16, 16];
      },
      formatter: params => {
        const yr = +params[0].axisValue;
        const d  = data.find(d => d.year === yr);
        const dp = data.find(d => d.year === yr - 1);
        if (!d) return '';
        const pct = dp && dp.oil != null && d.oil != null
          ? (Math.abs(d.oil - dp.oil) / Math.max(d.oil, dp.oil) * 100).toFixed(1)
          : null;
        return `<b>${yr} 年 · ${company}</b><br>
                证实储量：<b>${d.oil.toLocaleString()}</b> 百万桶<br>
                ${pct !== null ? `变化占比：<b>${pct}%</b>` : '初始值'}`;
      }
    },
    grid: { left: 64, right: 20, top: 24, bottom: 32 },
    xAxis: {
      type: 'category', data: years, boundaryGap: true,
      axisLabel: { color: '#555', fontSize: 18 },
      axisLine: { lineStyle: { color: '#bbb' } }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#555', fontSize: 18, formatter: v => (v/1000).toFixed(0) + 'k' },
      splitLine: { lineStyle: { color: '#e8e8e8' } },
      min: 0
    },
    series: [
      {
        name: '基础', type: 'bar', stack: 'total',
        data: baseData.map(v => ({ value: v, itemStyle: { color: COLOR_BASE } })),
        barMaxWidth: 30
      },
      {
        name: '增加', type: 'bar', stack: 'total',
        data: gainData.map(v => ({ value: v, itemStyle: { color: COLOR_GAIN } })),
        barMaxWidth: 30,
        labelLayout: { hideOverlap: true },
        label: {
          show: true, position: 'top', fontSize: 18, fontWeight: 'bold', color: colors.label,
          formatter: p => p.value > 0 ? '+' + p.value.toLocaleString() : ''
        }
      },
      {
        name: '减少', type: 'bar', stack: 'total',
        data: lossData.map(v => ({ value: v, itemStyle: { color: stripePattern } })),
        barMaxWidth: 30,
        labelLayout: { hideOverlap: true },
        label: {
          show: true, position: 'top', fontSize: 18, fontWeight: 'bold', color: '#666666',
          formatter: p => p.value > 0 ? '-' + p.value.toLocaleString() : ''
        }
      }
    ]
  });

  return chart;
}

/* ────── 图 2：中石油 vs 中海油 折线对比 ────── */
function renderCompare(el, ptrData, cncData) {
  const allYears = Array.from(new Set([
    ...ptrData.map(d => d.year),
    ...cncData.map(d => d.year)
  ])).sort();

  const ptrMap = Object.fromEntries(ptrData.map(d => [d.year, d]));
  const cncMap = Object.fromEntries(cncData.map(d => [d.year, d]));

  const ptrOil = allYears.map(y => ptrMap[y] ? ptrMap[y].oil : null);
  const cncOil = allYears.map(y => cncMap[y] ? cncMap[y].oil : null);

  const COLOR_PTR = '#c94a4a';
  const COLOR_CNC = '#2a7ab5';

  const chart = echarts.init(el);
  chart.setOption({
    backgroundColor: '#ffffff',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross', lineStyle: { width: 2 } },
      textStyle: { fontSize: 18 },
      position: (point, params, dom, rect, size) => {
        const [x] = point;
        const tw = size.contentSize[0];
        const vw = size.viewSize[0];
        return [x + 16 + tw > vw ? x - tw - 16 : x + 16, 16];
      },
      formatter: params => {
        const yr = +params[0].axisValue;
        const p = ptrMap[yr];
        const c = cncMap[yr];
        let html = `<b>${yr} 年</b><br>`;
        if (p && p.oil != null) {
          const ratio = c && c.oil != null ? (p.oil / c.oil).toFixed(1) : null;
          html += `<span style="color:${COLOR_PTR}">■</span> 中石油：<b>${p.oil.toLocaleString()}</b> 百万桶`;
          if (ratio) html += `　（${ratio}× 中海油）`;
          html += '<br>';
        }
        if (c && c.oil != null) {
          html += `<span style="color:${COLOR_CNC}">■</span> 中海油：<b>${c.oil.toLocaleString()}</b> 百万桶<br>`;
        }
        return html;
      }
    },
    legend: {
      data: ['中石油', '中海油'],
      top: 4,
      textStyle: { fontSize: 18, color: '#333' }
    },
    grid: { left: 64, right: 20, top: 40, bottom: 32 },
    xAxis: {
      type: 'category', data: allYears, boundaryGap: false,
      axisLabel: { color: '#555', fontSize: 18 },
      axisLine: { lineStyle: { color: '#bbb' } }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#555', fontSize: 18, formatter: v => (v/1000).toFixed(0) + 'k' },
      splitLine: { lineStyle: { color: '#e8e8e8' } },
      min: 0
    },
    series: [
      {
        name: '中石油', type: 'line',
        data: ptrOil, smooth: false,
        symbol: 'circle', symbolSize: 6, connectNulls: false,
        lineStyle: { color: COLOR_PTR, width: 3 },
        itemStyle: { color: COLOR_PTR },
        areaStyle: { color: 'rgba(201, 74, 74, 0.08)' }
      },
      {
        name: '中海油', type: 'line',
        data: cncOil, smooth: false,
        symbol: 'circle', symbolSize: 6, connectNulls: false,
        lineStyle: { color: COLOR_CNC, width: 3 },
        itemStyle: { color: COLOR_CNC },
        areaStyle: { color: 'rgba(42, 122, 181, 0.08)' }
      }
    ]
  });

  return chart;
}

/* ────── 图 3：中石油 vs 中海油 历年原油产量 ────── */
function renderProduction(el, ptrData, cncData) {
  const allYears = Array.from(new Set([
    ...ptrData.map(d => d.year),
    ...cncData.map(d => d.year)
  ])).sort();

  const ptrMap = Object.fromEntries(ptrData.map(d => [d.year, d]));
  const cncMap = Object.fromEntries(cncData.map(d => [d.year, d]));

  const ptrOil = allYears.map(y => ptrMap[y] ? ptrMap[y].oil : null);
  const cncOil = allYears.map(y => cncMap[y] ? cncMap[y].oil : null);

  const COLOR_PTR = '#c94a4a';
  const COLOR_CNC = '#2a7ab5';

  const chart = echarts.init(el);
  chart.setOption({
    backgroundColor: '#ffffff',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross', lineStyle: { width: 2 } },
      textStyle: { fontSize: 18 },
      position: (point, params, dom, rect, size) => {
        const [x] = point;
        const tw = size.contentSize[0];
        const vw = size.viewSize[0];
        return [x + 16 + tw > vw ? x - tw - 16 : x + 16, 16];
      },
      formatter: params => {
        const yr = +params[0].axisValue;
        const p = ptrMap[yr];
        const c = cncMap[yr];
        let html = `<b>${yr} 年</b><br>`;
        if (p && p.oil != null) {
          html += `<span style="color:${COLOR_PTR}">■</span> 中石油：<b>${p.oil.toLocaleString()}</b> 百万桶<br>`;
        }
        if (c && c.oil != null) {
          html += `<span style="color:${COLOR_CNC}">■</span> 中海油：<b>${c.oil.toLocaleString()}</b> 百万桶<br>`;
        }
        return html;
      }
    },
    legend: {
      data: ['中石油', '中海油'],
      top: 4,
      textStyle: { fontSize: 18, color: '#333' }
    },
    grid: { left: 64, right: 20, top: 40, bottom: 32 },
    xAxis: {
      type: 'category', data: allYears, boundaryGap: false,
      axisLabel: { color: '#555', fontSize: 18 },
      axisLine: { lineStyle: { color: '#bbb' } }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#555', fontSize: 18 },
      splitLine: { lineStyle: { color: '#e8e8e8' } },
      min: 0
    },
    series: [
      {
        name: '中石油', type: 'line',
        data: ptrOil, smooth: false,
        symbol: 'circle', symbolSize: 6, connectNulls: false,
        lineStyle: { color: COLOR_PTR, width: 3 },
        itemStyle: { color: COLOR_PTR }
      },
      {
        name: '中海油', type: 'line',
        data: cncOil, smooth: false,
        symbol: 'circle', symbolSize: 6, connectNulls: false,
        lineStyle: { color: COLOR_CNC, width: 3 },
        itemStyle: { color: COLOR_CNC }
      }
    ]
  });

  return chart;
}
</script>

<style scoped>
/* 源页 <style> 中本页元素依赖的布局规则；.chart-card 的圆角/投影/白底、.chart-title、
   #loading / #error-msg 已在 common/base.css 全局定义，这里不重复。
   本页所有节点都是模板里的静态元素（能拿到 scoped 属性），故用 scoped。 */
.oil-majors {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.chart-card {
  /* 圆角/投影/白底见 common/base.css，这里只管布局 */
  width: 100%;
  max-width: 1800px;
  margin: 0 auto;
  flex-shrink: 0;
}
.chart-box {
  width: 100%;
  height: 50vh;
}
</style>
