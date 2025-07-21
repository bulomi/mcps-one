import { EnhancedToastManager } from '@/utils/toast'

// 错误类型定义
export interface ApiError {
  message: string
  code?: string | number
  details?: any
}

import { LOG_LEVELS, type LogLevel } from '@/constants/logLevels'

// 错误级别定义（使用统一的日志级别常量）
export enum ErrorLevel {
  INFO = 'INFO',
  WARNING = 'WARNING', 
  ERROR = 'ERROR',
  CRITICAL = 'CRITICAL'
}

// 统一错误处理类
export class ErrorHandler {
  private static toastManager = EnhancedToastManager.getInstance()
  private static errorLog: Array<{timestamp: Date, level: ErrorLevel, message: string, error?: any}> = []

  /**
   * 记录错误日志
   * @param level 错误级别
   * @param message 错误消息
   * @param error 错误对象
   */
  private static logError(level: ErrorLevel, message: string, error?: any): void {
    const logEntry = {
      timestamp: new Date(),
      level,
      message,
      error
    }
    
    this.errorLog.push(logEntry)
    
    // 保持日志数量在合理范围内
    if (this.errorLog.length > 100) {
      this.errorLog.shift()
    }
    
    // 根据错误级别决定是否上报
    if (level === ErrorLevel.CRITICAL) {
      this.reportCriticalError(logEntry)
    }
  }

  /**
   * 上报严重错误
   * @param logEntry 日志条目
   */
  private static reportCriticalError(logEntry: any): void {
    // 这里可以实现错误上报逻辑，比如发送到监控系统
    console.error('Critical Error:', logEntry)
  }

  /**
   * 处理API错误
   * @param error 错误对象
   * @param customMessage 自定义错误消息
   * @param level 错误级别
   * @param showRetryOption 是否显示重试选项
   */
  static handleApiError(
    error: any, 
    customMessage?: string, 
    level: ErrorLevel = ErrorLevel.ERROR,
    showRetryOption: boolean = false
  ): void {
    let errorMessage = customMessage || '操作失败'
    let errorCode = 'UNKNOWN_ERROR'
    let shouldShowRetry = showRetryOption
    
    if (error?.response) {
      // HTTP错误响应
      const { status, data } = error.response
      errorCode = `HTTP_${status}`
      
      switch (status) {
        case 400:
          errorMessage = data?.detail || '请求参数错误'
          level = ErrorLevel.WARNING
          break
        case 401:
          errorMessage = '未授权访问，请检查权限'
          level = ErrorLevel.ERROR
          break
        case 403:
          errorMessage = '禁止访问，权限不足'
          level = ErrorLevel.ERROR
          break
        case 404:
          errorMessage = '请求的资源不存在'
          level = ErrorLevel.WARNING
          break
        case 422:
          errorMessage = data?.detail || '数据验证失败'
          level = ErrorLevel.WARNING
          break
        case 429:
          errorMessage = '请求过于频繁，请稍后重试'
          level = ErrorLevel.WARNING
          shouldShowRetry = true
          break
        case 500:
          errorMessage = '服务器内部错误，请稍后重试'
          level = ErrorLevel.CRITICAL
          shouldShowRetry = true
          break
        case 502:
          errorMessage = '网关错误，服务暂时不可用'
          level = ErrorLevel.CRITICAL
          shouldShowRetry = true
          break
        case 503:
          errorMessage = '服务暂时不可用，请稍后重试'
          level = ErrorLevel.ERROR
          shouldShowRetry = true
          break
        case 504:
          errorMessage = '请求超时，请稍后重试'
          level = ErrorLevel.ERROR
          shouldShowRetry = true
          break
        default:
          errorMessage = data?.detail || `请求失败 (${status})`
          shouldShowRetry = status >= 500
      }
    } else if (error?.request) {
      // 网络错误
      errorMessage = '网络连接失败，请检查网络设置'
      errorCode = 'NETWORK_ERROR'
      level = ErrorLevel.ERROR
      shouldShowRetry = true
    } else if (error?.message) {
      // 其他错误
      errorMessage = error.message
      errorCode = 'CLIENT_ERROR'
    }

    // 记录错误日志
    this.logError(level, errorMessage, { ...error, code: errorCode })
    
    // 显示错误消息，支持重试选项
    if (shouldShowRetry && error?.retryHandler) {
      this.showErrorWithRetry(errorMessage, error.retryHandler)
    } else {
      this.showError(errorMessage)
    }
    
    console.error('API Error:', error)
  }

