/**
 * API监控和性能分析工具
 * 提供API调用监控、性能分析和错误追踪功能
 */

// 避免循环依赖，直接定义错误类型
class ApiError extends Error {
  public readonly code: number;
  public readonly response?: Response;
  public readonly data?: any;

  constructor(message: string, code: number, response?: Response, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.response = response;
    this.data = data;
  }
}

class NetworkError extends Error {
  constructor(message: string = '网络连接失败') {
    super(message);
    this.name = 'NetworkError';
  }
}

class TimeoutError extends Error {
  constructor(message: string = '请求超时') {
    super(message);
    this.name = 'TimeoutError';
  }
}

// 监控数据接口
export interface ApiCallMetrics {
  url: string;
  method: string;
  duration: number;
  status: number;
  success: boolean;
  timestamp: number;
  error?: string;
  retryCount?: number;
}

export interface ApiPerformanceStats {
  totalCalls: number;
  successRate: number;
  averageResponseTime: number;
  errorRate: number;
  slowestEndpoints: Array<{
    url: string;
    averageTime: number;
    callCount: number;
  }>;
  errorsByType: Record<string, number>;
  recentErrors: Array<{
    url: string;
    error: string;
    timestamp: number;
  }>;
}

// 监控配置
interface MonitorConfig {
  enabled: boolean;
  maxMetricsHistory: number;
  slowRequestThreshold: number;
  errorReportingEnabled: boolean;
  performanceReportingInterval: number;
}

class ApiMonitor {
  private metrics: ApiCallMetrics[] = [];
  private config: MonitorConfig = {
    enabled: true,
    maxMetricsHistory: 1000,
    slowRequestThreshold: 2000, // 2秒
    errorReportingEnabled: true,
    performanceReportingInterval: 60000, // 1分钟
  };
  private performanceReportTimer?: number;

  constructor(config?: Partial<MonitorConfig>) {
    if (config) {
      this.config = { ...this.config, ...config };
    }
    
    if (this.config.enabled) {
      this.startPerformanceReporting();
    }
  }

  /**
   * 记录API调用指标
   */
  recordApiCall(metrics: Omit<ApiCallMetrics, 'timestamp'>): void {
    if (!this.config.enabled) return;

    const fullMetrics: ApiCallMetrics = {
      ...metrics,
      timestamp: Date.now(),
    };

    this.metrics.push(fullMetrics);

    // 限制历史记录数量
    if (this.metrics.length > this.config.maxMetricsHistory) {
      this.metrics = this.metrics.slice(-this.config.maxMetricsHistory);
    }

    // 检查慢请求
    if (metrics.duration > this.config.slowRequestThreshold) {
      this.reportSlowRequest(fullMetrics);
    }

    // 检查错误
    if (!metrics.success && this.config.errorReportingEnabled) {
      this.reportError(fullMetrics);
    }
  }

  /**
   * 获取性能统计信息
   */
  getPerformanceStats(timeRange?: number): ApiPerformanceStats {
    const now = Date.now();
    const cutoff = timeRange ? now - timeRange : 0;
    const relevantMetrics = this.metrics.filter(m => m.timestamp >= cutoff);

    if (relevantMetrics.length === 0) {
      return {
        totalCalls: 0,
        successRate: 0,
        averageResponseTime: 0,
        errorRate: 0,
        slowestEndpoints: [],
        errorsByType: {},
        recentErrors: [],
      };
    }

    const totalCalls = relevantMetrics.length;
    const successfulCalls = relevantMetrics.filter(m => m.success).length;
    const successRate = (successfulCalls / totalCalls) * 100;
    const errorRate = ((totalCalls - successfulCalls) / totalCalls) * 100;
    
    const totalResponseTime = relevantMetrics.reduce((sum, m) => sum + m.duration, 0);
    const averageResponseTime = totalResponseTime / totalCalls;

    // 计算最慢的端点
    const endpointStats = new Map<string, { totalTime: number; count: number }>();
    relevantMetrics.forEach(m => {
      const key = `${m.method} ${m.url}`;
      const existing = endpointStats.get(key) || { totalTime: 0, count: 0 };
      endpointStats.set(key, {
        totalTime: existing.totalTime + m.duration,
        count: existing.count + 1,
      });
    });

    const slowestEndpoints = Array.from(endpointStats.entries())
      .map(([url, stats]) => ({
        url,
        averageTime: stats.totalTime / stats.count,
        callCount: stats.count,
      }))
      .sort((a, b) => b.averageTime - a.averageTime)
      .slice(0, 10);

    // 统计错误类型
    const errorsByType: Record<string, number> = {};
    const recentErrors: Array<{ url: string; error: string; timestamp: number }> = [];
    
    relevantMetrics
      .filter(m => !m.success && m.error)
      .forEach(m => {
        const errorType = this.categorizeError(m.error!);
        errorsByType[errorType] = (errorsByType[errorType] || 0) + 1;
        
        if (recentErrors.length < 20) {
          recentErrors.push({
            url: `${m.method} ${m.url}`,
            error: m.error!,
            timestamp: m.timestamp,
          });
        }
      });

    recentErrors.sort((a, b) => b.timestamp - a.timestamp);

    return {
      totalCalls,
      successRate,
      averageResponseTime,
      errorRate,
      slowestEndpoints,
      errorsByType,
      recentErrors,
    };
  }

