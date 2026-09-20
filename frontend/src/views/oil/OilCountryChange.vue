<template>
  <div>
    <LoadingNote v-if="loading" />
    <div v-if="error" id="error-msg" style="display:block">加载失败：{{ error }}（请确保后端已启动）</div>
    <div ref="containerEl" id="container"></div>
  </div>
</template>

<script setup>
import LoadingNote from '../../components/LoadingNote.vue'
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { apiGet } from '../../api'

// 逐字搬自 dashboard/subject/oil/country_change_2001_2024.html：option 与渲染逻辑原样保留，
// 仅把取数改走统一 apiGet、容器改用组件 ref。图与数据一律不变。
const loading = ref(true)
const error = ref('')
const containerEl = ref(null)
let charts = []

const CONT_COLOR = {
  'Africa':             '#fc8452',
  'Asia Pacific':       '#73c0de',
  'CIS':                '#fac858',
  'Europe':             '#9a60b4',
  'Middle East':        '#ee6666',
  'North America':      '#5470c6',
  'S. & Cent. America': '#91cc75'
}

function onResize() { charts.forEach(c => c.chart.resize()) }

onMounted(async () => {
  try {
    const data = await apiGet('/api/production_region')
    loading.value = false
    render(data.country_compare, containerEl.value)
    window.addEventListener('resize', onResize)
  } catch (e) {
    loading.value = false
    error.value = e.message || String(e)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  charts.forEach(c => { try { c.chart.dispose() } catch (_) {} })
  charts = []
})

function render(compare, container) {
  const continents = Object.keys(compare)

  let globalMax = 0
  continents.forEach(cont => {
    compare[cont].forEach(e => { globalMax = Math.max(globalMax, e.v2001, e.v2024) })
  })
  globalMax = Math.ceil(globalMax / 1000) * 1000

  const patternCanvas = document.createElement('canvas')
  patternCanvas.width = 10
  patternCanvas.height = 10
  const pCtx = patternCanvas.getContext('2d')
  pCtx.fillStyle = '#f0f0f0'
  pCtx.fillRect(0, 0, 10, 10)
  pCtx.strokeStyle = '#999'
  pCtx.lineWidth = 1.5
  pCtx.beginPath(); pCtx.moveTo(0, 10); pCtx.lineTo(10, 0); pCtx.stroke()
  pCtx.beginPath(); pCtx.moveTo(-2, 2);  pCtx.lineTo(2, -2);  pCtx.stroke()
  pCtx.beginPath(); pCtx.moveTo(8, 12);  pCtx.lineTo(12, 8);  pCtx.stroke()
  const stripeImg = new Image()
  const stripePattern = { image: stripeImg, repeat: 'repeat' }
  stripeImg.onload = () => {
    charts.forEach(({ chart, losses }) => {
      chart.setOption({ series: [{}, {}, {
        itemStyle: { color: stripePattern },
        data: losses.map(v => ({ value: v, itemStyle: { color: stripePattern } }))
      }] })
    })
  }
  stripeImg.src = patternCanvas.toDataURL()

  continents.forEach(cont => {
    const entries = [...compare[cont]].sort((a, b) => b.v2024 - a.v2024)
    const color   = CONT_COLOR[cont] || '#888'

    const countries = entries.map(e => e.country)
    const base      = entries.map(e => Math.min(e.v2001, e.v2024))
    const gains     = entries.map(e => Math.max(0, e.v2024 - e.v2001))
    const losses    = entries.map(e => Math.max(0, e.v2001 - e.v2024))
    const meta = entries.map(e => ({
      v2001: e.v2001, v2024: e.v2024,
      diff: parseFloat((e.v2024 - e.v2001).toFixed(1)),
      pct: Math.max(e.v2001, e.v2024) > 0
        ? ((e.v2024 - e.v2001) / Math.max(e.v2001, e.v2024) * 100).toFixed(1)
        : null
    }))

    const h = Math.max(260, countries.length * 32 + 120)
    const block = document.createElement('div')
    block.className = 'chart-block chart-card'
    const titleEl = document.createElement('h2')
    titleEl.className = 'chart-title'
    titleEl.style.cssText = `text-align:left;padding:10px 0 0 16px;color:${color}`
    titleEl.textContent = cont
    block.appendChild(titleEl)
    const div = document.createElement('div')
    div.style.width = '100%'
    div.style.height = h + 'px'
    block.appendChild(div)
    container.appendChild(block)

    const chart = echarts.init(div)
    charts.push({ chart, losses })
    chart.setOption({
      backgroundColor: '#ffffff',
      tooltip: {
        trigger: 'axis',
        textStyle: { fontSize: 18 },
        axisPointer: { type: 'shadow' },
        formatter: params => {
          const name = params[0].axisValue
          const i    = countries.indexOf(name)
          if (i < 0) return ''
          const m    = meta[i]
          const sign = m.diff >= 0 ? '+' : ''
          const pctStr = m.pct !== null ? `（${sign}${m.pct}%）` : ''
          return `<b>${name}</b><br>
                  2001：<b>${m.v2001.toLocaleString()}</b> 千桶/日<br>
                  2024：<b>${m.v2024.toLocaleString()}</b> 千桶/日<br>
                  变化：<b>${sign}${m.diff.toLocaleString()}</b> ${pctStr}`
        }
      },
      legend: {
        data: ['保留', '增加', '减少'],
        top: 8, right: 20,
        itemGap: 20,
        textStyle: { color: '#333', fontSize: 18 }
      },
      grid: { left: 210, right: 96, top: 40, bottom: 30 },
      xAxis: {
        type: 'value',
        min: 0,
        max: globalMax,
        axisLabel: { color: '#555', fontSize: 18, formatter: v => (v/1000).toFixed(0)+'k' },
        splitLine: { lineStyle: { color: '#eee' } }
      },
      yAxis: {
        type: 'category',
        data: countries,
        axisLabel: { color: '#333', fontSize: 18 },
        axisLine: { lineStyle: { color: '#ddd' } },
        axisTick: { show: false }
      },
      series: [
        {
          name: '保留',
          type: 'bar', stack: 'total', barMaxWidth: 14,
          itemStyle: { color: '#3ba562' },
          data: base.map(v => ({ value: v, itemStyle: { color: '#3ba562' } }))
        },
        {
          name: '增加',
          type: 'bar', stack: 'total', barMaxWidth: 14,
          itemStyle: { color: '#31d86e' },
          data: gains.map(v => ({ value: v, itemStyle: { color: '#31d86e' } })),
          labelLayout: { hideOverlap: true },
          label: {
            show: true, position: 'right', fontSize: 18, color: '#1a7a3a',
            formatter: p => p.value > 0 ? '+' + p.value.toLocaleString() : ''
          }
        },
        {
          name: '减少',
          type: 'bar', stack: 'total', barMaxWidth: 14,
          itemStyle: { color: stripePattern },
          data: losses.map(v => ({ value: v, itemStyle: { color: stripePattern } })),
          labelLayout: { hideOverlap: true },
          label: {
            show: true, position: 'right', fontSize: 18, color: '#6b7280',
            formatter: p => p.value > 0 ? '-' + p.value.toLocaleString() : ''
          }
        }
      ]
    })
  })
}
</script>

<style>
#container { max-width: 1800px; margin: 0 auto; padding: 20px 24px 40px; }
.chart-block { width: 100%; margin-bottom: 24px; }
</style>
