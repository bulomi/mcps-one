/**
 * 应用状态管理
 * 
 * 基于新的统一配置管理器，提供向后兼容的应用状态接口
 */

import { defineStore } from 'pinia'
import { computed, watch } from 'vue'
import { useConfigStore } from './config'

export interface AppConfig {
  appName: string
  version: string
  showTitle: boolean
  logLevel: string
  language: string
  timezone: string
  logo: string
}

export const useAppStore = defineStore('app', () => {
  // 使用统一配置管理器
  const configStore = useConfigStore()
  
  // 计算属性，从配置管理器获取值
  const appName = computed({
    get: () => configStore.get('app.name', 'MCPS.ONE'),
    set: (value: string) => {
      configStore.set('app.name', value)
      // 同时更新网站标题
      const subtitle = configStore.get('app.subtitle', '')
      if (subtitle && subtitle.trim()) {
        document.title = `${value} - ${subtitle}`
      } else {
        document.title = value
      }
    }
  })
  
  const version = computed({
    get: () => configStore.get('app.version', '1.0.0'),
    set: (value: string) => configStore.set('app.version', value)
  })
  
  const showTitle = computed({
    get: () => configStore.get('app.showTitle', true),
    set: (value: boolean) => configStore.set('app.showTitle', value)
  })
  
  const logLevel = computed({
    get: () => configStore.get('logging.level', 'INFO'),
    set: (value: string) => configStore.set('logging.level', value)
  })
  
  const language = computed({
    get: () => configStore.get('app.language', 'zh-CN'),
    set: (value: string) => configStore.set('app.language', value)
  })
  
  const timezone = computed({
    get: () => configStore.get('app.timezone', 'Asia/Shanghai'),
    set: (value: string) => configStore.set('app.timezone', value)
  })
  
  const logo = computed({
    get: () => configStore.get('app.logoUrl', ''),
    set: (value: string) => configStore.set('app.logoUrl', value)
  })
  
  // 加载状态
  const loading = computed(() => configStore.loading)
  
  // 计算属性
  const appTitle = computed(() => appName.value)
  
  // 更新应用名称
  const updateAppName = (newName: string) => {
    appName.value = newName
  }
  
  // 更新应用配置
  const updateAppConfig = (config: Partial<AppConfig>) => {
    if (config.appName !== undefined) {
      configStore.set('app.name', config.appName)
    }
    if (config.version !== undefined) {
      configStore.set('app.version', config.version)
    }
    if (config.showTitle !== undefined) {
      configStore.set('app.showTitle', config.showTitle)
    }
    if (config.logLevel !== undefined) {
      configStore.set('logging.level', config.logLevel)
    }
    if (config.language !== undefined) {
      configStore.set('app.language', config.language)
    }
    if (config.timezone !== undefined) {
      configStore.set('app.timezone', config.timezone)
    }
    if (config.logo !== undefined) {
      configStore.set('app.logoUrl', config.logo)
    }
  }
  
  // 从后端加载应用配置
  const loadAppConfig = async () => {
    await configStore.loadFromServer()
  }
  
  // 保存应用配置到后端
  const saveAppConfig = async () => {
    await configStore.saveToServer()
  }
  
  // 初始化应用配置
  const initializeApp = async () => {
    await configStore.initialize()
  }
  
  // 初始化配置管理器
  configStore.initialize()
  
  // 监听配置变化，自动更新页面标题
  watch(
    () => ({
      title: configStore.get('app.name', 'MCPS.ONE'),
      subtitle: configStore.get('app.subtitle', '')
    }),
    ({ title, subtitle }) => {
      if (subtitle && subtitle.trim()) {
        document.title = `${title} - ${subtitle}`
      } else {
        document.title = title
      }
    },
    { immediate: true, deep: true }
  )
  
  return {
    // 状态
    appName,
    version,
    showTitle,
    logLevel,
    language,
    timezone,
    logo,
    loading,
    
    // 计算属性
    appTitle,
    
    // 方法
    updateAppName,
    updateAppConfig,
    loadAppConfig,
    saveAppConfig,
    initializeApp,
    
    // 配置管理器实例（用于高级操作）
    configStore
  }
})