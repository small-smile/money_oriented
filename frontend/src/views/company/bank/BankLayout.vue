<template>
  <!-- 银行页唯一的一条 header：复刻 bank-header.js —— 左上角 brand + 居中的页面链接/银行切换器。
       全局 SiteHeader 在银行路由下不渲染（见 App.vue），故本条 sticky 到 top:0（base.css .site-nav）。 -->
  <nav class="site-nav">
    <router-link class="brand" to="/">📊 行业看板</router-link>
    <div class="nav-center">
      <router-link :to="`/company/shareholder?code=${code}`">股东</router-link>
      <router-link
        v-for="s in SUBPAGES"
        :key="s.seg"
        :to="pagePath(code, s.seg)"
        :class="{ active: isActive(s.seg) }"
      >{{ s.title }}</router-link>
      <div class="nav-banks" ref="boxEl">
        <label>银行</label>
        <button type="button" class="nav-bank-trigger" ref="triggerEl" title="点击按机构类型选择银行" @click.stop="toggle">
          <span class="cur-name">{{ curName }}</span><span class="caret">▾</span>
        </button>
      </div>
    </div>
  </nav>

  <!-- 面板 position:fixed 且必须挂在 .site-nav 之外（导航条 overflow-x:auto 会裁掉），用 Teleport 到 body。 -->
  <Teleport to="body">
    <div class="nav-bank-panel" :hidden="!open" ref="panelEl">
      <div class="nav-bank-col" v-for="g in groups" :key="g.tier">
        <div class="bg-head">{{ g.tier }}（{{ g.list.length }}）</div>
        <div class="bg-items">
          <button
            type="button"
            v-for="b in g.list"
            :key="b.code"
            class="bg-item"
            :class="{ active: b.code === curCode }"
            @click="switchBank(b.code)"
          >
            <span class="bg-name">{{ b.name }}</span>
            <span class="bg-date" v-if="b.aListDate">A {{ b.aListDate }}</span>
            <span class="bg-date" v-if="b.hListDate">H {{ b.hListDate }}</span>
          </button>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- 切换银行/切换页面都要让子页重挂载（原站每次切换都整页重载），故按 fullPath 打 key。 -->
  <router-view :key="route.fullPath" />
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ensureBanks, exposeGlobals, setCompanyCode } from './useBankLegacy'
// 银行页专属正文样式（dashboard/company/page.css 逐字复制）。base.css 已在 main.js 全局引入，不重复。
import './legacy/page.css'

const route = useRoute()
const router = useRouter()

const DEFAULT_CODE = '601077' // 与 charts.js / 后端 DEFAULT_BANK_CODE 一致
const TIER_ORDER = ['国有大行', '股份行', '城商行', '农商行']
// 顺序与 bank-header.js 的 PAGES 一致（去掉「股东」单列，它是独立路由）
const SUBPAGES = [
  { seg: 'index', title: '业绩' },
  { seg: 'asset', title: '资产端' },
  { seg: 'debt', title: '负债端' },
  { seg: 'risk', title: '风控' },
  { seg: 'intro', title: '简介' },
  { seg: 'balance-sheet', title: '资产负债表' },
]

const banks = ref([])
const open = ref(false)
const boxEl = ref(null)
const triggerEl = ref(null)
const panelEl = ref(null)

const code = computed(() => {
  const c = route.params.code
  return /^[0-9]{5,6}$/.test(c || '') ? String(c) : DEFAULT_CODE
})
const curCode = computed(() => (banks.value.some((b) => b.code === code.value) ? code.value : DEFAULT_CODE))
const curName = computed(() => {
  const b = banks.value.find((x) => x.code === curCode.value)
  return b ? b.name : curCode.value
})
const curSub = computed(() => {
  const seg = route.path.split('/').filter(Boolean).pop()
  return SUBPAGES.some((s) => s.seg === seg) ? seg : 'index'
})

