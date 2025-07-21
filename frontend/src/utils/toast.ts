/**
 * Toast 通知管理器
 * 提供全局的 Toast 通知功能
 */

import { reactive } from 'vue'

export interface ToastAction {
  label: string
  handler: () => void | Promise<void>
  style?: 'primary' | 'secondary'
}

export interface Toast {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title?: string
  message: string
  duration?: number
  dismissible?: boolean
  actions?: ToastAction[]
  createdAt: number
}

export interface ToastOptions {
  title?: string
  duration?: number
  dismissible?: boolean
  actions?: ToastAction[]
}

export class EnhancedToastManager {
  private static instance: EnhancedToastManager
  private toasts = reactive<Toast[]>([])
  private nextId = 1
  private callbacks: Set<(toasts: Toast[]) => void> = new Set()

  static getInstance(): EnhancedToastManager {
    if (!this.instance) {
      this.instance = new EnhancedToastManager()
    }
    return this.instance
  }

  // 获取所有Toast
  getToasts() {
    return this.toasts
  }

  // 订阅Toast变化
  subscribe(callback: (toasts: Toast[]) => void): () => void {
    this.callbacks.add(callback)
    return () => this.callbacks.delete(callback)
  }

  private notifyCallbacks(): void {
    this.callbacks.forEach(callback => callback([...this.toasts]))
  }

  // 显示Toast
  show(options: { type: Toast['type'], message: string } & ToastOptions): string {
    const id = `toast-${this.nextId++}`
    const toast: Toast = {
      id,
      type: options.type,
      message: options.message,
      title: options.title,
      duration: options.duration ?? (options.type === 'error' ? 0 : 5000),
      dismissible: options.dismissible ?? true,
      actions: options.actions,
      createdAt: Date.now()
    }

    this.toasts.push(toast)
    this.notifyCallbacks()

    // 自动关闭
    if (toast.duration && toast.duration > 0) {
      setTimeout(() => {
        this.dismiss(id)
      }, toast.duration)
    }

    return id
  }

  // 成功提示
  success(message: string, options?: ToastOptions): string {
    return this.show({ type: 'success', message, ...options })
  }

  // 错误提示
  error(message: string, options?: ToastOptions): string {
    return this.show({ type: 'error', message, ...options })
  }

  // 警告提示
  warning(message: string, options?: ToastOptions): string {
    return this.show({ type: 'warning', message, ...options })
  }

  // 信息提示
  info(message: string, options?: ToastOptions): string {
    return this.show({ type: 'info', message, ...options })
  }

  // 关闭Toast
  dismiss(id: string) {
    const index = this.toasts.findIndex(toast => toast.id === id)
    if (index > -1) {
      this.toasts.splice(index, 1)
      this.notifyCallbacks()
    }
  }

  // 清空所有Toast
  clear() {
    this.toasts.splice(0)
    this.notifyCallbacks()
  }
}

// 默认导出
export default EnhancedToastManager.getInstance()