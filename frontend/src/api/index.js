import axios from 'axios'

// 后端统一响应信封 {code,data,msg?}（backend/shared.py 的 success/error）。集中解包：
// 组件只拿 data；code 非 200 抛带 msg 的错误。数据仍走原有 /api，不改口径、不动 data/。
const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '',
  timeout: 300000,
})

export async function apiGet(path, params) {
  const res = await http.get(path, { params })
  const body = res.data
  if (body && typeof body === 'object' && 'code' in body) {
    if (body.code !== 200) {
      const err = new Error(body.msg || `接口返回 ${body.code}`)
      err.code = body.code
      err.data = body.data
      throw err
    }
    return body.data
  }
  return body
}

export default http
