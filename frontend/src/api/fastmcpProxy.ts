import { api, withRetry, withCache, handleApiError, clearCache } from './utils';
import type { ApiResponse, PaginatedResponse } from './utils';
import type { LogLevel } from '@/constants/logLevels';

// FastMCP代理服务器状态
export interface FastMCPProxyStatus {
  running: boolean;
  host: string;
  port: number;
  uptime: number;
  request_count: number;
  error_count: number;
  active_requests: number;
  active_sessions: number;
  max_concurrent_tools: number;
  session_isolation_enabled: boolean;
  concurrent_safety_enabled: boolean;
  transport_bridge_enabled: boolean;
  cache_enabled: boolean;
  cache_valid: boolean;
  timestamp: string;
}

// FastMCP工具状态
export interface FastMCPToolStatus {
  tool_name: string;
  status: 'running' | 'stopped' | 'error' | 'starting' | 'stopping';
  uptime?: number;
  last_activity?: string;
  session_count?: number;
  active_sessions?: string[];
  error_message?: string;
  performance?: {
    requests_per_second: number;
    avg_response_time: number;
    error_rate: number;
  };
}

// FastMCP工具配置
export interface FastMCPToolConfig {
  name: string;
  display_name: string;
  description?: string;
  command: string[];
  args?: string[];
  env?: Record<string, string>;
  working_directory?: string;
  timeout?: number;
  auto_restart?: boolean;
  enabled: boolean;
  session_isolation?: boolean;
  concurrent_safety?: boolean;
}

// FastMCP进程信息
export interface FastMCPProcessInfo {
  process_id: string;
  tool_name: string;
  pid?: number;
  status: 'running' | 'stopped' | 'error';
  start_time?: string;
  uptime?: number;
  memory_usage?: number;
  cpu_usage?: number;
  command: string[];
  session_count?: number;
}

// FastMCP工具信息
export interface FastMCPToolInfo {
  name: string;
  display_name: string;
  description?: string;
  version?: string;
  status: FastMCPToolStatus;
  config: FastMCPToolConfig;
  process?: FastMCPProcessInfo;
  capabilities?: string[];
  last_error?: string;
  session_count: number;
  request_count: number;
  error_count: number;
  performance_metrics: {
    total_requests: number;
    successful_requests: number;
    failed_requests: number;
    avg_response_time: number;
    success_rate: number;
    memory_usage: number;
    cpu_usage: number;
  };
  session_metrics: {
    total_sessions: number;
    active_sessions: number;
    avg_session_duration: number;
  };
}

// FastMCP代理服务器指标
export interface FastMCPProxyMetrics {
  server_info: {
    name: string;
    version: string;
    host: string;
    port: number;
    uptime_seconds: number;
    start_time?: string;
  };
  request_metrics: {
    total_requests: number;
    total_errors: number;
    error_rate: number;
    active_requests: number;
    requests_per_second: number;
  };
  session_metrics: {
    total_sessions: number;
    active_sessions: number;
    avg_session_duration: number;
    session_isolation_enabled: boolean;
  };
  tool_metrics: {
    total_tools: number;
    active_tools: number;
    max_concurrent_tools: number;
    tool_timeout: number;
  };
  performance_metrics: {
    avg_response_time: number;
    memory_usage: number;
    cpu_usage: number;
    concurrent_safety_enabled: boolean;
    transport_bridge_enabled: boolean;
  };
  cache_metrics: {
    cache_enabled: boolean;
    cache_ttl: number;
    cache_valid: boolean;
    cache_hit_rate: number;
  };
  timestamp: string;
}

// FastMCP日志条目
export interface FastMCPLogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  source: string;
  details?: Record<string, any>;
}

// FastMCP会话信息
export interface FastMCPSessionInfo {
  session_id: string;
  tool_name: string;
  start_time: string;
  last_activity: string;
  request_count: number;
  status: 'active' | 'idle' | 'terminated';
  client_info?: {
    user_agent?: string;
    ip_address?: string;
  };
}

