/**
 * 格式化工具函数
 */

/**
 * 格式化字节数为可读格式
 * @param {number} bytes - 字节数
 * @param {number} decimals - 小数位数
 * @returns {string} 格式化后的字符串
 */
export function formatBytes(bytes, decimals = 2) {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
  
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}

/**
 * 格式化时间戳为可读格式
 * @param {string|Date} timestamp - 时间戳
 * @param {string} format - 格式类型 ('datetime', 'date', 'time', 'relative')
 * @returns {string} 格式化后的时间字符串
 */
export function formatTime(timestamp, format = 'datetime') {
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
 * @param {Date} date - 日期对象
 * @returns {string} 相对时间字符串
 */
export function formatRelativeTime(date) {
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
 * 格式化百分比
 * @param {number} value - 数值
 * @param {number} decimals - 小数位数
 * @returns {string} 格式化后的百分比字符串
 */
export function formatPercentage(value, decimals = 1) {
  if (typeof value !== 'number' || isNaN(value)) return '0%'
  return `${value.toFixed(decimals)}%`
}

/**
 * 格式化数字
 * @param {number} value - 数值
 * @param {number} decimals - 小数位数
 * @returns {string} 格式化后的数字字符串
 */
export function formatNumber(value, decimals = 0) {
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
 * 格式化持续时间
 * @param {number} seconds - 秒数
 * @returns {string} 格式化后的持续时间字符串
 */
export function formatDuration(seconds) {
  if (typeof seconds !== 'number' || isNaN(seconds) || seconds < 0) {
    return '0秒'
  }
  
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  const parts = []
  
  if (days > 0) parts.push(`${days}天`)
  if (hours > 0) parts.push(`${hours}小时`)
  if (minutes > 0) parts.push(`${minutes}分钟`)
  if (secs > 0 || parts.length === 0) parts.push(`${secs}秒`)
  
  return parts.join('')
}

/**
 * 格式化网络速率
 * @param {number} bytesPerSecond - 每秒字节数
 * @param {number} decimals - 小数位数
 * @returns {string} 格式化后的速率字符串
 */
export function formatNetworkSpeed(bytesPerSecond, decimals = 2) {
  if (typeof bytesPerSecond !== 'number' || isNaN(bytesPerSecond) || bytesPerSecond < 0) {
    return '0 B/s'
  }
  
  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['B/s', 'KB/s', 'MB/s', 'GB/s', 'TB/s']
  
  const i = Math.floor(Math.log(bytesPerSecond) / Math.log(k))
  
  return parseFloat((bytesPerSecond / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}

/**
 * 格式化CPU核心数
 * @param {number} cores - 核心数
 * @returns {string} 格式化后的核心数字符串
 */
export function formatCpuCores(cores) {
  if (typeof cores !== 'number' || isNaN(cores) || cores <= 0) {
    return '未知'
  }
  
  return `${cores}核`
}

/**
 * 格式化温度
 * @param {number} celsius - 摄氏度
 * @param {number} decimals - 小数位数
 * @returns {string} 格式化后的温度字符串
 */
export function formatTemperature(celsius, decimals = 1) {
  if (typeof celsius !== 'number' || isNaN(celsius)) {
    return '未知'
  }
  
  return `${celsius.toFixed(decimals)}°C`
}

/**
 * 格式化状态
 * @param {string} status - 状态值
 * @returns {string} 格式化后的状态字符串
 */
export function formatStatus(status) {
  const statusMap = {
    'running': '运行中',
    'stopped': '已停止',
    'sleeping': '休眠',
    'zombie': '僵尸进程',
    'disk-sleep': '磁盘休眠',
    'idle': '空闲',
    'waking': '唤醒中',
    'dead': '已死亡',
    'wake-kill': '唤醒终止',
    'parked': '暂停',
    'active': '活跃',
    'inactive': '非活跃',
    'pending': '等待中',
    'completed': '已完成',
    'failed': '失败',
    'success': '成功',
    'warning': '警告',
    'error': '错误',
    'info': '信息'
  }
  
  return statusMap[status] || status || '未知'
}

/**
 * 格式化优先级
 * @param {number} priority - 优先级数值
 * @returns {string} 格式化后的优先级字符串
 */
export function formatPriority(priority) {
  if (typeof priority !== 'number' || isNaN(priority)) {
    return '普通'
  }
  
  if (priority < -10) return '最高'
  if (priority < -5) return '高'
  if (priority < 0) return '较高'
  if (priority === 0) return '普通'
  if (priority < 5) return '较低'
  if (priority < 10) return '低'
  return '最低'
}

/**
 * 截断文本
 * @param {string} text - 原始文本
 * @param {number} maxLength - 最大长度
 * @param {string} suffix - 后缀
 * @returns {string} 截断后的文本
 */
export function truncateText(text, maxLength = 50, suffix = '...') {
  if (!text || typeof text !== 'string') return ''
  
  if (text.length <= maxLength) return text
  
  return text.substring(0, maxLength - suffix.length) + suffix
}

/**
 * 格式化文件路径
 * @param {string} path - 文件路径
 * @param {number} maxLength - 最大显示长度
 * @returns {string} 格式化后的路径
 */
export function formatPath(path, maxLength = 60) {
  if (!path || typeof path !== 'string') return ''
  
  if (path.length <= maxLength) return path
  
  const parts = path.split(/[\/\\]/)
  if (parts.length <= 2) return truncateText(path, maxLength)
  
  const filename = parts[parts.length - 1]
  const directory = parts[0]
  
  if (filename.length + directory.length + 6 <= maxLength) {
    return `${directory}/.../${filename}`
  }
  
  return truncateText(path, maxLength)
}

export default {
  formatBytes,
  formatTime,
  formatRelativeTime,
  formatPercentage,
  formatNumber,
  formatDuration,
  formatNetworkSpeed,
  formatCpuCores,
  formatTemperature,
  formatStatus,
  formatPriority,
  truncateText,
  formatPath
}