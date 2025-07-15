import { ref, Ref } from 'vue'

// 加载状态管理类
export class LoadingManager {
  private static loadingStates: Map<string, Ref<boolean>> = new Map()

  /**
   * 获取或创建加载状态
   * @param key 加载状态的唯一标识
   * @returns 响应式的加载状态
   */
  static getLoadingState(key: string): Ref<boolean> {
    if (!this.loadingStates.has(key)) {
      this.loadingStates.set(key, ref(false))
    }
    return this.loadingStates.get(key)!
  }

  /**
   * 设置加载状态
   * @param key 加载状态的唯一标识
   * @param loading 加载状态
   */
  static setLoading(key: string, loading: boolean): void {
    const state = this.getLoadingState(key)
    state.value = loading
  }

  /**
   * 开始加载
   * @param key 加载状态的唯一标识
   */
  static startLoading(key: string): void {
    this.setLoading(key, true)
  }

  /**
   * 停止加载
   * @param key 加载状态的唯一标识
   */
  static stopLoading(key: string): void {
    this.setLoading(key, false)
  }

  /**
   * 检查是否正在加载
   * @param key 加载状态的唯一标识
   * @returns 是否正在加载
   */
  static isLoading(key: string): boolean {
    const state = this.loadingStates.get(key)
    return state?.value || false
  }

  /**
   * 清除加载状态
   * @param key 加载状态的唯一标识
   */
  static clearLoading(key: string): void {
    this.loadingStates.delete(key)
  }

  /**
   * 清除所有加载状态
   */
  static clearAllLoading(): void {
    this.loadingStates.clear()
  }

  /**
   * 包装异步操作，自动管理加载状态
   * @param key 加载状态的唯一标识
   * @param asyncOperation 异步操作函数
   * @returns Promise
   */
  static async withLoading<T>(
    key: string, 
    asyncOperation: () => Promise<T>
  ): Promise<T> {
    try {
      this.startLoading(key)
      const result = await asyncOperation()
      return result
    } finally {
      this.stopLoading(key)
    }
  }
}

// 导出便捷的组合式函数
export function useLoading(key: string) {
  const loading = LoadingManager.getLoadingState(key)
  
  const startLoading = () => LoadingManager.startLoading(key)
  const stopLoading = () => LoadingManager.stopLoading(key)
  const setLoading = (state: boolean) => LoadingManager.setLoading(key, state)
  const withLoading = <T>(asyncOperation: () => Promise<T>) => 
    LoadingManager.withLoading(key, asyncOperation)

  return {
    loading,
    startLoading,
    stopLoading,
    setLoading,
    withLoading
  }
}

// 导出便捷方法
export const getLoadingState = (key: string) => LoadingManager.getLoadingState(key)
export const setLoading = (key: string, loading: boolean) => LoadingManager.setLoading(key, loading)
export const startLoading = (key: string) => LoadingManager.startLoading(key)
export const stopLoading = (key: string) => LoadingManager.stopLoading(key)
export const withLoading = <T>(key: string, asyncOperation: () => Promise<T>) => 
  LoadingManager.withLoading(key, asyncOperation)