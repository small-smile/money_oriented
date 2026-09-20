<template>
  <!-- 银行·营收支出瀑布：迁移示范页 —— 不碰 legacy IIFE，改用新基础设施
       （useApiData 取数 + ChartCard 骨架 + chartTheme 主题 + EChart 容器）。
       收支拆成两幅图：① 营收构成（按经营分部）② 营收 → 支出 → 净利。 -->
  <div class="bank-income-waterfall">
    <!-- 同业对比开关：本行瀑布 ↔ 同业结构对比（留在本页、不走路由切换；复用油价页 .stack-tabs 胶囊控件） -->
    <div class="stack-tabs peer-tabs" ref="tabsEl">
      <span class="tab-slider" :style="sliderStyle"></span>
      <button
        v-for="t in TABS"
        :key="t.key"
        type="button"
        class="stack-tab"
        :class="{ active: view === t.key }"
        @click="setView(t.key)"
      >
        <span class="tab-dot" :style="{ color: t.color }"></span><span>{{ t.label }}</span>
      </button>
    </div>
    <ChartCard
      :title="revCardTitle"
      :sub="revCardSub"
      :loading="revCardLoading"
      :error="revCardError"
      :empty="!revCardOption"
      :empty-text="revCardEmptyText"
      :note="revCardNote"
    >
      <EChart v-if="revCardOption" :key="revCardKey" :option="revCardOption" :height="revCardHeight" />
    </ChartCard>
    <ChartCard
      :title="pnlCardTitle"
      :sub="pnlCardSub"
      :loading="pnlCardLoading"
      :error="pnlCardError"
      :empty="!pnlCardOption"
      :empty-text="pnlCardEmptyText"
      :note="pnlCardNote"
    >
      <EChart v-if="pnlCardOption" :key="pnlCardKey" :option="pnlCardOption" :height="pnlCardHeight" />
    </ChartCard>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import ChartCard from '../../../components/ChartCard.vue'
import EChart from '../../../components/EChart.vue'
import { useApiData } from '../../../composables/useApiData'
import { apiGet } from '../../../api'
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
const revTitle = computed(() => `${bankName.value || '银行'}　营收构成（公司/零售/同业/其他）`)
const pnlTitle = computed(() => `${bankName.value || '银行'}　营收 → 支出 → 净利`)
const cardSub = computed(() => (reportYear.value ? `${reportYear.value} 年 · 单位：亿元` : '单位：亿元'))
const revNote =
  '营业收入按经营分部归并为「公司 / 零售 / 同业 / 其他」四类（各行分部命名不一，按业务性质归类：对公·批发→公司，' +
  '个人·零售→零售，资金·金融市场→同业，未分配等→其他）；仅当分部合计与营业收入吻合（差 < 0.5 亿）时拆解，' +
  '按地域分部、口径不吻合或未披露分部则此图留空，直接看下方利润形成图。'
const pnlNote =
  '营业收入 −（信用减值损失 ＋ 其他营业支出与税负）＝ 净利润。信用减值损失为年报披露值（减值损失科目）；' +
  '「其他营业支出与税负」＝ 营业收入 − 净利润 − 信用减值损失 的倒推合计（含业务及管理费、税金及附加、所得税、少数股东损益等），' +
  '非年报单列科目；缺信用减值数据的行合并为单一「营业支出与税负」。'

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

// ① 营收构成：直接读后端预拆好的 seg-rev.std（公司/零售/同业/其他，归类规则见
// data/extract/gen_company_charts.py 的 seg_bucket）；无 std（地域分部/未披露）或口径不吻合则留空。
const optionRevenue = computed(() => {
  const d = data.value
  const perf = d && d.perf
  if (!perf || !Array.isArray(perf.years) || !perf.years.length) return null
  const i = perf.years.length - 1
  const revenue = Number(perf.revenue && perf.revenue[i])
  if (!isFinite(revenue)) return null
  const std = d['seg-rev'] && d['seg-rev'].std
  const arr = std && std.segs && std['rev' + String(perf.years[i]).slice(-2)]
  if (!Array.isArray(arr) || std.segs.length !== arr.length) return null
  const vals = arr.map((x) => Number(x) / 100) // 百万 → 亿
  // 四类合计与营业收入口径不吻合（差 ≥ 0.5 亿）则不拆解、此图留空
  if (Math.abs(revenue - vals.reduce((a, b) => a + b, 0)) >= 0.5) return null
  const steps = std.segs
    .map((name, k) => ({ name, value: vals[k], color: COLOR.navy }))
    .filter((s) => Math.abs(s.value) >= 0.005)
  steps.push({ name: '营业收入', value: revenue, color: '#2c5f8a', total: true })
  return build(steps)
})

