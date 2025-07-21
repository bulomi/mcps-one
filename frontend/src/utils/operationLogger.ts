// 操作日志类型定义
export interface OperationLog {
  id: string
  timestamp: string
  userId?: string
  action: string
  module: string
  details: any
  result: 'success' | 'error' | 'warning'
  duration?: number
  userAgent: string
  ip?: string
}

// 操作类型枚举
export enum OperationAction {
  // MCP工具操作
  MCP_TOOL_START = 'mcp_tool_start',
  MCP_TOOL_STOP = 'mcp_tool_stop',
  MCP_TOOL_RESTART = 'mcp_tool_restart',
  MCP_TOOL_CONNECT = 'mcp_tool_connect',
  MCP_TOOL_DISCONNECT = 'mcp_tool_disconnect',
  MCP_TOOL_CALL = 'mcp_tool_call',
  
  // 会话操作
  SESSION_CREATE = 'session_create',
  SESSION_DELETE = 'session_delete',
  SESSION_UPDATE = 'session_update',
  
  // 系统设置
  SETTINGS_UPDATE = 'settings_update',
  SETTINGS_BACKUP = 'settings_backup',
  SETTINGS_RESTORE = 'settings_restore',
  
  // 告警操作

  
  // 日志操作
  LOG_VIEW = 'log_view',
  LOG_EXPORT = 'log_export',
  LOG_CLEAR = 'log_clear',
  
  // 用户操作
  USER_LOGIN = 'user_login',
  USER_LOGOUT = 'user_logout',
  USER_FEEDBACK = 'user_feedback'
}

// 模块枚举
export enum OperationModule {
  MCP_AGENT = 'mcp_agent',
  DASHBOARD = 'dashboard',

  LOGS = 'logs',
  SETTINGS = 'settings',
  PROXY = 'proxy',
  SYSTEM = 'system'
}

// 操作日志管理器
export class OperationLogger {
  private static readonly STORAGE_KEY = 'operation_logs'
  private static readonly MAX_LOGS = 1000 // 最大保存日志数量

  /**
   * 记录操作日志
   * @param action 操作类型
   * @param module 模块
   * @param details 详细信息
   * @param result 操作结果
   * @param duration 操作耗时（毫秒）
   */
  static log(
    action: OperationAction,
    module: OperationModule,
    details: any = {},
    result: 'success' | 'error' | 'warning' = 'success',
    duration?: number
  ): void {
    const log: OperationLog = {
      id: this.generateId(),
      timestamp: new Date().toISOString(),
      action,
      module,
      details,
      result,
      duration,
      userAgent: navigator.userAgent
    }

    this.saveLog(log)
  }

  /**
   * 记录成功操作
   */
  static logSuccess(
    action: OperationAction,
    module: OperationModule,
    details: any = {},
    duration?: number
  ): void {
    this.log(action, module, details, 'success', duration)
  }

  /**
   * 记录错误操作
   */
  static logError(
    action: OperationAction,
    module: OperationModule,
    details: any = {},
    duration?: number
  ): void {
    this.log(action, module, details, 'error', duration)
  }

  /**
   * 记录警告操作
   */
  static logWarning(
    action: OperationAction,
    module: OperationModule,
    details: any = {},
    duration?: number
  ): void {
    this.log(action, module, details, 'warning', duration)
  }

  /**
   * 获取操作日志
   * @param limit 限制数量
   * @param module 模块过滤
   * @param action 操作过滤
   * @returns 操作日志列表
   */
  static getLogs(
    limit?: number,
    module?: OperationModule,
    action?: OperationAction
  ): OperationLog[] {
    const logs = this.getAllLogs()
    
    let filteredLogs = logs
    
    if (module) {
      filteredLogs = filteredLogs.filter(log => log.module === module)
    }
    
    if (action) {
      filteredLogs = filteredLogs.filter(log => log.action === action)
    }
    
    if (limit) {
      filteredLogs = filteredLogs.slice(0, limit)
    }
    
    return filteredLogs
  }

  /**
   * 获取今日操作统计
   */
  static getTodayStats(): Record<string, number> {
    const today = new Date().toDateString()
    const logs = this.getAllLogs().filter(log => 
      new Date(log.timestamp).toDateString() === today
    )
    
    const stats: Record<string, number> = {
      total: logs.length,
      success: 0,
      error: 0,
      warning: 0
    }
    
    logs.forEach(log => {
      stats[log.result]++
    })
    
    return stats
  }

  /**
   * 清除操作日志
   * @param beforeDate 清除指定日期之前的日志
   */
  static clearLogs(beforeDate?: Date): void {
    if (beforeDate) {
      const logs = this.getAllLogs().filter(log => 
        new Date(log.timestamp) >= beforeDate
      )
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(logs))
    } else {
      localStorage.removeItem(this.STORAGE_KEY)
    }
  }

  /**
   * 导出操作日志
   * @param format 导出格式
   */
  static exportLogs(format: 'json' | 'csv' = 'json'): string {
    const logs = this.getAllLogs()
    
    if (format === 'csv') {
      const headers = ['ID', '时间', '操作', '模块', '结果', '耗时', '详情']
      const csvContent = [
        headers.join(','),
        ...logs.map(log => [
          log.id,
          log.timestamp,
          log.action,
          log.module,
          log.result,
          log.duration || '',
          JSON.stringify(log.details).replace(/"/g, '""')
        ].join(','))
      ].join('\n')
      
      return csvContent
    }
    
    return JSON.stringify(logs, null, 2)
  }

  /**
   * 保存日志到本地存储
   */
  private static saveLog(log: OperationLog): void {
    const logs = this.getAllLogs()
    logs.unshift(log) // 新日志添加到开头
    
    // 限制日志数量
    if (logs.length > this.MAX_LOGS) {
      logs.splice(this.MAX_LOGS)
    }
    
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(logs))
  }

  /**
   * 从本地存储获取所有日志
   */
  private static getAllLogs(): OperationLog[] {
    try {
      const logsJson = localStorage.getItem(this.STORAGE_KEY)
      return logsJson ? JSON.parse(logsJson) : []
    } catch (error) {
      console.error('Failed to parse operation logs:', error)
      return []
    }
  }

  /**
   * 生成唯一ID
   */
  private static generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }
}

// 导出便捷方法
export const logOperation = OperationLogger.log.bind(OperationLogger)
export const logSuccess = OperationLogger.logSuccess.bind(OperationLogger)
export const logError = OperationLogger.logError.bind(OperationLogger)
export const logWarning = OperationLogger.logWarning.bind(OperationLogger)
export const getOperationLogs = OperationLogger.getLogs.bind(OperationLogger)
export const getTodayStats = OperationLogger.getTodayStats.bind(OperationLogger)
export const clearOperationLogs = OperationLogger.clearLogs.bind(OperationLogger)
export const exportOperationLogs = OperationLogger.exportLogs.bind(OperationLogger)