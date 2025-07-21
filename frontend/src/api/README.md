# API 模块优化说明

本文档说明了为解决 307 重定向问题和提升代码质量而进行的 API 模块重构。

## 问题背景

原始问题：`GET /api/v1/tools HTTP/1.1" 307 Temporary Redirect`

这个问题通常由以下原因引起：
- API 路径末尾缺少斜杠导致服务器重定向
- 硬编码的 API 路径缺乏统一管理
- 缺乏路径验证和规范化机制

## 解决方案

### 1. API 路径常量化 (`constants.ts`)

**目的**：统一管理所有 API 路径，避免硬编码

```typescript
// 使用前
const response = await axios.get('/api/v1/tools')

// 使用后
const response = await api.get(TOOLS_PATHS.LIST)
```

**特性**：
- 分模块组织路径常量
- 提供路径验证函数
- 自动路径规范化
- 动态路径构建支持

### 2. 统一 API 请求工具 (`utils.ts`)

**目的**：提供类型安全、功能丰富的 API 请求封装

**核心功能**：
- 🔒 **类型安全**：完整的 TypeScript 类型定义
- 🛡️ **错误处理**：统一的错误类型和处理机制
- 🔄 **重试机制**：自动重试失败的请求
- 💾 **请求缓存**：智能缓存机制减少重复请求
- 📊 **性能监控**：集成 API 调用监控
- ⚡ **超时控制**：可配置的请求超时
- 🔐 **认证支持**：自动添加认证头

### 3. API 监控系统 (`monitor.ts`)

**目的**：实时监控 API 性能，快速发现问题

**监控指标**：
- 请求数量和频率
- 响应时间统计
- 错误率和错误类型
- 最慢端点识别
- 实时性能指标

**使用方式**：
```typescript
// 自动监控（已集成到 apiRequest 中）
const data = await api.get('/api/v1/tools')

// 手动获取统计
const stats = apiMonitor.getPerformanceStats()
const realTime = apiMonitor.getRealTimeMetrics()
```

### 4. 开发工具集成

**DevTools 组件**：
- 快捷键 `Ctrl+Shift+D` 切换显示
- 实时 API 状态显示
- 一键清除缓存
- 应用重新加载

**API 监控面板**：
- 实时性能指标
- 详细统计报告
- 错误追踪
- 数据导出功能

## 文件结构

```
src/api/
├── constants.ts          # API 路径常量
├── utils.ts             # 统一 API 请求工具
├── monitor.ts           # API 监控系统
├── auth.ts              # 认证相关 API
├── tools.ts             # 工具管理 API
├── system.ts            # 系统管理 API
├── index.ts             # 统一导出
├── __tests__/           # 测试文件
│   └── api-paths.test.ts
└── README.md            # 本文档
```

## 使用指南

### 基本用法

```typescript
import { api, TOOLS_PATHS } from '@/api'

// GET 请求
const tools = await api.get(TOOLS_PATHS.LIST)

// POST 请求
const newTool = await api.post(TOOLS_PATHS.CREATE, {
  name: 'My Tool',
  config: {}
})

// 带重试的请求
const data = await withRetry(() => api.get('/api/v1/data'))

// 带缓存的请求
const cachedData = await withCache('tools-list', () => api.get(TOOLS_PATHS.LIST))
```

### 错误处理

```typescript
import { handleApiError, ApiError } from '@/api'

try {
  const data = await api.get('/api/v1/tools')
} catch (error) {
  const handled = handleApiError(error)
  console.error('API 错误:', handled.message)
  
  if (error instanceof ApiError) {
    // 处理 API 特定错误
    console.log('状态码:', error.status)
    console.log('错误详情:', error.details)
  }
}
```

### 监控使用

```typescript
import { apiMonitor, performanceAnalyzer } from '@/api'

// 获取性能统计
const stats = apiMonitor.getPerformanceStats()
console.log('平均响应时间:', stats.averageResponseTime)
console.log('错误率:', stats.errorRate)

// 生成性能报告
const report = performanceAnalyzer.generateReport()
console.log(report)

// 清除监控数据
apiMonitor.clearMetrics()
```

## 开发环境功能

### 开发工具栏

