import { api, withRetry, withCache, handleApiError, clearCache } from './utils';
import type { ApiResponse, PaginatedResponse } from './utils';
import { TOOLS_PATHS } from './constants';

export interface Tool {
  id: number;
  name: string;
  display_name?: string;
  description: string;
  type?: 'builtin' | 'custom' | 'external' | 'mcp';
  category: string;
  tags: string[];
  command?: string;
  working_directory?: string;
  environment_variables?: Record<string, string>;
  connection_type?: 'stdio' | 'http' | 'websocket';
  host?: string;
  port?: number;
  path?: string;
  auto_start?: boolean;
  restart_on_failure?: boolean;
  max_restart_attempts?: number;
  timeout?: number;
  version?: string;
  author?: string;
  homepage?: string;
  enabled?: boolean;
  config?: Record<string, any>;
  status: 'active' | 'inactive' | 'error';
  createdAt: string;
  updatedAt: string;
  documentation?: string;
}

export interface CreateToolRequest {
  // ToolBase fields
  name: string;
  display_name: string;
  description?: string;
  type?: 'builtin' | 'custom' | 'external';
  category?: string;
  tags?: string[];
  
  // ToolConfigBase fields
  command: string;
  working_directory?: string;
  environment_variables?: Record<string, string>;
  connection_type?: 'stdio' | 'http' | 'websocket';
  host?: string;
  port?: number;
  path?: string;
  auto_start?: boolean;
  restart_on_failure?: boolean;
  max_restart_attempts?: number;
  timeout?: number;
  
  // ToolMetadata fields
  version?: string;
  author?: string;
  homepage?: string;
  
  // ToolCreate specific
  enabled?: boolean;
}

export interface UpdateToolRequest extends Partial<CreateToolRequest> {
  id: number;
}

export interface ToolStatus {
  id: number;
  status: 'running' | 'stopped' | 'error' | 'starting' | 'stopping';
  lastStarted?: string;
  lastStopped?: string;
  errorMessage?: string;
  uptime?: number;
  memoryUsage?: number;
  cpuUsage?: number;
}

export interface ToolStats {
  total: number;
  active: number;
  inactive: number;
  error: number;
  categories: Record<string, number>;
  recentActivity: Array<{
    toolId: number;
    action: string;
    timestamp: string;
  }>;
}

export interface ToolLog {
  id: number;
  toolId: number;
  level: 'info' | 'warn' | 'error' | 'debug';
  message: string;
  timestamp: string;
  metadata?: Record<string, any>;
}



export interface SearchFilters {
  category?: string;
  tags?: string[];
  status?: string;
  author?: string;
}

