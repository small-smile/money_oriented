<template>
  <div ref="rootEl">
    <LoadingNote v-if="loading" />
    <div v-if="error" id="error-msg" style="display:block">加载失败：{{ error }}（请确保 Flask 后端已启动）</div>

    <div id="cards" style="display:none">
      <!-- Card 0: 全球总产量与回归趋势 -->
      <section class="card">
        <h2 class="chart-title">全球石油总产量与回归趋势（1965-2024）<span class="sub" id="total-sub">—</span></h2>
        <div id="chart-total"></div>
      </section>

      <!-- Card 1: 各地区产量 / 占比 —— 卡片堆叠，页签切换；外层 scroller/stage 做吸顶变比例 -->
      <div class="pin-scroller" id="region-scroller">
        <div class="pin-stage" id="region-stage">
          <div class="stack-tabs" id="region-tabs"></div>
          <div class="card-stack" id="region-stack">
            <div class="stack-card front" data-name="各地区石油产量" data-color="#5470c6">
              <h2 class="chart-title">各地区石油产量（堆叠面积图，1965-2024）<span class="sub" id="region-abs-sub">悬浮到某层查看该地区独立走势</span></h2>
              <div id="chart-region-abs"></div>
              <div class="stack-detail-wrap">
                <div id="region-detail-title-abs" class="stack-detail-title">—</div>
                <div id="chart-region-detail-abs" class="stack-detail-chart"></div>
              </div>
              <div class="card-peek">各地区石油产量 · 点击切到前面</div>
            </div>
            <div class="stack-card back" data-name="各地区产量占比" data-color="#ee6666">
              <h2 class="chart-title">各地区石油产量占比（百分比堆叠，1965-2024）<span class="sub">悬浮到某层查看该地区独立走势</span></h2>
              <div id="chart-region-pct"></div>
              <div class="stack-detail-wrap">
                <div id="region-detail-title-pct" class="stack-detail-title">—</div>
                <div id="chart-region-detail-pct" class="stack-detail-chart"></div>
              </div>
              <div class="card-peek">各地区石油产量占比 · 点击切到前面</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Card 2: 各国产量 / 各国产量占比 —— 卡片堆叠；同样吸顶变比例 -->
      <div class="pin-scroller" id="country-scroller">
        <div class="pin-stage" id="country-stage">
          <div class="stack-tabs" id="country-tabs"></div>
          <div class="card-stack" id="country-stack">
            <div class="stack-card front" data-name="各国石油产量" data-color="#5470c6">
              <h2 class="chart-title">各国石油产量堆叠图（1965-2024）<span class="sub">悬浮到某层切换底部详情 | 同洲同色 | 单位：千桶/日</span></h2>
              <div class="stack-wrap">
                <div id="chart-country-stack" class="stack-main"></div>
                <div class="stack-detail-wrap">
                  <div id="country-detail-title" class="stack-detail-title">—</div>
                  <div id="chart-country-detail" class="stack-detail-chart"></div>
                </div>
              </div>
              <div class="card-peek">各国石油产量 · 点击切到前面</div>
            </div>
            <div class="stack-card back" data-name="各国产量占比" data-color="#ee6666">
              <h2 class="chart-title">各国石油产量占全球比例堆叠图（1965-2024）<span class="sub">悬浮到某层查看该国独立走势 | 同洲同色</span></h2>
              <div class="stack-wrap">
                <div id="chart-percent-stack" class="stack-main"></div>
                <div class="stack-detail-wrap">
                  <div id="percent-detail-title" class="stack-detail-title">—</div>
                  <div id="chart-percent-detail" class="stack-detail-chart"></div>
                </div>
              </div>
              <div class="card-peek">各国石油产量占比 · 点击切到前面</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import LoadingNote from '../../components/LoadingNote.vue'
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { apiGet } from '../../api'

// 逐字迁移自 dashboard/subject/oil/region_production.html：所有 ECharts option、HTML 悬浮图例
// （.stack-legend / buildStackLegend）、卡片堆叠页签、吸顶变比例逻辑原样保留；仅把取数改走统一
// apiGet、把 document.getElementById 改成组件根 ref 下的 querySelector，并登记 window 监听 / 定时器 /
// ResizeObserver 以便 onBeforeUnmount 统一清理。图与数据一律不变。
const loading = ref(true)
const error = ref('')
const rootEl = ref(null)

// 所有元素查找都走组件根 ref（原页用 document.getElementById）；根卸载后返回 null，防止在途回调报错
const $id = sel => (rootEl.value ? rootEl.value.querySelector(sel) : null)

// 统一登记 window 监听 / ResizeObserver / setInterval，onBeforeUnmount 时逐个撤销
const cleanups = []
function onWin(type, handler, opts) {
  window.addEventListener(type, handler, opts)
  cleanups.push(() => window.removeEventListener(type, handler, opts))
}

const REGION_COLORS = {
  'North America':      '#5470c6',
  'CIS':                '#fac858',
  'Middle East':        '#e6a23c',
  'S. & Cent. America': '#91cc75',
  'Africa':             '#fc8452',
  'Asia Pacific':       '#5ab9c1',
  'Europe':             '#9a60b4'
}

// Shared data
let _years, _regionData, _regions, _regionPctData
let _regionTotals, _totalFit
let _countryAll, _countryMeta, _sortedCountries
let _pctData, _sortedByPct

// Chart handles
let totalChart = null
let regionAbsChart = null, regionPctChart = null
let regionDetailAbsChart = null, regionDetailPctChart = null
let currentRegion = null
let countryStackChart = null, countryDetailChart = null
let currentCountry = null
let percentStackChart = null, percentDetailChart = null
let currentPercentCountry = null

// 对 ln(y) 做最小二乘线性回归；返回 CAGR = exp(slope)-1, R², 拟合区间
function fitLogLinear(years, values) {
  const pts = []
  for (let i = 0; i < years.length; i++) {
    const y = +years[i]
    const v = values[i]
    if (v != null && v > 0) pts.push([y, Math.log(v)])
  }
  if (pts.length < 2) return null
  const n = pts.length
  const mx = pts.reduce((s, p) => s + p[0], 0) / n
  const my = pts.reduce((s, p) => s + p[1], 0) / n
  let num = 0, denX = 0, denY = 0
  for (const [x, y] of pts) {
    num  += (x - mx) * (y - my)
    denX += (x - mx) ** 2
    denY += (y - my) ** 2
  }
  const slope = num / denX
  const intercept = my - slope * mx
  const r2 = denY > 0 ? (num * num) / (denX * denY) : 1
  return { slope, intercept, cagr: Math.exp(slope) - 1, r2, first: pts[0][0], last: pts[pts.length - 1][0], n }
}

