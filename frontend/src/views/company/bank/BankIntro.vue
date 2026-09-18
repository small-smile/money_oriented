<template>
  <!-- intro.html <body> → ./legacy/intro.body.html（?raw + v-html 原样注入） -->
  <div ref="rootEl" class="bank-legacy-page" v-html="bodyHtml"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { exposeGlobals, ensureBanks, setCompanyCode, loadLegacyScripts, cleanupLegacy } from './useBankLegacy'
import bodyHtml from './legacy/intro.body.html?raw'

const route = useRoute()
const rootEl = ref(null)
let nodes = []

// 逐字复刻 intro.html 里那段内联 <script>：把 KPI 卡的 A/H 股 IPO 日期从 window.__BANKS 里
// 601077（本页主体银行，正文固定为渝农商行）的 aListDate/hListDate 取出覆盖硬编码兜底日期。
function applyIntroIpoDates() {
  const PAGE_CODE = '601077'
  const banks = Array.isArray(window.__BANKS) ? window.__BANKS : []
  const bank = banks.find((b) => b.code === PAGE_CODE)
  if (!bank) return
  const root = rootEl.value
  if (!root) return
  const a = root.querySelector('[data-ipo="a"]')
  const h = root.querySelector('[data-ipo="h"]')
  if (a && bank.aListDate) a.textContent = bank.aListDate
  if (h && bank.hListDate) h.textContent = bank.hListDate
}

onMounted(async () => {
  exposeGlobals()
  setCompanyCode(route.params.code)
  await ensureBanks()
  applyIntroIpoDates()
  nodes = loadLegacyScripts()
})
onBeforeUnmount(() => {
  cleanupLegacy(rootEl.value, nodes)
  nodes = []
})
</script>