  /**
   * 获取特定端点的性能数据
   */
  getEndpointStats(endpoint: string, timeRange?: number): {
    callCount: number;
    successRate: number;
    averageResponseTime: number;
    p95ResponseTime: number;
    errorCount: number;
  } {
    const now = Date.now();
    const cutoff = timeRange ? now - timeRange : 0;
    const endpointMetrics = this.metrics.filter(
      m => m.timestamp >= cutoff && `${m.method} ${m.url}` === endpoint
    );

    if (endpointMetrics.length === 0) {
      return {
        callCount: 0,
        successRate: 0,
        averageResponseTime: 0,
        p95ResponseTime: 0,
        errorCount: 0,
      };
    }

    const callCount = endpointMetrics.length;
    const successfulCalls = endpointMetrics.filter(m => m.success).length;
    const successRate = (successfulCalls / callCount) * 100;
    const errorCount = callCount - successfulCalls;

    const responseTimes = endpointMetrics.map(m => m.duration).sort((a, b) => a - b);
    const averageResponseTime = responseTimes.reduce((sum, time) => sum + time, 0) / responseTimes.length;
    const p95Index = Math.floor(responseTimes.length * 0.95);
    const p95ResponseTime = responseTimes[p95Index] || 0;

    return {
      callCount,
      successRate,
      averageResponseTime,
      p95ResponseTime,
      errorCount,
    };
  }

  /**
   * 清除监控数据
   */
  clearMetrics(): void {
    this.metrics = [];
  }

  /**
   * 导出监控数据
   */
  exportMetrics(): ApiCallMetrics[] {
    return [...this.metrics];
  }

  /**
   * 启用/禁用监控
   */
  setEnabled(enabled: boolean): void {
    this.config.enabled = enabled;
    if (enabled) {
      this.startPerformanceReporting();
    } else {
      this.stopPerformanceReporting();
    }
  }