onMounted(async () => {
  try {
    const d = await apiGet('/api/production_region')
    _years           = d.years
    _regionData      = d.region_data
    _countryAll      = d.country_all_data
    _countryMeta     = d.country_meta
    _sortedCountries = d.sorted_countries

    // 统一排序：产量大的在下（堆叠底部），小的在上；序列顺序 = 末年值降序
    _regions = Object.keys(_regionData).sort((a, b) => {
      const va = _regionData[a][_regionData[a].length - 1] || 0
      const vb = _regionData[b][_regionData[b].length - 1] || 0
      return vb - va
    })
    const regionTotals = _years.map((_, yi) =>
      _regions.reduce((s, r) => s + (_regionData[r][yi] || 0), 0)
    )
    _regionTotals = regionTotals

    // 总产量回归增速（log-linear 拟合）
    const totalFit = fitLogLinear(_years, regionTotals)
    _totalFit = totalFit
    if (totalFit) {
      $id('#region-abs-sub').textContent =
        `全球总产量回归年增速 ${(totalFit.cagr * 100).toFixed(2)}% (${totalFit.first}-${totalFit.last}, R²=${totalFit.r2.toFixed(3)}) | 悬浮到某层查看该地区独立走势`
    }

    _regionPctData = {}
    _regions.forEach(r => {
      _regionPctData[r] = _regionData[r].map((v, yi) =>
        regionTotals[yi] > 0 ? parseFloat(((v / regionTotals[yi]) * 100).toFixed(2)) : 0
      )
    })

    // 各国：与地区统一——末年产量降序（产量大的在堆叠底部）
    _sortedCountries = [..._sortedCountries].sort((a, b) => {
      const va = _countryAll[a][_countryAll[a].length - 1] || 0
      const vb = _countryAll[b][_countryAll[b].length - 1] || 0
      return vb - va
    })

    // Country percent: precompute
    const countryTotals = _years.map((_, yi) =>
      _sortedCountries.reduce((s, c) => s + (_countryAll[c][yi] || 0), 0)
    )
    _pctData = {}
    const pctMeta = {}
    _sortedCountries.forEach(c => {
      const pcts = _countryAll[c].map((v, yi) =>
        countryTotals[yi] > 0 ? parseFloat(((v || 0) / countryTotals[yi] * 100).toFixed(3)) : 0
      )
      _pctData[c] = pcts
      const first = pcts.find(v => v > 0) ?? 0
      const last  = pcts[pcts.length - 1]
      pctMeta[c] = { pctChange: parseFloat((last - first).toFixed(2)), pctLast: last }
    })
    // 与绝对值堆叠同序：末年占比降序（占比大的在底部）
    _sortedByPct = [..._sortedCountries].sort((a, b) => pctMeta[b].pctLast - pctMeta[a].pctLast)
    window._pctMeta = pctMeta

    loading.value = false
    $id('#cards').style.display = 'block'

    initTotal()
    initRegion()
    initCountry()
    initPercent()
    initRegionStack()    // 页签宽度依赖可见布局，必须在 #cards 显示之后
    initCountryStack()

    onWin('resize', () => {
      [totalChart,
       regionAbsChart, regionPctChart, regionDetailAbsChart, regionDetailPctChart,
       countryStackChart, countryDetailChart,
       percentStackChart, percentDetailChart].forEach(c => c && c.resize())
    })

    initPinnedRatio('region-scroller', 'region-stage', [
      ['chart-region-abs', 'chart-region-detail-abs'],
      ['chart-region-pct', 'chart-region-detail-pct']
    ])
    initPinnedRatio('country-scroller', 'country-stage', [
      ['chart-country-stack', 'chart-country-detail'],
      ['chart-percent-stack', 'chart-percent-detail']
    ])
  } catch (e) {
    loading.value = false
    error.value = e.message || String(e)
  }
})

onBeforeUnmount(() => {
  cleanups.forEach(fn => { try { fn() } catch (_) {} })
  cleanups.length = 0
  ;[totalChart,
    regionAbsChart, regionPctChart, regionDetailAbsChart, regionDetailPctChart,
    countryStackChart, countryDetailChart,
    percentStackChart, percentDetailChart].forEach(c => { try { c && c.dispose() } catch (_) {} })
})

// ============================================================
// Card 0: 全球总产量 + log-linear 回归
// ============================================================
function initTotal() {
  totalChart = echarts.init($id('#chart-total'))

  // 拟合值：ln(y) = a + b·year  →  y_hat = exp(a + b·year)
  const fitLine = _totalFit
    ? _years.map(y => parseFloat(Math.exp(_totalFit.intercept + _totalFit.slope * (+y)).toFixed(1)))
    : []

  if (_totalFit) {
    $id('#total-sub').textContent =
      `回归年增速 ${(_totalFit.cagr * 100).toFixed(2)}%（${_totalFit.first}-${_totalFit.last}，`
      + `R²=${_totalFit.r2.toFixed(3)}，n=${_totalFit.n}）| 蓝实线=实际，红虚线=ln(y)=a+b·t 拟合 | 单位：千桶/日`
  }

  totalChart.setOption({
    backgroundColor: '#ffffff',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross', lineStyle: { width: 2 } },
      textStyle: { fontSize: 18 },
      formatter: params => {
        const year = params[0].axisValue
        const act = params.find(p => p.seriesName === '实际总产量')
        const fit = params.find(p => p.seriesName === '回归趋势')
        let html = `<b>${year} 年</b><br>`
        if (act) {
          html += `${act.marker}实际: <b>${Math.round(act.value).toLocaleString()}</b>`
          const i = act.dataIndex
          if (i > 0 && _regionTotals[i - 1] > 0) {
            const yoy = (_regionTotals[i] / _regionTotals[i - 1] - 1) * 100
            html += `　同比 ${yoy >= 0 ? '+' : ''}${yoy.toFixed(1)}%`
          }
          html += '<br>'
        }
        if (fit) html += `${fit.marker}趋势: ${Math.round(fit.value).toLocaleString()}<br>`
        if (act && fit && fit.value > 0) {
          const dev = (act.value / fit.value - 1) * 100
          html += `<hr style="margin:3px 0;border-color:#ddd">偏离趋势: <b>${dev >= 0 ? '+' : ''}${dev.toFixed(1)}%</b>`
        }
        return html
      }
    },

    legend: { data: ['实际总产量', '回归趋势'], top: 8, textStyle: { color: '#333', fontSize: 18 } },
    grid: { left: 72, right: 120, top: 46, bottom: 30 },
    toolbox: { feature: { saveAsImage: {}, dataZoom: { yAxisIndex: 'none' }, restore: {} }, right: 8, top: 4 },
    // 不用 inside dataZoom：只要存在 inside，ECharts 就会 preventDefault 滚轮事件，页面无法下滚
    xAxis: {
      type: 'category', data: _years, boundaryGap: false,
      axisLabel: { color: '#555', fontSize: 18 }, axisLine: { lineStyle: { color: '#bbb' } }
    },
    yAxis: {
      type: 'value', name: '千桶/日',
      nameTextStyle: { color: '#555', fontSize: 18, align: 'right' },
      axisLabel: { color: '#555', fontSize: 18, formatter: v => (v/1000).toFixed(0) + 'k' },
      splitLine: { lineStyle: { color: '#e8e8e8' } }
    },
    series: [
      {
        name: '实际总产量', type: 'line', data: _regionTotals,
        smooth: true, showSymbol: false, z: 3,
        lineStyle: { color: '#5470c6', width: 2.5 },
        itemStyle: { color: '#5470c6' },
        areaStyle: { color: '#5470c6', opacity: 0.12 }
      },
      {
        name: '回归趋势', type: 'line', data: fitLine,
        smooth: false, showSymbol: false, z: 4,
        lineStyle: { color: '#ee6666', width: 2, type: 'dashed' },
        itemStyle: { color: '#ee6666' },
        // 把回归增速直接标在趋势线末端，不用去看副标题
        endLabel: {
          show: true, color: '#ee6666', fontSize: 18, fontWeight: 'bold',
          formatter: () => _totalFit
            ? `${_totalFit.cagr >= 0 ? '+' : ''}${(_totalFit.cagr * 100).toFixed(2)}%/年`
            : ''
        }
      }
    ]
  }, true)
}

