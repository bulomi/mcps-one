/**
 * API路径常量定义
 * 统一管理所有API路径，避免硬编码
 */

// 基础路径
export const BASE_PATHS = {
  AUTH: '/auth',
  TOOLS: '/tools',
  MCP_AGENT: '/mcp-agent',
  MCP_UNIFIED: '/mcp-unified',
  SYSTEM: '/system'
  // SESSIONS: '/sessions' // 会话管理功能已移除
} as const

// 认证相关API路径
export const AUTH_PATHS = {
  LOGIN: `${BASE_PATHS.AUTH}/login/`,
  LOGOUT: `${BASE_PATHS.AUTH}/logout/`,
  REFRESH: `${BASE_PATHS.AUTH}/refresh/`,
  ME: `${BASE_PATHS.AUTH}/me/`,
  CHANGE_PASSWORD: `${BASE_PATHS.AUTH}/change-password/`
} as const

// 工具管理API路径
export const TOOLS_PATHS = {
  LIST: `${BASE_PATHS.TOOLS}/`,
  DETAIL: (id: number) => `${BASE_PATHS.TOOLS}/${id}/`,
  CREATE: `${BASE_PATHS.TOOLS}/`,
  UPDATE: (id: number) => `${BASE_PATHS.TOOLS}/${id}/`,
  DELETE: (id: number) => `${BASE_PATHS.TOOLS}/${id}/`,
  START: (id: number) => `${BASE_PATHS.TOOLS}/${id}/start/`,
  STOP: (id: number) => `${BASE_PATHS.TOOLS}/${id}/stop/`,
  RESTART: (id: number) => `${BASE_PATHS.TOOLS}/${id}/restart/`,
  STATUS: (id: number) => `${BASE_PATHS.TOOLS}/${id}/status/`,
  LOGS: (id: number) => `${BASE_PATHS.TOOLS}/${id}/logs/`,

  VALIDATE_CONFIG: `${BASE_PATHS.TOOLS}/validate-config/`,
  CATEGORIES: `${BASE_PATHS.TOOLS}/categories/`,
  TAGS: `${BASE_PATHS.TOOLS}/tags/`,
  SEARCH: `${BASE_PATHS.TOOLS}/search/`,
  STATS: `${BASE_PATHS.TOOLS}/stats/`
} as const

// MCP代理API路径
export const MCP_AGENT_PATHS = {
  TOOLS: `${BASE_PATHS.MCP_AGENT}/tools/`,
  TOOL_CALL: (toolName: string) => `${BASE_PATHS.MCP_AGENT}/tools/${toolName}/call/`,
  TOOL_CAPABILITIES: (toolName: string) => `${BASE_PATHS.MCP_AGENT}/tools/${toolName}/capabilities/`,
  TOOL_RESOURCES: (toolName: string) => `${BASE_PATHS.MCP_AGENT}/tools/${toolName}/resources/`,
  TOOL_RESOURCE_READ: (toolName: string) => `${BASE_PATHS.MCP_AGENT}/tools/${toolName}/resources/read/`,
  TOOL_PROMPTS: (toolName: string) => `${BASE_PATHS.MCP_AGENT}/tools/${toolName}/prompts/`,
  TOOL_PROMPT_GET: (toolName: string) => `${BASE_PATHS.MCP_AGENT}/tools/${toolName}/prompts/get/`,
  TOOL_STATUS: (toolName: string) => `${BASE_PATHS.MCP_AGENT}/tools/${toolName}/status/`,
  // SESSIONS: `${BASE_PATHS.MCP_AGENT}/sessions/`, // 会话管理功能已移除
  // SESSION_EXECUTE: (sessionId: string) => `${BASE_PATHS.MCP_AGENT}/sessions/${sessionId}/execute/` // 会话管理功能已移除
} as const

