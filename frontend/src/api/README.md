# 前端 API 模块说明

本文档详细说明了 MCPS.ONE 前端 API 模块的架构、功能和使用方法。该模块提供了完整的类型安全 API 接口，支持工具管理、MCP 服务集成、系统管理等核心功能。

## 模块概述

前端 API 模块采用模块化设计，提供统一的接口规范和错误处理机制，主要解决以下问题：
- 统一 API 路径管理，避免硬编码
- 提供类型安全的 TypeScript 接口
- 集成错误处理、重试机制和缓存功能
- 支持 Unicode 字符处理和双重编码解析
- 提供完整的 MCP 服务集成

## 核心功能

### 1. 工具管理 API (`tools.ts`)

**功能概述**：提供完整的工具生命周期管理接口

**主要接口**：
```typescript
// 工具 CRUD 操作
toolsApi.getTools()           // 获取工具列表
toolsApi.getTool(id)          // 获取工具详情
toolsApi.createTool(data)     // 创建新工具
toolsApi.updateTool(id, data) // 更新工具
toolsApi.deleteTool(id)       // 删除工具

// 工具状态控制
toolsApi.startTool(id)        // 启动工具
toolsApi.stopTool(id)         // 停止工具
toolsApi.restartTool(id)      // 重启工具
toolsApi.getToolStatus(id)    // 获取工具状态

// 工具管理功能
toolsApi.searchTools(query, filters)  // 搜索工具
toolsApi.getToolCategories()          // 获取分类列表
toolsApi.getToolTags()                // 获取标签列表
toolsApi.getToolStats()               // 获取统计信息
toolsApi.getToolLogs(id)              // 获取工具日志
```

**工具状态支持**：
- `running` - 运行中
- `stopped` - 已停止
- `starting` - 启动中
- `stopping` - 停止中
- `error` - 错误状态
- `unknown` - 未知状态

### 2. MCP 代理服务 API (`mcp.ts`)

**功能概述**：提供 MCP (Model Context Protocol) 代理服务接口

**主要接口**：
```typescript
// 工具调用
mcpApi.callTool(toolName, request)           // 调用 MCP 工具
mcpApi.getToolCapabilities(toolName)         // 获取工具能力
mcpApi.listTools()                           // 列出可用工具

// 资源管理
mcpApi.listResources(toolName)              // 列出资源
mcpApi.readResource(toolName, request)       // 读取资源

// 提示管理
mcpApi.listPrompts(toolName)                // 列出提示
mcpApi.getPrompt(toolName, request)          // 获取提示

// 状态管理
mcpApi.getToolStatus(toolName)              // 获取工具状态
mcpApi.reconnectTool(toolName)              // 重连工具
mcpApi.disconnectTool(toolName)             // 断开工具
```

### 3. MCP 统一服务 API (`mcp-unified.ts`)

**功能概述**：提供统一的 MCP 服务管理接口

**主要接口**：
```typescript
// 服务管理
mcpUnifiedApi.getServiceStatus()            // 获取服务状态
mcpUnifiedApi.startService()                // 启动服务
mcpUnifiedApi.stopService()                 // 停止服务
mcpUnifiedApi.switchServiceMode(config)     // 切换服务模式
mcpUnifiedApi.reloadConfig()                // 重新加载配置

// 监控和工具
mcpUnifiedApi.getServiceMetrics()           // 获取服务指标
mcpUnifiedApi.getAvailableTools()           // 获取可用工具
mcpUnifiedApi.callTool(request)             // 调用工具
mcpUnifiedApi.healthCheck()                 // 健康检查
```

**服务模式**：
- `proxy_only` - 仅代理模式
- `server_only` - 仅服务器模式

### 4. API 路径常量化 (`constants.ts`)

**功能概述**：统一管理所有 API 路径，避免硬编码

