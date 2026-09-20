<template>
  <!-- 全站统一的取数占位。DOM 仍是 base.css 认的 #loading —— 逐字迁移来的老页面脚本
       按 id 找它再隐藏（Shareholder / OilCountryConsumption），所以结构不能换。 -->
  <div id="loading">{{ text }}</div>
</template>

<script setup>
import { LOADING_TEXT } from '../site.config'

defineProps({ text: { type: String, default: LOADING_TEXT } })
</script>