// ============================================================
// Tab 1: 地区产量 (region_production.html 原内容)
// ============================================================
function buildRegionOption(dataMap, isAbs) {
  const series = _regions.map(r => ({
    name: r, type: 'line', stack: 'total',
    areaStyle: { opacity: 0.75 }, emphasis: { focus: 'series' },
    smooth: true, showSymbol: false,
    data: dataMap[r], color: REGION_COLORS[r]
  }))
  return {
    backgroundColor: '#ffffff',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross', lineStyle: { width: 2 } },
      position: [12, 12],
      textStyle: { fontSize: 18 },
      formatter: params => {
        const year = params[0].axisValue
        // 找出当前悬浮地区并置顶
        const cur = params.find(p => p.seriesName === currentRegion)
        const others = params.filter(p => p.seriesName !== currentRegion).reverse()
        const total = params.reduce((s, p) => s + (p.value || 0), 0)
        let html = `<b>${year} 年</b>`
        if (cur) {
          const share = total > 0 ? (cur.value / total * 100).toFixed(1) : '0.0'
          const label = isAbs
            ? `${(cur.value || 0).toLocaleString()}（占 ${share}%）`
            : `${(cur.value || 0).toFixed(1)}%`
          html += `<div style="margin:4px 0;padding:6px 8px;background:#fff6d6;border-left:3px solid #f0a500;border-radius:2px;font-size:18px;">
                                ${cur.marker}<b>${cur.seriesName}</b>：<b>${label}</b>
                             </div>`
        }
        others.forEach(p => {
          const val = isAbs
            ? (p.value || 0).toLocaleString()
            : (p.value || 0).toFixed(1) + '%'
          html += `${p.marker}${p.seriesName}: ${val}<br>`
        })
        if (isAbs) html += `<hr style="margin:3px 0;border-color:#ddd">合计: <b>${total.toLocaleString()}</b>`
        return html
      }
    },

    legend: {
      data: _regions, top: 8, type: 'scroll',
      textStyle: { color: '#333', fontSize: 18 },
      formatter: name => {
        const d = dataMap[name]
        const change = d[d.length - 1] - d[0]
        const sign = change >= 0 ? '+' : ''
        return isAbs
          ? `${name}  (${sign}${Math.round(change).toLocaleString()})`
          : `${name}  (${sign}${change.toFixed(1)}%)`
      }
    },
    grid: { left: 72, right: 96, top: 46, bottom: 24 },
    toolbox: { feature: { saveAsImage: {}, dataZoom: { yAxisIndex: 'none' }, restore: {} }, right: 8, top: 4 },
    // 不用 inside dataZoom：只要存在 inside，ECharts 就会 preventDefault 滚轮事件，页面无法下滚
    xAxis: {
      type: 'category', data: _years, boundaryGap: false,
      axisLabel: { color: '#555', fontSize: 18 }, axisLine: { lineStyle: { color: '#bbb' } }
    },
    yAxis: isAbs ? {
      type: 'value', name: '千桶/日',
      nameTextStyle: { color: '#555', fontSize: 18, align: 'right' },
      axisLabel: { color: '#555', fontSize: 18, formatter: v => (v/1000).toFixed(0) + 'k' },
      splitLine: { lineStyle: { color: '#e8e8e8' } }
    } : {
      type: 'value', name: '%', min: 0, max: 100,
      nameTextStyle: { color: '#555', fontSize: 18, align: 'right' },
      axisLabel: { color: '#555', fontSize: 18, formatter: v => v + '%' },
      splitLine: { lineStyle: { color: '#e8e8e8' } }
    },
    series
  }
}

function bindRegionHover(chartDom, chart, dataMap, onHit) {
  let current = null
  chartDom.onmousemove = e => {
    const rect = chartDom.getBoundingClientRect()
    const px = e.clientX - rect.left
    const py = e.clientY - rect.top
    const dataCoord = chart.convertFromPixel('grid', [px, py])
    if (!dataCoord) return
    const xi = Math.round(dataCoord[0])
    if (xi < 0 || xi >= _years.length) return
    let cum = 0, hit = null
    for (const r of _regions) {
      const val = dataMap[r][xi] || 0
      const prevCum = cum
      cum += val
      const botPx = chart.convertToPixel('grid', [xi, prevCum])[1]
      const topPx = chart.convertToPixel('grid', [xi, cum])[1]
      if (py >= topPx && py <= botPx) { hit = r; break }
    }
    if (hit && hit !== current) {
      current = hit
      currentRegion = hit   // 用于两图 tooltip 高亮当前地区
      onHit(hit)
    }
  }
}

function initRegion() {
  regionAbsChart = echarts.init($id('#chart-region-abs'))
  regionPctChart = echarts.init($id('#chart-region-pct'))
  regionDetailAbsChart = echarts.init($id('#chart-region-detail-abs'))
  regionDetailPctChart = echarts.init($id('#chart-region-detail-pct'))
  regionAbsChart.setOption(buildRegionOption(_regionData, true), true)
  regionPctChart.setOption(buildRegionOption(_regionPctData, false), true)
  bindRegionHover($id('#chart-region-abs'), regionAbsChart, _regionData,
    r => showRegionDetailInto(r, 'region-detail-title-abs', regionDetailAbsChart, false))
  bindRegionHover($id('#chart-region-pct'), regionPctChart, _regionPctData,
    r => showRegionDetailInto(r, 'region-detail-title-pct', regionDetailPctChart, true))
  currentRegion = _regions[0]
  showRegionDetailInto(currentRegion, 'region-detail-title-abs', regionDetailAbsChart, false)
  showRegionDetailInto(currentRegion, 'region-detail-title-pct', regionDetailPctChart, true)
}

