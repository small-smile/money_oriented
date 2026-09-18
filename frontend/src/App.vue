<template>
  <SiteHeader v-if="useSiteHeader" />
  <main>
    <router-view />
  </main>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import SiteHeader from './components/SiteHeader.vue'

const route = useRoute()
// 单一动态 header：首页(hub 本身即导航)、银行页(自带含切换器的银行导航)、食品页(自带 mini-nav)
// 各自只有自己那一条 header，这里不再叠加全局 SiteHeader；其余页面用 SiteHeader 的分组导航。
const useSiteHeader = computed(() => {
  const p = route.path
  return p !== '/' && !p.startsWith('/company/bank')
})
</script>

<style scoped>
main { min-height: 60vh; }
</style>
