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

// 复刻 dashboard/common/site-header.js 的分组导航：按当前路由所属分组列出该行业的页面链接，
// 样式沿用 base.css 的 .site-nav / .brand / a.active（与原站一致）。各批次迁移时在此补齐分组。
const route = useRoute()

const GROUPS = [
  {
    prefix: '/subject/oil/',
    pages: [
      { to: '/subject/oil/price', title: '油价 K 线' },
      { to: '/subject/oil/region-production', title: '产量总览' },
      { to: '/subject/oil/consumption', title: '消费总览' },
      { to: '/subject/oil/country-change', title: '2001 vs 2024' },
      { to: '/subject/oil/majors', title: '油企' },
      { to: '/subject/oil/cnooc-roa', title: '中海油 油价·ROA' },
    ],
  },
  {
    prefix: '/industry/bank/',
    pages: [
      { to: '/industry/bank/overview', title: 'A/H 股概览' },
      { to: '/industry/bank/tsf', title: '社会融资规模' },
      { to: '/industry/bank/npl-formation', title: '息差与不良生成对比' },
      { to: '/industry/bank/reform-timeline', title: '重要变革时间线' },
      { to: '/company/shareholder?code=601077', title: '股权结构' },
    ],
  },
  {
    prefix: '/industry/insurance/',
    pages: [
      { to: '/industry/insurance/overview', title: 'A/H 股概览' },
      { to: '/industry/insurance/peers', title: '五大险企对比' },
      { to: '/company/shareholder?code=601318', title: '股权结构' },
    ],
  },
  {
    prefix: '/industry/realestate/',
    pages: [
      { to: '/industry/realestate/overview', title: '央企名录与政策线' },
      { to: '/industry/realestate/peers', title: '六家央企开发商对比' },
      { to: '/company/shareholder?code=600048', title: '股权结构' },
    ],
  },
  {
    prefix: '/industry/cement/',
    pages: [
      { to: '/industry/cement/overview', title: '名录与供给侧政策线' },
      { to: '/industry/cement/peers', title: '八家水泥企业对比' },
      { to: '/company/shareholder?code=600585', title: '股权结构' },
    ],
  },
  {
    prefix: '/industry/telecom/',
    pages: [
      { to: '/industry/telecom/overview', title: '名录与变革时间线' },
      { to: '/industry/telecom/peers', title: '三大运营商对比' },
      { to: '/company/telecom', title: '公司详情' },
      { to: '/company/shareholder?code=600941', title: '股权结构' },
    ],
  },
  {
    prefix: '/company/telecom/',
    pages: [
      { to: '/company/telecom/index', title: '业绩' },
      { to: '/company/telecom/operation', title: '客户与网络' },
      { to: '/company/telecom/segment', title: '分部' },
      { to: '/company/shareholder?code=600941', title: '股权结构' },
    ],
  },
  {
    prefix: '/company/cmcc/',
    pages: [
      { to: '/company/cmcc/index', title: '业绩' },
      { to: '/company/cmcc/product', title: '产品更迭' },
      { to: '/company/cmcc/operation', title: '客户与网络' },
      { to: '/company/cmcc/intro', title: '简介与股权' },
    ],
  },
  {
    prefix: '/company/baidu/',
    pages: [
      { to: '/company/baidu/index', title: '业绩' },
      { to: '/company/baidu/segment', title: '分部与运营' },
      { to: '/company/baidu/balance-sheet', title: '资产与现金' },
      { to: '/company/shareholder?code=09888', title: '股权结构' },
      { to: '/company/baidu/intro', title: '简介' },
    ],
  },
  {
    prefix: '/company/food/',
    pages: [
      { to: '/company/food/overview', title: '年报概览' },
      { to: '/company/food/peer-comparison', title: '同业对比' },
      { to: '/company/shareholder?code=605338', title: '股权结构' },
    ],
  },
]

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
  const g = GROUPS.find((x) => x.prefix === prefix)
  return g ? g.pages : []
}
// 银行板块的股权页挂「银行公司导航」（股东 + 六个栏目，按 code 指到 /company/bank/:code/*），
// 其余板块挂各自的行业分组导航。
function shareholderLinks(industry, code) {
  if (industry === 'bank') {
    const segs = [['index', '业绩'], ['asset', '资产端'], ['debt', '负债端'], ['risk', '风控'], ['intro', '简介'], ['balance-sheet', '资产负债表']]
    return [
      { to: `/company/shareholder?code=${code}`, title: '股东' },
      ...segs.map(([s, t]) => ({ to: `/company/bank/${code}/${s}`, title: t })),
    ]
  }
  const map = { insurer: '/industry/insurance/', developer: '/industry/realestate/', cement: '/industry/cement/', telecom: '/industry/telecom/', tech: '/company/baidu/' }
  return map[industry] ? groupPages(map[industry]) : []
}

const links = computed(() => {
  if (route.path === '/company/shareholder' && shBoard.value) {
    return shareholderLinks(shBoard.value.industry, shBoard.value.code)
  }
  const g = GROUPS.find((x) => route.path.startsWith(x.prefix))
  return g ? g.pages : []
})
</script>