// MCP统一服务API路径
export const MCP_UNIFIED_PATHS = {
  SERVICE_STATUS: `${BASE_PATHS.MCP_UNIFIED}/service/status/`,
  SERVICE_START: `${BASE_PATHS.MCP_UNIFIED}/service/start/`,
  SERVICE_STOP: `${BASE_PATHS.MCP_UNIFIED}/service/stop/`,
  SERVICE_SWITCH_MODE: `${BASE_PATHS.MCP_UNIFIED}/service/switch-mode/`,
  SERVICE_RELOAD_CONFIG: `${BASE_PATHS.MCP_UNIFIED}/service/reload-config/`,
  SERVICE_METRICS: `${BASE_PATHS.MCP_UNIFIED}/service/metrics/`,
  TOOLS: `${BASE_PATHS.MCP_UNIFIED}/tools/`,
  TOOL_CALL: `${BASE_PATHS.MCP_UNIFIED}/tools/call/`,
  HEALTH: `${BASE_PATHS.MCP_UNIFIED}/health/`
} as const

// 系统管理API路径
export const SYSTEM_PATHS = {
  STATS: `${BASE_PATHS.SYSTEM}/stats/`,
  LOGS: `${BASE_PATHS.SYSTEM}/logs/`,
  CONFIG: `${BASE_PATHS.SYSTEM}/config/`,
  CONFIG_UPDATE: (key: string) => `${BASE_PATHS.SYSTEM}/config/${key}/`,
  SETTINGS: `${BASE_PATHS.SYSTEM}/settings/`,
  CONFIG_EXPORT: `${BASE_PATHS.SYSTEM}/config/export/`,
  CONFIG_IMPORT: `${BASE_PATHS.SYSTEM}/config/import/`,
  CONFIG_RESET: `${BASE_PATHS.SYSTEM}/config/reset/`
} as const

// 会话管理API路径
// 会话管理功能已移除
// export const SESSIONS_PATHS = {
//   LIST: `${BASE_PATHS.SESSIONS}/`,
//   DETAIL: (sessionId: string) => `${BASE_PATHS.SESSIONS}/${sessionId}/`,
//   CREATE: `${BASE_PATHS.SESSIONS}/`,
//   UPDATE: (sessionId: string) => `${BASE_PATHS.SESSIONS}/${sessionId}/`,
//   DELETE: (sessionId: string) => `${BASE_PATHS.SESSIONS}/${sessionId}/`,
//   ACTIVATE: (sessionId: string) => `${BASE_PATHS.SESSIONS}/${sessionId}/activate/`,
//   DEACTIVATE: (sessionId: string) => `${BASE_PATHS.SESSIONS}/${sessionId}/deactivate/`,
//   TERMINATE: (sessionId: string) => `${BASE_PATHS.SESSIONS}/${sessionId}/terminate/`,
//   ACTIVITY: (sessionId: string) => `${BASE_PATHS.SESSIONS}/${sessionId}/activity/`,
//   STATS: `${BASE_PATHS.SESSIONS}/stats/`,
//   RECENT: `${BASE_PATHS.SESSIONS}/recent/`,
//   CLEANUP: `${BASE_PATHS.SESSIONS}/cleanup/`
// } as const

// 路径验证函数
export const validateApiPath = (path: string): string => {
  let normalizedPath = path;
  
  // 处理双斜杠
  normalizedPath = normalizedPath.replace(/\/+/g, '/');
  
  // 确保路径不以斜杠结尾（除了根路径）
  if (normalizedPath !== '/' && normalizedPath.endsWith('/')) {
    console.warn(`API路径不应以斜杠结尾: ${normalizedPath}`);
    normalizedPath = normalizedPath.slice(0, -1);
  }
  
  return normalizedPath;
};

// 路径构建辅助函数
export const buildApiPath = (...segments: string[]): string => {
  const path = segments
    .filter(segment => segment && segment.trim() !== '')
    .map(segment => segment.replace(/^\/+|\/+$/g, ''))
    .join('/');
  
  return validateApiPath(`/${path}`);
};