// ② 营收 → 支出 → 净利：营业收入 −（信用减值损失 + 其他营业支出与税负）= 净利润。
const optionProfit = computed(() => {
  const d = data.value
  const perf = d && d.perf
  if (!perf || !Array.isArray(perf.years) || !perf.years.length) return null
  const i = perf.years.length - 1
  const revenue = Number(perf.revenue && perf.revenue[i])
  const profit = Number(perf.profit && perf.profit[i])
  if (!isFinite(revenue) || !isFinite(profit)) return null
  const cost = revenue - profit
  const steps = [{ name: '营业收入', value: revenue, color: '#2c5f8a', total: true }]
  // 拆出年报披露的「信用减值损失」（creditamount.impAmt，百万→亿，按年份对齐 perf），其余归入倒推残差
  const ca = d.creditamount
  const wy = ca && Array.isArray(ca.years) ? ca.years.indexOf(perf.years[i]) : -1
  const imp = wy >= 0 && ca.impAmt ? Number(ca.impAmt[wy]) / 100 : NaN
  if (isFinite(imp) && imp > 0 && imp < cost) {
    steps.push({ name: '信用减值损失', value: -imp, color: '#c0392b' })
    steps.push({ name: '其他营业支出与税负', value: -(cost - imp), color: '#e59866' })
  } else {
    steps.push({ name: '营业支出与税负', value: -cost, color: COLOR.red })
  }
  steps.push({ name: '净利润', value: profit, color: COLOR.green, total: true })
  return build(steps)
})

// ── 同业对比：留在本页、不走路由切换 ─────────────────────────────
// 导航栏「切换银行」换 ?code= 整页重取（每次只看一家）；这里加「本行 / 本行同类 / 全部上市
// 银行」一个开关，选同业时并发拉各行 /api/company_charts 缓存、按最新披露年度做横比。
// 瀑布是单主体分解、多家无法叠画，且各行体量差一个数量级、绝对亿元横比小行贴底，故同业视图
// 一律改用免体量的「占营收比」100% 堆叠横条。
const TIER_COLORS = { 国有大行: '#c0392b', 股份行: '#1f6feb', 城商行: '#0f766e', 农商行: '#b45309' }
// 四类展示顺序/图例（映射规则本身在后端 gen_company_charts.py，前端只读预拆好的 seg-rev.std）
const REV_BUCKETS = ['公司', '零售', '同业', '其他']

const { data: banksData } = useApiData('/api/banks')
const banks = computed(() => banksData.value || [])
const focusTier = computed(() => {
  const t = data.value && data.value._bank && data.value._bank.tier
  if (t) return t
  const b = banks.value.find((x) => x.code === code.value)
  return b ? b.tier : ''
})

const view = ref('self') // self | peer | all
const TABS = computed(() => [
  { key: 'self', label: '本行', color: COLOR.navy },
  { key: 'peer', label: focusTier.value ? `本行同类 · ${focusTier.value}` : '本行同类', color: TIER_COLORS[focusTier.value] || COLOR.muted },
  { key: 'all', label: '全部上市银行', color: COLOR.muted },
])
const isPeer = computed(() => view.value !== 'self')

const cache = reactive({}) // code -> payload；本行用主数据填，避免重复请求
watch(data, (d) => { if (d && code.value) cache[code.value] = d }, { immediate: true })

const targetCodes = computed(() => {
  if (!isPeer.value) return []
  const inScope = view.value === 'all' ? banks.value : banks.value.filter((b) => b.tier === focusTier.value)
  const codes = inScope.map((b) => b.code)
  if (code.value && !codes.includes(code.value)) codes.unshift(code.value)
  return codes
})

