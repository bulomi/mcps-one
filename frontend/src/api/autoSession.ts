/**
 * 自动会话管理API接口
 */

import api from './index'

// 类型定义
export interface AutoSessionRequest {
  message: string
  task_type?: string
  context?: Record<string, any>
  parallel?: boolean
  max_iterations?: number
  timeout?: number
}

export interface AutoSessionConfigUpdate {
  idle_timeout?: number
  hibernation_timeout?: number
  max_session_lifetime?: number
  max_concurrent_sessions?: number
  session_pool_size?: number
  enable_auto_tool_selection?: boolean
  tool_selection_strategy?: string
  cleanup_interval?: number
}

export interface SessionActionRequest {
  action: 'wake_up' | 'hibernate' | 'destroy'
  force?: boolean
}

export interface AutoSessionInfo {
  session_id: string
  state: string
  created_at: string
  last_activity: string
  expires_at?: string
  tools: string[]
  task_count: number
  config: Record<string, any>
}

export interface AutoSessionStats {
  total_sessions: number
  active_sessions: number
  idle_sessions: number
  hibernating_sessions: number
  pool_size: number
  max_concurrent: number
  config: {
    idle_timeout: number
    hibernation_timeout: number
    max_session_lifetime: number
    session_pool_size: number
    auto_tool_selection: boolean
    tool_selection_strategy: string
  }
}

export interface AutoSessionConfig {
  idle_timeout: number
  hibernation_timeout: number
  max_session_lifetime: number
  max_concurrent_sessions: number
  session_pool_size: number
  enable_auto_tool_selection: boolean
  tool_selection_strategy: string
  cleanup_interval: number
}

// API接口
export const autoSessionApi = {
  /**
   * 自动执行任务
   */
  async autoExecuteTask(data: AutoSessionRequest) {
    return api.post('/auto-session/execute/', data)
  },

  /**
   * 获取所有自动会话
   */
  async getAutoSessions() {
    return api.get('/auto-session/sessions/')
  },

  /**
   * 获取会话详情
   */
  async getAutoSessionInfo(sessionId: string) {
    return api.get(`/auto-session/sessions/${sessionId}/`)
  },

  /**
   * 会话操作（唤醒、休眠、销毁）
   */
  async sessionAction(sessionId: string, data: SessionActionRequest) {
    return api.post(`/auto-session/sessions/${sessionId}/action/`, data)
  },

  /**
   * 获取自动会话统计
   */
  async getAutoSessionStats() {
    return api.get('/auto-session/stats/')
  },

  /**
   * 更新自动会话配置
   */
  async updateAutoSessionConfig(data: AutoSessionConfigUpdate) {
    return api.put('/auto-session/config/', data)
  },

  /**
   * 获取自动会话配置
   */
  async getAutoSessionConfig() {
    return api.get('/auto-session/config/')
  },

  /**
   * 手动清理会话
   */
  async manualCleanupSessions(force: boolean = false) {
    return api.post('/auto-session/cleanup/', null, {
      params: { force }
    })
  },

  /**
   * 补充会话池
   */
  async refillSessionPool() {
    return api.post('/auto-session/pool/refill/')
  },

  /**
   * 自动会话管理健康检查
   */
  async autoSessionHealthCheck() {
    return api.get('/auto-session/health/')
  }
}

export default autoSessionApi