export const toolsApi = {
  /**
   * 获取工具列表
   */
  getTools: async (page?: number, pageSize?: number): Promise<PaginatedResponse<Tool>> => {
    try {
      const params = page && pageSize ? `?page=${page}&pageSize=${pageSize}` : '';
      return await withCache(
        `tools-list-${params}`,
        () => api.get<Tool[]>(`${TOOLS_PATHS.LIST}${params}`),
        2 * 60 * 1000 // 2分钟缓存
      );
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },
  
  /**
   * 获取单个工具详情
   */
  getTool: async (id: number): Promise<ApiResponse<Tool>> => {
    try {
      return await withCache(
        `tool-${id}`,
        () => api.get<Tool>(TOOLS_PATHS.DETAIL(id)),
        5 * 60 * 1000 // 5分钟缓存
      );
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },
  
  /**
   * 创建新工具
   */
  createTool: async (data: CreateToolRequest): Promise<ApiResponse<Tool>> => {
    try {
      const result = await api.post<Tool>(TOOLS_PATHS.CREATE, data);
      // 清除相关缓存
      clearCache('tools-list');
      clearCache('tool-categories');
      clearCache('tool-tags');
      return result;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },
  
  /**
   * 更新工具
   */
  updateTool: async (id: number, data: Partial<CreateToolRequest>): Promise<ApiResponse<Tool>> => {
    try {
      const result = await api.put<Tool>(TOOLS_PATHS.UPDATE(id), data);
      // 清除相关缓存
      clearCache(`tool-${id}`);
      clearCache('tools-list');
      return result;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },
  
  /**
   * 删除工具
   */
  deleteTool: async (id: number, force: boolean = false): Promise<ApiResponse<void>> => {
    try {
      const url = force ? `${TOOLS_PATHS.DELETE(id)}?force=true` : TOOLS_PATHS.DELETE(id);
      const result = await api.delete<void>(url);
      // 清除相关缓存
      clearCache(`tool-${id}`);
      clearCache('tools-list');
      return result;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },
  
  /**
   * 启动工具
   */
  startTool: async (id: number): Promise<ApiResponse<void>> => {
    try {
      return await withRetry(() => api.post<void>(TOOLS_PATHS.START(id)));
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },
  
  /**
   * 停止工具
   */
  stopTool: async (id: number): Promise<ApiResponse<void>> => {
    try {
      return await api.post<void>(TOOLS_PATHS.STOP(id));
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },
  
  /**
   * 重启工具
   */
  restartTool: async (id: number): Promise<ApiResponse<void>> => {
    try {
      return await withRetry(() => api.post<void>(TOOLS_PATHS.RESTART(id)));
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },
  
  /**
   * 获取工具状态
   */
  getToolStatus: async (id: number): Promise<ApiResponse<ToolStatus>> => {
    try {
      return await api.get<ToolStatus>(TOOLS_PATHS.STATUS(id));
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },
  
  /**
   * 验证工具配置
   */
  validateToolConfig: async (config: Record<string, any>): Promise<ApiResponse<{ valid: boolean; errors?: string[] }>> => {
    try {
      return await api.post<{ valid: boolean; errors?: string[] }>(TOOLS_PATHS.VALIDATE_CONFIG, { config });
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },
  
  /**
   * 获取工具分类列表
   */
  getToolCategories: async (): Promise<ApiResponse<string[]>> => {
    try {
      return await withCache(
        'tool-categories',
        () => api.get<string[]>(TOOLS_PATHS.CATEGORIES),
        10 * 60 * 1000 // 10分钟缓存
      );
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },
  
  /**
   * 获取工具标签列表
   */
  getToolTags: async (): Promise<ApiResponse<string[]>> => {
    try {
      return await withCache(
        'tool-tags',
        () => api.get<string[]>(TOOLS_PATHS.TAGS),
        10 * 60 * 1000 // 10分钟缓存
      );
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },
  
  /**
   * 搜索工具
   */
  searchTools: async (query: string, filters?: SearchFilters): Promise<ApiResponse<Tool[]>> => {
    try {
      const params = new URLSearchParams({ query });
      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            if (Array.isArray(value)) {
              value.forEach(v => params.append(key, v));
            } else {
              params.append(key, String(value));
            }
          }
        });
      }
      return await api.get<Tool[]>(`${TOOLS_PATHS.SEARCH}?${params.toString()}`);
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },
  
  /**
   * 获取工具统计信息
   */
  getToolStats: async (): Promise<ApiResponse<ToolStats>> => {
    try {
      return await withCache(
        'tool-stats',
        () => api.get<ToolStats>(TOOLS_PATHS.STATS),
        1 * 60 * 1000 // 1分钟缓存
      );
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },
  
  /**
   * 获取工具日志
   */
  getToolLogs: async (id: number, limit?: number, level?: string): Promise<ApiResponse<ToolLog[]>> => {
    try {
      const params = new URLSearchParams();
      if (limit) params.append('limit', String(limit));
      if (level) params.append('level', level);
      const query = params.toString() ? `?${params.toString()}` : '';
      return await api.get<ToolLog[]>(`${TOOLS_PATHS.LOGS(id)}${query}`);
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },
  
  /**
   * 清除工具日志
   */
  clearToolLogs: async (id: number): Promise<ApiResponse<void>> => {
    try {
      return await api.delete<void>(TOOLS_PATHS.LOGS(id));
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },
  


  /**
   * 获取工具分类列表 (别名)
   */
  getCategories: async (): Promise<ApiResponse<string[]>> => {
    return toolsApi.getToolCategories();
  },
};

export default toolsApi;