  /**
   * 更新配置
   */
  updateConfig(config: Partial<MonitorConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * 获取当前配置
   */
  getConfig(): MonitorConfig {
    return { ...this.config };
  }

  /**
   * 获取实时性能指标
   */
  getRealTimeMetrics(): {
    activeRequests: number;
    requestsPerMinute: number;
    averageResponseTime: number;
    errorRate: number;
  } {
    const now = Date.now();
    const oneMinuteAgo = now - 60000;
    const recentMetrics = this.metrics.filter(m => m.timestamp >= oneMinuteAgo);

    const requestsPerMinute = recentMetrics.length;
    const averageResponseTime = recentMetrics.length > 0 
      ? recentMetrics.reduce((sum, m) => sum + m.duration, 0) / recentMetrics.length 
      : 0;
    const errorCount = recentMetrics.filter(m => !m.success).length;
    const errorRate = recentMetrics.length > 0 ? (errorCount / recentMetrics.length) * 100 : 0;

    return {
      activeRequests: 0, // 这需要在请求拦截器中跟踪
      requestsPerMinute,
      averageResponseTime,
      errorRate,
    };
  }

  private categorizeError(error: string): string {
    if (error.includes('Network') || error.includes('网络')) {
      return 'Network Error';
    }
    if (error.includes('timeout') || error.includes('超时')) {
      return 'Timeout Error';
    }
    if (error.includes('401') || error.includes('未授权')) {
      return 'Authentication Error';
    }
    if (error.includes('403') || error.includes('权限')) {
      return 'Authorization Error';
    }
    if (error.includes('404') || error.includes('不存在')) {
      return 'Not Found Error';
    }
    if (error.includes('500') || error.includes('服务器')) {
      return 'Server Error';
    }
    return 'Unknown Error';
  }

  private reportSlowRequest(metrics: ApiCallMetrics): void {
    console.warn(`慢请求检测: ${metrics.method} ${metrics.url} 耗时 ${metrics.duration}ms`);
    
    // 可以在这里发送到监控服务
    if (typeof window !== 'undefined' && 'navigator' in window && 'sendBeacon' in navigator) {
      const data = JSON.stringify({
        type: 'slow_request',
        ...metrics,
      });
      navigator.sendBeacon('/api/v1/monitoring/slow-requests', data);
    }
  }

  private reportError(metrics: ApiCallMetrics): void {
    console.error(`API错误: ${metrics.method} ${metrics.url} - ${metrics.error}`);
    
    // 可以在这里发送到错误监控服务
    if (typeof window !== 'undefined' && 'navigator' in window && 'sendBeacon' in navigator) {
      const data = JSON.stringify({
        type: 'api_error',
        ...metrics,
      });
      navigator.sendBeacon('/api/v1/monitoring/errors', data);
    }
  }

  private startPerformanceReporting(): void {
    if (this.performanceReportTimer) {
      clearInterval(this.performanceReportTimer);
    }

    this.performanceReportTimer = window.setInterval(() => {
      const stats = this.getPerformanceStats(this.config.performanceReportingInterval);
      
      // 可以在这里发送到监控服务
      if (typeof window !== 'undefined' && 'navigator' in window && 'sendBeacon' in navigator) {
        const data = JSON.stringify({
          type: 'performance_report',
          timestamp: Date.now(),
          stats,
        });
        navigator.sendBeacon('/api/v1/monitoring/performance', data);
      }
    }, this.config.performanceReportingInterval);
  }

  private stopPerformanceReporting(): void {
    if (this.performanceReportTimer) {
      clearInterval(this.performanceReportTimer);
      this.performanceReportTimer = undefined;
    }
  }
}

// 创建全局监控实例
export const apiMonitor = new ApiMonitor();

// 监控装饰器
export function monitorApiCall<T extends (...args: any[]) => Promise<any>>(
  target: T,
  endpoint: string,
  method: string = 'GET'
): T {
  return (async (...args: any[]) => {
    const startTime = performance.now();
    let success = false;
    let error: string | undefined;
    let status = 0;

    try {
      const result = await target(...args);
      success = true;
      status = 200; // 假设成功状态
      return result;
    } catch (err) {
      if (err instanceof ApiError) {
        status = err.code;
        error = err.message;
      } else if (err instanceof NetworkError) {
        error = err.message;
      } else if (err instanceof TimeoutError) {
        error = err.message;
      } else {
        error = err instanceof Error ? err.message : '未知错误';
      }
      throw err;
    } finally {
      const duration = performance.now() - startTime;
      apiMonitor.recordApiCall({
        url: endpoint,
        method,
        duration,
        status,
        success,
        error,
      });
    }
  }) as T;
}

// 性能分析工具
export const performanceAnalyzer = {
  /**
   * 分析API性能趋势
   */
  analyzeTrends(timeRange: number = 24 * 60 * 60 * 1000): {
    trend: 'improving' | 'degrading' | 'stable';
    changePercentage: number;
    recommendation: string;
  } {
    const now = Date.now();
    const halfRange = timeRange / 2;
    
    const recentStats = apiMonitor.getPerformanceStats(halfRange);
    const olderStats = apiMonitor.getPerformanceStats(timeRange);
    
    const recentAvgTime = recentStats.averageResponseTime;
    const olderAvgTime = olderStats.averageResponseTime;
    
    if (olderAvgTime === 0) {
      return {
        trend: 'stable',
        changePercentage: 0,
        recommendation: '数据不足，无法分析趋势',
      };
    }
    
    const changePercentage = ((recentAvgTime - olderAvgTime) / olderAvgTime) * 100;
    
    let trend: 'improving' | 'degrading' | 'stable';
    let recommendation: string;
    
    if (changePercentage > 10) {
      trend = 'degrading';
      recommendation = '性能下降，建议检查慢查询和网络状况';
    } else if (changePercentage < -10) {
      trend = 'improving';
      recommendation = '性能改善，继续保持当前优化策略';
    } else {
      trend = 'stable';
      recommendation = '性能稳定，可考虑进一步优化';
    }
    
    return {
      trend,
      changePercentage: Math.abs(changePercentage),
      recommendation,
    };
  },
  
  /**
   * 生成性能报告
   */
  generateReport(): string {
    const stats = apiMonitor.getPerformanceStats();
    const trends = this.analyzeTrends();
    
    return `
# API性能报告

## 总体统计
- 总请求数: ${stats.totalCalls}
- 成功率: ${stats.successRate.toFixed(2)}%
- 平均响应时间: ${stats.averageResponseTime.toFixed(2)}ms
- 错误率: ${stats.errorRate.toFixed(2)}%

## 性能趋势
- 趋势: ${trends.trend}
- 变化幅度: ${trends.changePercentage.toFixed(2)}%
- 建议: ${trends.recommendation}

## 最慢端点
${stats.slowestEndpoints.map(ep => 
  `- ${ep.url}: ${ep.averageTime.toFixed(2)}ms (${ep.callCount}次调用)`
).join('\n')}

## 错误统计
${Object.entries(stats.errorsByType).map(([type, count]) => 
  `- ${type}: ${count}次`
).join('\n')}
    `.trim();
  },
};

export default apiMonitor;