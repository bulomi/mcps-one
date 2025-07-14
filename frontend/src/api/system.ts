import api from './index'

// 系统统计信息类型
export interface SystemStats {
  totalTools: number
  activeTools: number
  totalSessions: number
  activeSessions: number
  totalTasks: number
  completedTasks: number
  failedTasks: number
  systemUptime: string
  memoryUsage: {
    used: number
    total: number
    percentage: number
  }
  cpuUsage: number
}

// 系统日志类型
export interface SystemLog {
  id: number
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL'
  message: string
  module: string
  timestamp: string
  details?: any
}

// 系统配置类型
export interface SystemConfig {
  id: number
  key: string
  value: any
  description?: string
  category: string
  updated_at: string
}

// 系统API接口
export const systemApi = {
  // 获取系统统计信息
  getStats: async (): Promise<SystemStats> => {
    return await api.get('/system/stats')
  },

  // 获取系统日志
  getLogs: async (params?: {
    level?: string
    module?: string
    start_time?: string
    end_time?: string
    page?: number
    size?: number
  }): Promise<{
    items: SystemLog[]
    total: number
    page: number
    size: number
    pages: number
  }> => {
    return await api.get('/system/logs', { params })
  },

  // 获取系统配置
  getConfigs: async (category?: string): Promise<SystemConfig[]> => {
    const params = category ? { category } : {}
    return await api.get('/system/config', { params })
  },

  // 更新系统配置
  updateConfig: async (key: string, value: any): Promise<SystemConfig> => {
    return await api.put(`/system/config/${key}`, { value })
  },

  // 批量保存系统设置
  saveSettings: async (settings: any): Promise<{ success: boolean; message: string }> => {
    return await api.post('/system/settings/save', settings)
  },

  // 导入系统设置
  importSettings: async (settings: any): Promise<{ success: boolean; message: string }> => {
    return await api.post('/system/settings/import', settings)
  },

  // 导出系统设置
  exportSettings: async (): Promise<any> => {
    return await api.get('/system/settings/export')
  },

  // 测试数据库连接
  testDatabaseConnection: async (config?: any): Promise<{ success: boolean; message: string }> => {
    return await api.post('/system/test/database', config)
  },

  // 创建数据库备份
  createBackup: async (data?: any): Promise<{ success: boolean; message: string; backup_id: string }> => {
    return await api.post('/system/backups', data)
  },

  // 获取备份列表
  getBackups: async (): Promise<any[]> => {
    return await api.get('/system/backups')
  },

  // 下载备份
  downloadBackup: async (backupId: string): Promise<Blob> => {
    return await api.get(`/system/backups/${backupId}/download`, {
      responseType: 'blob'
    })
  },

  // 删除备份
  deleteBackup: async (backupId: string): Promise<{ success: boolean; message: string }> => {
    return await api.delete(`/system/backups/${backupId}`)
  },

  // 测试邮件通知
  testEmailNotification: async (email: string): Promise<{ success: boolean; message: string }> => {
    return await api.post(`/system/test/email?email=${encodeURIComponent(email)}`)
  },

  // 测试Webhook通知
  testWebhookNotification: async (url: string): Promise<{ success: boolean; message: string }> => {
    return await api.post(`/system/test/webhook?url=${encodeURIComponent(url)}`)
  },

  // 清理缓存
  clearCache: async (): Promise<{ success: boolean; message: string }> => {
    return await api.post('/system/cache/clear')
  },

  // 重置设置为默认值
  resetToDefaults: async (confirm: boolean = true): Promise<{ success: boolean; message: string }> => {
    return await api.post(`/system/settings/reset?confirm=${confirm}`)
  },

  // 获取系统信息
  getSystemInfo: async (): Promise<{
    version: string
    python_version: string
    platform: string
    architecture: string
    hostname: string
    uptime: string
    memory: {
      used: number
      total: number
      percentage: number
    }
    disk: {
      used: number
      total: number
      percentage: number
    }
    database_version: string
    last_update: string
  }> => {
    return await api.get('/system/info')
  },

  // 健康检查
  healthCheck: async (): Promise<{
    status: 'healthy' | 'unhealthy'
    checks: {
      database: boolean
      mcp_agent: boolean
      file_system: boolean
    }
    timestamp: string
  }> => {
    return await api.get('/system/health')
  }
}

export default systemApi