import { api, withRetry, withCache, handleApiError, clearCache } from './utils';
import type { ApiResponse, PaginatedResponse } from './utils';

export interface Proxy {
  id: number;
  name: string;
  display_name: string;
  description?: string;
  type: 'http' | 'https' | 'socks4' | 'socks5';
  protocol: 'http' | 'https' | 'socks4' | 'socks5';
  host: string;
  port: number;
  username?: string;
  password?: string;
  auth_type?: string;
  timeout?: number;
  max_connections?: number;
  retry_count?: number;
  status: 'active' | 'inactive' | 'testing' | 'error';
  enabled: boolean;
  category_id?: number;
  tags?: string[];
  country?: string;
  region?: string;
  city?: string;
  isp?: string;
  anonymity_level?: string;
  speed_mbps?: number;
  uptime_percentage?: number;
  last_checked_at?: string;
  last_success_at?: string;
  total_requests?: number;
  successful_requests?: number;
  failed_requests?: number;
  average_response_time?: number;
  created_at: string;
  updated_at: string;
}

export interface CreateProxyRequest {
  name: string;
  display_name: string;
  description?: string;
  type: 'http' | 'https' | 'socks4' | 'socks5';
  protocol: 'http' | 'https' | 'socks4' | 'socks5';
  host: string;
  port: number;
  username?: string;
  password?: string;
  auth_type?: string;
  timeout?: number;
  max_connections?: number;
  retry_count?: number;
  enabled?: boolean;
  category_id?: number;
  tags?: string[];
  country?: string;
  region?: string;
  city?: string;
  isp?: string;
  anonymity_level?: string;
}

export interface UpdateProxyRequest extends Partial<CreateProxyRequest> {
  id: number;
}

export interface ProxyTestResult {
  id: number;
  proxy_id: number;
  test_type?: string;
  target_url?: string;
  success: boolean;
  response_time?: number;
  status_code?: number;
  error_message?: string;
  test_data?: Record<string, any>;
  created_at: string;
}

export interface ProxyCategory {
  id: number;
  name: string;
  display_name: string;
  description?: string;
  icon?: string;
  color?: string;
  sort_order?: number;
  created_at: string;
  updated_at: string;
}

export interface ProxyStats {
  total: number;
  active: number;
  inactive: number;
  testing: number;
  error: number;
  by_type: Record<string, number>;
  by_country: Record<string, number>;
  average_response_time: number;
  success_rate: number;
}

export interface ProxySearchFilters {
  category?: string;
  proxy_type?: string;
  status?: string;
  enabled?: boolean;
  country?: string;
  search?: string;
}

const PROXY_PATHS = {
  LIST: '/proxy',
  DETAIL: (id: number) => `/proxy/${id}`,
  CREATE: '/proxy',
  UPDATE: (id: number) => `/proxy/${id}`,
  DELETE: (id: number) => `/proxy/${id}`,
  TEST: (id: number) => `/proxy/${id}/test`,
  TEST_ALL: '/proxy/test-all',
  STATUS: '/proxy/stats',
  ACTIVE: '/proxy/active',
  CATEGORIES: '/proxy/categories',
  CREATE_CATEGORY: '/proxy/categories',
  ENUMS: '/proxy/enums'
};

