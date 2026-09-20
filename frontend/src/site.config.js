// 全站「板块 → 页面」唯一来源：router / SiteHeader 导航分组 / Home 首页卡片皆从此派生。
// 加一个行业/专题：在这里加一条路由 + 对应导航分组（+ 首页卡片），三处自动生效，
// 不必再分别改 router、SiteHeader、Home。数据仍走后端 /api，样式复用 base.css。
// 注：所有路由（含首页）都用 () => import() 懒加载，本文件因此不静态依赖任何 .vue，
// Home 与本文件无循环引用，且可被 node 直接 import 做配置校验（见 scripts/check-config.mjs）。

// ── 路由（router/index.js 直接消费）────────────────────────────────────
export const routes = [
  { path: '/', name: 'home', component: () => import('./views/Home.vue'), meta: { title: '行业看板' } },

  // 石油专题
  { path: '/subject/oil/country-change', name: 'oil-country-change', component: () => import('./views/oil/OilCountryChange.vue'), meta: { title: '各洲石油产量对比：2001 vs 2024' } },
  { path: '/subject/oil/price', component: () => import('./views/oil/OilPriceHistory.vue'), meta: { title: '油价 K 线' } },
  { path: '/subject/oil/region-production', component: () => import('./views/oil/OilRegionProduction.vue'), meta: { title: '产量总览' } },
  { path: '/subject/oil/consumption', component: () => import('./views/oil/OilCountryConsumption.vue'), meta: { title: '消费总览' } },
  { path: '/subject/oil/majors', component: () => import('./views/oil/OilMajors.vue'), meta: { title: '油企' } },
  { path: '/subject/oil/cnooc-roa', component: () => import('./views/oil/OilCnoocRoa.vue'), meta: { title: '中海油 油价·ROA' } },

  // 行业
  { path: '/industry/bank/overview', component: () => import('./views/industry/bank/BankOverview.vue'), meta: { title: '银行 A/H 股概览' } },
  { path: '/industry/bank/tsf', component: () => import('./views/industry/bank/BankTsf.vue'), meta: { title: '社会融资规模' } },
  { path: '/industry/bank/npl-formation', component: () => import('./views/industry/bank/BankNplFormation.vue'), meta: { title: '息差与不良生成对比' } },
  { path: '/industry/bank/reform-timeline', component: () => import('./views/industry/bank/BankReformTimeline.vue'), meta: { title: '银行业重要变革时间线' } },
  { path: '/industry/insurance/overview', component: () => import('./views/industry/insurance/InsuranceOverview.vue'), meta: { title: '保险 A/H 股概览' } },
  { path: '/industry/insurance/peers', component: () => import('./views/industry/insurance/InsurancePeers.vue'), meta: { title: '五大险企对比' } },
  { path: '/industry/realestate/overview', component: () => import('./views/industry/realestate/RealestateOverview.vue'), meta: { title: '央企名录与政策线' } },
  { path: '/industry/realestate/peers', component: () => import('./views/industry/realestate/RealestatePeers.vue'), meta: { title: '六家央企开发商对比' } },
  { path: '/industry/cement/overview', component: () => import('./views/industry/cement/CementOverview.vue'), meta: { title: '名录与供给侧政策线' } },
  { path: '/industry/cement/peers', component: () => import('./views/industry/cement/CementPeers.vue'), meta: { title: '八家水泥企业对比' } },
  { path: '/industry/telecom/overview', component: () => import('./views/industry/telecom/TelecomOverview.vue'), meta: { title: '名录与变革时间线' } },
  { path: '/industry/telecom/peers', component: () => import('./views/industry/telecom/TelecomPeers.vue'), meta: { title: '三大运营商对比' } },

  // 股权结构（全站一页，按 ?code= 服务各板块）
  { path: '/company/shareholder', component: () => import('./views/company/Shareholder.vue'), meta: { title: '股权结构' } },

  // 通信运营商公司详情
  { path: '/company/telecom', redirect: '/company/telecom/index' },
  { path: '/company/telecom/index', component: () => import('./views/company/telecom/TelecomIndex.vue'), meta: { title: '通信公司·业绩' } },
  { path: '/company/telecom/operation', component: () => import('./views/company/telecom/TelecomOperation.vue'), meta: { title: '通信公司·客户与网络' } },
  { path: '/company/telecom/segment', component: () => import('./views/company/telecom/TelecomSegment.vue'), meta: { title: '通信公司·分部' } },
  // 中国移动
  { path: '/company/cmcc/index', component: () => import('./views/company/cmcc/CmccIndex.vue'), meta: { title: '中国移动·业绩' } },
  { path: '/company/cmcc/product', component: () => import('./views/company/cmcc/CmccProduct.vue'), meta: { title: '中国移动·产品更迭' } },
  { path: '/company/cmcc/operation', component: () => import('./views/company/cmcc/CmccOperation.vue'), meta: { title: '中国移动·客户与网络' } },
  { path: '/company/cmcc/intro', component: () => import('./views/company/cmcc/CmccIntro.vue'), meta: { title: '中国移动·简介与股权' } },

  // 百度
  { path: '/company/baidu/index', component: () => import('./views/company/baidu/BaiduIndex.vue'), meta: { title: '百度·业绩' } },
  { path: '/company/baidu/segment', component: () => import('./views/company/baidu/BaiduSegment.vue'), meta: { title: '百度·分部与运营' } },
  { path: '/company/baidu/balance-sheet', component: () => import('./views/company/baidu/BaiduBalanceSheet.vue'), meta: { title: '百度·资产与现金' } },
  { path: '/company/baidu/intro', component: () => import('./views/company/baidu/BaiduIntro.vue'), meta: { title: '百度·简介' } },

  // 食品
  { path: '/company/food/overview', component: () => import('./views/company/food/FoodOverview.vue'), meta: { title: '巴比食品' } },
  { path: '/company/food/peer-comparison', component: () => import('./views/company/food/FoodPeerComparison.vue'), meta: { title: '食品·同业对比' } },

  // 孤立的石油公司页（源页为空骨架，routed 以免丢失）
  { path: '/company/oil/petro-income-waterfall', component: () => import('./views/company/oil/PetroIncomeWaterfall.vue'), meta: { title: '中石油 利润→营收 瀑布图' } },

  // 银行公司详情（同一份页面按 code 渲染 + 切换器）
  { path: '/company/bank', redirect: '/company/bank/601077/index' },
  {
    path: '/company/bank/:code',
    component: () => import('./views/company/bank/BankLayout.vue'),
    children: [
      { path: '', redirect: (to) => `/company/bank/${to.params.code}/index` },
      { path: 'index', component: () => import('./views/company/bank/BankIndex.vue'), meta: { title: '银行·业绩' } },
      { path: 'asset', component: () => import('./views/company/bank/BankAsset.vue'), meta: { title: '银行·资产端' } },
      { path: 'debt', component: () => import('./views/company/bank/BankDebt.vue'), meta: { title: '银行·负债端' } },
      { path: 'risk', component: () => import('./views/company/bank/BankRisk.vue'), meta: { title: '银行·风控' } },
      { path: 'intro', component: () => import('./views/company/bank/BankIntro.vue'), meta: { title: '银行·简介' } },
      { path: 'balance-sheet', component: () => import('./views/company/bank/BankBalanceSheet.vue'), meta: { title: '银行·资产负债表' } },
      { path: 'income-waterfall', component: () => import('./views/company/bank/BankIncomeWaterfall.vue'), meta: { title: '银行·营收支出瀑布' } },
    ],
  },
]

