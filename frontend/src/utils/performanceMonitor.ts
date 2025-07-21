/**
 * 性能监控工具
 * 用于监控应用性能并提供用户体验优化建议
 */

import { ref, reactive } from 'vue'
import { ux } from './userExperience'

// 性能指标接口
interface PerformanceMetrics {
  // 页面加载性能
  pageLoadTime: number
  domContentLoadedTime: number
  firstContentfulPaint: number
  largestContentfulPaint: number
  
  // API 请求性能
  apiResponseTimes: Map<string, number[]>
  slowApiCalls: Array<{ url: string; duration: number; timestamp: number }>
  
  // 用户交互性能
  interactionLatency: number[]
  
  // 内存使用
  memoryUsage?: {
    usedJSHeapSize: number
    totalJSHeapSize: number
    jsHeapSizeLimit: number
  }
  
  // 错误统计
  errorCount: number
  lastErrors: Array<{ message: string; timestamp: number; stack?: string }>
}

// 性能阈值配置
const PERFORMANCE_THRESHOLDS = {
  SLOW_API_THRESHOLD: 3000, // 3秒
  HIGH_INTERACTION_LATENCY: 100, // 100ms
  MAX_ERROR_COUNT: 5, // 最大错误数
  MEMORY_WARNING_THRESHOLD: 0.8 // 内存使用警告阈值
}

class PerformanceMonitor {
  private metrics: PerformanceMetrics = {
    pageLoadTime: 0,
    domContentLoadedTime: 0,
    firstContentfulPaint: 0,
    largestContentfulPaint: 0,
    apiResponseTimes: new Map(),
    slowApiCalls: [],
    interactionLatency: [],
    errorCount: 0,
    lastErrors: []
  }
  
  private isMonitoring = false
  private performanceObserver?: PerformanceObserver
  
  /**
   * 开始性能监控
   */
  startMonitoring() {
    if (this.isMonitoring) return
    
    this.isMonitoring = true
    this.initializePageMetrics()
    this.setupPerformanceObserver()
    this.setupErrorTracking()
    this.setupMemoryMonitoring()
    
    // 性能监控已启动
  }
  
  /**
   * 停止性能监控
   */
  stopMonitoring() {
    this.isMonitoring = false
    
    if (this.performanceObserver) {
      this.performanceObserver.disconnect()
    }
    
    // 性能监控已停止
  }
  
  /**
   * 初始化页面性能指标
   */
  private initializePageMetrics() {
    if (typeof window !== 'undefined' && window.performance) {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
      
      if (navigation) {
        this.metrics.pageLoadTime = navigation.loadEventEnd - navigation.fetchStart
        this.metrics.domContentLoadedTime = navigation.domContentLoadedEventEnd - navigation.fetchStart
      }
    }
  }
  