// === 卡片堆叠切换：页签是主入口，点后卡露出的那条也能翻到前面（同 price_history.html）===
function initCardStack(stackId, tabBarId, chartOf) {
  const stackEl = $id('#' + stackId)
  const tabBar = $id('#' + tabBarId)
  const cards = Array.from(stackEl.querySelectorAll(':scope > .stack-card'))

  const slider = document.createElement('span')
  slider.className = 'tab-slider'
  tabBar.appendChild(slider)

  const tabs = cards.map((card, i) => {
    const tab = document.createElement('button')
    tab.type = 'button'
    tab.className = 'stack-tab'
    tab.innerHTML = '<span class="tab-dot" style="color:' + card.dataset.color + '"></span>'
      + '<span>' + card.dataset.name + '</span>'
    tab.addEventListener('click', () => activate(i))
    tabBar.appendChild(tab)
    return tab
  })

  function moveSlider(tab) {
    slider.style.width = tab.offsetWidth + 'px'
    slider.style.transform = 'translateX(' + tab.offsetLeft + 'px)'
  }

  function activate(idx) {
    cards.forEach((c, i) => {
      c.classList.toggle('front', i === idx)
      c.classList.toggle('back', i !== idx)
    })
    tabs.forEach((t, i) => t.classList.toggle('active', i === idx))
    moveSlider(tabs[idx])
    // 翻到前面后重新量一次尺寸，避免坐标换算偏移
    Object.entries(chartOf).forEach(([divId, charts]) => {
      if (cards[idx].querySelector('#' + divId)) {
        charts.forEach(c => c && c.resize())
      }
    })
    // 前后卡露出的那条一有一无，可用高度跟着变；让吸顶比例按当前进度重算一遍
    window.dispatchEvent(new Event('pin-ratio-refresh'))
  }

  cards.forEach((card, i) => card.addEventListener('click', () => {
    if (card.classList.contains('front')) return   // 前卡的点击留给图表本身
    activate(i)
  }))

  activate(cards.findIndex(c => c.classList.contains('front')))
  onWin('resize', () => moveSlider(tabBar.querySelector('.stack-tab.active')))
  if (document.fonts) document.fonts.ready.then(
    () => moveSlider(tabBar.querySelector('.stack-tab.active')))
}

function initRegionStack() {
  initCardStack('region-stack', 'region-tabs', {
    'chart-region-abs': [regionAbsChart, regionDetailAbsChart],
    'chart-region-pct': [regionPctChart, regionDetailPctChart]
  })
}

function initCountryStack() {
  initCardStack('country-stack', 'country-tabs', {
    'chart-country-stack': [countryStackChart, countryDetailChart],
    'chart-percent-stack': [percentStackChart, percentDetailChart]
  })
}

function showRegionDetailInto(region, titleId, chart, isPct) {
  $id('#' + titleId).textContent = isPct
    ? `${region} — 独立占比走势（占全球 %）`
    : `${region} — 独立产量走势（千桶/日）`
  const color = REGION_COLORS[region] || '#5470c6'
  chart.setOption({
    backgroundColor: '#fafafa',
    tooltip: {
      trigger: 'axis', axisPointer: { type: 'cross', lineStyle: { width: 1 } },
      textStyle: { fontSize: 18 },
      valueFormatter: v => isPct ? (v || 0).toFixed(2) + '%' : Math.round(v || 0).toLocaleString()
    },
    grid: { left: 72, right: 96, top: 24, bottom: 24 },
    // 不用 inside dataZoom：只要存在 inside，ECharts 就会 preventDefault 滚轮事件，页面无法下滚
    xAxis: {
      type: 'category', data: _years, boundaryGap: false,
      axisLabel: { color: '#555', fontSize: 18 }, axisLine: { lineStyle: { color: '#bbb' } }
    },
    yAxis: isPct ? {
      type: 'value', min: 0,
      axisLabel: { color: '#555', fontSize: 18, formatter: v => v + '%' },
      splitLine: { lineStyle: { color: '#eee' } }
    } : {
      type: 'value',
      axisLabel: { color: '#555', fontSize: 18, formatter: v => (v/1000).toFixed(0) + 'k' },
      splitLine: { lineStyle: { color: '#eee' } }
    },
    series: [{
      type: 'line', data: (isPct ? _regionPctData : _regionData)[region],
      smooth: true, showSymbol: false,
      areaStyle: { color, opacity: 0.15 },
      lineStyle: { color, width: 2 }, itemStyle: { color }
    }]
  }, true)
}

