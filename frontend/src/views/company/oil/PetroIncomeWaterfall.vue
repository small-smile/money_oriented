<template>
  <div class="petro-income-waterfall"></div>
</template>

<script setup>
// 1:1 迁移自 dashboard/company/oil/petro_income_waterfall.html。
// 该源页是一个占位骨架：<head> 只 <link> 了 common/base.css（已全局引入），页内 <style>
// 定义了 body 版式与 .chart-card 布局，<title> 为「中石油 2025 利润→营收 反向瀑布图（按金额升序）」，
// 但 <body> 完全为空——没有任何 <script> / <script src>、没有 ECharts option、
// 不调用任何 /api、也没有内联/示意数据。
// 因此本组件如实复现：无图、无数据、无取数/渲染/dispose 逻辑（无可收集的 echarts 实例），
// 只保留与源页一致的根容器版式，可见效果与源页同为一张空白页。
</script>

<style scoped>
/* 源页 <style> 中本页依赖的规则。
   * reset、body 的背景/字体/颜色、.chart-card 的圆角/投影/白底已在 common/base.css 全局定义，这里不重复。
   源页 body 的版式（padding / flex 纵列 / gap）映射到页面根类；.chart-card 只保留其布局部分。
   本页无动态注入节点，全部为模板静态元素，故用 scoped。 */
.petro-income-waterfall {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.chart-card {
  /* 圆角/投影/白底见 common/base.css，这里只管布局 */
  width: 100%;
  max-width: 1800px;
  margin: 0 auto;
  flex-shrink: 0;
}
</style>