**路径分类**：
```typescript
// 基础路径
BASE_PATHS.AUTH          // 认证相关
BASE_PATHS.TOOLS         // 工具管理
BASE_PATHS.MCP_AGENT     // MCP 代理
BASE_PATHS.MCP_UNIFIED   // MCP 统一服务
BASE_PATHS.SYSTEM        // 系统管理

// 具体路径示例
TOOLS_PATHS.LIST         // /tools/
TOOLS_PATHS.START(id)    // /tools/{id}/start/
MCP_AGENT_PATHS.TOOLS    // /mcp-agent/tools/
```

### 5. 统一 API 请求工具 (`utils.ts`)

**功能概述**：提供类型安全、功能丰富的 API 请求封装

**核心特性**：
- 🔒 **类型安全**：完整的 TypeScript 类型定义
- 🛡️ **错误处理**：统一的错误类型和处理机制
- 🔄 **重试机制**：自动重试失败的请求
- ⚡ **超时控制**：可配置的请求超时
- 🔐 **认证支持**：自动添加认证头
- 🌐 **Unicode 支持**：处理 Unicode 转义序列
- 📦 **双重编码处理**：解决 FastMCP 库编码问题

## 文件结构

```
src/api/
├── constants.ts          # API 路径常量定义
├── utils.ts             # 统一 API 请求工具和类型定义
├── tools.ts             # 工具管理 API 接口
├── mcp.ts               # MCP 代理服务 API 接口
├── mcp-unified.ts       # MCP 统一服务 API 接口
├── auth.ts              # 认证相关 API 接口
├── system.ts            # 系统管理 API 接口
├── index.ts             # 统一导出入口
└── README.md            # 本文档
```

### 文件说明

- **`constants.ts`** - 定义所有 API 路径常量，按模块分类管理
- **`utils.ts`** - 提供核心的 API 请求函数、类型定义和错误处理
- **`tools.ts`** - 工具管理相关的所有 API 接口和类型定义
- **`mcp.ts`** - MCP 代理服务的 API 接口，支持工具调用、资源管理等
- **`mcp-unified.ts`** - MCP 统一服务的 API 接口，提供服务管理功能
- **`auth.ts`** - 用户认证和授权相关的 API 接口
- **`system.ts`** - 系统配置、日志、统计等管理接口
- **`index.ts`** - 统一导出所有 API 接口，便于外部使用

## 使用指南

### 基本用法

#### 1. 工具管理示例

```typescript
import { toolsApi } from '@/api'

// 获取工具列表
const response = await toolsApi.getTools()
if (response.success) {
  console.log('工具列表:', response.data)
}

// 创建新工具
const newTool = await toolsApi.createTool({
  name: 'my-tool',
  display_name: '我的工具',
  description: '这是一个示例工具',
  command: 'python script.py',
  type: 'custom',
  category: 'development'
})

// 启动工具
const startResult = await toolsApi.startTool(toolId)
if (startResult.success) {
  console.log('工具启动成功')
}

// 获取工具状态
const status = await toolsApi.getToolStatus(toolId)
console.log('工具状态:', status.data?.status)
```

#### 2. MCP 服务示例

```typescript
import { mcpApi, mcpUnifiedApi } from '@/api'

// 调用 MCP 工具
const result = await mcpApi.callTool('tool-name', {
  tool_name: 'example-tool',
  arguments: { param1: 'value1' }
})

// 获取 MCP 统一服务状态
const serviceStatus = await mcpUnifiedApi.getServiceStatus()
console.log('服务状态:', serviceStatus)

// 切换服务模式
const modeResult = await mcpUnifiedApi.switchServiceMode({
  enable_server: true,
  enable_proxy: false
})
```

#### 3. 直接使用 API 客户端

```typescript
import { api, TOOLS_PATHS } from '@/api'

// GET 请求
const response = await api.get(TOOLS_PATHS.LIST)

// POST 请求
const createResponse = await api.post(TOOLS_PATHS.CREATE, {
  name: 'My Tool',
  command: 'echo hello'
})

// 带查询参数的请求
const searchResponse = await api.get(TOOLS_PATHS.SEARCH, {
  params: { query: 'python', category: 'development' }
})
```

