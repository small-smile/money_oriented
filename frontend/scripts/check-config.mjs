// 零依赖配置完整性冒烟测试：`npm run smoke`（= node scripts/check-config.mjs）
// 校验 site.config 的 routes / navGroups / hubSections / bankSubPages 自洽，
// 守住「加行业/专题只改一处」时 to/seg 不与路由脱节。site.config 全懒加载，可被 node 直接 import。
import { routes, navGroups, hubSections, bankSubPages } from '../src/site.config.js'

const errors = []
const ok = (cond, msg) => { if (!cond) errors.push(msg) }
const stripQuery = (to) => String(to).split('?')[0].split('#')[0]

// 收集所有路由 path 与 /company/bank/:code 的子 seg
const routePaths = new Set()
const bankChildSegs = new Set()
for (const r of routes) {
  routePaths.add(r.path)
  if (r.path === '/company/bank/:code' && Array.isArray(r.children)) {
    for (const c of r.children) if (c.path) bankChildSegs.add(c.path)
  }
}

// 1) routes path 不重复
const seen = new Set()
for (const r of routes) {
  ok(!seen.has(r.path), `路由 path 重复：${r.path}`)
  seen.add(r.path)
}

// 2) navGroups 的 to（去 query）要能落到某条路由
for (const g of navGroups) {
  ok(typeof g.prefix === 'string' && g.prefix, 'navGroups 存在缺 prefix 的分组')
  for (const p of g.pages) {
    ok(routePaths.has(stripQuery(p.to)), `navGroups[${g.prefix}] 链接无对应路由：${p.to}`)
  }
}

// 3) hubSections 卡片：status 合法；有 to 的要能落到路由
for (const s of hubSections) {
  for (const c of s.cards) {
    ok(['done', 'wip', 'empty'].includes(c.status), `hub「${s.title}」卡片 status 非法：${c.status}`)
    if (c.to) ok(routePaths.has(stripQuery(c.to)), `hub「${s.title}」卡片链接无对应路由：${c.to}`)
  }
}

// 4) bankSubPages 的 seg 要与银行子路由一致
for (const s of bankSubPages) {
  ok(bankChildSegs.has(s.seg), `bankSubPages seg 无对应银行子路由：${s.seg}`)
}

if (errors.length) {
  console.error('✗ site.config 校验失败：')
  for (const e of errors) console.error('  - ' + e)
  process.exit(1)
}
console.log(
  `✓ site.config 校验通过：routes=${routes.length} navGroups=${navGroups.length} ` +
  `hubSections=${hubSections.length} bankSubPages=${bankSubPages.length}`
)
