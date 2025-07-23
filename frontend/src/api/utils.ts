// API 响应接口
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  code?: number;
}

// 分页响应接口
export interface PaginatedResponse<T = any> extends ApiResponse<T[]> {
  pagination?: {
    page: number;
    pageSize: number;
    total: number;
    totalPages: number;
  };
}

// 运行时类型导出（用于解决Vite模块导入问题）
export type { ApiResponse, PaginatedResponse }

// API 错误类
export class ApiError extends Error {
  public readonly code: number;
  public readonly response?: Response;
  public readonly data?: any;

  constructor(message: string, code: number, response?: Response, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.response = response;
    this.data = data;
  }
}

// 网络错误类
export class NetworkError extends Error {
  constructor(message: string = '网络连接失败') {
    super(message);
    this.name = 'NetworkError';
  }
}

// 超时错误类
export class TimeoutError extends Error {
  constructor(message: string = '请求超时') {
    super(message);
    this.name = 'TimeoutError';
  }
}

// API 基础配置
export const API_BASE_URL = '/api/v1';
const DEFAULT_TIMEOUT = 10000;

/**
 * 解码Unicode转义序列为中文字符
 * 解决FastMCP库返回的Unicode转义序列问题
 */
const decodeUnicodeEscapes = (text: string): string => {
  if (typeof text !== 'string') {
    return text;
  }
  
  // 解码Unicode转义序列 (\uXXXX)
  return text.replace(/\\u([0-9a-fA-F]{4})/g, (match, code) => {
    return String.fromCharCode(parseInt(code, 16));
  });
};

/**
 * 递归处理对象中的所有字符串，解码Unicode转义序列
 */
const processUnicodeInObject = (obj: any): any => {
  if (typeof obj === 'string') {
    return decodeUnicodeEscapes(obj);
  }
  
  if (Array.isArray(obj)) {
    return obj.map(item => processUnicodeInObject(item));
  }
  
  if (obj && typeof obj === 'object') {
    const processed: any = {};
    for (const [key, value] of Object.entries(obj)) {
      processed[key] = processUnicodeInObject(value);
    }
    return processed;
  }
  
  return obj;
};

/**
 * 处理可能的双重JSON编码问题
 */
const handleDoubleEncoding = (data: any): any => {
  // 如果数据是字符串且看起来像JSON，尝试解析
  if (typeof data === 'string' && (data.startsWith('{') || data.startsWith('[') || data.startsWith('"'))) {
    try {
      const parsed = JSON.parse(data);
      return processUnicodeInObject(parsed);
    } catch {
      // 如果解析失败，直接处理Unicode转义
      return decodeUnicodeEscapes(data);
    }
  }
  
  return processUnicodeInObject(data);
};

// 创建请求函数
const createRequest = async <T = any>(
  method: string,
  path: string,
  body?: any,
  options: RequestInit & { params?: Record<string, any> } = {}
): Promise<ApiResponse<T>> => {
  let url = `${API_BASE_URL}${path}`;
  
  // 处理查询参数
  if (options.params && Object.keys(options.params).length > 0) {
    const searchParams = new URLSearchParams();
    Object.entries(options.params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    });
    url += `?${searchParams.toString()}`;
  }
  
  // 检查是否是 FormData
  const isFormData = body instanceof FormData;
  
  const config: RequestInit = {
    method,
    headers: {
      // 如果是 FormData，不设置 Content-Type，让浏览器自动设置
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...options.headers,
    },
    ...options,
  };

  // 添加认证头
  const token = localStorage.getItem('access_token');
  if (token) {
    (config.headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
  }

  // 添加请求体
  if (body && method !== 'GET') {
    if (isFormData) {
      // 对于 FormData，直接使用
      config.body = body;
    } else {
      // 对于其他类型，JSON 序列化
      config.body = JSON.stringify(body);
    }
  }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT);
    
    config.signal = controller.signal;
    
    const response = await fetch(url, config);
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        errorData.message || `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        response,
        errorData
      );
    }
    
    const responseData = await response.json();
    
    // 处理Unicode转义序列和双重编码问题
    const processedData = handleDoubleEncoding(responseData);
    
    // 如果后端返回的是标准格式 {success, data, message}，直接返回
    if (processedData && typeof processedData === 'object' && 'success' in processedData) {
      return {
        ...processedData,
        code: response.status
      };
    }
    
    // 否则包装为标准格式
    return {
      success: true,
      data: processedData,
      code: response.status
    };
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    
    if (error instanceof Error && error.name === 'AbortError') {
      throw new TimeoutError('请求超时');
    }
    
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new NetworkError('网络连接失败');
    }
    
    throw new ApiError(
      error instanceof Error ? error.message : '未知错误',
      0
    );
  }
};

// API 客户端
export const api = {
  get: async <T = any>(path: string, options?: RequestInit & { params?: Record<string, any> }): Promise<ApiResponse<T>> => {
    return createRequest<T>('GET', path, undefined, options);
  },
  
  post: async <T = any>(path: string, body?: any, options?: RequestInit): Promise<ApiResponse<T>> => {
    return createRequest<T>('POST', path, body, options);
  },
  
  put: async <T = any>(path: string, body?: any, options?: RequestInit): Promise<ApiResponse<T>> => {
    return createRequest<T>('PUT', path, body, options);
  },
  
  delete: async <T = any>(path: string, options?: RequestInit): Promise<ApiResponse<T>> => {
    return createRequest<T>('DELETE', path, undefined, options);
  }
};

// 错误处理函数
export const handleApiError = (error: unknown): string => {
  if (error instanceof Error) {
    return error.message;
  }
  return '未知错误';
};

// 重试函数
export const withRetry = async <T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> => {
  let lastError: Error;
  
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));
      
      // 如果是最后一次尝试，直接抛出错误
      if (attempt === maxRetries) {
        throw lastError;
      }
      
      // 对于某些错误类型，不进行重试
      if (error instanceof ApiError && error.code >= 400 && error.code < 500) {
        throw error;
      }
      
      // 等待一段时间后重试
      await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, attempt)));
    }
  }
  
  throw lastError!;
};

// 缓存函数
export const withCache = async <T>(
  key: string,
  fn: () => Promise<T>
): Promise<T> => {
  return fn();
};

// 清除缓存函数
export const clearCache = (): void => {
  // 清除缓存逻辑
};