### 错误处理

#### 1. 基本错误处理

```typescript
import { toolsApi, handleApiError, ApiError, NetworkError, TimeoutError } from '@/api'

try {
  const response = await toolsApi.getTools()
  if (response.success) {
    console.log('获取成功:', response.data)
  } else {
    console.error('API 返回错误:', response.message)
  }
} catch (error) {
  const errorMessage = handleApiError(error)
  console.error('请求失败:', errorMessage)
  
  // 根据错误类型进行不同处理
  if (error instanceof ApiError) {
    console.log('HTTP 状态码:', error.code)
    console.log('错误详情:', error.data)
  } else if (error instanceof NetworkError) {
    console.log('网络连接失败，请检查网络')
  } else if (error instanceof TimeoutError) {
    console.log('请求超时，请稍后重试')
  }
}
```

#### 2. 重试机制

```typescript
import { withRetry } from '@/api'

// 自动重试失败的请求
try {
  const data = await withRetry(
    () => toolsApi.getToolStatus(toolId),
    3,    // 最大重试次数
    1000  // 重试延迟（毫秒）
  )
} catch (error) {
  console.error('重试后仍然失败:', handleApiError(error))
}
```

### 类型定义

#### 1. 工具相关类型

```typescript
// 工具基础接口
interface Tool {
  id: number
  name: string
  display_name?: string
  description: string
  type?: 'builtin' | 'custom' | 'external' | 'mcp'
  category: string
  tags: string[]
  command?: string
  working_directory?: string
  environment_variables?: Record<string, string>
  connection_type?: 'stdio' | 'http' | 'websocket'
  host?: string
  port?: number
  path?: string
  auto_start?: boolean
  restart_on_failure?: boolean
  max_restart_attempts?: number
  timeout?: number
  status: 'active' | 'inactive' | 'error'
  createdAt: string
  updatedAt: string
}

// 工具状态接口
interface ToolStatus {
  id: number
  status: 'running' | 'stopped' | 'error' | 'starting' | 'stopping'
  lastStarted?: string
  lastStopped?: string
  errorMessage?: string
  uptime?: number
  memoryUsage?: number
  cpuUsage?: number
}
```

#### 2. MCP 相关类型

```typescript
// MCP 工具调用请求
interface ToolCallRequest {
  tool_name: string
  arguments: Record<string, any>
}

// MCP 工具调用响应
interface ToolCallResponse {
  tool_name: string
  arguments: Record<string, any>
  result: any
  success: boolean
}

// MCP 服务状态
interface ServiceStatus {
  mode: 'proxy_only' | 'server_only'
  is_running: boolean
  proxy_running: boolean
  server_running: boolean
  api_running: boolean
  proxy_tools_count: number
  uptime: number
  last_error?: string
}
```

#### 3. API 响应类型

```typescript
// 基础 API 响应
interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
  code?: number
}

// 分页响应
interface PaginatedResponse<T = any> extends ApiResponse<T[]> {
  pagination?: {
    page: number
    pageSize: number
    total: number
    totalPages: number
  }
}
```

## 测试

运行 API 路径测试：
```bash
npm test src/api/__tests__/api-paths.test.ts
```

测试覆盖：
- API 路径验证
- 路径规范化
- 动态路径构建
- 错误处理

## 最佳实践

### 1. 使用专用 API 接口
```typescript
// ✅ 推荐：使用专用的 API 接口
import { toolsApi } from '@/api'
const tools = await toolsApi.getTools()

// ✅ 也可以：使用路径常量
import { api, TOOLS_PATHS } from '@/api'
const tools = await api.get(TOOLS_PATHS.LIST)

// ❌ 避免：硬编码路径
const tools = await api.get('/api/v1/tools')
```

### 2. 正确处理响应数据
```typescript
// ✅ 检查响应状态
const response = await toolsApi.getTools()
if (response.success && response.data) {
  console.log('工具列表:', response.data)
} else {
  console.error('获取失败:', response.message)
}

// ✅ 使用类型断言确保类型安全
const tool = response.data as Tool[]
```

