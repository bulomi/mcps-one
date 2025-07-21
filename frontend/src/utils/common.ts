/**
 * 通用工具函数
 * 减少前端代码重复，提供统一的工具函数
 */

import { h } from 'vue'
import { NTag, NIcon } from 'naive-ui'
import { CheckmarkCircleOutline, CloseCircleOutline, TimeOutline, WarningOutline } from '@vicons/ionicons5'

/**
 * 状态映射工具
 */
export class StatusMapper {
  /**
   * 映射工具状态到前端显示
   */
  static mapToolStatus(backendStatus: string): {
    frontendStatus: 'active' | 'inactive' | 'error' | 'starting' | 'stopping'
    type: 'success' | 'default' | 'error' | 'warning'
    text: string
    icon?: any
  } {
    switch (backendStatus) {
      case 'running':
        return {
          frontendStatus: 'active',
          type: 'success',
          text: '运行中',
          icon: CheckmarkCircleOutline
        }
      case 'stopped':
        return {
          frontendStatus: 'inactive',
          type: 'default',
          text: '已停止',
          icon: CloseCircleOutline
        }
      case 'starting':
        return {
          frontendStatus: 'starting',
          type: 'warning',
          text: '启动中',
          icon: TimeOutline
        }
      case 'stopping':
        return {
          frontendStatus: 'stopping',
          type: 'warning',
          text: '停止中',
          icon: TimeOutline
        }
      case 'error':
      case 'unknown':
      default:
        return {
          frontendStatus: 'error',
          type: 'error',
          text: '错误',
          icon: WarningOutline
        }
    }
  }

  /**
   * 映射任务状态
   */
  static mapTaskStatus(status: string): { type: string; text: string; frontendStatus?: string } {
    switch (status) {
      case 'pending':
        return { type: 'warning', text: '等待中' }
      case 'running':
        return { type: 'info', text: '执行中' }
      case 'completed':
        return { type: 'success', text: '已完成' }
      case 'failed':
        return { type: 'error', text: '失败' }
      case 'cancelled':
        return { type: 'error', text: '已取消' }
      default:
        return { type: 'default', text: status || '未知' }
    }
  }

  /**
   * 映射执行模式
   */
  static mapExecutionMode(mode: string): string {
    switch (mode) {
      case 'single_tool':
        return '单工具'
      case 'multi_tool':
        return '多工具'
      case 'auto':
        return '自动'
      default:
        return mode
    }
  }
}

/**
 * 渲染工具
 */
export class RenderUtils {
  /**
   * 渲染状态标签
   */
  static renderStatusTag(status: string, mapper: 'tool' | 'task' = 'tool') {
    const statusInfo = mapper === 'tool' 
      ? StatusMapper.mapToolStatus(status)
      : StatusMapper.mapTaskStatus(status)
    
    return h(NTag, {
      type: statusInfo.type
    }, {
      default: () => statusInfo.text,
      icon: statusInfo.icon ? () => h(NIcon, null, { default: () => h(statusInfo.icon) }) : undefined
    })
  }

  /**
   * 渲染代码块
   */
  static renderCodeBlock(content: string, maxLength: number = 50) {
    const displayContent = content.length > maxLength 
      ? content.substring(0, maxLength) + '...'
      : content
    
    return h('code', {
      style: 'background: #f5f5f5; padding: 2px 6px; border-radius: 4px; font-size: 12px;',
      title: content
    }, displayContent || 'N/A')
  }

  /**
   * 渲染工具名称
   */
  static renderToolName(name: string) {
    return h('div', {
      style: 'font-weight: 600; color: #2080f0;'
    }, name)
  }
}

/**
 * 数据处理工具
 */
export class DataUtils {
  /**
   * 标准化API响应数据
   */
  static normalizeApiResponse<T>(response: any): T[] {
    // 处理API响应数据结构
    let data = response
    if (response && typeof response === 'object' && 'data' in response) {
      data = response.data
    }
    
    // 处理分页格式或直接数组格式
    if (data && typeof data === 'object' && 'items' in data) {
      return data.items || []
    } else if (Array.isArray(data)) {
      return data
    } else {
      return []
    }
  }

  /**
   * 安全的JSON解析
   */
  static safeJsonParse<T>(jsonString: string, defaultValue: T): T {
    try {
      return JSON.parse(jsonString)
    } catch {
      return defaultValue
    }
  }

  /**
   * 过滤和搜索数据
   */
  static filterData<T extends Record<string, any>>(
    data: T[],
    searchQuery: string,
    searchFields: (keyof T)[],
    filters: Record<string, any> = {}
  ): T[] {
    let result = data
    
    // 搜索过滤
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      result = result.filter(item => 
        searchFields.some(field => 
          String(item[field]).toLowerCase().includes(query)
        )
      )
    }
    
    // 其他过滤条件
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        result = result.filter(item => item[key] === value)
      }
    })
    
    return result
  }
}

/**
 * 时间格式化工具
 */
export class TimeUtils {
  /**
   * 格式化时间
   */
  static formatTime(timeStr: string): string {
    if (!timeStr) return 'N/A'
    return new Date(timeStr).toLocaleString('zh-CN')
  }

  /**
   * 获取相对时间
   */
  static getRelativeTime(date: Date): string {
    const now = new Date()
    const diff = Math.floor((now.getTime() - date.getTime()) / 1000)
    
    if (diff < 60) {
      return `${diff}秒前`
    } else if (diff < 3600) {
      return `${Math.floor(diff / 60)}分钟前`
    } else if (diff < 86400) {
      return `${Math.floor(diff / 3600)}小时前`
    } else {
      return date.toLocaleString('zh-CN')
    }
  }

  /**
   * 计算相对时间
   */
  static getRelativeTime(time: string | Date): string {
    if (!time) return 'N/A'
    
    const date = typeof time === 'string' ? new Date(time) : time
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    
    const seconds = Math.floor(diff / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)
    
    if (days > 0) return `${days}天前`
    if (hours > 0) return `${hours}小时前`
    if (minutes > 0) return `${minutes}分钟前`
    return `${seconds}秒前`
  }
}

/**
 * 文件操作工具
 */
export class FileUtils {
  /**
   * 下载文件
   */
  static downloadFile(blob: Blob, filename: string) {
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  /**
   * 生成带时间戳的文件名
   */
  static generateTimestampFilename(baseName: string, extension: string): string {
    const timestamp = new Date().toISOString().split('T')[0]
    return `${baseName}-${timestamp}.${extension}`
  }
}

/**
 * 验证工具
 */
export class ValidationUtils {
  /**
   * 验证工具ID
   */
  static isValidToolId(id: any): boolean {
    return id !== null && id !== undefined && !isNaN(Number(id))
  }

  /**
   * 验证URL
   */
  static isValidUrl(url: string): boolean {
    try {
      new URL(url)
      return true
    } catch {
      return false
    }
  }

  /**
   * 验证端口号
   */
  static isValidPort(port: any): boolean {
    const portNum = Number(port)
    return !isNaN(portNum) && portNum > 0 && portNum <= 65535
  }
}