const peerLoading = ref(false)
watch(targetCodes, async (codes) => {
  const missing = codes.filter((c) => !(c in cache))
  if (!missing.length) return
  peerLoading.value = true
  await Promise.all(missing.map(async (c) => {
    try { cache[c] = await apiGet('/api/company_charts', { code: c }) } catch (_) { cache[c] = null }
  }))
  peerLoading.value = false
})
// 某行最新披露年度的利润结构（占营收比）——图②同业对比用
function profitStruct(c) {
  const d = cache[c]
  const perf = d && d.perf
  if (!perf || !Array.isArray(perf.years) || !perf.years.length) return null
  const i = perf.years.length - 1
  const revenue = Number(perf.revenue && perf.revenue[i])
  const profit = Number(perf.profit && perf.profit[i])
  if (!isFinite(revenue) || !isFinite(profit) || revenue <= 0) return null
  const cost = revenue - profit
  const ca = d.creditamount
  const wy = ca && Array.isArray(ca.years) ? ca.years.indexOf(perf.years[i]) : -1
  const impRaw = wy >= 0 && ca.impAmt ? Number(ca.impAmt[wy]) / 100 : NaN
  const imp = isFinite(impRaw) && impRaw > 0 && impRaw < cost ? impRaw : 0
  const b = d._bank || {}
  return {
    code: c, name: b.shortName || c, year: perf.years[i], revenue, profit, imp, other: cost - imp,
    profitPct: (profit / revenue) * 100, impPct: (imp / revenue) * 100,
    otherPct: ((cost - imp) / revenue) * 100, margin: (profit / revenue) * 100,
  }
}
const pnlRows = computed(() =>
  targetCodes.value.map(profitStruct).filter(Boolean).sort((a, b) => a.margin - b.margin)
)
function barSeg(rows, key, focus) {
  return rows.map((r) => ({ value: +r[key].toFixed(2), itemStyle: { opacity: r.code === focus ? 1 : 0.82 } }))
}
// 某行最新披露年度的营收结构（公司/零售/同业/其他 占营收比）——图①同业对比用；
// 归并不出四类（地域分部等）或与营收口径不吻合的行返回 null，不进对比。
function revStruct(c) {
  const d = cache[c]
  const perf = d && d.perf
  if (!perf || !Array.isArray(perf.years) || !perf.years.length) return null
  const i = perf.years.length - 1
  const revenue = Number(perf.revenue && perf.revenue[i])
  if (!isFinite(revenue) || revenue <= 0) return null
  const std = d['seg-rev'] && d['seg-rev'].std
  const arr = std && std.segs && std['rev' + String(perf.years[i]).slice(-2)]
  if (!Array.isArray(arr) || std.segs.length !== arr.length) return null
  const agg = { 公司: 0, 零售: 0, 同业: 0, 其他: 0 }
  std.segs.forEach((name, k) => { agg[name] += Number(arr[k]) / 100 })
  if (Math.abs(revenue - REV_BUCKETS.reduce((a, b) => a + agg[b], 0)) >= 0.5) return null
  const meta = d._bank || {}
  const pct = (v) => (v / revenue) * 100
  return {
    code: c, name: meta.shortName || c, year: perf.years[i], revenue,
    公司: agg.公司, 零售: agg.零售, 同业: agg.同业, 其他: agg.其他,
    公司Pct: pct(agg.公司), 零售Pct: pct(agg.零售), 同业Pct: pct(agg.同业), 其他Pct: pct(agg.其他),
  }
}
const revRows = computed(() => targetCodes.value.map(revStruct).filter(Boolean))
// 图②同业对比：净利 / 信用减值 / 其他支出与税负 占营收比，100% 堆叠横条，净利率降序
const optionCompare = computed(() => {
  const rows = pnlRows.value
  if (rows.length < 2) return null
  const focus = code.value
  return {
    grid: { ...gridBase, left: 8, right: 56, top: 34, bottom: 30 },
    legend: { top: 2, data: ['净利润', '信用减值损失', '其他营业支出与税负'], textStyle: { color: COLOR.axis, fontSize: 12 } },
    tooltip: {
      trigger: 'axis', axisPointer: { type: 'shadow' },
      formatter: (ps) => {
        const r = rows[ps[0].dataIndex]
        return `<b>${r.name}</b>　${r.year} 年<br/>营业收入　${fmtYi(r.revenue)} 亿<br/>` +
          `净利润　${fmtYi(r.profit)} 亿（净利率 ${r.margin.toFixed(2)}%）<br/>` +
          (r.imp > 0 ? `信用减值损失　${fmtYi(r.imp)} 亿（占营收 ${r.impPct.toFixed(2)}%）<br/>` : '') +
          `其他营业支出与税负　${fmtYi(r.other)} 亿（占营收 ${r.otherPct.toFixed(2)}%）`
      },
    },
    xAxis: valAxis({ max: 100, axisLabel: { formatter: '{value}%', color: COLOR.axis, fontSize: 12 } }),
    yAxis: catAxis(rows.map((r) => r.name), {
      axisLabel: {
        color: COLOR.axis, fontSize: 13,
        formatter: (v, idx) => (rows[idx].code === focus ? `{me|${v}}` : v),
        rich: { me: { fontSize: 13, fontWeight: 700, color: '#10243e' } },
      },
    }),
    series: [
      { name: '净利润', type: 'bar', stack: 's', barMaxWidth: 22, itemStyle: { color: COLOR.green }, data: barSeg(rows, 'profitPct', focus),
        label: { show: true, position: 'insideRight', color: '#fff', fontSize: 11, formatter: (p) => rows[p.dataIndex].margin.toFixed(1) + '%' } },
      { name: '信用减值损失', type: 'bar', stack: 's', barMaxWidth: 22, itemStyle: { color: '#c0392b' }, data: barSeg(rows, 'impPct', focus) },
      { name: '其他营业支出与税负', type: 'bar', stack: 's', barMaxWidth: 22, itemStyle: { color: '#e59866' }, data: barSeg(rows, 'otherPct', focus) },
    ],
  }
})
// 图①同业对比：公司 / 零售 / 同业 / 其他 占营收比，100% 堆叠横条（保留类型分组顺序）
const REV_SEG_COLORS = { 公司: COLOR.navy, 零售: COLOR.green, 同业: COLOR.gold, 其他: COLOR.muted }
const optionRevCompare = computed(() => {
  const rows = revRows.value
  if (rows.length < 2) return null
  const focus = code.value
  return {
    grid: { ...gridBase, left: 8, right: 56, top: 34, bottom: 30 },
    legend: { top: 2, data: REV_BUCKETS, textStyle: { color: COLOR.axis, fontSize: 12 } },
    tooltip: {
      trigger: 'axis', axisPointer: { type: 'shadow' },
      formatter: (ps) => {
        const r = rows[ps[0].dataIndex]
        return `<b>${r.name}</b>　${r.year} 年<br/>营业收入　${fmtYi(r.revenue)} 亿<br/>` +
          REV_BUCKETS.map((b) => `${b}　${fmtYi(r[b])} 亿（${r[b + 'Pct'].toFixed(1)}%）`).join('<br/>')
      },
    },
    xAxis: valAxis({ max: 100, axisLabel: { formatter: '{value}%', color: COLOR.axis, fontSize: 12 } }),
    yAxis: catAxis(rows.map((r) => r.name), {
      axisLabel: {
        color: COLOR.axis, fontSize: 13,
        formatter: (v, idx) => (rows[idx].code === focus ? `{me|${v}}` : v),
        rich: { me: { fontSize: 13, fontWeight: 700, color: '#10243e' } },
      },
    }),
    series: REV_BUCKETS.map((b) => ({
      name: b, type: 'bar', stack: 's', barMaxWidth: 22, itemStyle: { color: REV_SEG_COLORS[b] }, data: barSeg(rows, b + 'Pct', focus),
    })),
  }
})
// 卡片视图分派：本行→单行瀑布，同业→结构对比
const scopeLabel = computed(() => (view.value === 'all' ? '全部上市银行' : `同类 · ${focusTier.value || '同业'}`))
const revCardTitle = computed(() => (isPeer.value ? `营收结构对比 · ${scopeLabel.value}` : revTitle.value))
const pnlCardTitle = computed(() => (isPeer.value ? `盈利结构对比 · ${scopeLabel.value}（净利率降序）` : pnlTitle.value))
const cmpSub = '各行最新披露年度 · 单位：占营业收入 %'
const revCardSub = computed(() => (isPeer.value ? cmpSub : cardSub.value))
const pnlCardSub = computed(() => (isPeer.value ? cmpSub : cardSub.value))
const revCmpNote =
  '免体量口径：各行按最新披露年度把营业收入拆成 公司/零售/同业/其他 四类占比（合计 100%）横比。' +
  '按地域分部或无法归入四类的行（如本行按地域披露时）不纳入；深色为本页银行，各行最新年度可能不一致。'
