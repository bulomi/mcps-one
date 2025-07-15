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

// 代理会话创建请求
export interface AgentSessionCreate {
  name: string
  description?: string
  config: {
    mode: 'single_tool' | 'multi_tool' | 'auto'
    tools: string[]
    max_iterations?: number
    timeout?: number
  }
}

// 代理任务执行请求
export interface AgentExecuteRequest {
  message: string
  context?: Record<string, any>
  tools?: string[]
}

// 任务结果
export interface TaskResult {
  task_id: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  result?: any
  error?: string
  steps: Array<{
    step_id: string
    tool_name: string
    action: string
    input: any
    output?: any
    error?: string
    timestamp: string
  }>
  created_at: string
  updated_at: string
}

// MCP代理服务API
export const mcpApi = {
  // 工具调用相关
  async callTool(toolName: string, request: ToolCallRequest): Promise<ToolCallResponse> {
    const response = await api.post(`/mcp-agent/tools/${toolName}/call`, request)
    return response.data.data
  },

  async getToolCapabilities(toolName: string): Promise<ToolCapabilities> {
    const response = await api.get(`/mcp-agent/tools/${toolName}/capabilities`)
    return response.data.data
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
    return response.data.data
  },

  // 资源管理相关
  async listResources(toolName: string): Promise<{
    tool_name: string
    resources: any[]
  }> {
    const response = await api.get(`/mcp-agent/tools/${toolName}/resources`)
    return response.data.data
  },

  async readResource(toolName: string, request: ResourceReadRequest): Promise<{
    tool_name: string
    uri: string
    data: any
  }> {
    const response = await api.post(`/mcp-agent/tools/${toolName}/resources/read`, request)
    return response.data.data
  },

  // 提示管理相关
  async listPrompts(toolName: string): Promise<{
    tool_name: string
    prompts: any[]
  }> {
    const response = await api.get(`/mcp-agent/tools/${toolName}/prompts`)
    return response.data.data
  },

  async getPrompt(toolName: string, request: PromptGetRequest): Promise<{
    tool_name: string
    name: string
    data: any
  }> {
    const response = await api.post(`/mcp-agent/tools/${toolName}/prompts/get`, request)
    return response.data.data
  },

  // 代理会话管理
  async createSession(request: AgentSessionCreate): Promise<{
    session_id: string
    name: string
    description?: string
    config: any
    status: string
    created_at: string
  }> {
    const response = await api.post('/mcp-agent/sessions', request)
    return response.data.data
  },

  async executeTask(sessionId: string, request: AgentExecuteRequest): Promise<{
    task_id: string
    session_id: string
    status: string
    message: string
  }> {
    const response = await api.post(`/mcp-agent/sessions/${sessionId}/execute`, request)
    return response.data.data
  },

  async getTaskStatus(taskId: string): Promise<TaskResult> {
    const response = await api.get(`/mcp-agent/tasks/${taskId}/status`)
    return response.data.data
  },

  // 健康检查
  async healthCheck(): Promise<{
    status: string
    timestamp: string
  }> {
    const response = await api.get('/mcp-agent/health')
    return response.data.data
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
    return response.data.data
  },

  async reconnectTool(toolName: string): Promise<{
    tool_name: string
    status: string
    message: string
  }> {
    const response = await api.post(`/mcp-agent/tools/${toolName}/reconnect`)
    return response.data.data
  },

  async disconnectTool(toolName: string): Promise<{
    tool_name: string
    status: string
    message: string
  }> {
    const response = await api.post(`/mcp-agent/tools/${toolName}/disconnect`)
    return response.data.data
  }
}

export default mcpApi