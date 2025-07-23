/**
 * 格式化工具函数 - TypeScript 版本
 */

/**
 * 格式化字节大小
 * @param bytes - 字节数
 * @param decimals - 小数位数
 * @returns 格式化后的字节字符串
 */
export function formatBytes(bytes: number, decimals: number = 2): string {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
  
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}

/**
 * 格式化日期时间
 * @param timestamp - 时间戳或日期字符串
 * @param format - 格式类型
 * @returns 格式化后的时间字符串
 */
export function formatDateTime(timestamp: string | Date | number, format: 'datetime' | 'date' | 'time' | 'relative' = 'datetime'): string {
  if (!timestamp) return '-'
  
  const date = new Date(timestamp)
  
  if (isNaN(date.getTime())) return '-'
  
  switch (format) {
    case 'date':
      return date.toLocaleDateString('zh-CN')
    
    case 'time':
      return date.toLocaleTimeString('zh-CN', { 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit'
      })
    
    case 'datetime':
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    
    case 'relative':
      return formatRelativeTime(date)
    
    default:
      return date.toLocaleString('zh-CN')
  }
}

/**
 * 格式化相对时间
 * @param date - 日期对象
 * @returns 相对时间字符串
 */
export function formatRelativeTime(date: Date): string {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  
  if (days > 0) {
    return `${days}天前`
  } else if (hours > 0) {
    return `${hours}小时前`
  } else if (minutes > 0) {
    return `${minutes}分钟前`
  } else if (seconds > 0) {
    return `${seconds}秒前`
  } else {
    return '刚刚'
  }
}

/**
 * 格式化持续时间
 * @param seconds - 秒数
 * @returns 格式化后的持续时间字符串
 */
export function formatDuration(seconds: number): string {
  if (typeof seconds !== 'number' || isNaN(seconds) || seconds < 0) {
    return '0秒'
  }
  
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  const parts: string[] = []
  
  if (days > 0) parts.push(`${days}天`)
  if (hours > 0) parts.push(`${hours}小时`)
  if (minutes > 0) parts.push(`${minutes}分钟`)
  if (secs > 0 || parts.length === 0) parts.push(`${secs}秒`)
  
  return parts.join('')
}

/**
 * 格式化百分比
 * @param value - 数值
 * @param decimals - 小数位数
 * @returns 格式化后的百分比字符串
 */
export function formatPercentage(value: number, decimals: number = 1): string {
  if (typeof value !== 'number' || isNaN(value)) return '0%'
  return `${value.toFixed(decimals)}%`
}

/**
 * 格式化数字
 * @param value - 数值
 * @param decimals - 小数位数
 * @returns 格式化后的数字字符串
 */
export function formatNumber(value: number, decimals: number = 0): string {
  if (typeof value !== 'number' || isNaN(value)) return '0'
  
  if (value >= 1000000000) {
    return (value / 1000000000).toFixed(decimals) + 'B'
  } else if (value >= 1000000) {
    return (value / 1000000).toFixed(decimals) + 'M'
  } else if (value >= 1000) {
    return (value / 1000).toFixed(decimals) + 'K'
  } else {
    return value.toFixed(decimals)
  }
}

/**
 * 格式化状态
 * @param status - 状态值
 * @returns 格式化后的状态字符串
 */
export function formatStatus(status: string): string {
  const statusMap: Record<string, string> = {
    'running': '运行中',
    'stopped': '已停止',
    'starting': '启动中',
    'stopping': '停止中',
    'restarting': '重启中',
    'active': '活跃',
    'inactive': '非活跃',
    'pending': '等待中',
    'completed': '已完成',
    'failed': '失败',
    'success': '成功',
    'warning': '警告',
    'error': '错误',
    'unknown': '未知'
  }
  
  return statusMap[status] || status
}

/**
 * 格式化日志级别
 * @param level - 日志级别
 * @returns 格式化后的日志级别字符串
 */
export function formatLogLevel(level: string): string {
  const levelMap: Record<string, string> = {
    'debug': '调试',
    'info': '信息',
    'warn': '警告',
    'warning': '警告',
    'error': '错误',
    'fatal': '致命',
    'trace': '跟踪'
  }
  
  return levelMap[level.toLowerCase()] || level
}

/**
 * 格式化时间 - 兼容性函数
 * @param timestamp - 时间戳或日期字符串
 * @returns 格式化后的时间字符串
 */
export function formatTime(timestamp: string | Date | number): string {
  return formatDateTime(timestamp, 'datetime')
}

/**
 * 格式化工具类型
 * @param type - 工具类型
 * @returns 格式化后的工具类型字符串
 */
export function formatToolType(type: string): string {
  const typeMap: Record<string, string> = {
    'function': '函数',
    'resource': '资源',
    'prompt': '提示',
    'tool': '工具',
    'service': '服务',
    'api': 'API',
    'database': '数据库',
    'file': '文件',
    'network': '网络',
    'system': '系统'
  }
  
  return typeMap[type] || type
}