### 3. 统一错误处理
```typescript
// ✅ 在组件中统一处理错误
const handleToolOperation = async (operation: () => Promise<any>) => {
  try {
    const result = await operation()
    if (result.success) {
      // 成功处理
      return result.data
    } else {
      // API 返回的业务错误
      throw new Error(result.message || '操作失败')
    }
  } catch (error) {
    // 网络错误或其他异常
    const message = handleApiError(error)
    console.error('操作失败:', message)
    throw error
  }
}

// 使用示例
const startTool = () => handleToolOperation(() => toolsApi.startTool(toolId))
```

### 4. MCP 服务集成
```typescript
// ✅ 检查服务状态后再调用
const callMcpTool = async (toolName: string, args: any) => {
  // 先检查服务状态
  const status = await mcpUnifiedApi.getServiceStatus()
  if (!status.is_running) {
    throw new Error('MCP 服务未运行')
  }
  
  // 调用工具
  return await mcpUnifiedApi.callTool({
    tool_name: toolName,
    arguments: args
  })
}
```

### 5. 性能优化建议
```typescript
// ✅ 使用重试机制处理临时错误
const getToolWithRetry = async (id: number) => {
  return await withRetry(
    () => toolsApi.getTool(id),
    3,    // 最大重试 3 次
    1000  // 每次重试间隔 1 秒
  )
}

// ✅ 批量操作时控制并发数
const startMultipleTools = async (toolIds: number[]) => {
  const batchSize = 3 // 每批处理 3 个
  const results = []
  
  for (let i = 0; i < toolIds.length; i += batchSize) {
    const batch = toolIds.slice(i, i + batchSize)
    const batchResults = await Promise.allSettled(
      batch.map(id => toolsApi.startTool(id))
    )
    results.push(...batchResults)
  }
  
  return results
}
```

## 配置选项

### API 基础配置
```typescript
// 在 utils.ts 中的配置
export const API_BASE_URL = '/api/v1'  // API 基础路径
const DEFAULT_TIMEOUT = 10000          // 默认超时时间（10秒）
```

### 请求配置选项
```typescript
// 所有 API 请求都支持以下配置
interface RequestOptions {
  headers?: Record<string, string>     // 自定义请求头
  params?: Record<string, any>         // 查询参数
  timeout?: number                     // 请求超时时间
}

// 使用示例
const response = await api.get(TOOLS_PATHS.LIST, {
  headers: { 'Custom-Header': 'value' },
  params: { page: 1, pageSize: 20 },
  timeout: 5000
})
```

### 重试配置
```typescript
// withRetry 函数的配置选项
const data = await withRetry(
  () => toolsApi.getTool(id),
  3,     // maxRetries: 最大重试次数
  1000   // delay: 重试间隔（毫秒）
)
```

## 故障排除

### 常见问题及解决方案

#### 1. API 请求失败
```typescript
// 问题：请求返回 404 或 500 错误
// 解决方案：检查 API 路径和服务器状态
try {
  const response = await toolsApi.getTools()
  console.log('请求成功:', response)
} catch (error) {
  if (error instanceof ApiError) {
    console.error('API 错误:', error.status, error.message)
    // 检查错误状态码
    if (error.status === 404) {
      console.log('检查 API 路径是否正确')
    } else if (error.status >= 500) {
      console.log('服务器内部错误，请稍后重试')
    }
  }
}
```

#### 2. 网络连接问题
```typescript
// 问题：网络超时或连接失败
// 解决方案：使用重试机制和错误处理
try {
  const data = await withRetry(
    () => toolsApi.getTools(),
    3,    // 重试 3 次
    2000  // 每次间隔 2 秒
  )
} catch (error) {
  if (error instanceof NetworkError) {
    console.error('网络连接失败，请检查网络状态')
  } else if (error instanceof TimeoutError) {
    console.error('请求超时，请稍后重试')
  }
}
```

