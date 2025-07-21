import { api, withRetry, withCache, handleApiError, clearCache } from './utils';
import type { ApiResponse, PaginatedResponse } from './utils';
import type { LogLevel } from '@/constants/logLevels';

// MCP代理服务器状态
export interface MCPProxyStatus {
  running: boolean;
  host: string;
  port: number;
  uptime: number;
  request_count: number;
  error_count: number;
  active_requests: number;
  max_concurrent_tools: number;
  cache_enabled: boolean;
  cache_valid: boolean;
}

// 工具状态
export interface ToolStatus {
  tool_name: string;
  status: 'running' | 'stopped' | 'error' | 'starting' | 'stopping';
  process_id?: string;
  uptime?: number;
  last_activity?: string;
  error_message?: string;
}

// 工具配置
export interface ToolConfig {
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
}

// 进程信息
export interface ProcessInfo {
  process_id: string;
  tool_name: string;
  pid?: number;
  status: 'running' | 'stopped' | 'error';
  start_time?: string;
  uptime?: number;
  memory_usage?: number;
  cpu_usage?: number;
  command: string[];
}

// 工具信息
export interface ToolInfo {
  name: string;
  display_name: string;
  description?: string;
  version?: string;
  status: ToolStatus;
  config: ToolConfig;
  process?: ProcessInfo;
  capabilities?: string[];
  last_error?: string;
}

// 代理服务器指标
export interface ProxyMetrics {
  server_info: {
    name: string;
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
  };
  tool_metrics: {
    max_concurrent_tools: number;
    tool_timeout: number;
  };
  cache_metrics: {
    cache_enabled: boolean;
    cache_ttl: number;
    cache_valid: boolean;
  };
  timestamp: string;
}

// 日志条目
export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  source: string;
  details?: Record<string, any>;
}

// 配置更新请求
export interface ConfigUpdateRequest {
  config: Record<string, any>;
}

// 工具操作请求
export interface ToolActionRequest {
  tool_name: string;
  action: 'start' | 'stop' | 'restart';
  force?: boolean;
}

// 工具发现结果
export interface ToolDiscoveryResult {
  discovered_tools: ToolConfig[];
  total_found: number;
  scan_duration: number;
  scan_paths: string[];
}

// 健康检查结果
export interface HealthCheckResult {
  status: 'healthy' | 'unhealthy' | 'degraded';
  checks: {
    name: string;
    status: 'pass' | 'fail' | 'warn';
    message?: string;
    duration?: number;
  }[];
  timestamp: string;
}

// API路径常量
const MCP_PROXY_PATHS = {
  STATUS: '/mcp-proxy/status',
  START: '/mcp-proxy/start',
  STOP: '/mcp-proxy/stop',
  RESTART: '/mcp-proxy/restart',
  TOOLS: '/mcp-proxy/tools',
  TOOL_DETAIL: (toolName: string) => `/mcp-proxy/tools/${toolName}`,
  TOOL_START: (toolName: string) => `/mcp-proxy/tools/${toolName}/start`,
  TOOL_STOP: (toolName: string) => `/mcp-proxy/tools/${toolName}/stop`,
  TOOL_RESTART: (toolName: string) => `/mcp-proxy/tools/${toolName}/restart`,
  TOOL_STATUS: (toolName: string) => `/mcp-proxy/tools/${toolName}/status`,
  METRICS: '/mcp-proxy/metrics',
  LOGS: '/mcp-proxy/logs',
  CONFIG: '/mcp-proxy/config',
  DISCOVER: '/mcp-proxy/discover',
  RELOAD: '/mcp-proxy/reload',
  HEALTH: '/mcp-proxy/health'
};

// MCP代理服务器API
export const mcpProxyApi = {
  // 获取代理服务器状态
  getStatus: (): Promise<ApiResponse<MCPProxyStatus>> => {
    return withRetry(() => api.get(MCP_PROXY_PATHS.STATUS));
  },

  // 启动代理服务器
  start: (): Promise<ApiResponse<{ status: string }>> => {
    return api.post(MCP_PROXY_PATHS.START);
  },

  // 停止代理服务器
  stop: (): Promise<ApiResponse<{ status: string }>> => {
    return api.post(MCP_PROXY_PATHS.STOP);
  },

  // 重启代理服务器
  restart: (): Promise<ApiResponse<{ status: string }>> => {
    return api.post(MCP_PROXY_PATHS.RESTART);
  },

  // 获取工具列表
  getTools: (): Promise<ApiResponse<ToolInfo[]>> => {
    return withCache(
      'mcp-proxy-tools',
      () => api.get(MCP_PROXY_PATHS.TOOLS),
      30000 // 30秒缓存
    );
  },

  // 获取工具详情
  getToolDetail: (toolName: string): Promise<ApiResponse<ToolInfo>> => {
    return api.get(MCP_PROXY_PATHS.TOOL_DETAIL(toolName));
  },

  // 启动工具
  startTool: (toolName: string): Promise<ApiResponse<{ status: string }>> => {
    clearCache('mcp-proxy-tools');
    return api.post(MCP_PROXY_PATHS.TOOL_START(toolName));
  },

  // 停止工具
  stopTool: (toolName: string, force = false): Promise<ApiResponse<{ status: string }>> => {
    clearCache('mcp-proxy-tools');
    return api.post(MCP_PROXY_PATHS.TOOL_STOP(toolName), { force });
  },

  // 重启工具
  restartTool: (toolName: string): Promise<ApiResponse<{ status: string }>> => {
    clearCache('mcp-proxy-tools');
    return api.post(MCP_PROXY_PATHS.TOOL_RESTART(toolName));
  },

  // 获取工具状态
  getToolStatus: (toolName: string): Promise<ApiResponse<ToolStatus>> => {
    return api.get(MCP_PROXY_PATHS.TOOL_STATUS(toolName));
  },

  // 获取代理服务器指标
  getMetrics: (): Promise<ApiResponse<ProxyMetrics>> => {
    return api.get(MCP_PROXY_PATHS.METRICS);
  },

  // 获取日志
  getLogs: (params?: {
    level?: string;
    limit?: number;
    offset?: number;
  }): Promise<ApiResponse<LogEntry[]>> => {
    return api.get(MCP_PROXY_PATHS.LOGS, { params });
  },

  // 更新配置
  updateConfig: (config: ConfigUpdateRequest): Promise<ApiResponse<{ status: string }>> => {
    return api.put(MCP_PROXY_PATHS.CONFIG, config);
  },

  // 获取配置
  getConfig: (): Promise<ApiResponse<Record<string, any>>> => {
    return api.get(MCP_PROXY_PATHS.CONFIG);
  },

  // 发现工具
  discoverTools: (params?: {
    paths?: string[];
    recursive?: boolean;
  }): Promise<ApiResponse<ToolDiscoveryResult>> => {
    return api.post(MCP_PROXY_PATHS.DISCOVER, params);
  },

  // 重新加载配置
  reloadConfig: (): Promise<ApiResponse<{ status: string }>> => {
    clearCache('mcp-proxy-tools');
    return api.post(MCP_PROXY_PATHS.RELOAD);
  },

  // 健康检查
  healthCheck: (): Promise<ApiResponse<HealthCheckResult>> => {
    return api.get(MCP_PROXY_PATHS.HEALTH);
  }
};

// 导出默认API
export default mcpProxyApi;