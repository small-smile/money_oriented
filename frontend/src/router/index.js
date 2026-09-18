import { createRouter, createWebHistory } from 'vue-router'
import { routes } from '../site.config'

// 路由表现已抽到 src/site.config.js（唯一来源，SiteHeader / Home 同源）。
// 本文件只负责装配 router 实例与两个全局钩子。
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
