<template>
  <nav class="site-nav">
    <router-link class="brand" to="/">📊 行业看板</router-link>
    <router-link
      v-for="p in links"
      :key="p.to"
      :to="p.to"
      :class="{ active: route.path === p.to.split('?')[0] }"
    >{{ p.title }}</router-link>
  </nav>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { apiGet } from '../api'
// 分组导航数据抽到 src/site.config.js（与 router / Home 同源）。本组件只保留「按路由挑分组」的逻辑。
import { navGroups, shareholderBoardPrefix, bankSubPages } from '../site.config'

const route = useRoute()

// 股权结构页没有固定路由分组：按 ?code= 问后端 /api/nav 得所属板块，再挂该板块导航
// （复刻原站 shareholder.html 按 /api/nav 动态载 header 的行为）。
const shBoard = ref(null)
watch(
  () => route.fullPath,
  async () => {
    if (route.path === '/company/shareholder') {
      try {
        const d = await apiGet('/api/nav', { code: route.query.code || '' })
        shBoard.value = { industry: d.industry, code: d.code || route.query.code || '' }
      } catch (e) {
        shBoard.value = null
      }
    } else {
      shBoard.value = null
    }
  },
  { immediate: true }
)

function groupPages(prefix) {
  const g = navGroups.find((x) => x.prefix === prefix)
  return g ? g.pages : []
}
// 银行板块的股权页挂「银行公司导航」（股东 + bankSubPages 各栏，按 code 指到 /company/bank/:code/*），
// 其余板块挂各自的行业分组导航。
function shareholderLinks(industry, code) {
  if (industry === 'bank') {
    return [
      { to: `/company/shareholder?code=${code}`, title: '股东' },
      ...bankSubPages.map((s) => ({ to: `/company/bank/${code}/${s.seg}`, title: s.title })),
    ]
  }
  const prefix = shareholderBoardPrefix[industry]
  return prefix ? groupPages(prefix) : []
}

const links = computed(() => {
  if (route.path === '/company/shareholder' && shBoard.value) {
    return shareholderLinks(shBoard.value.industry, shBoard.value.code)
  }
  const g = navGroups.find((x) => route.path.startsWith(x.prefix))
  return g ? g.pages : []
})
</script>
