<template>
  <!-- index.html <body> 结构逐字复制到 ./legacy/index.body.html，用 ?raw + v-html 原样注入，
       避免任何模板编译改写；onMounted 再注入 legacy 脚本，让原逻辑按 DOM id 渲染进这些容器。 -->
  <div ref="rootEl" class="bank-legacy-page" v-html="bodyHtml"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { exposeGlobals, ensureBanks, setCompanyCode, loadLegacyScripts, cleanupLegacy } from './useBankLegacy'
import bodyHtml from './legacy/index.body.html?raw'

const route = useRoute()
const rootEl = ref(null)
let nodes = []

onMounted(async () => {
  exposeGlobals() // window.echarts / window.axios
  setCompanyCode(route.params.code) // window.COMPANY_CODE（core.js 读它，非法回退 601077）
  await ensureBanks() // window.__BANKS 就绪后再加载脚本（switcher.js / ROE 对比读它）
  nodes = loadLegacyScripts() // core…statement…switcher…charts，charts 末尾自执行 fetch+renderAll
})
onBeforeUnmount(() => {
  cleanupLegacy(rootEl.value, nodes)
  nodes = []
})
</script>
