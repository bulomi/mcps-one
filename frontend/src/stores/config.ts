/**
 * 统一配置管理 Store
 * 
 * 提供配置的统一管理、类型安全和响应式更新功能。
 * 支持配置分层、热重载和本地缓存。
 */

import { defineStore } from 'pinia'
import { ref, computed, watch, readonly } from 'vue'
import { systemApi } from '../api/system'
import type { SystemConfig } from '../api/system'

// 配置类型定义
export interface AppConfig {
  // 应用基础配置
  app: {
    name: string
    version: string
    description: string
    showTitle: boolean
    logoUrl: string
  }
  
  // 服务器配置
  server: {
    host: string
    port: number
    debug: boolean
  }
  
  // 功能开关
  features: {
    developerMode: boolean
    apiDocs: boolean
    verboseErrors: boolean
    experimentalFeatures: boolean
    autoUpdate: boolean
    healthCheck: boolean
    websocketEnabled: boolean
  }
  
  // 通知配置
  notifications: {
    email: {
      enabled: boolean
      smtpHost: string
      smtpPort: number
      senderEmail: string
      password: string
      useSSL: boolean
      useTLS: boolean
    }
    webhook: {
      enabled: boolean
      url: string
      timeout: number
      retryCount: number
      events: string[]
    }
  }
  
  // MCP 配置
  mcp: {
    maxProcesses: number
    processTimeout: number
    restartDelay: number
    toolsDir: string
    logsDir: string
    server: {
      enabled: boolean
      transport: string
      host: string
      port: number
      logLevel: string
      showBanner: boolean
      maxConnections: number
      connectionTimeout: number
      statelessHttp: boolean
    }
    proxy: {
      enabled: boolean
      autoStart: boolean
      gracefulShutdown: boolean
      toolStartupTimeout: number
      healthCheckInterval: number
      retryCount: number
      enableMetrics: boolean
    }
  }
  
  // 日志配置
  logging: {
    level: string
    format: string
    file: string
    maxFileSize: string
    backupCount: number
    consoleOutput: boolean
  }
  
  // 国际化配置
  i18n: {
    defaultLanguage: string
    supportedLanguages: string[]
    timezone: string
  }
}

// 配置来源
enum ConfigSource {
  DEFAULT = 'default',
  FILE = 'file',
  DATABASE = 'database',
  RUNTIME = 'runtime'
}

// 配置项信息
export interface ConfigItem {
  key: string
  value: any
  source: ConfigSource
  description: string
  updatedAt: string
  isSensitive: boolean
}

// 默认配置
const defaultConfig: AppConfig = {
  app: {
    name: 'MCPS.ONE',
    version: '1.0.0',
    description: 'MCP 工具管理平台',
    showTitle: true,
    logoUrl: ''
  },
  server: {
    host: '0.0.0.0',
    port: 8000,
    debug: false
  },
  features: {
    developerMode: false,
    apiDocs: true,
    verboseErrors: false,
    experimentalFeatures: false,
    autoUpdate: false,
    healthCheck: true,
    websocketEnabled: true
  },
  notifications: {
    email: {
      enabled: false,
      smtpHost: '',
      smtpPort: 587,
      senderEmail: '',
      password: '',
      useSSL: false,
      useTLS: true
    },
    webhook: {
      enabled: false,
      url: '',
      timeout: 30,
      retryCount: 3,
      events: ['tool_error', 'system_error', 'backup_completed']
    }
  },
  mcp: {
    maxProcesses: 10,
    processTimeout: 30,
    restartDelay: 5,
    toolsDir: './data/tools',
    logsDir: './data/logs',
    server: {
      enabled: false,
      transport: 'stdio',
      host: '127.0.0.1',
      port: 8001,
      logLevel: 'INFO',
      showBanner: true,
      maxConnections: 10,
      connectionTimeout: 30,
      statelessHttp: false
    },
    proxy: {
      enabled: true,
      autoStart: true,
      gracefulShutdown: true,
      toolStartupTimeout: 60,
      healthCheckInterval: 30,
      retryCount: 3,
      enableMetrics: true
    }
  },
  logging: {
    level: 'INFO',
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    file: './data/logs/app.log',
    maxFileSize: '10MB',
    backupCount: 5,
    consoleOutput: true
  },
  i18n: {
    defaultLanguage: 'zh-CN',
    supportedLanguages: ['zh-CN', 'en-US', 'ja-JP'],
    timezone: 'Asia/Shanghai'
  }
}

