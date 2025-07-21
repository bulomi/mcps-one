import { GlobalLoadingManager } from '@/utils/loading'
import { EnhancedToastManager, type ToastAction } from '@/utils/toast'
import { ErrorHandler, withRetry } from './errorHandler'
import { LoadingManager } from './loadingManager'

/**
 * 用户体验增强工具类
 * 提供统一的用户反馈、加载状态管理和错误处理
 */
export class UserExperience {
  private static loadingManager = GlobalLoadingManager.getInstance()
  private static toastManager = EnhancedToastManager.getInstance()

  /**
   * 显示操作确认对话框
   */
  static async confirm(
    message: string,
    title: string = '确认操作',
    options?: {
      confirmText?: string
      cancelText?: string
      type?: 'warning' | 'error' | 'info'
    }
  ): Promise<boolean> {
    return new Promise((resolve) => {
      const { confirmText = '确认', cancelText = '取消', type = 'warning' } = options || {}
      
      const actions: ToastAction[] = [
        {
          label: cancelText,
          type: 'default',
          handler: () => resolve(false)
        },
        {
          label: confirmText,
          type: type === 'error' ? 'error' : 'primary',
          handler: () => resolve(true)
        }
      ]

      this.toastManager.show({
        type: type,
        title,
        message,
        duration: 0,
        dismissible: false,
        actions
      })
    })
  }

  /**
   * 执行带用户反馈的异步操作
   */
  static async executeWithFeedback<T>(
    operation: () => Promise<T>,
    options: {
      loadingMessage?: string
      successMessage?: string
      errorMessage?: string
      showProgress?: boolean
      confirmMessage?: string
      confirmTitle?: string
      retryOptions?: {
        maxRetries?: number
        retryDelay?: number
      }
    } = {}
  ): Promise<T | null> {
    const {
      loadingMessage = '处理中...',
      successMessage,
      errorMessage,
      showProgress = false,
      confirmMessage,
      confirmTitle = '确认操作',
      retryOptions
    } = options

    try {
      // 如果需要确认，先显示确认对话框
      if (confirmMessage) {
        const confirmed = await this.confirm(confirmMessage, confirmTitle)
        if (!confirmed) {
          return null
        }
      }

      // 执行操作
      const operationKey = `operation-${Date.now()}`
      
      return await LoadingManager.withLoading(
        async () => {
          if (retryOptions) {
            return await withRetry(
              operation,
              retryOptions.maxRetries,
              retryOptions.retryDelay,
              errorMessage
            )
          } else {
            return await operation()
          }
        },
        {
          loadingKey: operationKey,
          message: loadingMessage,
          showGlobalLoading: true,
          showProgress,
          showSuccessMessage: !!successMessage,
          showErrorMessage: !!errorMessage
        }
      )
    } catch (error) {
      // 错误已经在 LoadingManager.withLoading 中处理
      throw error
    }
  }