// ── 导航分组（SiteHeader 消费）：按路由前缀分组；nav 标题常比 meta 标题更短，故单列。 ──
export const navGroups = [
  { prefix: '/subject/oil/', pages: [
    { to: '/subject/oil/price', title: '油价 K 线' },
    { to: '/subject/oil/region-production', title: '产量总览' },
    { to: '/subject/oil/consumption', title: '消费总览' },
    { to: '/subject/oil/country-change', title: '2001 vs 2024' },
    { to: '/subject/oil/majors', title: '油企' },
    { to: '/subject/oil/cnooc-roa', title: '中海油 油价·ROA' },
  ] },
  { prefix: '/industry/bank/', pages: [
    { to: '/industry/bank/overview', title: 'A/H 股概览' },
    { to: '/industry/bank/tsf', title: '社会融资规模' },
    { to: '/industry/bank/npl-formation', title: '息差与不良生成对比' },
    { to: '/industry/bank/reform-timeline', title: '重要变革时间线' },
    { to: '/company/shareholder?code=601077', title: '股权结构' },
  ] },
  { prefix: '/industry/insurance/', pages: [
    { to: '/industry/insurance/overview', title: 'A/H 股概览' },
    { to: '/industry/insurance/peers', title: '五大险企对比' },
    { to: '/company/shareholder?code=601318', title: '股权结构' },
  ] },
  { prefix: '/industry/realestate/', pages: [
    { to: '/industry/realestate/overview', title: '央企名录与政策线' },
    { to: '/industry/realestate/peers', title: '六家央企开发商对比' },
    { to: '/company/shareholder?code=600048', title: '股权结构' },
  ] },
  { prefix: '/industry/cement/', pages: [
    { to: '/industry/cement/overview', title: '名录与供给侧政策线' },
    { to: '/industry/cement/peers', title: '八家水泥企业对比' },
    { to: '/company/shareholder?code=600585', title: '股权结构' },
  ] },
  { prefix: '/industry/telecom/', pages: [
    { to: '/industry/telecom/overview', title: '名录与变革时间线' },
    { to: '/industry/telecom/peers', title: '三大运营商对比' },
    { to: '/company/telecom', title: '公司详情' },
    { to: '/company/shareholder?code=600941', title: '股权结构' },
  ] },
  { prefix: '/company/telecom/', pages: [
    { to: '/company/telecom/index', title: '业绩' },
    { to: '/company/telecom/operation', title: '客户与网络' },
    { to: '/company/telecom/segment', title: '分部' },
    { to: '/company/shareholder?code=600941', title: '股权结构' },
  ] },
  { prefix: '/company/cmcc/', pages: [
    { to: '/company/cmcc/index', title: '业绩' },
    { to: '/company/cmcc/product', title: '产品更迭' },
    { to: '/company/cmcc/operation', title: '客户与网络' },
    { to: '/company/cmcc/intro', title: '简介与股权' },
  ] },
  { prefix: '/company/baidu/', pages: [
    { to: '/company/baidu/index', title: '业绩' },
    { to: '/company/baidu/segment', title: '分部与运营' },
    { to: '/company/baidu/balance-sheet', title: '资产与现金' },
    { to: '/company/shareholder?code=09888', title: '股权结构' },
    { to: '/company/baidu/intro', title: '简介' },
  ] },
  { prefix: '/company/food/', pages: [
    { to: '/company/food/overview', title: '年报概览' },
    { to: '/company/food/peer-comparison', title: '同业对比' },
    { to: '/company/shareholder?code=605338', title: '股权结构' },
  ] },
]

