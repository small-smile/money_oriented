<template>
  <!-- 银行·营收支出瀑布：迁移示范页 —— 不碰 legacy IIFE，改用新基础设施
       （useApiData 取数 + ChartCard 骨架 + chartTheme 主题 + EChart 容器）。 -->
  <div class="bank-income-waterfall">
    <ChartCard
      :title="cardTitle"
      :sub="cardSub"
      :loading="loading"
      :error="error"
      :empty="!option"
      empty-text="该行暂无营收/利润数据"
      :note="note"
    >
      <EChart v-if="option" :option="option" height="520px" />
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
const cardTitle = computed(() => `${bankName.value || '银行'}　营收 → 支出 → 净利 瀑布图`)
const cardSub = computed(() => (reportYear.value ? `${reportYear.value} 年 · 单位：亿元` : '单位：亿元'))
const note =
  '「营业支出与税负」为营业收入 − 净利润 的倒推合计（含营业支出、税金及所得税、少数股东损益等全部扣减项），' +
  '非年报单列科目；营收各分部、营业收入、净利润均为年报披露值。分部收入合计与营业收入不吻合时不画分部拆解。'

const option = computed(() => {
  const d = data.value
  const perf = d && d.perf
  if (!perf || !Array.isArray(perf.years) || !perf.years.length) return null
  const i = perf.years.length - 1
  const revenue = Number(perf.revenue && perf.revenue[i])
  const profit = Number(perf.profit && perf.profit[i])
  if (!isFinite(revenue) || !isFinite(profit)) return null
  const cost = revenue - profit

  const cats = [], base = [], vals = [], colors = [], labels = []
  const push = (name, b, v, color, signed) => {
    cats.push(name); base.push(b); vals.push(v); colors.push(color); labels.push(signed)
  }

  // 营收分部买入（仅当该行披露了当年分部收入，且合计与营业收入吻合，否则退回三段瀑布）
  const seg = d['seg-rev']
  const segArr = seg && seg.segs && seg['rev' + String(perf.years[i]).slice(-2)]
  if (Array.isArray(segArr) && seg.segs.length === segArr.length) {
    const segVals = segArr.map((x) => Number(x) / 100) // 百万 → 亿
    if (Math.abs(segVals.reduce((a, b2) => a + b2, 0) - revenue) < 0.5) {
      let acc = 0
      seg.segs.forEach((name, k) => { push(name, acc, segVals[k], COLOR.navy, '+' + fmtYi(segVals[k])); acc += segVals[k] })
    }
  }
  push('营业收入', 0, revenue, '#2c5f8a', fmtYi(revenue))
  push('营业支出与税负', profit, cost, COLOR.red, '−' + fmtYi(cost))
  push('净利润', 0, profit, COLOR.green, fmtYi(profit))

  return {
    grid: { ...gridBase, top: 30, bottom: 64 },
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
})
</script>

<style scoped>
.bank-income-waterfall { padding: 16px; }
</style>
