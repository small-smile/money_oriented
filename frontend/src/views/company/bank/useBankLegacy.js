// 银行公司详情页 · legacy 图表桥接
// ---------------------------------------------------------------------------
// dashboard/company/bank/{charts.js, charts/*.js} 是一整套普通全局脚本（非 ESM）：
// 它们按 DOM id 用全局 echarts/axios 渲染，读 window.COMPANY_CODE / window.__BANKS，
// charts.js 末尾自执行 fetch(/api/company_charts?code=)+renderAll。为「零漂移」1:1 迁移，
// 这些脚本被逐字复制进 ./legacy/，这里用 ?raw 取其原文，在运行时按原顺序注入执行，
// 不改一字。数据仍走 /api，样式仍靠 base.css（全局）+ ./legacy/page.css。
import * as echarts from 'echarts'
import axios from 'axios'
import { apiGet } from '../../../api'

// 加载顺序即 dashboard/company/bank/*.html 里的 <script> 顺序：
// core → compare → perf → asset → debt → risk → intro → statement → switcher → charts
// charts.js 必须最后（定义 renderAll 并自执行拉数+渲染，早了 __BANK_SECTIONS 还没注册完）。
import coreSrc from './legacy/core.js?raw'
import compareSrc from './legacy/compare.js?raw'
import perfSrc from './legacy/perf.js?raw'
import assetSrc from './legacy/asset.js?raw'
import debtSrc from './legacy/debt.js?raw'
import riskSrc from './legacy/risk.js?raw'
import introSrc from './legacy/intro.js?raw'
import statementSrc from './legacy/statement.js?raw'
import switcherSrc from './legacy/switcher.js?raw'
import chartsSrc from './legacy/charts.js?raw'

const LEGACY_ORDER = [
  ['core', coreSrc],
  ['compare', compareSrc],
  ['perf', perfSrc],
  ['asset', assetSrc],
  ['debt', debtSrc],
  ['risk', riskSrc],
  ['intro', introSrc],
  ['statement', statementSrc],
  ['switcher', switcherSrc],
  ['charts', chartsSrc],
]

// legacy 脚本以裸名 echarts / axios 使用（echarts.init、axios.get(...).then(res=>res.data.code)）。
// 把打包进来的 echarts、原始 axios 挂到 window，脚本即可原样运行；axios 用原始实例（不解包信封），
// 因为 charts.js/switcher.js 自己按 res.data.code / res.data.data 读后端信封。
export function exposeGlobals() {
  if (!window.echarts) window.echarts = echarts
  if (!window.axios) window.axios = axios
}

// /api/banks → window.__BANKS：切换器分组 + switcher.js 的 ROE/不良总额对比都读它。
// 整个会话缓存一次（apiGet 解包信封，直接拿到数组）。
let banksPromise = null
export function ensureBanks() {
  if (!banksPromise) {
    banksPromise = apiGet('/api/banks')
      .then((list) => {
        window.__BANKS = Array.isArray(list) ? list : []
        return window.__BANKS
      })
      .catch((e) => {
        console.error('加载银行清单 /api/banks 失败', e)
        window.__BANKS = Array.isArray(window.__BANKS) ? window.__BANKS : []
        return window.__BANKS
      })
  }
  return banksPromise
}

// 设定当前银行代码；core.js 只认 5~6 位数字，非法则由 core.js 自己回退到默认 601077。
export function setCompanyCode(code) {
  if (/^[0-9]{5,6}$/.test(code || '')) window.COMPANY_CODE = String(code)
}

// 按原顺序把 10 个 legacy 脚本拼成一段，包进一次性 IIFE 后整体注入执行。
// 为什么不分 10 个 <script> 逐个注入（原站的做法）：
//   · 原站每个页面是独立文档、脚本跑在同一份全局作用域里；core.js 顶层的 const
//     （EMPTY_D / KEY_DOM / PIE_BASE …）与各 helper 供后面的分区脚本与 charts.js 共享。
//   · SPA 里同一页会被多次挂载（切银行 / 切栏目都重挂），若逐个注入，第二次执行 core.js
//     顶层 const 会抛 “Identifier 'KEY_DOM' has already been declared”，且移除 <script>
//     节点并不会撤销已建立的全局词法绑定。
//   · 把 10 段包进同一个 IIFE：① 它们之间仍共享同一作用域（与原站等价，KEY_DOM/initChart
//     照样被 charts.js / 分区取用）；② 每次挂载用「全新的」IIFE 作用域，天然规避重复声明；
//     ③ 脚本内容一个字节都不改（?raw 原文按原顺序拼接，段间只加注释与分号边界）。
// charts.js 仍在末尾：定义 renderAll 并自执行 axios.get(/api/company_charts)+renderAll。
export function loadLegacyScripts() {
  const combined =
    '(function(){\n' +
    LEGACY_ORDER.map(([name, code]) => `/* ==== legacy/${name}.js ==== */\n${code}`).join('\n;\n') +
    '\n})();'
  const s = document.createElement('script')
  s.type = 'text/javascript'
  s.dataset.bankLegacy = 'combined'
  s.text = combined
  document.body.appendChild(s) // 内联脚本插入即同步执行
  return [s]
}

// 卸载：销毁本页容器内所有 echarts 实例（含 legacy 动态建的 .chart），移除注入的 script 节点。
export function cleanupLegacy(container, nodes) {
  try {
    if (container && window.echarts) {
      container.querySelectorAll('.chart, [id^="chart-"]').forEach((el) => {
        const inst = window.echarts.getInstanceByDom(el)
        if (inst) inst.dispose()
      })
    }
  } catch (_) { /* 容器已卸载则忽略 */ }
  ;(nodes || []).forEach((s) => {
    try { s.remove() } catch (_) { /* noop */ }
  })
}
