/**
 * MCP代理服务相关API接口
 */
import { api } from './utils'

/**
 * 调用MCP工具
 * @param {string} toolName - 工具名称
 * @param {Object} data - 调用参数
 * @param {string} data.tool_name - 工具方法名
 * @param {Object} data.arguments - 方法参数
 * @returns {Promise}
 */
export const callTool = (toolName, data) => {
  return api.post(`/mcp-agent/tools/${toolName}/call`, data)
}

/**
 * 获取工具能力
 * @param {string} toolName - 工具名称
 * @returns {Promise}
 */
export const getToolCapabilities = (toolName) => {
  return api.get(`/mcp-agent/tools/${toolName}/capabilities`)
}

/**
 * 获取工具列表
 * @returns {Promise}
 */
export const getTools = () => {
  return api.get('/mcp-agent/tools')
}

/**
 * 获取工具资源列表
 * @param {string} toolName - 工具名称
 * @returns {Promise}
 */
export const getToolResources = (toolName) => {
  return api.get(`/mcp-agent/tools/${toolName}/resources`)
}

/**
 * 读取工具资源
 * @param {string} toolName - 工具名称
 * @param {Object} data - 读取参数
 * @param {string} data.uri - 资源URI
 * @returns {Promise}
 */
export const readToolResource = (toolName, data) => {
  return api.post(`/mcp-agent/tools/${toolName}/resources/read`, data)
}

/**
 * 获取工具提示列表
 * @param {string} toolName - 工具名称
 * @returns {Promise}
 */
export const getToolPrompts = (toolName) => {
  return api.get(`/mcp-agent/tools/${toolName}/prompts`)
}

/**
 * 获取工具提示
 * @param {string} toolName - 工具名称
 * @param {Object} data - 提示参数
 * @param {string} data.name - 提示名称
 * @param {Object} data.arguments - 提示参数
 * @returns {Promise}
 */
export const getToolPrompt = (toolName, data) => {
  return api.post(`/mcp-agent/tools/${toolName}/prompts/get`, data)
}

/**
 * 创建代理会话
 * @param {Object} data - 会话创建参数
 * @param {string} data.name - 会话名称
 * @param {string} data.description - 会话描述
 * @param {Object} data.config - 会话配置
 * @returns {Promise}
 */
export const createSession = (data) => {
  return api.post('/mcp-agent/sessions', data)
}

/**
 * 执行代理任务
 * @param {string} sessionId - 会话ID
 * @param {Object} data - 任务执行参数
 * @param {string} data.message - 任务消息
 * @param {Object} data.context - 任务上下文
 * @returns {Promise}
 */
export const executeTask = (sessionId, data) => {
  return api.post(`/mcp-agent/sessions/${sessionId}/execute`, data)
}

/**
 * 获取任务状态
 * @param {string} taskId - 任务ID
 * @returns {Promise}
 */
export const getTaskStatus = (taskId) => {
  return api.get(`/mcp-agent/tasks/${taskId}/status/`)
}

/**
 * 健康检查
 * @returns {Promise}
 */
export const healthCheck = () => {
  return api.get('/mcp-agent/health/')
}

/**
 * 获取工具连接状态
 * @param {string} toolName - 工具名称
 * @returns {Promise}
 */
export const getToolStatus = (toolName) => {
  return api.get(`/mcp-agent/tools/${toolName}/status/`)
}

/**
 * 重连工具
 * @param {string} toolName - 工具名称
 * @returns {Promise}
 */
export const reconnectTool = (toolName) => {
  return api.post(`/mcp-agent/tools/${toolName}/reconnect/`)
}

/**
 * 断开工具连接
 * @param {string} toolName - 工具名称
 * @returns {Promise}
 */
export const disconnectTool = (toolName) => {
  return api.post(`/mcp-agent/tools/${toolName}/disconnect/`)
}

/**
 * 获取MCP连接状态
 * @returns {Promise}
 */
export const getConnectionStatus = () => {
  return api.get('/mcp-unified/service/status/')
}



const mcpAgentApi = {
  callTool,
  getToolCapabilities,
  getTools,
  getToolResources,
  readToolResource,
  getToolPrompts,
  getToolPrompt,
  createSession,
  executeTask,
  getTaskStatus,
  healthCheck,
  getConnectionStatus,
  reconnectTool,
  disconnectTool
}

export { mcpAgentApi }
export default mcpAgentApi