const pnlCmpNote =
  '免体量口径：各行按最新披露年度把营业收入拆成 净利润 / 信用减值损失 / 其他营业支出与税负 三段占比（合计 100%），' +
  '比结构而非规模——绝对亿元跨行差一个数量级、小行贴底。深色为本页银行；缺信用减值披露的行该段计 0、并入其他；' +
  '各行最新年度可能不一致，具体见悬浮。'
const revCardNote = computed(() => (isPeer.value ? revCmpNote : revNote))
const pnlCardNote = computed(() => (isPeer.value ? pnlCmpNote : pnlNote))
const revCardLoading = computed(() => (isPeer.value ? peerLoading.value : loading.value))
const pnlCardLoading = computed(() => (isPeer.value ? peerLoading.value : loading.value))
const revCardError = computed(() => (isPeer.value ? '' : error.value))
const pnlCardError = computed(() => (isPeer.value ? '' : error.value))
const revCardOption = computed(() => (isPeer.value ? optionRevCompare.value : optionRevenue.value))
const pnlCardOption = computed(() => (isPeer.value ? optionCompare.value : optionProfit.value))
const rowH = 28
const revCardHeight = computed(() => (isPeer.value ? Math.max(360, revRows.value.length * rowH + 96) + 'px' : '440px'))
const pnlCardHeight = computed(() => (isPeer.value ? Math.max(360, pnlRows.value.length * rowH + 96) + 'px' : '440px'))
const revCardEmptyText = computed(() => (isPeer.value ? '所选范围内无可归类到四类的营收结构' : '该行分部收入未披露，或与营业收入口径不吻合'))
const pnlCardEmptyText = computed(() => (isPeer.value ? '所选范围暂无可比数据' : '该行暂无营收/利润数据'))
const revCardKey = computed(() => (isPeer.value ? `rc-${revRows.value.length}` : 'r-self'))
const pnlCardKey = computed(() => (isPeer.value ? `pc-${pnlRows.value.length}` : 'p-self'))
// 胶囊滑块：贴到选中项（宽度/位置在 DOM 更新后量，选中态加粗会改变宽度）
const tabsEl = ref(null)
const sliderStyle = ref({})
function moveSlider() {
  const bar = tabsEl.value
  if (!bar) return
  const idx = Math.max(0, TABS.value.findIndex((t) => t.key === view.value))
  const btn = bar.querySelectorAll('.stack-tab')[idx]
  if (btn) sliderStyle.value = { width: btn.offsetWidth + 'px', transform: `translateX(${btn.offsetLeft}px)` }
}
function setView(k) {
  if (view.value === k) return
  view.value = k
  nextTick(moveSlider)
}
watch([focusTier, banks], () => nextTick(moveSlider))
function onWinResize() { moveSlider() }
onMounted(() => {
  nextTick(moveSlider)
  window.addEventListener('resize', onWinResize)
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => nextTick(moveSlider))
})
onBeforeUnmount(() => window.removeEventListener('resize', onWinResize))
</script>

<style scoped>
.bank-income-waterfall { padding: 16px; }

/* 同业对比开关：复用油价页 .stack-tabs 胶囊分段控件（chart-view-switch 规则） */
.peer-tabs { max-width: var(--content-w, 1200px); margin: 4px auto 6px; padding: 0 20px; box-sizing: border-box; }
.stack-tabs {
  position: relative; display: flex; width: fit-content; margin-left: auto;
  padding: 5px; background: #eceff3; border-radius: 999px;
  box-shadow: inset 0 1px 3px rgba(15, 23, 42, 0.07);
}

.stack-tab {
  position: relative; z-index: 1; display: inline-flex; align-items: center; gap: 8px;
  font: inherit; font-size: 15px; line-height: 1.4; padding: 8px 18px; background: transparent;
  border: none; border-radius: 999px; color: #6b7280; white-space: nowrap; cursor: pointer;
  transition: color 0.25s ease;
}

</style>