export const proxyApi = {
  /**
   * 获取代理列表
   */
  getProxies: async (
    page?: number, 
    pageSize?: number, 
    filters?: ProxySearchFilters
  ): Promise<PaginatedResponse<Proxy>> => {
    try {
      const params = new URLSearchParams();
      if (page) params.append('page', page.toString());
      if (pageSize) params.append('page_size', pageSize.toString());
      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value !== undefined && value !== null && value !== '') {
            params.append(key, value.toString());
          }
        });
      }
      const queryString = params.toString();
      const url = queryString ? `${PROXY_PATHS.LIST}?${queryString}` : PROXY_PATHS.LIST;
      
      return await withCache(
        `proxies-list-${queryString}`,
        () => api.get<Proxy[]>(url),
        2 * 60 * 1000 // 2分钟缓存
      );
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  /**
   * 获取单个代理详情
   */
  getProxy: async (id: number): Promise<ApiResponse<Proxy>> => {
    try {
      return await withCache(
        `proxy-${id}`,
        () => api.get<Proxy>(PROXY_PATHS.DETAIL(id)),
        5 * 60 * 1000 // 5分钟缓存
      );
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  /**
   * 创建新代理
   */
  createProxy: async (data: CreateProxyRequest): Promise<ApiResponse<Proxy>> => {
    try {
      const result = await api.post<Proxy>(PROXY_PATHS.CREATE, data);
      // 清除相关缓存
      clearCache('proxies-list');
      clearCache('proxy-categories');
      clearCache('proxy-stats');
      return result;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  /**
   * 更新代理
   */
  updateProxy: async (id: number, data: Partial<CreateProxyRequest>): Promise<ApiResponse<Proxy>> => {
    try {
      const result = await api.put<Proxy>(PROXY_PATHS.UPDATE(id), data);
      // 清除相关缓存
      clearCache(`proxy-${id}`);
      clearCache('proxies-list');
      clearCache('proxy-stats');
      return result;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  /**
   * 删除代理
   */
  deleteProxy: async (id: number): Promise<ApiResponse<void>> => {
    try {
      const result = await api.delete<void>(PROXY_PATHS.DELETE(id));
      // 清除相关缓存
      clearCache(`proxy-${id}`);
      clearCache('proxies-list');
      clearCache('proxy-stats');
      return result;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  /**
   * 测试单个代理
   */
  testProxy: async (id: number): Promise<ApiResponse<ProxyTestResult>> => {
    try {
      return await withRetry(() => api.post<ProxyTestResult>(PROXY_PATHS.TEST(id)));
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  /**
   * 批量测试所有代理
   */
  testAllProxies: async (): Promise<ApiResponse<ProxyTestResult[]>> => {
    try {
      return await api.post<ProxyTestResult[]>(PROXY_PATHS.TEST_ALL);
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  /**
   * 获取代理统计信息
   */
  getProxyStats: async (): Promise<ApiResponse<ProxyStats>> => {
    try {
      return await withCache(
        'proxy-stats',
        () => api.get<ProxyStats>(PROXY_PATHS.STATUS),
        1 * 60 * 1000 // 1分钟缓存
      );
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  /**
   * 获取活跃代理列表
   */
  getActiveProxies: async (): Promise<ApiResponse<Proxy[]>> => {
    try {
      return await withCache(
        'active-proxies',
        () => api.get<Proxy[]>(PROXY_PATHS.ACTIVE),
        30 * 1000 // 30秒缓存
      );
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  /**
   * 获取代理分类列表
   */
  getProxyCategories: async (): Promise<ApiResponse<ProxyCategory[]>> => {
    try {
      return await withCache(
        'proxy-categories',
        () => api.get<ProxyCategory[]>(PROXY_PATHS.CATEGORIES),
        10 * 60 * 1000 // 10分钟缓存
      );
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  /**
   * 创建代理分类
   */
  createProxyCategory: async (data: Omit<ProxyCategory, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse<ProxyCategory>> => {
    try {
      const result = await api.post<ProxyCategory>(PROXY_PATHS.CREATE_CATEGORY, data);
      // 清除相关缓存
      clearCache('proxy-categories');
      return result;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  /**
   * 获取代理枚举值
   */
  getProxyEnums: async (): Promise<ApiResponse<{
    types: string[];
    protocols: string[];
    statuses: string[];
  }>> => {
    try {
      return await withCache(
        'proxy-enums',
        () => api.get(PROXY_PATHS.ENUMS),
        60 * 60 * 1000 // 1小时缓存
      );
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  /**
   * 批量操作代理
   */
  batchOperation: async (operation: 'enable' | 'disable' | 'delete' | 'test', ids: number[]): Promise<ApiResponse<void>> => {
    try {
      const result = await api.post<void>(`${PROXY_PATHS.LIST}/batch`, {
        operation,
        ids
      });
      // 清除相关缓存
      clearCache('proxies-list');
      clearCache('proxy-stats');
      return result;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  }
};

export default proxyApi;