// FastMCP配置更新请求
export interface FastMCPConfigUpdateRequest {
  config: Record<string, any>;
  apply_immediately?: boolean;
}

// FastMCP工具操作请求
export interface FastMCPToolActionRequest {
  tool_name: string;
  action: 'start' | 'stop' | 'restart';
  force?: boolean;
  session_id?: string;
}

// FastMCP工具发现结果
export interface FastMCPToolDiscoveryResult {
  discovered_tools: FastMCPToolConfig[];
  total_found: number;
  scan_duration: number;
  scan_paths: string[];
}

// FastMCP健康检查结果
export interface FastMCPHealthCheckResult {
  status: 'healthy' | 'unhealthy' | 'degraded';
  checks: {
    name: string;
    status: 'pass' | 'fail' | 'warn';
    message?: string;
    duration?: number;
  }[];
  timestamp: string;
}

// FastMCP代理启动请求
export interface FastMCPProxyStartRequest {
  host?: string;
  port?: number;
  max_connections?: number;
  enable_session_isolation?: boolean;
  enable_concurrent_safety?: boolean;
  enable_transport_bridge?: boolean;
}

// API路径常量
const FASTMCP_PROXY_PATHS = {
  STATUS: '/fastmcp-proxy/status',
  START: '/fastmcp-proxy/start',
  STOP: '/fastmcp-proxy/stop',
  RESTART: '/fastmcp-proxy/restart',
  TOOLS: '/fastmcp-proxy/tools',
  TOOL_DETAIL: (toolName: string) => `/fastmcp-proxy/tools/${toolName}`,
  TOOL_START: (toolName: string) => `/fastmcp-proxy/tools/${toolName}/start`,
  TOOL_STOP: (toolName: string) => `/fastmcp-proxy/tools/${toolName}/stop`,
  TOOL_RESTART: (toolName: string) => `/fastmcp-proxy/tools/${toolName}/restart`,
  TOOL_STATUS: (toolName: string) => `/fastmcp-proxy/tools/${toolName}/status`,
  METRICS: '/fastmcp-proxy/metrics',
  LOGS: '/fastmcp-proxy/logs',
  CONFIG: '/fastmcp-proxy/config',
  DISCOVER: '/fastmcp-proxy/discover',
  RELOAD: '/fastmcp-proxy/reload',
  HEALTH: '/fastmcp-proxy/health',
  SESSIONS: '/fastmcp-proxy/sessions',
  TERMINATE_SESSION: (sessionId: string) => `/fastmcp-proxy/sessions/${sessionId}`
};

