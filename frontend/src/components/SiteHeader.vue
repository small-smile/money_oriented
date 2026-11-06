<template>
  <!-- 银行代码的股权页：换成银行页同一条 header（含按机构类型分列的银行筛选面板） -->
  <BankNav v-if="isBankShareholder" :code="shBoard.code" current="shareholder" />
  <nav v-else class="site-nav">
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
import { navGroups, shareholderBoardPrefix } from '../site.config'
import BankNav from '../views/company/bank/BankNav.vue'

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
// 银行板块的股权页整条换成 BankNav（与银行详情页同一份导航 + 银行筛选），其余板块挂各自的行业分组导航。
const isBankShareholder = computed(() =>
  route.path === '/company/shareholder' && !!shBoard.value && shBoard.value.industry === 'bank')

const links = computed(() => {
  if (route.path === '/company/shareholder' && shBoard.value) {
    const prefix = shareholderBoardPrefix[shBoard.value.industry]
    return prefix ? groupPages(prefix) : []
  }
  const g = navGroups.find((x) => route.path.startsWith(x.prefix))
  return g ? g.pages : []
})
</script>