// ============================================================
// Tab 2: 各国产量 (country_production_stack.html 原内容)
// ============================================================
function initCountry() {
  countryStackChart = echarts.init($id('#chart-country-stack'))

  const series = _sortedCountries.map(c => {
    const baseColor = REGION_COLORS[_countryMeta[c].continent] || '#888'
    return {
      name: c, type: 'line', stack: 'total',
      areaStyle: { opacity: 0.65 },
      data: _countryAll[c],
      smooth: true, showSymbol: false, connectNulls: true,
      lineStyle: { width: 0.5 },
      itemStyle: { color: baseColor },
      emphasis: { focus: 'series', areaStyle: { opacity: 1 } }
    }
  })

  // —— 图例见 initCountry 末尾的 buildStackLegend 调用 ——
  const RESERVE = 150   // 主图右侧给图例起始列留出的宽度（与 grid.right 对齐）

  countryStackChart.setOption({
    backgroundColor: '#ffffff',
    tooltip: {
      trigger: 'axis',
      position: [12, 12],
      axisPointer: { type: 'cross', lineStyle: { width: 2 } },
      textStyle: { fontSize: 18 },
      formatter: params => {
        let html = `<b>${params[0].axisValue} 年</b>`
        const items = params.filter(p => p.value != null && p.value > 0)
                            .sort((a, b) => b.value - a.value)
        const cur = items.find(p => p.seriesName === currentCountry)
        if (cur) {
          const rank = items.indexOf(cur) + 1
          html += `<div style="margin:4px 0;padding:6px 8px;background:#fff6d6;border-left:3px solid #f0a500;border-radius:2px;font-size:18px;">
                                ${cur.marker}<b>${cur.seriesName}</b>：<b>${cur.value.toLocaleString()}</b>　千桶/日
                                <span style="color:#888;font-size:18px;">（当年第 ${rank} 名 / 共 ${items.length}）</span>
                             </div>`
        }
        items.filter(p => p.seriesName !== currentCountry)
             .slice(0, 8)
             .forEach(p => {
               html += `${p.marker}${p.seriesName}: <b>${p.value.toLocaleString()}</b><br>`
             })
        if (items.length > 9) html += `…（共 ${items.length} 条）`
        return html
      }
    },

    legend: { show: false, data: _sortedCountries, selectedMode: 'multiple' },
    grid: { left: 72, right: RESERVE, top: 40, bottom: 40 },
    toolbox: { feature: { saveAsImage: {}, dataZoom: { yAxisIndex: 'none' }, restore: {} }, right: 10, top: 8 },
    // 不加 dataZoom：年度点一次画全，看局部用 toolbox 的框选缩放
    xAxis: {
      type: 'category', data: _years, boundaryGap: false,
      axisLabel: { color: '#555', fontSize: 18 }, axisLine: { lineStyle: { color: '#bbb' } }
    },
    yAxis: {
      type: 'value', name: '千桶/日',
      nameTextStyle: { color: '#555', fontSize: 18, align: 'right' },
      axisLabel: { color: '#555', fontSize: 18, formatter: v => (v/1000).toFixed(0) + 'k' },
      splitLine: { lineStyle: { color: '#e8e8e8' } }
    },
    series
  })

  const chartDom = $id('#chart-country-stack')
  let countryLegend = null
  chartDom.addEventListener('mousemove', e => {
    const rect = chartDom.getBoundingClientRect()
    const px = e.clientX - rect.left
    const py = e.clientY - rect.top
    const dataCoord = countryStackChart.convertFromPixel('grid', [px, py])
    if (!dataCoord) return
    const xi = Math.round(dataCoord[0])
    if (xi < 0 || xi >= _years.length) return
    let cumulative = 0, hit = null
    for (let si = 0; si < _sortedCountries.length; si++) {
      const c = _sortedCountries[si]
      const val = _countryAll[c][xi] || 0
      const prevCum = cumulative
      cumulative += val
      const botPx = countryStackChart.convertToPixel('grid', [xi, prevCum])[1]
      const topPx = countryStackChart.convertToPixel('grid', [xi, cumulative])[1]
      if (py >= topPx && py <= botPx) { hit = c; break }
    }
    if (hit && hit !== currentCountry) {
      currentCountry = hit
      showCountryDetail(hit)
      if (countryLegend) countryLegend.syncActive()
    }
  })

  // HTML 悬浮图例（各洲并排、坍塌成多列、悬浮/点击切独立走势），与占比卡共用 buildStackLegend
  currentCountry = _sortedCountries[0]
  countryLegend = buildStackLegend(
    chartDom, 'country-legend', _sortedCountries,
    () => currentCountry,
    c => { currentCountry = c; showCountryDetail(c) }
  )
  showCountryDetail(currentCountry)
  countryLegend.syncActive()
}

function showCountryDetail(country) {
  $id('#country-detail-title').textContent =
    `${country}（${_countryMeta[country].continent}）— 独立产量走势（千桶/日）`
  if (!countryDetailChart) countryDetailChart = echarts.init($id('#chart-country-detail'))
  const color = REGION_COLORS[_countryMeta[country].continent] || '#5470c6'
  countryDetailChart.setOption({
    backgroundColor: '#fafafa',
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross', lineStyle: { width: 1 } }, textStyle: { fontSize: 18 } },
    grid: { left: 72, right: 96, top: 12, bottom: 40 },
    // 不用 inside dataZoom：只要存在 inside，ECharts 就会 preventDefault 滚轮事件，页面无法下滚
    xAxis: {
      type: 'category', data: _years, boundaryGap: false,
      axisLabel: { color: '#555', fontSize: 18 },
      axisLine: { lineStyle: { color: '#bbb' } }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#555', fontSize: 18, formatter: v => (v/1000).toFixed(0) + 'k' },
      splitLine: { lineStyle: { color: '#eee' } }
    },
    series: [{
      type: 'line', data: _countryAll[country],
      smooth: true, showSymbol: false, connectNulls: true,
      areaStyle: { color, opacity: 0.15 },
      lineStyle: { color, width: 2 }, itemStyle: { color }
    }]
  }, true)
}

// 通用：给某张堆叠卡建一条 HTML 悬浮图例（各洲并排、坍塌成多列、悬浮/点击切独立走势）
// order=国家排序，getCurrent()=当前选中国，onPick(c)=切到该国并刷新独立走势
function buildStackLegend(chartDom, legendId, order, getCurrent, onPick) {
  const RESERVE = 150
  const contOrder = Object.keys(REGION_COLORS)
    .filter(cont => order.some(c => _countryMeta[c].continent === cont))
  const legendBox = document.createElement('div')
  legendBox.id = legendId
  legendBox.className = 'stack-legend'
  contOrder.forEach(cont => {
    const col = document.createElement('div')
    col.className = 'cl-col'
    const head = document.createElement('div')
    head.className = 'cl-head'
    head.textContent = cont
    head.style.color = REGION_COLORS[cont] || '#333'
    col.appendChild(head)
    const items = document.createElement('div')
    items.className = 'cl-items'
    order.filter(c => _countryMeta[c].continent === cont).forEach(c => {
      const it = document.createElement('div')
      it.className = 'cl-item'
      it.dataset.name = c
      it.title = c
      const dot = document.createElement('span')
      dot.className = 'cl-dot'
      dot.style.background = REGION_COLORS[cont] || '#888'
      const nm = document.createElement('span')
      nm.className = 'cl-name'
      nm.textContent = c
      it.append(dot, nm)
      const pick = () => {
        if (getCurrent() === c) return
        onPick(c)
        legendBox.querySelectorAll('.cl-item').forEach(el =>
          el.classList.toggle('active', el === it))
      }
      it.addEventListener('click', pick)
      it.addEventListener('mouseenter', pick)
      items.appendChild(it)
    })
    col.appendChild(items)
    legendBox.appendChild(col)
  })
  chartDom.appendChild(legendBox)

  function syncActive() {
    legendBox.querySelectorAll('.cl-item').forEach(el =>
      el.classList.toggle('active', el.dataset.name === getCurrent()))
  }
  // 图例变矮（主图吸顶收缩）时，把每个洲的国家从单列铺成多列，避免被裁掉
  function layoutLegendColumns() {
    const ITEM_W = 124, GAP = 14, itemH = 30
    legendBox.querySelectorAll('.cl-col').forEach(col => {
      const items = col.querySelector('.cl-items')
      const head = col.querySelector('.cl-head')
      const n = items.children.length
      const availH = col.clientHeight - head.offsetHeight
      if (availH <= 0 || !n) return
      const perCol = Math.max(1, Math.floor(availH / itemH))
      const cols = Math.max(1, Math.ceil(n / perCol))
      items.style.height = availH + 'px'
      items.style.columnCount = cols
      items.style.width = (cols * ITEM_W + (cols - 1) * GAP) + 'px'
    })
  }
  // 长条固定在主图右侧预留带，一直伸到视口右缘（伸出卡片）
  function place() {
    const r = chartDom.getBoundingClientRect()
    if (!r.width) return
    const GAP = 16   // 图例左缘离开绘图区右缘一点，别压到堆叠图上（也免得磨砂透出图表色）
    const leftRel = Math.max(0, r.width - RESERVE + GAP)
    legendBox.style.left = leftRel + 'px'
    legendBox.style.width = Math.max(RESERVE - GAP, window.innerWidth - 8 - (r.left + leftRel)) + 'px'
    layoutLegendColumns()
  }
  place()
  const ro = new ResizeObserver(place)
  ro.observe(chartDom)
  cleanups.push(() => ro.disconnect())
  onWin('resize', place)
  // 切卡/吸顶比例变化时重排：图例从隐藏变可见后 clientHeight 才不为 0，需重算列数
  onWin('pin-ratio-refresh', place)

  // 鼠标在图例条上：竖向滚轮转成横向滚动，横向到头也不带动页面上下
  legendBox.addEventListener('wheel', e => {
    const d = e.deltaY || e.deltaX
    if (!d) return
    legendBox.scrollLeft += d
    e.preventDefault()
  }, { passive: false })

  return { syncActive, place }
}

