import { api, withCache, handleApiError } from './utils';
import type { ApiResponse } from './utils';
import { SYSTEM_PATHS } from './constants';
import type { LogLevel, LogLevelLowercase } from '@/constants/logLevels';

export interface SystemStats {
  cpu: {
    usage: number;
    cores: number;
    model?: string;
    frequency?: number;
  };
  memory: {
    total: number;
    used: number;
    available: number;
    percentage: number;
  };
  disk: {
    total: number;
    used: number;
    available: number;
    percentage: number;
  };
  network?: {
    bytesReceived: number;
    bytesSent: number;
    packetsReceived: number;
    packetsSent: number;
  };
  uptime: number;
  loadAverage?: number[];
  processes?: number;
  timestamp: string;
  totalTools: number
  activeTools: number
  // totalSessions: number // 会话管理功能已移除
  // activeSessions: number // 会话管理功能已移除
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

export interface LogEntry {
  id: number;
  timestamp: string;
  level: LogLevelLowercase;
  message: string;
  module?: string;
  source?: string;
  metadata?: Record<string, any>;
}

// 系统日志类型
export interface SystemLog {
  id: number
  level: LogLevel
  message: string
  module: string
  timestamp: string
  details?: any
}

export interface ConfigItem {
  key: string;
  value: any;
  description?: string;
  type: 'string' | 'number' | 'boolean' | 'object' | 'array';
  category?: string;
  required?: boolean;
  defaultValue?: any;
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    options?: any[];
  };
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

export interface SystemSettings {
  general: {
    theme: 'light' | 'dark' | 'auto';
    language: string;
    timezone: string;
    autoSave: boolean;
  };
  security: {
    // sessionTimeout: number; // 会话管理功能已移除
    maxLoginAttempts: number;
    passwordPolicy: {
      minLength: number;
      requireUppercase: boolean;
      requireLowercase: boolean;
      requireNumbers: boolean;
      requireSpecialChars: boolean;
    };
  };
  performance: {
    cacheSize: number;
    maxConcurrentTasks: number;
    requestTimeout: number;
  };
  logging: {
    level: string;
    maxFileSize: number;
    retentionDays: number;
  };
}

export interface ConfigExportData {
  version: string;
  timestamp: string;
  configs: ConfigItem[];
  settings: SystemSettings;
}

export interface ConfigImportResult {
  success: boolean;
  imported: number;
  skipped: number;
  errors: string[];
  warnings: string[];
}

// 系统API接口
export const systemApi = {
  /**
   * 获取系统统计信息
   */
  getStats: async (): Promise<ApiResponse<SystemStats>> => {
    try {
      return await withCache(
        'system-stats',
        () => api.get<SystemStats>(SYSTEM_PATHS.STATS || '/system/stats'),
        30 * 1000 // 30秒缓存
      );
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  /**
   * 获取系统日志
   */
  getLogs: async (params?: {
    level?: string
    module?: string
    start_time?: string
    end_time?: string
    page?: number
    size?: number
  }): Promise<ApiResponse<{
    items: SystemLog[]
    total: number
    page: number
    size: number
    pages: number
  }>> => {
    try {
      return await api.get(SYSTEM_PATHS.LOGS || '/system/logs', { params })
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  /**
   * 获取系统配置列表
   */
  getConfigs: async (category?: string): Promise<ApiResponse<SystemConfig[]>> => {
    try {
      const params = category ? { category } : {}
      return await withCache(
        `system-configs-${category || 'all'}`,
        () => api.get<SystemConfig[]>(SYSTEM_PATHS.CONFIG || '/system/config', { params }),
        5 * 60 * 1000 // 5分钟缓存
      );
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  /**
   * 更新单个配置项
   */
  updateConfig: async (key: string, value: any): Promise<ApiResponse<SystemConfig>> => {
    try {
      const result = await api.put<SystemConfig>((SYSTEM_PATHS.CONFIG_UPDATE && SYSTEM_PATHS.CONFIG_UPDATE(key)) || `/system/config/${key}`, { value })
      // 清除相关缓存
      if (typeof clearCache === 'function') clearCache('system-configs');
      return result;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  /**
   * 批量保存系统设置
   */
  saveSettings: async (settings: any): Promise<ApiResponse<{ success: boolean; message: string }>> => {
    try {
      const result = await api.post<{ success: boolean; message: string }>(SYSTEM_PATHS.SETTINGS || '/system/settings', settings)
      // 清除相关缓存
      if (typeof clearCache === 'function') clearCache('system-settings');
      return result;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  /**
   * 获取所有系统设置
   */
  getAllSettings: async (): Promise<ApiResponse<any>> => {
    try {
      return await withCache(
        'system-settings',
        () => api.get<any>(SYSTEM_PATHS.SETTINGS || '/system/settings'),
        10 * 60 * 1000 // 10分钟缓存
      );
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  /**
   * 导出系统配置
   */
  exportConfig: async (includeSettings: boolean = true): Promise<Blob> => {
    try {
      const params = includeSettings ? '?includeSettings=true' : '';
      const path = `${SYSTEM_PATHS.CONFIG_EXPORT || '/system/config/export'}${params}`;
      const response = await api.get(path, { responseType: 'blob' });
      return response.data || response;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  /**
   * 导入系统配置
   */
  importConfig: async (configData: any, overwrite: boolean = false): Promise<ApiResponse<{ success: boolean; message: string }>> => {
    try {
      const formData = new FormData();
      if (configData instanceof File) {
        formData.append('file', configData);
      } else {
        formData.append('data', JSON.stringify(configData));
      }
      formData.append('overwrite', String(overwrite));
      
      const result = await api.post<{ success: boolean; message: string }>(SYSTEM_PATHS.CONFIG_IMPORT || '/system/config/import', formData)
      // 清除所有相关缓存
      if (typeof clearCache === 'function') clearCache('system-');
      return result;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  /**
   * 重置配置为默认值
   */
  resetConfig: async (category?: string): Promise<ApiResponse<{ success: boolean; message: string }>> => {
    try {
      const params = category ? `?category=${category}` : '';
      const result = await api.post<{ success: boolean; message: string }>(`${SYSTEM_PATHS.CONFIG_RESET || '/system/config/reset'}${params}`)
      // 清除所有相关缓存
      if (typeof clearCache === 'function') clearCache('system-');
      return result;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  /**
   * 验证配置值
   */
  validateConfig: async (key: string, value: any): Promise<ApiResponse<{ valid: boolean; errors?: string[] }>> => {
    try {
      return await api.post<{ valid: boolean; errors?: string[] }>('/system/config/validate', { key, value });
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  // 获取配置统计信息
  getConfigStats: async (): Promise<any> => {
    return await api.get('/system/config/stats/')
  },

  // 上传LOGO文件
  uploadLogo: async (formData: FormData): Promise<ApiResponse<{ url: string }>> => {
    try {
      return await api.post<{ url: string }>('/system/upload/logo', formData);
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },



  // 测试数据库连接
  testDatabaseConnection: async (config?: any): Promise<{ success: boolean; message: string }> => {
    return await api.post('/system/test/database/', config)
  },

  // 创建数据库备份
  createBackup: async (data?: any): Promise<{ success: boolean; message: string; backup_id: string }> => {
    return await api.post('/system/backups/', data)
  },

  // 获取备份列表
  getBackups: async (): Promise<any[]> => {
    return await api.get('/system/backups/')
  },

  // 下载备份
  downloadBackup: async (backupId: string): Promise<Blob> => {
    return await api.get(`/system/backups/${backupId}/download/`, {
      responseType: 'blob'
    })
  },

  // 删除备份
  deleteBackup: async (backupId: string): Promise<{ success: boolean; message: string }> => {
    return await api.delete(`/system/backups/${backupId}/`)
  },

  // 邮件和Webhook测试方法已删除

  // 清理缓存
  clearCache: async (): Promise<{ success: boolean; message: string }> => {
    return await api.post('/system/cache/clear/')
  },

  // 重置设置为默认值（保持向后兼容）
  resetToDefaults: async (confirm: boolean = true): Promise<{ success: boolean; message: string }> => {
    return await api.post('/system/config/reset/')
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
    return await api.get('/system/info/')
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
    return await api.get('/system/health/')
  },

  /**
   * 获取系统健康状态
   */
  getHealthStatus: async (): Promise<ApiResponse<{ status: 'healthy' | 'warning' | 'critical'; checks: Record<string, any> }>> => {
    try {
      return await api.get<{ status: 'healthy' | 'warning' | 'critical'; checks: Record<string, any> }>('/system/health');
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },
}

// 导入clearCache函数（如果可用）
let clearCache: ((prefix: string) => void) | undefined;
try {
  const utils = await import('./utils');
  clearCache = utils.clearCache;
} catch {
  // clearCache不可用时的fallback
  clearCache = undefined;
}

export default systemApi