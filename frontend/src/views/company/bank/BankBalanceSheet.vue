<template>
  <!-- balance-sheet.html <body> → ./legacy/balance-sheet.body.html（?raw + v-html 原样注入） -->
  <div ref="rootEl" class="bank-legacy-page" v-html="bodyHtml"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { exposeGlobals, ensureBanks, setCompanyCode, loadLegacyScripts, cleanupLegacy } from './useBankLegacy'
import bodyHtml from './legacy/balance-sheet.body.html?raw'

const route = useRoute()
const rootEl = ref(null)
let nodes = []

onMounted(async () => {
  exposeGlobals()
  setCompanyCode(route.params.code)
  await ensureBanks()
  nodes = loadLegacyScripts()
})
onBeforeUnmount(() => {
  cleanupLegacy(rootEl.value, nodes)
  nodes = []
})
</script>
