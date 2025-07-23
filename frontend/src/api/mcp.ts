import api from './index'

// MCP工具调用请求
export interface ToolCallRequest {
  tool_name: string
  arguments: Record<string, any>
}

// MCP工具调用响应
export interface ToolCallResponse {
  tool_name: string
  arguments: Record<string, any>
  result: any
  success: boolean
}

// 工具能力信息
export interface ToolCapabilities {
  tools?: Array<{
    name: string
    description: string
    inputSchema: any
  }>
  resources?: Array<{
    uri: string
    name: string
    description?: string
    mimeType?: string
  }>
  prompts?: Array<{
    name: string
    description: string
    arguments?: any
  }>
}

// 资源读取请求
export interface ResourceReadRequest {
  uri: string
}

// 提示获取请求
export interface PromptGetRequest {
  name: string
  arguments?: Record<string, any>
}



// MCP代理服务API
export const mcpApi = {
  // 工具调用相关
  async callTool(toolName: string, request: ToolCallRequest): Promise<ToolCallResponse> {
    const response = await api.post(`/mcp-agent/tools/${toolName}/call`, request)
    return response
  },

  async getToolCapabilities(toolName: string): Promise<ToolCapabilities> {
    const response = await api.get(`/mcp-agent/tools/${toolName}/capabilities`)
    return response
  },

  async listTools(): Promise<{
    tools: Array<{
      id: number
      name: string
      description: string
      is_enabled: boolean
      is_connected: boolean
      capabilities?: ToolCapabilities
    }>
    total: number
  }> {
    const response = await api.get('/mcp-agent/tools')
    return response
  },

  // 资源管理相关
  async listResources(toolName: string): Promise<{
    tool_name: string
    resources: any[]
  }> {
    const response = await api.get(`/mcp-agent/tools/${toolName}/resources`)
    return response
  },

async readResource(toolName: string, request: ResourceReadRequest): Promise<{
    tool_name: string
    uri: string
    data: any
  }> {
    const response = await api.post(`/mcp-agent/tools/${toolName}/resources/read`, request)
    return response
  },

  // 提示管理相关
  async listPrompts(toolName: string): Promise<{
    tool_name: string
    prompts: any[]
  }> {
    const response = await api.get(`/mcp-agent/tools/${toolName}/prompts`)
    return response
  },

  async getPrompt(toolName: string, request: PromptGetRequest): Promise<{
    tool_name: string
    name: string
    data: any
  }> {
    const response = await api.post(`/mcp-agent/tools/${toolName}/prompts/get`, request)
    return response
  },



  // 健康检查
  async healthCheck(): Promise<{
    status: string
    timestamp: string
  }> {
    const response = await api.get('/mcp-agent/health/')
    return response
  },

  // 工具状态管理
  async getToolStatus(toolName: string): Promise<{
    tool_name: string
    status: string
    is_connected: boolean
    process_id?: number
    last_check: string
  }> {
    const response = await api.get(`/mcp-agent/tools/${toolName}/status`)
    return response
  },

  async reconnectTool(toolName: string): Promise<{
    tool_name: string
    status: string
    message: string
  }> {
    const response = await api.post(`/mcp-agent/tools/${toolName}/reconnect/`)
    return response
  },

  async disconnectTool(toolName: string): Promise<{
    tool_name: string
    status: string
    message: string
  }> {
    const response = await api.post(`/mcp-agent/tools/${toolName}/disconnect/`)
    return response
  },


}

export default mcpApi