// FastMCP代理服务器API
export const fastmcpProxyApi = {
  // 获取代理服务器状态
  getStatus: (): Promise<ApiResponse<FastMCPProxyStatus>> => {
    return withRetry(() => api.get(FASTMCP_PROXY_PATHS.STATUS));
  },

  // 启动代理服务器
  start: (config?: FastMCPProxyStartRequest): Promise<ApiResponse<{ status: string }>> => {
    return api.post(FASTMCP_PROXY_PATHS.START, config);
  },

  // 停止代理服务器
  stop: (): Promise<ApiResponse<{ status: string }>> => {
    return api.post(FASTMCP_PROXY_PATHS.STOP);
  },

  // 重启代理服务器
  restart: (): Promise<ApiResponse<{ status: string }>> => {
    return api.post(FASTMCP_PROXY_PATHS.RESTART);
  },

  // 获取工具列表
  getTools: (enabledOnly = false): Promise<ApiResponse<{ tools: FastMCPToolInfo[]; total: number }>> => {
    return withCache(
      `fastmcp-proxy-tools-${enabledOnly}`,
      () => api.get(FASTMCP_PROXY_PATHS.TOOLS, { params: { enabled_only: enabledOnly } }),
      30000 // 30秒缓存
    );
  },

  // 获取工具详情
  getToolDetail: (toolName: string): Promise<ApiResponse<FastMCPToolInfo>> => {
    return api.get(FASTMCP_PROXY_PATHS.TOOL_DETAIL(toolName));
  },

  // 启动工具
  startTool: (toolName: string): Promise<ApiResponse<{ tool_name: string; status: string; session_id?: string }>> => {
    clearCache('fastmcp-proxy-tools-true');
    clearCache('fastmcp-proxy-tools-false');
    return api.post(FASTMCP_PROXY_PATHS.TOOL_START(toolName));
  },

  // 停止工具
  stopTool: (toolName: string, force = false): Promise<ApiResponse<{ tool_name: string; status: string }>> => {
    clearCache('fastmcp-proxy-tools-true');
    clearCache('fastmcp-proxy-tools-false');
    return api.post(FASTMCP_PROXY_PATHS.TOOL_STOP(toolName), { params: { force } });
  },

  // 重启工具
  restartTool: (toolName: string): Promise<ApiResponse<{ tool_name: string; status: string; session_id?: string }>> => {
    clearCache('fastmcp-proxy-tools-true');
    clearCache('fastmcp-proxy-tools-false');
    return api.post(FASTMCP_PROXY_PATHS.TOOL_RESTART(toolName));
  },

  // 获取工具状态
  getToolStatus: (toolName: string): Promise<ApiResponse<FastMCPToolStatus>> => {
    return api.get(FASTMCP_PROXY_PATHS.TOOL_STATUS(toolName));
  },

  // 获取代理服务器指标
  getMetrics: (): Promise<ApiResponse<FastMCPProxyMetrics>> => {
    return api.get(FASTMCP_PROXY_PATHS.METRICS);
  },

  // 获取日志
  getLogs: (params?: {
    level?: string;
    limit?: number;
    offset?: number;
  }): Promise<ApiResponse<{ logs: FastMCPLogEntry[]; total: number }>> => {
    return api.get(FASTMCP_PROXY_PATHS.LOGS, { params });
  },

  // 更新配置
  updateConfig: (config: FastMCPConfigUpdateRequest): Promise<ApiResponse<{ status: string }>> => {
    return api.put(FASTMCP_PROXY_PATHS.CONFIG, config);
  },

  // 获取配置
  getConfig: (): Promise<ApiResponse<Record<string, any>>> => {
    return api.get(FASTMCP_PROXY_PATHS.CONFIG);
  },

  // 发现工具
  discoverTools: (params?: {
    paths?: string[];
    recursive?: boolean;
  }): Promise<ApiResponse<FastMCPToolDiscoveryResult>> => {
    return api.post(FASTMCP_PROXY_PATHS.DISCOVER, params);
  },

  // 重新加载配置
  reloadConfig: (): Promise<ApiResponse<{ status: string }>> => {
    clearCache('fastmcp-proxy-tools-true');
    clearCache('fastmcp-proxy-tools-false');
    return api.post(FASTMCP_PROXY_PATHS.RELOAD);
  },

  // 健康检查
  healthCheck: (): Promise<ApiResponse<FastMCPHealthCheckResult>> => {
    return api.get(FASTMCP_PROXY_PATHS.HEALTH);
  },

  // 获取会话列表（FastMCP特有）
  getSessions: (): Promise<ApiResponse<{ sessions: FastMCPSessionInfo[]; total: number; active_count: number }>> => {
    return api.get(FASTMCP_PROXY_PATHS.SESSIONS);
  },

  // 终止会话（FastMCP特有）
  terminateSession: (sessionId: string): Promise<ApiResponse<{ session_id: string; status: string }>> => {
    return api.delete(FASTMCP_PROXY_PATHS.TERMINATE_SESSION(sessionId));
  }
};

// 导出默认API
export default fastmcpProxyApi;