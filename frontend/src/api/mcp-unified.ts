/**
 * MCP统一服务API接口
 */
import { api } from './utils'

export interface ServiceStatus {
  mode: 'proxy_only' | 'server_only' | 'both' | 'disabled'
  is_running: boolean
  proxy_running: boolean
  server_running: boolean
  proxy_tools_count: number
  uptime: number
  last_error?: string
}

export interface ServiceMetrics {
  cpu_percent: number
  memory_usage: number
  active_connections: number
  total_requests: number
  error_count: number
  avg_response_time: number
}

export interface ToolInfo {
  name: string
  description?: string
  source: string
  schema?: any
}

export interface ServiceModeRequest {
  enable_server: boolean
  enable_proxy: boolean
}

export interface ToolCallRequest {
  tool_name: string
  arguments: Record<string, any>
  source?: string
}

export interface ToolCallResponse {
  success: boolean
  result?: any
  error?: string
  execution_time: number
}

/**
 * 获取服务状态
 */
export const getServiceStatus = (): Promise<ServiceStatus> => {
  return api.get('/mcp-unified/service/status')
}

/**
 * 启动服务
 */
export const startService = (): Promise<{ message: string }> => {
  return api.post('/mcp-unified/service/start')
}

/**
 * 停止服务
 */
export const stopService = (): Promise<{ message: string }> => {
  return api.post('/mcp-unified/service/stop')
}

/**
 * 切换服务模式
 */
export const switchServiceMode = (data: ServiceModeRequest): Promise<{ message: string }> => {
  return api.post('/mcp-unified/service/switch-mode', data)
}

/**
 * 重新加载配置
 */
export const reloadConfig = (): Promise<{ message: string }> => {
  return api.post('/mcp-unified/service/reload-config')
}

/**
 * 获取服务指标
 */
export const getServiceMetrics = (): Promise<ServiceMetrics> => {
  return api.get('/mcp-unified/service/metrics')
}

/**
 * 获取可用工具列表
 */
export const getAvailableTools = (): Promise<ToolInfo[]> => {
  return api.get('/mcp-unified/tools')
}

/**
 * 调用工具
 */
export const callTool = (data: ToolCallRequest): Promise<ToolCallResponse> => {
  return api.post('/mcp-unified/tools/call', data)
}

/**
 * 健康检查
 */
export const healthCheck = (): Promise<{ status: string; timestamp: string }> => {
  return api.get('/mcp-unified/health')
}

/**
 * 获取服务配置
 * TODO: 后端暂未实现此API
 */
// export const getServiceConfig = (): Promise<Record<string, any>> => {
//   return request({ method: 'GET', url: '/mcp-unified/config' })
// }

/**
 * 更新服务配置
 * TODO: 后端暂未实现此API
 */
// export const updateServiceConfig = (config: Record<string, any>): Promise<{ message: string }> => {
//   return request({ method: 'POST', url: '/mcp-unified/config', data: config })
// }

const mcpUnifiedApi = {
  getServiceStatus,
  startService,
  stopService,
  switchServiceMode,
  reloadConfig,
  getServiceMetrics,
  getAvailableTools,
  callTool,
  healthCheck
  // getServiceConfig,     // TODO: 后端暂未实现
  // updateServiceConfig  // TODO: 后端暂未实现
}

export { mcpUnifiedApi }
export default mcpUnifiedApi