// 股权页按 ?code= 反查板块后要挂的「非银行板块」导航前缀（银行板块另有专属栏目，见下）。
export const shareholderBoardPrefix = {
  insurer: '/industry/insurance/',
  developer: '/industry/realestate/',
  cement: '/industry/cement/',
  telecom: '/industry/telecom/',
  tech: '/company/baidu/',
}

// 银行公司详情栏目：BankLayout 顶栏 + 股权页银行导航共用；加银行子页只改这一处。
export const bankSubPages = [
  { seg: 'index', title: '业绩' },
  { seg: 'asset', title: '资产端' },
  { seg: 'debt', title: '负债端' },
  { seg: 'risk', title: '风控' },
  { seg: 'intro', title: '简介' },
  { seg: 'balance-sheet', title: '资产负债表' },
  { seg: 'income-waterfall', title: '营收瀑布' },
]

// ── 首页板块卡片（Home.vue 消费）：按产业链顺序排；status: done|wip|empty；flow 为可选传导说明（HTML）。 ──
export const hubSections = [
  { title: '食品', cards: [
    { to: '/company/food/overview', status: 'wip', tag: '食品', tagClass: 'tag-consumption', name: '食品', desc: '巴比食品 605338 年报 · 同业对比' },
  ] },
  {
    title: '地产链', hint: '上游 → 下游',
    flow: '<code>水泥（上游）</code> → 发货当期确认收入 → <code>地产（下游）</code> → 竣工结转后确认收入。水泥的营收拐点<b>领先</b>开发商约 2 年。注意水泥需求里还有很大一块来自基建（公路、桥梁、水利），不随地产销售同步，读水泥时别只对着地产看。<b>地产（开发商）板块已不再维护</b>，卡片已从本页隐藏。',
    cards: [
      { to: '/industry/cement/overview', status: 'wip', tag: '水泥', tagClass: 'tag-cement', name: '水泥', pos: '　上游', desc: '八家水泥企业名录 · 供给侧政策线 · 净现金分化与吨毛利代理指标' },
      { status: 'empty', tag: '装修', tagClass: 'tag-decor', name: '装修' },
    ],
  },
  {
    title: '金融', hint: '为上下游提供杠杆',
    cards: [
      { to: '/industry/bank/overview', status: 'wip', tag: '银行', tagClass: 'tag-bank', name: '银行', desc: 'A/H 股上市银行名录 · 渝农商行 601077 年报全景' },
      { to: '/industry/insurance/overview', status: 'wip', tag: '保险', tagClass: 'tag-insurance', name: '保险', desc: 'A/H 股上市险企名录 · 五大险企历年数据横向对比' },
    ],
  },
  {
    title: '科技', hint: '广告收入是上面各板块景气的同步指标',
    cards: [
      { to: '/company/baidu/index', status: 'wip', tag: '互联网', tagClass: 'tag-tech', name: '百度集团', pos: '　09888 / BIDU', desc: 'FY2025 20-F · 业绩 / 分部与运营 / 资产与现金 / 股权结构 / 简介' },
    ],
  },
  {
    title: '能源', hint: '全行业的成本项',
    flow: '煤炭与电力占水泥吨成本的五到六成，油价则决定运输与化工成本——<code>能源</code>是读上面所有板块毛利率时的共同外生变量。',
    cards: [
      { to: '/subject/oil/price', status: 'done', tag: '石油', tagClass: 'tag-price', name: '石油', desc: '量价 · 产量 · 消费 · 储量 · 油企盈利' },
    ],
  },
  {
    title: '酒店', hint: '消费服务，不并入地产',
    cards: [
      { status: 'empty', tag: '酒店', tagClass: 'tag-hotel', name: '酒店' },
    ],
  },
  {
    title: '通信', hint: '上游 → 下游',
    flow: '<code>三大运营商（上游）</code> 提供接入与流量 → <code>互联网（下游）</code> 把流量变现为广告与电商成交。运营商的资本开支与 ARPU 是读互联网板块用户增长天花板时的参照。',
    cards: [
      { to: '/industry/telecom/overview', status: 'wip', tag: '运营商', tagClass: 'tag-telecom', name: '三大运营商', pos: '　上游', desc: '移动/电信/联通名录与变革时间线 · 三家对比 · 各家公司详情（业绩／收入构成／运营与资本开支）' },
      { to: '/company/cmcc/index', status: 'wip', tag: '运营商', tagClass: 'tag-telecom', name: '中国移动', pos: '　941 / 600941　上游', desc: '1997 年上市至今 · 业绩 / 产品更迭（语音→流量→算力）/ 客户与网络 / 简介与股权' },
    ],
  },
  {
    title: '互联网',
    cards: [
      { status: 'empty', tag: '在线广告', tagClass: 'tag-ad', name: '在线广告', pos: '　下游' },
      { status: 'empty', tag: '电商', tagClass: 'tag-ecommerce', name: '电商', pos: '　下游' },
    ],
  },
]

// ── 全站共用文案 ──────────────────────────────────────────────────────
// 取数占位只写这一处：LoadingNote.vue（老页面的 #loading 占位）与 ChartCard.vue
// （图表卡片三态）都取它，改一次全站生效。
export const LOADING_TEXT = '数据加载中…'