// ============================================================
// Tab 3: 产量占比 (country_production_percent.html 原内容)
// ============================================================
function initPercent() {
  percentStackChart = echarts.init($id('#chart-percent-stack'))

  percentStackChart.setOption({
    backgroundColor: '#ffffff',
    tooltip: {
      trigger: 'axis',
      position: [12, 12],
      axisPointer: { type: 'cross', lineStyle: { width: 2 } },
      textStyle: { fontSize: 18 },
      formatter: params => {
        let html = `<b>${params[0].axisValue} 年</b>`
        const items = params.filter(p => p.value != null && p.value > 0)
                            .sort((a, b) => b.value - a.value)
        const cur = items.find(p => p.seriesName === currentPercentCountry)
        if (cur) {
          const rank = items.indexOf(cur) + 1
          html += `<div style="margin:4px 0;padding:6px 8px;background:#fff6d6;border-left:3px solid #f0a500;border-radius:2px;font-size:18px;">
                                ${cur.marker}<b>${cur.seriesName}</b>：<b>${cur.value.toFixed(2)}%</b>
                                <span style="color:#888;font-size:18px;">（当年第 ${rank} 名 / 共 ${items.length}）</span>
                             </div>`
        }
        items.filter(p => p.seriesName !== currentPercentCountry)
             .slice(0, 8)
             .forEach(p => {
               html += `${p.marker}${p.seriesName}: <b>${p.value.toFixed(1)}%</b><br>`
             })
        if (items.length > 9) html += `…（共 ${items.length} 条）`
        return html
      }
    },
    // 图例改用 HTML 悬浮图例（见 initPercent 末尾 buildStackLegend），右侧留白与产量卡一致
    grid: { left: 72, right: 150, top: 40, bottom: 40 },
    toolbox: { feature: { saveAsImage: {}, dataZoom: { yAxisIndex: 'none' }, restore: {} }, right: 10, top: 8 },
    // 不加 dataZoom：年度点一次画全，看局部用 toolbox 的框选缩放
    xAxis: {
      type: 'category', data: _years, boundaryGap: false,
      axisLabel: { color: '#555', fontSize: 18 }, axisLine: { lineStyle: { color: '#bbb' } }
    },
    yAxis: {
      type: 'value', name: '%',
      nameTextStyle: { color: '#555', fontSize: 18, align: 'right' },
      axisLabel: { color: '#555', fontSize: 18, formatter: v => v + '%' },
      splitLine: { lineStyle: { color: '#e8e8e8' } }
    },
    series: _sortedByPct.map(c => ({
      name: c, type: 'line', stack: 'total',
      areaStyle: { opacity: 0.7 }, emphasis: { focus: 'series', areaStyle: { opacity: 1 } },
      smooth: true, showSymbol: false, connectNulls: true,
      lineStyle: { width: 0.5 },
      data: _pctData[c], color: REGION_COLORS[_countryMeta[c].continent] || '#888'
    }))
  })

  const chartDom = $id('#chart-percent-stack')
  let percentLegend = null
  chartDom.addEventListener('mousemove', e => {
    const rect = chartDom.getBoundingClientRect()
    const px = e.clientX - rect.left
    const py = e.clientY - rect.top
    const dataCoord = percentStackChart.convertFromPixel('grid', [px, py])
    if (!dataCoord) return
    const xi = Math.round(dataCoord[0])
    if (xi < 0 || xi >= _years.length) return
    let cum = 0, hit = null
    for (const c of _sortedByPct) {
      const val = _pctData[c][xi] || 0
      const prevCum = cum
      cum += val
      const botPx = percentStackChart.convertToPixel('grid', [xi, prevCum])[1]
      const topPx = percentStackChart.convertToPixel('grid', [xi, cum])[1]
      if (py >= topPx && py <= botPx) { hit = c; break }
    }
    if (hit && hit !== currentPercentCountry) {
      currentPercentCountry = hit
      showPercentDetail(hit)
      if (percentLegend) percentLegend.syncActive()
    }
  })

  currentPercentCountry = _sortedByPct[0]
  showPercentDetail(currentPercentCountry)
  percentLegend = buildStackLegend(
    chartDom, 'percent-legend', _sortedByPct,
    () => currentPercentCountry,
    c => { currentPercentCountry = c; showPercentDetail(c) }
  )
  percentLegend.syncActive()
}

function showPercentDetail(country) {
  $id('#percent-detail-title').textContent =
    `${country}（${_countryMeta[country].continent}）— 独立占比走势（占全球 %）`
  if (!percentDetailChart) percentDetailChart = echarts.init($id('#chart-percent-detail'))
  const color = REGION_COLORS[_countryMeta[country].continent] || '#5470c6'
  percentDetailChart.setOption({
    backgroundColor: '#fafafa',
    tooltip: {
      trigger: 'axis', axisPointer: { type: 'cross', lineStyle: { width: 1 } },
      valueFormatter: v => (v || 0).toFixed(2) + '%',
      textStyle: { fontSize: 18 }
    },
    grid: { left: 72, right: 96, top: 12, bottom: 40 },
    // 不用 inside dataZoom：只要存在 inside，ECharts 就会 preventDefault 滚轮事件，页面无法下滚
    xAxis: {
      type: 'category', data: _years, boundaryGap: false,
      axisLabel: { color: '#555', fontSize: 18 }, axisLine: { lineStyle: { color: '#bbb' } }
    },
    yAxis: {
      type: 'value', min: 0,
      axisLabel: { color: '#555', fontSize: 18, formatter: v => v + '%' },
      splitLine: { lineStyle: { color: '#eee' } }
    },
    series: [{
      type: 'line', data: _pctData[country],
      smooth: true, showSymbol: false, connectNulls: true,
      areaStyle: { color, opacity: 0.15 },
      lineStyle: { color, width: 2 }, itemStyle: { color }
    }]
  }, true)
}

