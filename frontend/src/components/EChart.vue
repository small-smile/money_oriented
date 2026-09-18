<template>
  <div ref="el" class="chart" :style="{ height }"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

// 复用 ECharts 容器：init/setOption/resize/dispose。页面把从原 charts 代码逐字搬来的
// option 传进来即可，本组件不改动任何 option 内容（样式/图/数据保持原样）。
const props = defineProps({
  option: { type: Object, default: null },
  height: { type: String, default: '460px' },
})

const el = ref(null)
let chart = null

function render() {
  if (chart && props.option) chart.setOption(props.option, true)
}
function resize() {
  if (chart) chart.resize()
}

onMounted(() => {
  chart = echarts.init(el.value)
  render()
  window.addEventListener('resize', resize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  if (chart) {
    chart.dispose()
    chart = null
  }
})
watch(() => props.option, () => nextTick(render), { deep: true })
</script>

<style scoped>
.chart { width: 100%; }
</style>
