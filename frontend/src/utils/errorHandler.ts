import { useMessage } from 'naive-ui'

// 错误类型定义
export interface ApiError {
  message: string
  code?: string | number
  details?: any
}

// 统一错误处理类
export class ErrorHandler {
  private static message = useMessage()

  /**
   * 处理API错误
   * @param error 错误对象
   * @param customMessage 自定义错误消息
   */
  static handleApiError(error: any, customMessage?: string): void {
    let errorMessage = customMessage || '操作失败'
    
    if (error?.response) {
      // HTTP错误响应
      const { status, data } = error.response
      switch (status) {
        case 400:
          errorMessage = data?.detail || '请求参数错误'
          break
        case 401:
          errorMessage = '未授权访问，请检查权限'
          break
        case 403:
          errorMessage = '禁止访问，权限不足'
          break
        case 404:
          errorMessage = '请求的资源不存在'
          break
        case 422:
          errorMessage = data?.detail || '数据验证失败'
          break
        case 500:
          errorMessage = '服务器内部错误，请稍后重试'
          break
        case 502:
          errorMessage = '网关错误，服务暂时不可用'
          break
        case 503:
          errorMessage = '服务暂时不可用，请稍后重试'
          break
        default:
          errorMessage = data?.detail || `请求失败 (${status})`
      }
    } else if (error?.request) {
      // 网络错误
      errorMessage = '网络连接失败，请检查网络设置'
    } else if (error?.message) {
      // 其他错误
      errorMessage = error.message
    }

    this.showError(errorMessage)
    console.error('API Error:', error)
  }

  /**
   * 显示错误消息
   * @param message 错误消息
   */
  static showError(message: string): void {
    this.message.error(message)
  }

  /**
   * 显示成功消息
   * @param message 成功消息
   */
  static showSuccess(message: string): void {
    this.message.success(message)
  }

  /**
   * 显示警告消息
   * @param message 警告消息
   */
  static showWarning(message: string): void {
    this.message.warning(message)
  }

  /**
   * 显示信息消息
   * @param message 信息消息
   */
  static showInfo(message: string): void {
    this.message.info(message)
  }
}

// 导出便捷方法
export const showError = (message: string) => ErrorHandler.showError(message)
export const showSuccess = (message: string) => ErrorHandler.showSuccess(message)
export const showWarning = (message: string) => ErrorHandler.showWarning(message)
export const showInfo = (message: string) => ErrorHandler.showInfo(message)
export const handleApiError = (error: any, customMessage?: string) => 
  ErrorHandler.handleApiError(error, customMessage)