export const useConfigStore = defineStore('config', () => {
  // 状态
  const config = ref<AppConfig>(JSON.parse(JSON.stringify(defaultConfig)))
  const configItems = ref<Map<string, ConfigItem>>(new Map())
  const loading = ref(false)
  const lastUpdated = ref<Date | null>(null)
  const isDirty = ref(false)
  
  // 计算属性
  const appName = computed(() => config.value.app.name)
  const showTitle = computed(() => config.value.app.showTitle)
  const logoUrl = computed(() => config.value.app.logoUrl)
  const developerMode = computed(() => config.value.features.developerMode)
  const apiDocsEnabled = computed(() => config.value.features.apiDocs)
  
  // 监听配置变化
  watch(
    config,
    () => {
      isDirty.value = true
      // 自动保存到本地存储
      saveToLocalStorage()
    },
    { deep: true }
  )
  
  /**
   * 获取配置值
   */
  function get<T = any>(key: string, defaultValue?: T): T {
    const keys = key.split('.')
    let value: any = config.value
    
    for (const k of keys) {
      if (value && typeof value === 'object' && k in value) {
        value = value[k]
      } else {
        return defaultValue as T
      }
    }
    
    return value as T
  }
  
  /**
   * 设置配置值
   */
  function set(key: string, value: any): void {
    const keys = key.split('.')
    let current: any = config.value
    
    // 导航到父级对象
    for (let i = 0; i < keys.length - 1; i++) {
      const k = keys[i]
      if (!(k in current) || typeof current[k] !== 'object') {
        current[k] = {}
      }
      current = current[k]
    }
    
    // 设置值
    const lastKey = keys[keys.length - 1]
    current[lastKey] = value
    
    // 记录配置项信息
    configItems.value.set(key, {
      key,
      value,
      source: ConfigSource.RUNTIME,
      description: `运行时设置`,
      updatedAt: new Date().toISOString(),
      isSensitive: key.includes('password') || key.includes('secret') || key.includes('key')
    })
  }
  
  /**
   * 批量更新配置
   */
  function updateConfig(newConfig: Partial<AppConfig>): void {
    config.value = deepMerge(config.value, newConfig)
    lastUpdated.value = new Date()
  }
  
  /**
   * 从服务器加载配置
   */
  async function loadFromServer(): Promise<void> {
    loading.value = true
    try {
      const settings = await systemApi.getAllSettings()
      
      // 合并服务器配置
      if (settings && Object.keys(settings).length > 0) {
        updateConfig(settings)
        
        // 记录配置项来源
        Object.keys(flattenObject(settings)).forEach(key => {
          configItems.value.set(key, {
            key,
            value: get(key),
            source: ConfigSource.DATABASE,
            description: '服务器配置',
            updatedAt: new Date().toISOString(),
            isSensitive: key.includes('password') || key.includes('secret')
          })
        })
      }
      
      isDirty.value = false
      lastUpdated.value = new Date()
      
    } catch (error) {
      console.error('加载服务器配置失败:', error)
      // 回退到本地存储
      loadFromLocalStorage()
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 保存配置到服务器
   */
  async function saveToServer(): Promise<void> {
    loading.value = true
    try {
      await systemApi.saveSettings(config.value)
      
      isDirty.value = false
      lastUpdated.value = new Date()
      
    } catch (error) {
      console.error('保存配置到服务器失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 从本地存储加载配置
   */
  function loadFromLocalStorage(): void {
    try {
      const stored = localStorage.getItem('mcps-config')
      if (stored) {
        const parsedConfig = JSON.parse(stored)
        updateConfig(parsedConfig)
        
        // 标记为本地配置
        Object.keys(flattenObject(parsedConfig)).forEach(key => {
          configItems.value.set(key, {
            key,
            value: get(key),
            source: ConfigSource.RUNTIME,
            description: '本地存储',
            updatedAt: new Date().toISOString(),
            isSensitive: false
          })
        })
      }
    } catch (error) {
      console.error('从本地存储加载配置失败:', error)
    }
  }
  
  /**
   * 保存配置到本地存储
   */
  function saveToLocalStorage(): void {
    try {
      localStorage.setItem('mcps-config', JSON.stringify(config.value))
    } catch (error) {
      console.error('保存配置到本地存储失败:', error)
    }
  }
  
  /**
   * 重置配置到默认值
   */
  async function resetToDefault(): Promise<void> {
    loading.value = true
    try {
      await systemApi.resetConfig()
      config.value = JSON.parse(JSON.stringify(defaultConfig))
      configItems.value.clear()
      isDirty.value = false
      lastUpdated.value = new Date()
    } catch (error) {
      console.error('重置配置失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 导出配置
   */
  async function exportConfig(format: 'json' | 'yaml' = 'json'): Promise<string> {
    try {
      const exportedConfig = await systemApi.exportConfig()
      
      if (format === 'yaml') {
        // 简单的 YAML 导出（实际项目中可能需要 js-yaml 库）
        return JSON.stringify(exportedConfig, null, 2)
          .replace(/"/g, '')
          .replace(/,/g, '')
          .replace(/{/g, '')
          .replace(/}/g, '')
      }
      return JSON.stringify(exportedConfig, null, 2)
    } catch (error) {
      console.error('导出配置失败:', error)
      throw error
    }
  }
  
  /**
   * 导入配置
   */
  async function importConfig(configData: string, format: 'json' | 'yaml' = 'json'): Promise<void> {
    loading.value = true
    try {
      let parsedConfig: Partial<AppConfig>
      
      if (format === 'json') {
        parsedConfig = JSON.parse(configData)
      } else {
        // 简单的 YAML 解析（实际项目中应使用专门的库）
        parsedConfig = JSON.parse(configData)
      }
      
      await systemApi.importConfig(parsedConfig)
      updateConfig(parsedConfig)
      isDirty.value = false
      lastUpdated.value = new Date()
      
    } catch (error) {
      console.error('导入配置失败:', error)
      throw new Error('配置格式不正确')
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 获取配置统计信息
   */
  async function getConfigStats() {
    try {
      const serverStats = await systemApi.getConfigStats()
      
      const localStats = {
        total: configItems.value.size,
        sources: {} as Record<ConfigSource, number>,
        lastUpdated: lastUpdated.value,
        isDirty: isDirty.value
      }
      
      // 统计各来源的配置数量
      Object.values(ConfigSource).forEach(source => {
        localStats.sources[source] = 0
      })
      
      configItems.value.forEach(item => {
        localStats.sources[item.source]++
      })
      
      return {
        ...serverStats,
        local: localStats
      }
    } catch (error) {
      console.error('获取配置统计失败:', error)
      return {
        total: configItems.value.size,
        sources: {} as Record<ConfigSource, number>,
        lastUpdated: lastUpdated.value,
        isDirty: isDirty.value
      }
    }
  }
  
  // 工具函数
  function deepMerge(target: any, source: any): any {
    const result = { ...target }
    
    for (const key in source) {
      if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
        result[key] = deepMerge(target[key] || {}, source[key])
      } else {
        result[key] = source[key]
      }
    }
    
    return result
  }
  
  function flattenObject(obj: any, prefix = ''): Record<string, any> {
    const flattened: Record<string, any> = {}
    
    for (const key in obj) {
      const newKey = prefix ? `${prefix}.${key}` : key
      
      if (obj[key] && typeof obj[key] === 'object' && !Array.isArray(obj[key])) {
        Object.assign(flattened, flattenObject(obj[key], newKey))
      } else {
        flattened[newKey] = obj[key]
      }
    }
    
    return flattened
  }
  
  function convertConfigArrayToObject(configs: SystemConfig[]): Partial<AppConfig> {
    const result: any = {}
    
    configs.forEach(config => {
      const keys = config.key.split('.')
      let current = result
      
      for (let i = 0; i < keys.length - 1; i++) {
        const key = keys[i]
        if (!(key in current)) {
          current[key] = {}
        }
        current = current[key]
      }
      
      const lastKey = keys[keys.length - 1]
      current[lastKey] = parseConfigValue(config.value)
    })
    
    return result
  }
  
  function parseConfigValue(value: any): any {
    if (typeof value === 'string') {
      // 尝试解析布尔值
      if (value === 'true') return true
      if (value === 'false') return false
      
      // 尝试解析数字
      const num = Number(value)
      if (!isNaN(num) && isFinite(num)) return num
      
      // 尝试解析 JSON
      if (value.startsWith('{') || value.startsWith('[')) {
        try {
          return JSON.parse(value)
        } catch {
          // 解析失败，返回原字符串
        }
      }
    }
    
    return value
  }
  
  // 初始化
  function initialize(): void {
    // 优先从本地存储加载
    loadFromLocalStorage()
    
    // 暂时注释掉服务器加载，避免API错误
    // loadFromServer()
  }
  
  return {
    // 状态
    config: readonly(config),
    configItems: readonly(configItems),
    loading: readonly(loading),
    lastUpdated: readonly(lastUpdated),
    isDirty: readonly(isDirty),
    
    // 计算属性
    appName,
    showTitle,
    logoUrl,
    developerMode,
    apiDocsEnabled,
    
    // 方法
    get,
    set,
    updateConfig,
    loadFromServer,
    saveToServer,
    loadFromLocalStorage,
    saveToLocalStorage,
    resetToDefault,
    exportConfig,
    importConfig,
    getConfigStats,
    initialize
  }
})

// 类型导出
export type { AppConfig, ConfigItem, ConfigSource }