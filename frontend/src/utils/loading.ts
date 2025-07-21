interface LoadingState {
  visible: boolean
  message: string
  progress?: number
  showProgress?: boolean
  showCancel?: boolean
  onCancel?: () => void
}

// 全局加载状态管理
export class GlobalLoadingManager {
  private static instance: GlobalLoadingManager
  private loadingStates: Map<string, LoadingState> = new Map()
  private callbacks: Set<(state: LoadingState | null) => void> = new Set()

  static getInstance(): GlobalLoadingManager {
    if (!this.instance) {
      this.instance = new GlobalLoadingManager()
    }
    return this.instance
  }

  show(key: string, message: string, options?: {
    progress?: number
    showProgress?: boolean
    showCancel?: boolean
    onCancel?: () => void
  }): void {
    const state: LoadingState = {
      visible: true,
      message,
      progress: options?.progress,
      showProgress: options?.showProgress,
      showCancel: options?.showCancel,
      onCancel: options?.onCancel
    }
    
    this.loadingStates.set(key, state)
    this.notifyCallbacks()
  }

  hide(key: string): void {
    this.loadingStates.delete(key)
    this.notifyCallbacks()
  }

  updateProgress(key: string, progress: number, message?: string): void {
    const state = this.loadingStates.get(key)
    if (state) {
      state.progress = progress
      if (message) {
        state.message = message
      }
      this.notifyCallbacks()
    }
  }

  hideAll(): void {
    this.loadingStates.clear()
    this.notifyCallbacks()
  }

  getCurrentState(): LoadingState | null {
    // 返回最后添加的加载状态
    const states = Array.from(this.loadingStates.values())
    return states.length > 0 ? states[states.length - 1] : null
  }

  subscribe(callback: (state: LoadingState | null) => void): () => void {
    this.callbacks.add(callback)
    return () => this.callbacks.delete(callback)
  }

  private notifyCallbacks(): void {
    const currentState = this.getCurrentState()
    this.callbacks.forEach(callback => callback(currentState))
  }
}

export type { LoadingState }