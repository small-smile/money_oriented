<template>
  <!-- 银行·营收支出瀑布：迁移示范页 —— 不碰 legacy IIFE，改用新基础设施
       （useApiData 取数 + ChartCard 骨架 + chartTheme 主题 + EChart 容器）。
       收支拆成两幅图：① 营收构成（按经营分部）② 营收 → 支出 → 净利。 -->
  <div class="bank-income-waterfall">
    <ChartCard
      :title="revTitle"
      :sub="cardSub"
      :loading="loading"
      :error="error"
      :empty="!optionRevenue"
      empty-text="该行未披露分部收入"
      :note="revNote"
    >
      <EChart v-if="optionRevenue" :option="optionRevenue" height="440px" />
    </ChartCard>
    <ChartCard
      :title="pnlTitle"
      :sub="cardSub"
      :loading="loading"
      :error="error"
      :empty="!optionProfit"
      empty-text="该行暂无营收/利润数据"
      :note="pnlNote"
    >
      <EChart v-if="optionProfit" :option="optionProfit" height="440px" />
    </ChartCard>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import ChartCard from '../../../components/ChartCard.vue'
import EChart from '../../../components/EChart.vue'
import { useApiData } from '../../../composables/useApiData'
import { COLOR, catAxis, valAxis, gridBase, fmtYi } from '../../../chartTheme'

const route = useRoute()
// 与 BankLayout 一致：路由 code 决定取哪家行；非法回退默认 601077。切 code 由 useApiData 自动重取。
const code = computed(() => (/^[0-9]{5,6}$/.test(route.params.code || '') ? String(route.params.code) : '601077'))
const { data, loading, error } = useApiData('/api/company_charts', () => ({ code: code.value }))

const bankName = computed(() => (data.value && data.value._bank && data.value._bank.shortName) || '')
const reportYear = computed(() => {
  const ys = (data.value && data.value.perf && data.value.perf.years) || []
  return ys.length ? ys[ys.length - 1] : ''
})
const revTitle = computed(() => `${bankName.value || '银行'}　营收构成（按经营分部）`)
const pnlTitle = computed(() => `${bankName.value || '银行'}　营收 → 支出 → 净利`)
const cardSub = computed(() => (reportYear.value ? `${reportYear.value} 年 · 单位：亿元` : '单位：亿元'))
const revNote =
  '营业收入按经营分部（年报「分部信息」披露）拆分；分部收入合计与营业收入的差额（分部间抵销、' +
  '未分配项等口径差异）单列为「合并抵销/未分配差额」，非年报单列科目；差额 < 0.5 亿则不单列。'
const pnlNote =
  '「营业支出与税负」为营业收入 − 净利润 的倒推合计（含营业支出、税金及所得税、少数股东损益等全部扣减项），' +
  '非年报单列科目；营业收入、净利润均为年报披露值。'

// 瀑布通用：把各步 { name, value, color, total } 累加成「透明底柱 + 可见柱」。
// total 型柱从 0 起画完整高度并把累计对齐到该值（用于「营业收入 / 净利润」这类汇总列）；
// 非 total 为增量：正数向上、负数向下，标签带 +/− 号。
function waterfall(steps) {
  const cats = [], base = [], vals = [], colors = [], labels = []
  let acc = 0
  for (const s of steps) {
    if (s.total) {
      cats.push(s.name); base.push(0); vals.push(s.value); colors.push(s.color); labels.push(fmtYi(s.value))
      acc = s.value
    } else {
      const v = s.value
      cats.push(s.name); base.push(v >= 0 ? acc : acc + v); vals.push(Math.abs(v)); colors.push(s.color)
      labels.push((v >= 0 ? '+' : '−') + fmtYi(Math.abs(v)))
      acc += v
    }
  }
  return { cats, base, vals, colors, labels }
}

function build(steps) {
  const { cats, base, vals, colors, labels } = waterfall(steps)
  return {
    grid: { ...gridBase, top: 30, bottom: cats.length > 5 ? 72 : 48 },
    tooltip: { trigger: 'item', formatter: (p) => `${p.name}<br/>${labels[p.dataIndex]} 亿元` },
    xAxis: catAxis(cats, { axisLabel: { color: COLOR.axis, fontSize: 13, interval: 0, rotate: cats.length > 5 ? 18 : 0 } }),
    yAxis: valAxis({ name: '亿元' }),
    series: [
      { type: 'bar', stack: 'wf', silent: true, itemStyle: { color: 'transparent' }, emphasis: { disabled: true }, data: base },
      {
        type: 'bar', stack: 'wf', barMaxWidth: 56,
        data: vals.map((v, k) => ({ value: v, itemStyle: { color: colors[k] } })),
        label: { show: true, position: 'top', color: '#333', fontSize: 13, formatter: (p) => labels[p.dataIndex] },
      },
    ],
  }
}

// ① 营收构成：各分部逐段买入 →（差额）→ 营业收入 汇总列。无分部披露则空态。
const optionRevenue = computed(() => {
  const d = data.value
  const perf = d && d.perf
  if (!perf || !Array.isArray(perf.years) || !perf.years.length) return null
  const i = perf.years.length - 1
  const revenue = Number(perf.revenue && perf.revenue[i])
  if (!isFinite(revenue)) return null
  const seg = d['seg-rev']
  const segArr = seg && seg.segs && seg['rev' + String(perf.years[i]).slice(-2)]
  if (!Array.isArray(segArr) || seg.segs.length !== segArr.length) return null
  const segVals = segArr.map((x) => Number(x) / 100) // 百万 → 亿
  const steps = seg.segs.map((name, k) => ({ name, value: segVals[k], color: COLOR.navy }))
  const diff = revenue - segVals.reduce((a, b) => a + b, 0)
  if (Math.abs(diff) >= 0.5) steps.push({ name: '合并抵销/未分配差额', value: diff, color: COLOR.muted })
  steps.push({ name: '营业收入', value: revenue, color: '#2c5f8a', total: true })
  return build(steps)
})

// ② 营收 → 支出 → 净利：营业收入 −（倒推的）营业支出与税负 = 净利润。
const optionProfit = computed(() => {
  const d = data.value
  const perf = d && d.perf
  if (!perf || !Array.isArray(perf.years) || !perf.years.length) return null
  const i = perf.years.length - 1
  const revenue = Number(perf.revenue && perf.revenue[i])
  const profit = Number(perf.profit && perf.profit[i])
  if (!isFinite(revenue) || !isFinite(profit)) return null
  return build([
    { name: '营业收入', value: revenue, color: '#2c5f8a', total: true },
    { name: '营业支出与税负', value: -(revenue - profit), color: COLOR.red },
    { name: '净利润', value: profit, color: COLOR.green, total: true },
  ])
})
</script>

<style scoped>
.bank-income-waterfall { padding: 16px; }
</style>
