<template>
  <!-- 银行页唯一的一条 header（brand + 页面链接 + 银行切换器）抽到 BankNav，股权页的银行导航共用同一份。
       全局 SiteHeader 在银行路由下不渲染（见 App.vue）。 -->
  <BankNav :code="code" :current="curSub" />

  <!-- 切换银行/切换页面都要让子页重挂载（原站每次切换都整页重载），故按 fullPath 打 key。 -->
  <router-view :key="route.fullPath" />
</template>

<script setup>
import { computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ensureBanks, exposeGlobals, setCompanyCode } from './useBankLegacy'
// 银行页专属正文样式（dashboard/company/page.css 逐字复制）。base.css 已在 main.js 全局引入，不重复。
import './legacy/page.css'
import { bankSubPages } from '../../../site.config'
import BankNav from './BankNav.vue'

const route = useRoute()

const DEFAULT_CODE = '601077' // 与 charts.js / 后端 DEFAULT_BANK_CODE 一致
const SUBPAGES = bankSubPages

const code = computed(() => {
  const c = route.params.code
  return /^[0-9]{5,6}$/.test(c || '') ? String(c) : DEFAULT_CODE
})
const curSub = computed(() => {
  const seg = route.path.split('/').filter(Boolean).pop()
  return SUBPAGES.some((s) => s.seg === seg) ? seg : 'index'
})

// BankLayout 一挂载/切 code 就把 COMPANY_CODE 写进 window（子页脚本读它拉数据）
watch(code, (c) => setCompanyCode(c), { immediate: true })

// window.__BANKS（legacy 的 ROE/不良总额对比读它）仍由这里先拉一次；BankNav 拿的是同一份缓存
onMounted(() => {
  exposeGlobals()
  ensureBanks()
})
</script>

