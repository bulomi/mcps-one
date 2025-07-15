import axios from 'axios'
import { ErrorHandler } from '@/utils/errorHandler'

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证token等
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    // 如果响应数据有 data 字段，则返回 data 字段的内容
    // 否则返回原始响应数据
    if (response.data && typeof response.data === 'object' && 'data' in response.data) {
      return response.data.data
    }
    return response.data
  },
  (error) => {
    // 统一错误处理，但不自动显示错误消息
    // 让调用方决定是否显示错误消息
    if (error.response) {
      const { status, data } = error.response
      switch (status) {
        case 400:
          error.message = data?.detail || '请求参数错误'
          break
        case 401:
          error.message = '未授权访问'
          break
        case 403:
          error.message = '禁止访问'
          break
        case 404:
          error.message = '资源不存在'
          break
        case 422:
          error.message = data?.detail || '数据验证失败'
          break
        case 500:
          error.message = '服务器内部错误'
          break
        case 502:
          error.message = '网关错误，服务暂时不可用'
          break
        case 503:
          error.message = '服务暂时不可用，请稍后重试'
          break
        default:
          error.message = data?.detail || `请求失败 (${status})`
      }
    } else if (error.request) {
      error.message = '网络连接失败，请检查网络设置'
    } else {
      error.message = '请求失败'
    }
    
    return Promise.reject(error)
  }
)

export default api