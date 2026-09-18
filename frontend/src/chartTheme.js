// 全站 ECharts 通用主题：调色板 + 坐标轴基座 + 数字格式化。
// 新页面从这里取色/取轴/取格式，省掉每页各写一份 grid/axis/color；
// 旧页保持原样、不强制改造（迁移 1:1 原则）。
export const PALETTE = ['#1f4e79', '#c94a4a', '#2a9d8f', '#e9a23b', '#6c5b7b', '#3d7ea6', '#8ab17d', '#b5651d']

export const COLOR = {
  navy: '#1f4e79',   // 主色/收入
  red: '#c94a4a',    // 支出/下降
  green: '#1e8449',  // 利润/正向
  gold: '#e9a23b',   // 强调
  muted: '#94a3b8',
  grid: '#eef2f7',
  axis: '#6b7280',
}

// 金额（亿元）默认两位小数；空值统一显示占位符，不显示 NaN。
export function fmtYi(v, digits = 2) {
  if (v == null || Number.isNaN(Number(v))) return '—'
  return Number(v).toLocaleString('zh-CN', { minimumFractionDigits: digits, maximumFractionDigits: digits })
}
export function fmtPct(v, digits = 2) {
  if (v == null || Number.isNaN(Number(v))) return '—'
  return Number(v).toFixed(digits) + '%'
}
export function fmtThou(v) {
  if (v == null || Number.isNaN(Number(v))) return '—'
  return Number(v).toLocaleString('zh-CN')
}

// 通用坐标轴基座：extra 用扩展运算符覆盖，样式与全站灰度统一。
export function catAxis(data, extra = {}) {
  return {
    type: 'category',
    data,
    axisLine: { lineStyle: { color: COLOR.axis } },
    axisTick: { show: false },
    axisLabel: { color: COLOR.axis, fontSize: 13 },
    ...extra,
  }
}
export function valAxis(extra = {}) {
  return {
    type: 'value',
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: COLOR.axis, fontSize: 13 },
    splitLine: { lineStyle: { color: COLOR.grid } },
    ...extra,
  }
}
export const gridBase = { left: 48, right: 24, top: 24, bottom: 36, containLabel: true }
