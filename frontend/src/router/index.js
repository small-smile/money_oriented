import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'

// 页面按批次迁入；每迁一页在此登记一条路由。数据全部走后端 /api，
// 样式复用 base.css + 各页原有 CSS，图表 option 从原 charts 代码逐字搬入。
const routes = [
  { path: '/', name: 'home', component: Home, meta: { title: '行业看板' } },
  {
    path: '/subject/oil/country-change',
    name: 'oil-country-change',
    component: () => import('../views/oil/OilCountryChange.vue'),
    meta: { title: '各洲石油产量对比：2001 vs 2024' },
  },
  // 石油分组：全部迁完，逐字搬。
  { path: '/subject/oil/price', component: () => import('../views/oil/OilPriceHistory.vue'), meta: { title: '油价 K 线' } },
  { path: '/subject/oil/region-production', component: () => import('../views/oil/OilRegionProduction.vue'), meta: { title: '产量总览' } },
  { path: '/subject/oil/consumption', component: () => import('../views/oil/OilCountryConsumption.vue'), meta: { title: '消费总览' } },
  { path: '/subject/oil/majors', component: () => import('../views/oil/OilMajors.vue'), meta: { title: '油企' } },
  { path: '/subject/oil/cnooc-roa', component: () => import('../views/oil/OilCnoocRoa.vue'), meta: { title: '中海油 油价·ROA' } },

  // 行业分组（全部逐字迁移）
  { path: '/industry/bank/overview', component: () => import('../views/industry/bank/BankOverview.vue'), meta: { title: '银行 A/H 股概览' } },
  { path: '/industry/bank/tsf', component: () => import('../views/industry/bank/BankTsf.vue'), meta: { title: '社会融资规模' } },
  { path: '/industry/bank/npl-formation', component: () => import('../views/industry/bank/BankNplFormation.vue'), meta: { title: '息差与不良生成对比' } },
  { path: '/industry/bank/reform-timeline', component: () => import('../views/industry/bank/BankReformTimeline.vue'), meta: { title: '银行业重要变革时间线' } },
  { path: '/industry/insurance/overview', component: () => import('../views/industry/insurance/InsuranceOverview.vue'), meta: { title: '保险 A/H 股概览' } },
  { path: '/industry/insurance/peers', component: () => import('../views/industry/insurance/InsurancePeers.vue'), meta: { title: '五大险企对比' } },
  { path: '/industry/realestate/overview', component: () => import('../views/industry/realestate/RealestateOverview.vue'), meta: { title: '央企名录与政策线' } },
  { path: '/industry/realestate/peers', component: () => import('../views/industry/realestate/RealestatePeers.vue'), meta: { title: '六家央企开发商对比' } },
  { path: '/industry/cement/overview', component: () => import('../views/industry/cement/CementOverview.vue'), meta: { title: '名录与供给侧政策线' } },
  { path: '/industry/cement/peers', component: () => import('../views/industry/cement/CementPeers.vue'), meta: { title: '八家水泥企业对比' } },
  { path: '/industry/telecom/overview', component: () => import('../views/industry/telecom/TelecomOverview.vue'), meta: { title: '名录与变革时间线' } },
  { path: '/industry/telecom/peers', component: () => import('../views/industry/telecom/TelecomPeers.vue'), meta: { title: '三大运营商对比' } },

  // 股权结构（全站一页，按 ?code= 服务各板块）
  { path: '/company/shareholder', component: () => import('../views/company/Shareholder.vue'), meta: { title: '股权结构' } },

  // 通信运营商公司详情
  { path: '/company/telecom', redirect: '/company/telecom/index' },
  { path: '/company/telecom/index', component: () => import('../views/company/telecom/TelecomIndex.vue'), meta: { title: '通信公司·业绩' } },
  { path: '/company/telecom/operation', component: () => import('../views/company/telecom/TelecomOperation.vue'), meta: { title: '通信公司·客户与网络' } },
  { path: '/company/telecom/segment', component: () => import('../views/company/telecom/TelecomSegment.vue'), meta: { title: '通信公司·分部' } },

  // 中国移动
  { path: '/company/cmcc/index', component: () => import('../views/company/cmcc/CmccIndex.vue'), meta: { title: '中国移动·业绩' } },
  { path: '/company/cmcc/product', component: () => import('../views/company/cmcc/CmccProduct.vue'), meta: { title: '中国移动·产品更迭' } },
  { path: '/company/cmcc/operation', component: () => import('../views/company/cmcc/CmccOperation.vue'), meta: { title: '中国移动·客户与网络' } },
  { path: '/company/cmcc/intro', component: () => import('../views/company/cmcc/CmccIntro.vue'), meta: { title: '中国移动·简介与股权' } },

  // 百度
  { path: '/company/baidu/index', component: () => import('../views/company/baidu/BaiduIndex.vue'), meta: { title: '百度·业绩' } },
  { path: '/company/baidu/segment', component: () => import('../views/company/baidu/BaiduSegment.vue'), meta: { title: '百度·分部与运营' } },
  { path: '/company/baidu/balance-sheet', component: () => import('../views/company/baidu/BaiduBalanceSheet.vue'), meta: { title: '百度·资产与现金' } },
  { path: '/company/baidu/intro', component: () => import('../views/company/baidu/BaiduIntro.vue'), meta: { title: '百度·简介' } },

  // 食品
  { path: '/company/food/overview', component: () => import('../views/company/food/FoodOverview.vue'), meta: { title: '巴比食品' } },
  { path: '/company/food/peer-comparison', component: () => import('../views/company/food/FoodPeerComparison.vue'), meta: { title: '食品·同业对比' } },
  // 原孤立的石油公司页（源页为空骨架，routed 以免丢失）
  { path: '/company/oil/petro-income-waterfall', component: () => import('../views/company/oil/PetroIncomeWaterfall.vue'), meta: { title: '中石油 利润→营收 瀑布图' } },

  // 银行公司详情（同一份页面按 code 渲染 + 切换器）
  { path: '/company/bank', redirect: '/company/bank/601077/index' },
  {
    path: '/company/bank/:code',
    component: () => import('../views/company/bank/BankLayout.vue'),
    children: [
      { path: '', redirect: (to) => `/company/bank/${to.params.code}/index` },
      { path: 'index', component: () => import('../views/company/bank/BankIndex.vue'), meta: { title: '银行·业绩' } },
      { path: 'asset', component: () => import('../views/company/bank/BankAsset.vue'), meta: { title: '银行·资产端' } },
      { path: 'debt', component: () => import('../views/company/bank/BankDebt.vue'), meta: { title: '银行·负债端' } },
      { path: 'risk', component: () => import('../views/company/bank/BankRisk.vue'), meta: { title: '银行·风控' } },
      { path: 'intro', component: () => import('../views/company/bank/BankIntro.vue'), meta: { title: '银行·简介' } },
      { path: 'balance-sheet', component: () => import('../views/company/bank/BankBalanceSheet.vue'), meta: { title: '银行·资产负债表' } },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.afterEach((to) => {
  if (to.meta.title) document.title = to.meta.title
})

// 兜底：旧站的 *.html 地址去掉 .html 再匹配（保留 query/hash），如 /company/shareholder.html → /company/shareholder
router.beforeEach((to) => {
  if (to.path.endsWith('.html')) {
    return { path: to.path.slice(0, -5), query: to.query, hash: to.hash }
  }
})

export default router
