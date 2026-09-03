import axios from 'axios'
import { message } from 'antd'
import { useAuthStore } from '../stores/authStore'

export const api = axios.create({ baseURL: '/api/v1' })

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (resp) => resp,
  (error) => {
    // 网络错误（无 response）
    if (!error.response) {
      message.error('网络连接失败，请检查网络后重试')
      return Promise.reject(error)
    }
    // token 失效 → 清除登录态并跳转登录页（避免在登录页死循环）
    if (error.response?.status === 401 && window.location.pathname !== '/login') {
      useAuthStore.getState().logout()
      window.location.href = '/login'
      return Promise.reject(error)
    }
    // 429 限流
    if (error.response?.status === 429) {
      message.warning('请求过于频繁，请稍候再试')
      return Promise.reject(error)
    }
    // 其他错误：提取后端 message
    const msg = error.response?.data?.message
    if (msg && error.response.status >= 500) {
      message.error(msg)
    }
    return Promise.reject(error)
  },
)
