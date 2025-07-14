import api from './index'

// 工具数据类型
export interface Tool {
  id: number
  name: string
  description: string
  category: string
  status: 'active' | 'inactive' | 'error'
  config_path: string
  tags: string[]
  created_at: string
  updated_at: string
}

// 创建工具的请求数据类型
export interface CreateToolRequest {
  name: string
  description: string
  category: string
  config_path: string
  tags: string[]
}

// 更新工具的请求数据类型
export interface UpdateToolRequest {
  name?: string
  description?: string
  category?: string
  config_path?: string
  tags?: string[]
}

// 工具API接口
export const toolsApi = {
  // 获取工具列表
  getTools: async (): Promise<Tool[]> => {
    return await api.get('/tools')
  },

  // 根据ID获取工具详情
  getTool: async (id: number): Promise<Tool> => {
    return await api.get(`/tools/${id}`)
  },

  // 创建工具
  createTool: async (data: CreateToolRequest): Promise<Tool> => {
    return await api.post('/tools', data)
  },

  // 更新工具
  updateTool: async (id: number, data: UpdateToolRequest): Promise<Tool> => {
    return await api.put(`/tools/${id}`, data)
  },

  // 删除工具
  deleteTool: async (id: number): Promise<void> => {
    return await api.delete(`/tools/${id}`)
  },

  // 启动工具
  startTool: async (id: number): Promise<void> => {
    return await api.post(`/tools/${id}/start`)
  },

  // 停止工具
  stopTool: async (id: number): Promise<void> => {
    return await api.post(`/tools/${id}/stop`)
  },

  // 重启工具
  restartTool: async (id: number): Promise<void> => {
    return await api.post(`/tools/${id}/restart`)
  },

  // 获取工具状态
  getToolStatus: async (id: number): Promise<{ status: string; message?: string }> => {
    return await api.get(`/tools/${id}/status`)
  },

  // 验证工具配置
  validateToolConfig: async (configPath: string): Promise<{ valid: boolean; errors?: string[] }> => {
    return await api.post('/tools/validate-config', { config_path: configPath })
  },

  // 获取工具分类列表
  getCategories: async (): Promise<string[]> => {
    return await api.get('/tools/categories')
  },

  // 导出工具配置
  exportTools: async (toolIds?: number[]): Promise<Blob> => {
    const params = toolIds ? { tool_ids: toolIds } : {}
    return await api.get('/tools/export', { 
      params,
      responseType: 'blob'
    })
  },

  // 导入工具配置
  importTools: async (file: File): Promise<{ success: number; failed: number; errors?: string[] }> => {
    const formData = new FormData()
    formData.append('file', file)
    return await api.post('/tools/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  }
}

export default toolsApi