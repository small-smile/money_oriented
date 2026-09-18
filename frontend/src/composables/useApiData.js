import { ref, watch, unref } from 'vue'
import { apiGet } from '../api'

// 收敛各页重复的 loading/error/ref + onMounted + try/catch 样板。
// 用法：
//   const { data, loading, error, reload } = useApiData('/api/company_charts', () => ({ code: code.value }))
// params 传成函数（getter）时会响应式重取——银行页切 code 即自动刷新，无需手写 watch。
export function useApiData(path, params = null, { immediate = true } = {}) {
  const data = ref(null)
  const loading = ref(false)
  const error = ref('')

  async function reload() {
    loading.value = true
    error.value = ''
    try {
      const p = typeof params === 'function' ? params() : unref(params)
      const url = typeof path === 'function' ? path() : path
      data.value = await apiGet(url, p)
    } catch (e) {
      error.value = e && e.message ? e.message : String(e)
      data.value = null
    } finally {
      loading.value = false
    }
  }

  if (typeof params === 'function') {
    // getter 依赖的响应式值（如 code）变化即重取；immediate 触发首取。
    watch(params, reload, { immediate })
  } else if (immediate) {
    reload()
  }

  return { data, loading, error, reload }
}
