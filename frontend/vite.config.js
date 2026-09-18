import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 前后端分离期间：前端独立跑 vite dev（5173，带 HMR），/api 代理到 Flask（5000）。
// 老站不动：迁移完成前后端仍托管 dashboard/，Vue 只是并行搭建。
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
    allowedHosts: ['localhost', 'money.local'],
    proxy: {
      '/api': {
        target: process.env.VITE_API_TARGET || 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
    },
  },
  build: { outDir: 'dist' },
})