// ============================================================
// 吸顶改变高度比例（参考 demo/sticky-image-scroll.html）：
//   .pin-scroller 比一屏高出 620px，卡片在吸顶的 .pin-stage 里原地不动，
//   滚动进度 p(0→1) 直接改主图的真实宽高（不是 transform 缩放），
//   主图由大变小到左上角，底部详情图此消彼长地长大 —— 小主图就是选地区/选国家的选择器。
//   地区卡、各国卡各挂一份。
// ============================================================
function initPinnedRatio(scrollerId, stageId, pairs) {
  const MAIN_H = [0.78, 0.26]   // 主图占容器可用高度：78% → 26%
  const MAIN_W = [100, 34]      // 主图宽度：100% → 34%

  let scroller, stage, lastP = -1, ticking = false

  const lerp = (a, b, p) => a + (b - a) * p

  // 两张卡（前卡/后卡）同尺寸，一起按进度刷，切页签时不用重建
  function apply(p) {
    pairs.forEach(([mainId, detailId]) => {
      const mainEl = $id('#' + mainId)
      const detailEl = $id('#' + detailId)
      if (!mainEl || !detailEl) return
      const wrap = detailEl.closest('.stack-detail-wrap')
      const box = mainEl.parentElement   // 地区卡是 .stack-card，各国卡是 .stack-wrap
      const cs = getComputedStyle(box)
      // 可用高度 = 容器内容高 - 标题/露出条等固定块
      let fixed = 0
      for (const ch of box.children) {
        if (ch !== mainEl && ch !== wrap) fixed += ch.offsetHeight
      }
      const inner = box.clientHeight - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom)
      const avail = Math.max(240, inner - fixed)

      const mainH = Math.round(avail * lerp(MAIN_H[0], MAIN_H[1], p))
      const mainW = lerp(MAIN_W[0], MAIN_W[1], p)
      mainEl.style.width  = mainW.toFixed(2) + '%'
      mainEl.style.height = mainH + 'px'
      wrap.style.flexBasis = (avail - mainH) + 'px'   // 此消彼长，总高不变

      // 真实宽高变了就得重新量：hover 命中靠 convertFromPixel，尺寸必须是最新的
      const mainInst = echarts.getInstanceByDom(mainEl)
      if (mainInst) mainInst.resize()
      // 主图缩到不足一半宽时太窄，tooltip 会挤爆小图 —— 关掉；
      // 关的同时把当前正显示的 tooltip 也收掉（不只是拦下次 hover）
      const showTip = mainW >= 60
      if (mainInst && mainEl.dataset.tipShown !== String(showTip)) {
        mainInst.setOption({ tooltip: { show: showTip } })
        if (!showTip) mainInst.dispatchAction({ type: 'hideTip' })
        mainEl.dataset.tipShown = String(showTip)
      }
      const detailInst = echarts.getInstanceByDom(detailEl)
      if (detailInst) detailInst.resize()
    })
  }

  // 滚动进度：scroller 顶部滚过的距离 / (scroller 高 - 吸顶一屏)，同 demo
  function tick() {
    ticking = false
    if (!scroller || !stage) return
    const total = scroller.offsetHeight - stage.offsetHeight
    const scrolled = -scroller.getBoundingClientRect().top
    const p = total > 0 ? Math.min(1, Math.max(0, scrolled / total)) : 0
    if (Math.abs(p - lastP) < 0.002) return   // 进度没变就别白刷 canvas
    lastP = p
    apply(p)
  }

  function onScroll() { if (!ticking) { ticking = true; requestAnimationFrame(tick) } }

  const timer = setInterval(() => {
    scroller = $id('#' + scrollerId)
    stage = $id('#' + stageId)
    if (!scroller || !stage) return
    if (!echarts.getInstanceByDom($id('#' + pairs[0][0]) || document.body)) return
    clearInterval(timer)
    onWin('scroll', onScroll, { passive: true })
    onWin('resize', () => { lastP = -1; tick() })
    onWin('pin-ratio-refresh', () => { lastP = -1; tick() })
    tick()
  }, 120)
  cleanups.push(() => clearInterval(timer))
}
</script>

<!-- 逐字搬自源页 style 块，仅去掉 base.css 已全局提供的 reset / body / loading+error / chart-title。
     不加 scoped：图例、页签、卡片露出条等节点由 document.createElement 动态创建，拿不到 scoped 属性，
     统一走非 scoped 才能命中。 -->
<style>
#cards { max-width: 1800px; margin: 0 auto; padding: 20px 24px 40px; }

/* Stacked cards */
.card {
    background: #fff;
    border-radius: 10px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    margin: 0 0 24px;
    padding: 12px;
    display: flex;
    flex-direction: column;
}

/* Card 0: 全球总产量 + 回归趋势 */
#chart-total { width: 100%; height: 680px; }

/* Card 1: region — 两张图做成 price_history.html 那样的卡片堆叠（页签切换） */
/* 宽高由滚动进度逐帧设置（见 initStickyRatio），这里只给个兜底初值 */
#chart-region-abs, #chart-region-pct { width: 100%; height: 520px; flex: 0 0 auto; }

/* === 页签：胶囊式分段控件，白色滑块随选中项平移；靠右侧对齐 === */
.stack-tabs {
    position: relative;
    display: flex;
    width: fit-content;
    margin: 0 0 16px auto;   /* margin-left:auto 把整条页签推到右边 */
    padding: 5px;
    background: #eceff3;
    border-radius: 999px;
    box-shadow: inset 0 1px 3px rgba(15, 23, 42, 0.07);
}
.tab-slider {
    position: absolute;
    top: 5px; bottom: 5px; left: 0;
    border-radius: 999px;
    background: #fff;
    box-shadow: 0 2px 10px rgba(15, 23, 42, 0.14);
    transition: transform 0.32s cubic-bezier(0.4, 0, 0.2, 1),
                width 0.32s cubic-bezier(0.4, 0, 0.2, 1);
}