  /**
   * 批量操作的用户体验增强
   */
  static async executeBatchWithFeedback<T>(
    items: any[],
    operation: (item: any, index: number) => Promise<T>,
    options: {
      batchSize?: number
      loadingMessage?: string
      successMessage?: string
      errorMessage?: string
      confirmMessage?: string
      showProgress?: boolean
      continueOnError?: boolean
    } = {}
  ): Promise<{ results: T[], errors: Error[] }> {
    const {
      batchSize = 5,
      loadingMessage = '批量处理中...',
      successMessage,
      errorMessage,
      confirmMessage,
      showProgress = true,
      continueOnError = true
    } = options

    // 确认操作
    if (confirmMessage) {
      const confirmed = await this.confirm(
        `${confirmMessage}\n\n将处理 ${items.length} 个项目`,
        '批量操作确认'
      )
      if (!confirmed) {
        return { results: [], errors: [] }
      }
    }

    const operationKey = `batch-operation-${Date.now()}`
    const results: T[] = []
    const errors: Error[] = []
    let completed = 0

    try {
      this.loadingManager.show(operationKey, loadingMessage, {
        showProgress,
        progress: 0
      })

      // 分批处理
      for (let i = 0; i < items.length; i += batchSize) {
        const batch = items.slice(i, i + batchSize)
        
        const batchPromises = batch.map(async (item, batchIndex) => {
          const globalIndex = i + batchIndex
          try {
            const result = await operation(item, globalIndex)
            results[globalIndex] = result
            completed++
            
            // 更新进度
            if (showProgress) {
              const progress = Math.round((completed / items.length) * 100)
              this.loadingManager.updateProgress(
                operationKey,
                progress,
                `${loadingMessage} (${completed}/${items.length})`
              )
            }
            
            return result
          } catch (error) {
            const err = error instanceof Error ? error : new Error(String(error))
            errors.push(err)
            completed++
            
            if (!continueOnError) {
              throw err
            }
            
            // 更新进度
            if (showProgress) {
              const progress = Math.round((completed / items.length) * 100)
              this.loadingManager.updateProgress(
                operationKey,
                progress,
                `${loadingMessage} (${completed}/${items.length}, ${errors.length} 错误)`
              )
            }
            
            return null
          }
        })

        await Promise.all(batchPromises)
      }

      // 显示结果
      if (errors.length === 0) {
        if (successMessage) {
          this.toastManager.success(`${successMessage} (${results.length}/${items.length})`)
        }
      } else if (results.length > 0) {
        this.toastManager.warning(
          `部分操作完成: 成功 ${results.length}, 失败 ${errors.length}`
        )
      } else {
        if (errorMessage) {
          this.toastManager.error(`${errorMessage} (${errors.length} 个错误)`)
        }
      }

      return { results: results.filter(r => r !== null), errors }
    } finally {
      this.loadingManager.hide(operationKey)
    }
  }

  /**
   * 显示进度条操作
   */
  static async executeWithProgress<T>(
    operation: (updateProgress: (progress: number, message?: string) => void) => Promise<T>,
    options: {
      initialMessage?: string
      successMessage?: string
      errorMessage?: string
    } = {}
  ): Promise<T> {
    const {
      initialMessage = '处理中...',
      successMessage,
      errorMessage
    } = options

    const operationKey = `progress-operation-${Date.now()}`
    
    try {
      this.loadingManager.show(operationKey, initialMessage, {
        showProgress: true,
        progress: 0
      })

      const updateProgress = (progress: number, message?: string) => {
        this.loadingManager.updateProgress(
          operationKey,
          Math.max(0, Math.min(100, progress)),
          message || initialMessage
        )
      }

      const result = await operation(updateProgress)
      
      if (successMessage) {
        this.toastManager.success(successMessage)
      }
      
      return result
    } catch (error) {
      if (errorMessage) {
        ErrorHandler.handleApiError(error, errorMessage)
      }
      throw error
    } finally {
      this.loadingManager.hide(operationKey)
    }
  }

  /**
   * 显示操作结果摘要
   */
  static showOperationSummary(
    title: string,
    summary: {
      total: number
      success: number
      failed: number
      details?: string[]
    }
  ): void {
    const { total, success, failed, details } = summary
    const hasErrors = failed > 0
    
    const message = `总计: ${total}, 成功: ${success}, 失败: ${failed}`
    
    const actions: ToastAction[] = []
    
    if (details && details.length > 0) {
      actions.push({
        label: '查看详情',
        type: 'default',
        handler: () => {
          // 显示详细信息
          this.toastManager.info(details.join('\n'), {
            title: '操作详情',
            duration: 0
          })
        }
      })
    }

    this.toastManager.show({
      type: hasErrors ? (success > 0 ? 'warning' : 'error') : 'success',
      title,
      message,
      duration: hasErrors ? 0 : 5000,
      actions: actions.length > 0 ? actions : undefined
    })
  }

  /**
   * 快捷方法：成功提示
   */
  static success(message: string, title?: string): void {
    this.toastManager.success(message, { title })
  }

  /**
   * 快捷方法：错误提示
   */
  static error(message: string, title?: string): void {
    this.toastManager.error(message, { title })
  }

  /**
   * 快捷方法：警告提示
   */
  static warning(message: string, title?: string): void {
    this.toastManager.warning(message, { title })
  }

  /**
   * 快捷方法：信息提示
   */
  static info(message: string, title?: string): void {
    this.toastManager.info(message, { title })
  }
}

// 导出便捷方法
export const ux = UserExperience
export const { confirm, executeWithFeedback, executeBatchWithFeedback, executeWithProgress, showOperationSummary, success, error, warning, info } = UserExperience