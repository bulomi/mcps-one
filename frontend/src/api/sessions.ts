import api from './index'

// 会话状态枚举
export enum SessionStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  EXPIRED = 'expired',
  TERMINATED = 'terminated'
}

// 会话类型枚举
export enum SessionType {
  SINGLE_TOOL = 'single_tool',
  MULTI_TOOL = 'multi_tool',
  WORKFLOW = 'workflow',
  INTERACTIVE = 'interactive'
}

// 会话接口
export interface Session {
  id: string
  name: string
  description?: string
  type: SessionType
  status: SessionStatus
  tool_id?: string
  user_id?: string
  config: Record<string, any>
  metadata: Record<string, any>
  request_count: number
  response_count: number
  error_count: number
  created_at: string
  updated_at: string
  last_activity_at?: string
  expires_at?: string
}

// 会话创建请求
export interface SessionCreateRequest {
  name: string
  description?: string
  type: SessionType
  tool_id?: string
  config?: Record<string, any>
  metadata?: Record<string, any>
  expires_at?: string
}

// 会话更新请求
export interface SessionUpdateRequest {
  name?: string
  description?: string
  config?: Record<string, any>
  metadata?: Record<string, any>
  expires_at?: string
}

// 会话列表响应
export interface SessionListResponse {
  items: Session[]
  total: number
  page: number
  size: number
  pages: number
}

// 会话统计响应
export interface SessionStatsResponse {
  total_sessions: number
  active_sessions: number
  total_requests: number
  total_responses: number
  total_errors: number
  average_duration: number
}

// 会话活动请求
export interface SessionActivityRequest {
  request_count?: number
  response_count?: number
  error_count?: number
}

// 会话查询参数
export interface SessionQueryParams {
  page?: number
  size?: number
  status?: SessionStatus
  type?: SessionType
  tool_id?: string
  user_id?: string
  search?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

// 会话API
export const sessionsApi = {
  // 获取会话列表
  getSessions: (params?: SessionQueryParams): Promise<SessionListResponse> => {
    return api.get('/sessions', { params })
  },

  // 获取会话统计
  getSessionStats: (): Promise<SessionStatsResponse> => {
    return api.get('/sessions/stats')
  },

  // 获取最近会话
  getRecentSessions: (limit: number = 10): Promise<Session[]> => {
    return api.get('/sessions/recent', { params: { limit } })
  },

  // 获取会话详情
  getSession: (sessionId: string): Promise<Session> => {
    return api.get(`/sessions/${sessionId}`)
  },

  // 创建会话
  createSession: (data: SessionCreateRequest): Promise<Session> => {
    return api.post('/sessions', data)
  },

  // 更新会话
  updateSession: (sessionId: string, data: SessionUpdateRequest): Promise<Session> => {
    return api.put(`/sessions/${sessionId}`, data)
  },

  // 删除会话
  deleteSession: (sessionId: string): Promise<void> => {
    return api.delete(`/sessions/${sessionId}`)
  },

  // 激活会话
  activateSession: (sessionId: string): Promise<Session> => {
    return api.post(`/sessions/${sessionId}/activate`)
  },

  // 停用会话
  deactivateSession: (sessionId: string): Promise<Session> => {
    return api.post(`/sessions/${sessionId}/deactivate`)
  },

  // 终止会话
  terminateSession: (sessionId: string): Promise<Session> => {
    return api.post(`/sessions/${sessionId}/terminate`)
  },

  // 更新会话活动
  updateSessionActivity: (sessionId: string, data: SessionActivityRequest): Promise<Session> => {
    return api.post(`/sessions/${sessionId}/activity`, data)
  },

  // 清理过期会话
  cleanupExpiredSessions: (): Promise<{ cleaned_count: number }> => {
    return api.post('/sessions/cleanup')
  }
}