.stack-tab {
    position: relative;
    z-index: 1;
    display: inline-flex;
    align-items: center;
    gap: 9px;
    font: inherit;
    font-size: 18px;
    line-height: 1.4;
    padding: 10px 24px;
    background: transparent;
    border: none;
    border-radius: 999px;
    color: #6b7280;
    white-space: nowrap;
    cursor: pointer;
    transition: color 0.25s ease;
}
.stack-tab .tab-dot {
    width: 9px; height: 9px;
    border-radius: 50%;
    background: currentColor;
    opacity: 0.4;
    transition: opacity 0.25s ease, transform 0.25s ease;
}
.stack-tab:hover { color: #374151; }
.stack-tab.active { color: #0f172a; font-weight: 600; cursor: default; }
.stack-tab.active .tab-dot { opacity: 1; transform: scale(1.2); }

/* === 卡片堆叠：前卡在上，后卡向下露出一条 === */
.card-stack { position: relative; margin-bottom: 70px; }
.stack-card {
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 12px;
    box-shadow: 0 6px 20px rgba(15, 23, 42, 0.08);
    transition: transform 0.35s ease, box-shadow 0.35s ease;
    /* 与原 .card 一致：底部详情条靠 flex 才能拿到 200px 高度 */
    display: flex;
    flex-direction: column;
}
/* 前卡留在文档流里，由它决定 .card-stack 的高度 */
.stack-card.front { position: relative; z-index: 2; }

.stack-card.back {
    position: absolute;
    top: 0; left: 0; right: 0;
    z-index: 1;
    transform: translateY(16px) scale(0.985);
    cursor: pointer;
}
.stack-card.back:hover {
    transform: translateY(24px) scale(0.99);
    box-shadow: 0 10px 26px rgba(15, 23, 42, 0.12);
}
/* 露出的那条只在后卡显示，用来标明这是哪张图 */
.card-peek { display: none; }
.stack-card.back .card-peek {
    display: block;
    margin-top: 12px;
    padding-top: 10px;
    border-top: 1px solid #f3f4f6;
    font-size: 18px;
    color: #6b7280;
    text-align: center;
}

/* Card 2 & 3: stack main + detail bottom (200px) */
.stack-wrap {
    height: 760px;
    display: flex;
    flex-direction: column;
}
.stack-main { width: 100%; flex: 1 1 0; min-height: 0; }
.stack-detail-wrap {
    width: 100%;
    flex: 0 0 200px;
    border-top: 2px solid #eee;
    display: flex;
    flex-direction: column;
}
/* 滚到底后详情图才是主角，标题要一眼看到是哪个地区/国家 */
.stack-detail-title {
    text-align: center;
    font-size: 20px;
    font-weight: 600;
    color: #111827;
    letter-spacing: 0.2px;
    height: 28px;
    line-height: 28px;
    padding-top: 4px;
}
.stack-detail-chart { width: 100%; flex: 1 1 0; min-height: 0; }

/* === 吸顶滚动改变高度比例（参考 demo/sticky-image-scroll.html）===
 * .pin-scroller 比一屏高出的那段决定动画滚多久；.pin-stage 吸顶占满一屏，
 * 卡片留在原地不动，主图在这一屏里由大变小（真实宽高，不是 transform 缩放），
 * 底部详情图此消彼长地长大 —— 缩小后的主图就是选地区/选国家的选择器。 */
.pin-scroller { height: calc(100vh + 620px); }
.pin-stage {
    position: sticky;
    top: 0;
    height: 100vh;
    display: flex;
    flex-direction: column;
    padding: 12px 0 16px;
}
.pin-stage .stack-tabs { flex: 0 0 auto; }
/* 底部留出 68px：后卡整块下移，"点击切到前面"那条要露在前卡下面，不能被舞台裁掉 */
.pin-stage .card-stack { flex: 1 1 0; min-height: 0; margin-bottom: 68px; }
.pin-stage .stack-card.front { height: 100%; }
.pin-stage .stack-card.back { bottom: 0; transform: translateY(52px) scale(0.99); }
.pin-stage .stack-card.back:hover { transform: translateY(60px) scale(0.994); }
/* 各国那两张卡多一层 .stack-wrap：撑满卡片，高度不再写死 760px */
.pin-stage .stack-wrap { height: auto; flex: 1 1 0; min-height: 0; }
/* 主图变窄时左边不动、从右侧收（列向 flex 的交叉轴对齐）；高度由 JS 给 */
.pin-stage #chart-region-abs,
.pin-stage #chart-region-pct,
.pin-stage .stack-main { align-self: flex-start; flex: 0 0 auto; }
.pin-stage .stack-detail-wrap { flex: 0 0 auto; overflow: hidden; }

/* 各国图：图例做成 HTML 横向长条，可伸出卡片右侧、横向滚轮滚动、点击切显隐 */
.stack-main { position: relative; }
.stack-legend {
    position: absolute; top: 34px; bottom: 8px;
    display: flex; align-items: stretch; gap: 0;
    overflow-x: auto; overflow-y: hidden;
    z-index: 5; scrollbar-width: thin;
    padding: 12px 10px;
    background: rgba(255, 255, 255, 0.28);
    backdrop-filter: saturate(140%) blur(8px);
    -webkit-backdrop-filter: saturate(140%) blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.4);
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text",
        "Segoe UI", "PingFang SC", "Helvetica Neue", Arial, sans-serif;
}

.stack-legend::-webkit-scrollbar { height: 7px; }
.stack-legend::-webkit-scrollbar-thumb {
    background: rgba(120, 130, 145, 0.35); border-radius: 4px;
}
.stack-legend::-webkit-scrollbar-thumb:hover {
    background: rgba(120, 130, 145, 0.55);
}
.cl-col {
    flex: 0 0 auto; padding: 0 8px;
    display: flex; flex-direction: column; min-height: 0;
}
/* 图例变矮时，一个洲的国家从单列坍塌成多列：纵向填满后另起一列，整组变宽。
   列数由 JS（layoutLegendColumns）按当前可用高度算好，再写死 height/columnCount/width，
   纯 CSS 的 flex/multicol 在自动宽度下不会为新列撑宽、会溢出压到隔壁洲。 */
.cl-items { column-gap: 14px; column-fill: auto; }
.cl-head {
    flex: 0 0 auto;
    font-size: 18px; font-weight: 600; margin-bottom: 10px;
    white-space: nowrap; letter-spacing: 0.01em;
}
.cl-item {
    flex: 0 0 auto; width: 124px; box-sizing: border-box;
    display: flex; align-items: center; gap: 8px;
    font-size: 18px; line-height: 22px; color: #1d1d1f;
    cursor: pointer; white-space: nowrap; overflow: hidden; user-select: none;
    padding: 3px 8px; border-radius: 9px; margin: 1px 0;
    transition: background 0.15s ease, opacity 0.15s ease;
}
.cl-item:hover { background: rgba(0, 0, 0, 0.05); }
.cl-item.active { background: rgba(0, 0, 0, 0.08); font-weight: 600; }
.cl-item .cl-dot { width: 14px; height: 9px; border-radius: 3px; flex: 0 0 auto; }
.cl-item .cl-name { overflow: hidden; text-overflow: ellipsis; }
.cl-item.active .cl-dot { box-shadow: 0 0 0 2px rgba(0,0,0,0.12); }
/* 切到「各国产量占比」时，各国产量图退到后卡，它的图例别再浮在前卡上被遮挡 */
.stack-card.back .stack-legend { display: none; }
</style>
