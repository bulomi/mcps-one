/**
 * API模块统一导出
 * 提供类型安全的API调用接口和统一的错误处理
 */

// 导出核心工具和类型
export * from './utils';
export * from './constants';

// 导出各个API模块
export { authApi } from './auth';
export { toolsApi } from './tools';
export { systemApi } from './system';
// 会话管理功能已移除
export { mcpApi } from './mcp';
export { mcpAgentApi } from './mcp-agent';
export { mcpUnifiedApi } from './mcp-unified';

// 导出类型定义
export type { LoginRequest, LoginResponse, User } from './auth';
export type { Tool, CreateToolRequest, ToolStatus, ToolStats } from './tools';
export type { SystemStats, LogEntry, ConfigItem, SystemSettings } from './system';
// 会话管理功能已移除

// 兼容性导出（保持向后兼容）
import { api } from './utils';
export default api;

// 创建统一的API客户端实例
export const apiClient = {
  // 认证相关
  auth: {
    login: authApi.login,
    logout: authApi.logout,
    refreshToken: authApi.refreshToken,
    getCurrentUser: authApi.getCurrentUser,
    changePassword: authApi.changePassword,
  },
  
  // 工具管理
  tools: {
    getTools: toolsApi.getTools,
    getTool: toolsApi.getTool,
    createTool: toolsApi.createTool,
    updateTool: toolsApi.updateTool,
    deleteTool: toolsApi.deleteTool,
    startTool: toolsApi.startTool,
    stopTool: toolsApi.stopTool,
    restartTool: toolsApi.restartTool,
    getToolStatus: toolsApi.getToolStatus,
    validateToolConfig: toolsApi.validateToolConfig,
    getToolCategories: toolsApi.getToolCategories,
    getToolTags: toolsApi.getToolTags,
    searchTools: toolsApi.searchTools,
    getToolStats: toolsApi.getToolStats,
    getToolLogs: toolsApi.getToolLogs,
    clearToolLogs: toolsApi.clearToolLogs,
  
  },
  
  // 系统管理
  system: {
    getStats: systemApi.getStats,
    getLogs: systemApi.getLogs,
    getConfigs: systemApi.getConfigs,
    updateConfig: systemApi.updateConfig,
    saveSettings: systemApi.saveSettings,
    getAllSettings: systemApi.getAllSettings,
    exportConfig: systemApi.exportConfig,
    importConfig: systemApi.importConfig,
    resetConfig: systemApi.resetConfig,
    getHealthStatus: systemApi.getHealthStatus,
  },
};

// 导入各个API模块用于apiClient
import { authApi } from './auth';
import { toolsApi } from './tools';
import { systemApi } from './system';