#### 3. MCP 服务连接问题
```typescript
// 问题：MCP 服务调用失败
// 解决方案：检查服务状态
const checkMcpService = async () => {
  try {
    const status = await mcpUnifiedApi.getServiceStatus()
    if (!status.is_running) {
      console.log('MCP 服务未运行，尝试启动...')
      await mcpUnifiedApi.startService()
    }
  } catch (error) {
    console.error('MCP 服务检查失败:', error)
  }
}
```

#### 4. 数据格式问题
```typescript
// 问题：响应数据格式不正确
// 解决方案：检查数据结构和类型
const validateResponse = (response: any) => {
  if (!response || typeof response !== 'object') {
    throw new Error('响应数据格式错误')
  }
  
  if (!response.success) {
    throw new Error(response.message || '请求失败')
  }
  
  return response.data
}
```

### 调试技巧

#### 1. 启用详细日志
```typescript
// 在开发环境中启用详细日志
if (process.env.NODE_ENV === 'development') {
  // 拦截所有 API 请求进行日志记录
  const originalGet = api.get
  api.get = async (url: string, options?: any) => {
    console.log('API GET:', url, options)
    const result = await originalGet(url, options)
    console.log('API Response:', result)
    return result
  }
}
```

#### 2. 检查网络请求
```typescript
// 使用浏览器开发者工具
// 1. 打开 F12 开发者工具
// 2. 切换到 Network 标签页
// 3. 执行 API 请求
// 4. 查看请求详情、响应状态和数据
```

#### 3. 测试 API 连通性
```typescript
// 创建简单的健康检查函数
const healthCheck = async () => {
  try {
    const mcpStatus = await mcpUnifiedApi.healthCheck()
    console.log('MCP 服务状态:', mcpStatus)
    
    const systemStatus = await systemApi.getStatus()
    console.log('系统状态:', systemStatus)
    
    return { mcp: mcpStatus, system: systemStatus }
  } catch (error) {
    console.error('健康检查失败:', error)
    return null
  }
}
```

### 开发环境设置
```bash
# 1. 克隆项目
git clone <repository-url>
cd frontend

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev
```

### 添加新的 API 接口
1. **在 `constants.ts` 中添加路径常量**
```typescript
export const NEW_MODULE_PATHS = {
  BASE: '/new-module',
  LIST: '/new-module/list',
  DETAIL: (id: number) => `/new-module/${id}`
} as const
```

2. **创建 API 模块文件**
```typescript
// new-module.ts
import { api, ApiResponse } from './utils'
import { NEW_MODULE_PATHS } from './constants'

interface NewModuleItem {
  id: number
  name: string
  // 其他字段...
}

export const newModuleApi = {
  async getList(): Promise<ApiResponse<NewModuleItem[]>> {
    return await api.get(NEW_MODULE_PATHS.LIST)
  },
  
  async getDetail(id: number): Promise<ApiResponse<NewModuleItem>> {
    return await api.get(NEW_MODULE_PATHS.DETAIL(id))
  }
}
```

3. **在 `index.ts` 中导出**
```typescript
export * from './new-module'
export { NEW_MODULE_PATHS } from './constants'
```

### 代码规范
- ✅ 使用 TypeScript 进行类型安全
- ✅ 所有 API 路径使用 `constants.ts` 中的常量
- ✅ 统一使用 `utils.ts` 中的 `api` 对象
- ✅ 为所有接口定义 TypeScript 类型
- ✅ 使用 `ApiResponse<T>` 包装响应数据
- ✅ 添加适当的错误处理
- ✅ 遵循现有的命名约定

### 测试建议
```typescript
// 在浏览器控制台中测试新 API
import { newModuleApi } from '@/api'

// 测试获取列表
newModuleApi.getList().then(console.log).catch(console.error)

// 测试获取详情
newModuleApi.getDetail(1).then(console.log).catch(console.error)
```