  /**
   * 设置性能观察器
   */
  private setupPerformanceObserver() {
    if (typeof window !== 'undefined' && 'PerformanceObserver' in window) {
      this.performanceObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.entryType === 'paint') {
            if (entry.name === 'first-contentful-paint') {
              this.metrics.firstContentfulPaint = entry.startTime
            }
          } else if (entry.entryType === 'largest-contentful-paint') {
            this.metrics.largestContentfulPaint = entry.startTime
          } else if (entry.entryType === 'measure') {
            // 自定义性能测量
            this.handleCustomMeasure(entry)
          }
        }
      })
      
      try {
        this.performanceObserver.observe({ entryTypes: ['paint', 'largest-contentful-paint', 'measure'] })
      } catch (error) {
        // 性能观察器设置失败
      }
    }
  }
  
  /**
   * 设置错误追踪
   */
  private setupErrorTracking() {
    if (typeof window !== 'undefined') {
      window.addEventListener('error', (event) => {
        this.recordError(event.message, event.error?.stack)
      })
      
      window.addEventListener('unhandledrejection', (event) => {
        this.recordError(`Unhandled Promise Rejection: ${event.reason}`, event.reason?.stack)
      })
    }
  }
  
  /**
   * 设置内存监控
   */
  private setupMemoryMonitoring() {
    if (typeof window !== 'undefined' && 'performance' in window && 'memory' in performance) {
      setInterval(() => {
        const memory = (performance as any).memory
        if (memory) {
          this.metrics.memoryUsage = {
            usedJSHeapSize: memory.usedJSHeapSize,
            totalJSHeapSize: memory.totalJSHeapSize,
            jsHeapSizeLimit: memory.jsHeapSizeLimit
          }
          
          // 检查内存使用警告
          const memoryUsageRatio = memory.usedJSHeapSize / memory.jsHeapSizeLimit
          if (memoryUsageRatio > PERFORMANCE_THRESHOLDS.MEMORY_WARNING_THRESHOLD) {
            this.showMemoryWarning(memoryUsageRatio)
          }
        }
      }, 30000) // 每30秒检查一次
    }
  }
  
  /**
   * 记录 API 请求性能
   */
  recordApiCall(url: string, duration: number) {
    if (!this.metrics.apiResponseTimes.has(url)) {
      this.metrics.apiResponseTimes.set(url, [])
    }
    
    const times = this.metrics.apiResponseTimes.get(url)!
    times.push(duration)
    
    // 保持最近20次记录
    if (times.length > 20) {
      times.shift()
    }
    
    // 检查慢请求
    if (duration > PERFORMANCE_THRESHOLDS.SLOW_API_THRESHOLD) {
      this.metrics.slowApiCalls.push({
        url,
        duration,
        timestamp: Date.now()
      })
      
      // 保持最近10次慢请求记录
      if (this.metrics.slowApiCalls.length > 10) {
        this.metrics.slowApiCalls.shift()
      }
      
      this.showSlowApiWarning(url, duration)
    }
  }
  
  /**
   * 记录用户交互延迟
   */
  recordInteractionLatency(latency: number) {
    this.metrics.interactionLatency.push(latency)
    
    // 保持最近50次记录
    if (this.metrics.interactionLatency.length > 50) {
      this.metrics.interactionLatency.shift()
    }
    
    // 检查高延迟
    if (latency > PERFORMANCE_THRESHOLDS.HIGH_INTERACTION_LATENCY) {
      console.warn(`检测到高交互延迟: ${latency}ms`)
    }
  }
  
  /**
   * 记录错误
   */
  private recordError(message: string, stack?: string) {
    this.metrics.errorCount++
    this.metrics.lastErrors.push({
      message,
      stack,
      timestamp: Date.now()
    })
    
    // 保持最近10次错误记录
    if (this.metrics.lastErrors.length > 10) {
      this.metrics.lastErrors.shift()
    }
    
    // 检查错误频率
    if (this.metrics.errorCount > PERFORMANCE_THRESHOLDS.MAX_ERROR_COUNT) {
      this.showErrorFrequencyWarning()
    }
  }
  
  /**
   * 处理自定义性能测量
   */
  private handleCustomMeasure(entry: PerformanceEntry) {
    if (entry.name.startsWith('api-call-')) {
      const url = entry.name.replace('api-call-', '')
      this.recordApiCall(url, entry.duration)
    } else if (entry.name.startsWith('interaction-')) {
      this.recordInteractionLatency(entry.duration)
    }
  }
  
  /**
   * 显示慢 API 警告
   */
  private showSlowApiWarning(url: string, duration: number) {
    ux.warning(
      `API 请求响应较慢: ${Math.round(duration)}ms`,
      '性能提醒'
    )
  }
  
  /**
   * 显示内存使用警告
   */
  private showMemoryWarning(ratio: number) {
    ux.warning(
      `内存使用率较高: ${Math.round(ratio * 100)}%，建议刷新页面`,
      '内存警告'
    )
  }
  
  /**
   * 显示错误频率警告
   */
  private showErrorFrequencyWarning() {
    ux.error(
      '检测到频繁错误，请检查网络连接或联系技术支持',
      '错误警告'
    )
  }
  
  /**
   * 获取性能报告
   */
  getPerformanceReport() {
    const report = {
      ...this.metrics,
      averageApiResponseTime: this.calculateAverageApiResponseTime(),
      averageInteractionLatency: this.calculateAverageInteractionLatency(),
      performanceScore: this.calculatePerformanceScore()
    }
    
    return report
  }
  
  /**
   * 计算平均 API 响应时间
   */
  private calculateAverageApiResponseTime(): number {
    let totalTime = 0
    let totalCalls = 0
    
    for (const times of this.metrics.apiResponseTimes.values()) {
      totalTime += times.reduce((sum, time) => sum + time, 0)
      totalCalls += times.length
    }
    
    return totalCalls > 0 ? totalTime / totalCalls : 0
  }
  
  /**
   * 计算平均交互延迟
   */
  private calculateAverageInteractionLatency(): number {
    const latencies = this.metrics.interactionLatency
    return latencies.length > 0 
      ? latencies.reduce((sum, latency) => sum + latency, 0) / latencies.length 
      : 0
  }
  
  /**
   * 计算性能评分 (0-100)
   */
  private calculatePerformanceScore(): number {
    let score = 100
    
    // 页面加载时间评分
    if (this.metrics.pageLoadTime > 3000) score -= 20
    else if (this.metrics.pageLoadTime > 1500) score -= 10
    
    // API 响应时间评分
    const avgApiTime = this.calculateAverageApiResponseTime()
    if (avgApiTime > 2000) score -= 20
    else if (avgApiTime > 1000) score -= 10
    
    // 交互延迟评分
    const avgInteractionLatency = this.calculateAverageInteractionLatency()
    if (avgInteractionLatency > 100) score -= 15
    else if (avgInteractionLatency > 50) score -= 8
    
    // 错误频率评分
    if (this.metrics.errorCount > 5) score -= 25
    else if (this.metrics.errorCount > 2) score -= 10
    
    // 内存使用评分
    if (this.metrics.memoryUsage) {
      const memoryRatio = this.metrics.memoryUsage.usedJSHeapSize / this.metrics.memoryUsage.jsHeapSizeLimit
      if (memoryRatio > 0.8) score -= 15
      else if (memoryRatio > 0.6) score -= 8
    }
    
    return Math.max(0, score)
  }
  
  /**
   * 重置性能指标
   */
  resetMetrics() {
    this.metrics = {
      pageLoadTime: 0,
      domContentLoadedTime: 0,
      firstContentfulPaint: 0,
      largestContentfulPaint: 0,
      apiResponseTimes: new Map(),
      slowApiCalls: [],
      interactionLatency: [],
      errorCount: 0,
      lastErrors: []
    }
  }
}

// 创建全局性能监控实例
export const performanceMonitor = new PerformanceMonitor()

// 自动启动监控
if (typeof window !== 'undefined') {
  performanceMonitor.startMonitoring()
}

// 导出便捷方法
export const recordApiCall = performanceMonitor.recordApiCall.bind(performanceMonitor)
export const recordInteractionLatency = performanceMonitor.recordInteractionLatency.bind(performanceMonitor)
export const getPerformanceReport = performanceMonitor.getPerformanceReport.bind(performanceMonitor)