// tier 分组分列（与 bank-header.js 一致：未知 tier 归「其他」，TIER_ORDER 优先、其余置尾）
const groups = computed(() => {
  const m = new Map()
  for (const b of banks.value) {
    const t = b.tier || '其他'
    if (!m.has(t)) m.set(t, [])
    m.get(t).push(b)
  }
  const tiers = [...m.keys()].sort((a, c) => {
    const ia = TIER_ORDER.indexOf(a)
    const ic = TIER_ORDER.indexOf(c)
    return (ia < 0 ? TIER_ORDER.length : ia) - (ic < 0 ? TIER_ORDER.length : ic)
  })
  return tiers.map((t) => ({ tier: t, list: m.get(t) }))
})

function pagePath(c, seg) {
  return `/company/bank/${c}/${seg}`
}
function isActive(seg) {
  return curSub.value === seg
}
function switchBank(c) {
  open.value = false
  router.push(pagePath(c, curSub.value)) // 保持当前栏目，只换 code
}

// ── 面板折列 + 定位（逐段复刻 bank-header.js 的 layoutBankColumns()/place()）──
function layoutBankColumns() {
  const panel = panelEl.value
  if (!panel) return
  const cols = [...panel.querySelectorAll('.bg-items')]
  for (const items of cols) {
    items.style.height = 'auto'
    items.style.width = 'auto'
  }
  const top = panel.getBoundingClientRect().top
  const avail = Math.max(200, window.innerHeight - top - 40)
  const COL_GAP = 10
  for (const items of cols) {
    const kids = [...items.children]
    if (!kids.length) continue
    const head = items.previousElementSibling
    const headH = head ? head.getBoundingClientRect().height + 6 : 0
    const cap = Math.max(140, avail - headH - 28)
    const r0 = kids[0].getBoundingClientRect()
    const step = kids.length > 1 ? kids[1].getBoundingClientRect().top - r0.top : r0.height
    const perCol = Math.max(1, Math.floor((cap + (step - r0.height)) / step))
    const nCol = Math.ceil(kids.length / perCol)
    const rows = Math.min(kids.length, perCol)
    items.style.height = rows * step - (step - r0.height) + 'px'
    items.style.width = nCol * r0.width + (nCol - 1) * COL_GAP + 'px'
  }
}
function place() {
  const panel = panelEl.value
  const trigger = triggerEl.value
  if (!panel || !trigger) return
  const tr = trigger.getBoundingClientRect()
  panel.style.top = tr.bottom + 6 + 'px'
  panel.style.left = '0px'
  const w = panel.getBoundingClientRect().width
  panel.style.left = Math.max(12, Math.min(tr.left, window.innerWidth - 12 - w)) + 'px'
}
function reflow() {
  place()
  layoutBankColumns()
  place() // 折列后宽度变了再夹一次左边界
}
function toggle() {
  open.value = !open.value
  if (open.value) nextTick(reflow)
}

function onDocClick(e) {
  if (!open.value) return
  const inBox = boxEl.value && boxEl.value.contains(e.target)
  const inPanel = panelEl.value && panelEl.value.contains(e.target)
  if (!inBox && !inPanel) open.value = false
}
function onKey(e) {
  if (e.key === 'Escape') open.value = false
}
function onResize() {
  if (open.value) nextTick(reflow)
}
function onScroll() {
  if (open.value) place()
}

// BankLayout 一挂载/切 code 就把 COMPANY_CODE 写进 window（子页脚本读它拉数据）
watch(code, (c) => setCompanyCode(c), { immediate: true })

onMounted(async () => {
  exposeGlobals()
  banks.value = await ensureBanks()
  document.addEventListener('click', onDocClick)
  document.addEventListener('keydown', onKey)
  window.addEventListener('resize', onResize)
  window.addEventListener('scroll', onScroll, { passive: true })
})
onBeforeUnmount(() => {
  document.removeEventListener('click', onDocClick)
  document.removeEventListener('keydown', onKey)
  window.removeEventListener('resize', onResize)
  window.removeEventListener('scroll', onScroll)
})
</script>