在开发环境中，按 `Ctrl+Shift+D` 可以打开开发工具栏，提供：
- 实时 API 状态显示
- API 监控开关
- 缓存清除
- 应用重新加载

### API 监控面板

点击开发工具栏中的"API 监控"按钮可以打开详细的监控面板：
- 实时性能指标
- 端点性能排行
- 错误统计和追踪
- 数据导出和报告生成

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

### 1. 使用路径常量
```typescript
// ✅ 推荐
import { TOOLS_PATHS } from '@/api'
const data = await api.get(TOOLS_PATHS.LIST)

// ❌ 避免
const data = await api.get('/api/v1/tools')
```

### 2. 合理使用缓存
```typescript
// ✅ 适合缓存的场景：静态数据、配置信息
const config = await withCache('app-config', () => api.get(SYSTEM_PATHS.CONFIG))

// ❌ 不适合缓存：实时数据、用户特定数据
const userProfile = await api.get(AUTH_PATHS.PROFILE) // 不使用缓存
```

### 3. 错误处理
```typescript
// ✅ 统一错误处理
try {
  const data = await api.get('/api/v1/data')
  return data
} catch (error) {
  const handled = handleApiError(error)
  // 根据错误类型进行不同处理
  if (handled.isNetworkError) {
    // 网络错误处理
  } else if (handled.isTimeoutError) {
    // 超时错误处理
  }
  throw handled
}
```

### 4. 性能优化
```typescript
// ✅ 使用重试机制处理临时错误
const data = await withRetry(() => api.get('/api/v1/data'), {
  maxAttempts: 3,
  delay: 1000
})

// ✅ 合理设置超时时间
const data = await api.get('/api/v1/data', {
  timeout: 5000 // 5秒超时
})
```

## 配置选项

### API 请求配置
```typescript
interface ApiRequestConfig {
  timeout?: number          // 超时时间（毫秒）
  retries?: number         // 重试次数
  cache?: boolean          // 是否缓存
  headers?: Record<string, string> // 自定义头
}
```

### 监控配置
```typescript
apiMonitor.updateConfig({
  enabled: true,           // 是否启用监控
  maxMetrics: 1000,       // 最大指标数量
  retentionTime: 3600000  // 数据保留时间（1小时）
})
```

## 故障排除

### 常见问题

1. **307 重定向问题**
   - 确保使用 `constants.ts` 中定义的路径
   - 检查路径是否正确规范化

2. **请求超时**
   - 检查网络连接
   - 调整超时配置
   - 使用重试机制

3. **缓存问题**
   - 使用 `clearCache()` 清除缓存
   - 检查缓存键是否正确

4. **监控数据异常**
   - 使用 `apiMonitor.clearMetrics()` 重置数据
   - 检查监控是否启用

### 调试技巧

1. **启用详细日志**
```typescript
// 在开发环境中启用详细日志
if (import.meta.env.DEV) {
  apiMonitor.updateConfig({ enabled: true })
}
```

2. **使用开发工具**
   - 按 `Ctrl+Shift+D` 打开开发工具
   - 查看实时 API 状态
   - 使用监控面板分析性能

3. **检查网络请求**
   - 使用浏览器开发者工具
   - 查看 Network 标签页
   - 检查请求头和响应

## 更新日志

### v1.0.0 (当前版本)
- ✅ 创建 API 路径常量系统
- ✅ 实现统一 API 请求工具
- ✅ 集成 API 监控系统
- ✅ 添加开发工具支持
- ✅ 重构所有 API 模块
- ✅ 添加完整的测试覆盖
- ✅ 解决 307 重定向问题

## 贡献指南

在修改 API 模块时，请遵循以下原则：

1. **路径管理**：所有新的 API 路径必须添加到 `constants.ts`
2. **类型安全**：确保所有 API 调用都有正确的类型定义
3. **错误处理**：使用统一的错误处理机制
4. **测试覆盖**：为新功能添加相应的测试
5. **文档更新**：及时更新相关文档

---

通过这次重构，我们不仅解决了 307 重定向问题，还大幅提升了代码的可维护性、类型安全性和开发体验。所有的 API 调用现在都经过统一的处理流程，具备了监控、缓存、重试等企业级功能。