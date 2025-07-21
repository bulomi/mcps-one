import api from './index'

// 任务状态枚举
export enum TaskStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
  TIMEOUT = 'timeout'
}

// 任务类型枚举
export enum TaskType {
  SINGLE_TOOL = 'single_tool',
  MULTI_TOOL = 'multi_tool',
  WORKFLOW = 'workflow',
  SCHEDULED = 'scheduled',
  BATCH = 'batch'
}

// 任务优先级枚举
export enum TaskPriority {
  LOW = 'low',
  NORMAL = 'normal',
  HIGH = 'high',
  URGENT = 'urgent'
}

// 任务接口
export interface Task {
  id: string
  name: string
  description?: string
  type: TaskType
  priority: TaskPriority
  status: TaskStatus
  session_id?: string
  tool_id?: string
  user_id?: string
  parent_task_id?: string
  input_data: Record<string, any>
  output_data?: Record<string, any>
  config: Record<string, any>
  metadata: Record<string, any>
  progress: number
  error_message?: string
  retry_count: number
  max_retries: number
  created_at: string
  updated_at: string
  started_at?: string
  completed_at?: string
  scheduled_at?: string
  timeout_at?: string
  execution_time?: number
  cpu_usage?: number
  memory_usage?: number
}

// 任务创建请求
export interface TaskCreateRequest {
  name: string
  description?: string
  type: TaskType
  priority?: TaskPriority
  session_id?: string
  tool_id?: string
  parent_task_id?: string
  input_data: Record<string, any>
  config?: Record<string, any>
  metadata?: Record<string, any>
  max_retries?: number
  scheduled_at?: string
  timeout_at?: string
}

// 任务更新请求
export interface TaskUpdateRequest {
  name?: string
  description?: string
  priority?: TaskPriority
  input_data?: Record<string, any>
  config?: Record<string, any>
  metadata?: Record<string, any>
  max_retries?: number
  scheduled_at?: string
  timeout_at?: string
}

// 任务列表响应
export interface TaskListResponse {
  items: Task[]
  total: number
  page: number
  size: number
  pages: number
}

// 任务统计响应
export interface TaskStatsResponse {
  total_tasks: number
  status_counts: Record<TaskStatus, number>
  type_counts: Record<TaskType, number>
  priority_counts: Record<TaskPriority, number>
  average_execution_time: number
  success_rate: number
}

// 任务执行请求
export interface TaskExecutionRequest {
  input_data?: Record<string, any>
  config?: Record<string, any>
}

// 任务进度更新
export interface TaskProgressUpdate {
  progress: number
  status?: TaskStatus
  output_data?: Record<string, any>
  error_message?: string
}

// 任务批量操作
export interface TaskBatchOperation {
  task_ids: string[]
  operation: 'start' | 'cancel' | 'retry' | 'delete'
}

// 任务查询参数
export interface TaskQueryParams {
  page?: number
  size?: number
  status?: TaskStatus
  type?: TaskType
  priority?: TaskPriority
  session_id?: string
  tool_id?: string
  user_id?: string
  parent_task_id?: string
  search?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
  created_after?: string
  created_before?: string
}

// 任务API
export const tasksApi = {
  // 获取任务列表
  getTasks: (params?: TaskQueryParams): Promise<TaskListResponse> => {
    return api.get('/tasks/', { params })
  },

  // 获取任务统计
  getTaskStats: (): Promise<TaskStatsResponse> => {
    return api.get('/tasks/stats/')
  },

  // 获取最近任务
  getRecentTasks: (limit: number = 10): Promise<Task[]> => {
    return api.get('/tasks/recent/', { params: { limit } })
  },

  // 获取会话相关任务
  getSessionTasks: (sessionId: string, params?: TaskQueryParams): Promise<TaskListResponse> => {
    return api.get(`/tasks/session/${sessionId}/`, { params })
  },

  // 获取工具相关任务
  getToolTasks: (toolId: string, params?: TaskQueryParams): Promise<TaskListResponse> => {
    return api.get(`/tasks/tool/${toolId}/`, { params })
  },

  // 获取任务详情
  getTask: (taskId: string): Promise<Task> => {
    return api.get(`/tasks/${taskId}/`)
  },

  // 创建任务
  createTask: (data: TaskCreateRequest): Promise<Task> => {
    return api.post('/tasks/', data)
  },

  // 更新任务
  updateTask: (taskId: string, data: TaskUpdateRequest): Promise<Task> => {
    return api.put(`/tasks/${taskId}/`, data)
  },

  // 删除任务
  deleteTask: (taskId: string): Promise<void> => {
    return api.delete(`/tasks/${taskId}/`)
  },

  // 启动任务
  startTask: (taskId: string, data?: TaskExecutionRequest): Promise<Task> => {
    return api.post(`/tasks/${taskId}/start/`, data)
  },

  // 完成任务
  completeTask: (taskId: string, outputData?: Record<string, any>): Promise<Task> => {
    return api.post(`/tasks/${taskId}/complete/`, { output_data: outputData })
  },

  // 任务失败
  failTask: (taskId: string, errorMessage: string): Promise<Task> => {
    return api.post(`/tasks/${taskId}/fail/`, { error_message: errorMessage })
  },

  // 取消任务
  cancelTask: (taskId: string): Promise<Task> => {
    return api.post(`/tasks/${taskId}/cancel/`)
  },

  // 重试任务
  retryTask: (taskId: string): Promise<Task> => {
    return api.post(`/tasks/${taskId}/retry/`)
  },

  // 更新任务进度
  updateTaskProgress: (taskId: string, data: TaskProgressUpdate): Promise<Task> => {
    return api.post(`/tasks/${taskId}/progress/`, data)
  },

  // 批量操作任务
  batchOperateTasks: (data: TaskBatchOperation): Promise<{ success_count: number; error_count: number; errors: string[] }> => {
    return api.post('/tasks/batch/', data)
  },

  // 清理旧任务
  cleanupOldTasks: (days: number = 30): Promise<{ cleaned_count: number }> => {
    return api.post('/tasks/cleanup/', { days })
  }
}