  /**
   * 显示错误消息
   * @param message 错误消息
   */
  static showError(message: string): void {
    this.toastManager.error(message)
  }

  /**
   * 显示带重试选项的错误消息
   * @param message 错误消息
   * @param retryHandler 重试处理函数
   */
  private static showErrorWithRetry(message: string, retryHandler: () => Promise<any>): void {
    this.toastManager.error(message, {
      duration: 0, // 不自动关闭
      dismissible: true,
      actions: [
        {
          label: '重试',
          handler: async () => {
            try {
              await retryHandler()
            } catch (error) {
              this.handleApiError(error, '重试失败')
            }
          },
          style: 'primary'
        }
      ]
    })
  }

  /**
   * 显示成功消息
   * @param message 成功消息
   */
  static showSuccess(message: string): void {
    this.toastManager.success(message)
  }

  /**
   * 显示警告消息
   * @param message 警告消息
   */
  static showWarning(message: string): void {
    this.toastManager.warning(message)
  }

  /**
   * 显示信息消息
   * @param message 信息消息
   */
  static showInfo(message: string): void {
    this.toastManager.info(message)
  }

  /**
   * 获取错误日志
   * @param level 过滤的错误级别
   * @returns 错误日志数组
   */
  static getErrorLog(level?: ErrorLevel): Array<{timestamp: Date, level: ErrorLevel, message: string, error?: any}> {
    if (level) {
      return this.errorLog.filter(log => log.level === level)
    }
    return [...this.errorLog]
  }

  /**
   * 清空错误日志
   */
  static clearErrorLog(): void {
    this.errorLog = []
  }

  /**
   * 带重试机制的API调用
   * @param apiCall API调用函数
   * @param maxRetries 最大重试次数
   * @param retryDelay 重试延迟（毫秒）
   * @param customMessage 自定义错误消息
   */
  static async withRetry<T>(
    apiCall: () => Promise<T>,
    maxRetries: number = 3,
    retryDelay: number = 1000,
    customMessage?: string
  ): Promise<T> {
    let lastError: any
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await apiCall()
      } catch (error) {
        lastError = error
        
        if (attempt === maxRetries) {
          this.handleApiError(error, customMessage)
          throw error
        }
        
        // 检查是否应该重试
        if (this.shouldRetry(error)) {
          this.logError(ErrorLevel.WARNING, `API调用失败，正在重试 (${attempt}/${maxRetries})`, error)
          await this.delay(retryDelay * attempt) // 指数退避
        } else {
          this.handleApiError(error, customMessage)
          throw error
        }
      }
    }
    
    throw lastError
  }

  /**
   * 判断是否应该重试
   * @param error 错误对象
   */
  private static shouldRetry(error: any): boolean {
    if (error?.response) {
      const status = error.response.status
      // 只对网络错误和服务器错误重试
      return status >= 500 || status === 408 || status === 429
    }
    
    // 网络错误重试
    return !!error?.request
  }

  /**
   * 延迟函数
   * @param ms 延迟毫秒数
   */
  private static delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }
}

// 导出便捷方法
export const showError = (message: string) => ErrorHandler.showError(message)
export const showSuccess = (message: string) => ErrorHandler.showSuccess(message)
export const showWarning = (message: string) => ErrorHandler.showWarning(message)
export const showInfo = (message: string) => ErrorHandler.showInfo(message)
export const handleApiError = (
  error: any, 
  customMessage?: string, 
  level?: ErrorLevel,
  showRetryOption?: boolean
) => ErrorHandler.handleApiError(error, customMessage, level, showRetryOption)
export const withRetry = <T>(apiCall: () => Promise<T>, maxRetries?: number, retryDelay?: number, customMessage?: string) => 
  ErrorHandler.withRetry(apiCall, maxRetries, retryDelay, customMessage)
export const getErrorLog = (level?: ErrorLevel) => ErrorHandler.getErrorLog(level)
export const clearErrorLog = () => ErrorHandler.clearErrorLog()