<template>
  <!-- 图表卡片骨架：复用 base.css 的 .chart-card / .chart-title / .sub，统一 loading/error/empty 三态。
       图表本体通过默认插槽传入（通常是 <EChart :option="…" />）。 -->
  <section class="chart-card cc">
    <h2 v-if="title" class="chart-title">{{ title }}<span v-if="sub" class="sub">{{ sub }}</span></h2>
    <div v-if="loading" class="cc-state">{{ loadingText }}</div>
    <div v-else-if="error" class="cc-state cc-err">{{ error }}</div>
    <div v-else-if="empty" class="cc-state cc-empty">{{ emptyText }}</div>
    <slot v-else />
    <p v-if="note" class="cc-note">{{ note }}</p>
  </section>
</template>

<script setup>
import { LOADING_TEXT } from '../site.config'

defineProps({
  title: String,
  sub: String,
  note: String,
  loading: Boolean,
  error: String,
  empty: Boolean,
  loadingText: { type: String, default: LOADING_TEXT },
  emptyText: { type: String, default: '该项暂无数据' },
})
</script>

<style scoped>
.cc { max-width: var(--content-w, 1200px); margin: 16px auto; padding: 16px 20px 20px; }
.cc-state { text-align: center; padding: 48px; color: #666; font-size: 18px; }
.cc-err { color: #d32f2f; }
.cc-empty { color: #999; }
.cc-note { margin-top: 10px; color: #6b7280; font-size: 15px; line-height: 1.6; }
</style>
