# MCPS.ONE Pro 版本开发计划

## 📋 开发策略

**当前阶段专注Web端开发**：基于产品初期阶段和资源优化考虑，暂时专注于Vue 3 SPA主应用和管理后台的开发，确保核心功能的稳定性和用户体验。移动端H5和桌面端Electron将在获得一定用户基础规模后纳入开发计划。

**本地开发环境优先**：当前阶段专注于本地开发环境的完善和功能实现，暂时不考虑正式环境部署相关的复杂配置，优先确保本地开发体验的流畅性和功能完整性。

## 📋 项目概述

**项目名称**: MCPS.ONE Pro - 企业级MCP服务管理SaaS平台  
**项目类型**: 多租户SaaS服务  
**技术栈**: FastAPI + Vue 3 + PostgreSQL + Redis + Docker + Kubernetes  

## 🎯 产品定位

### 目标用户
- **个人Pro用户**: 专业开发者、自由职业者
- **团队用户**: 小型开发团队（2-10人）
- **企业用户**: 中大型企业（10+人）

### 核心价值
- 企业级MCP服务管理
- 多租户协作平台
- 专业开发者工具链
- 高可用SaaS服务

## 🏗️ 系统架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端层 (Frontend)                      │
├─────────────────────────────────────────────────────────────┤
│           Vue 3 SPA           │        管理后台              │
│        (主要Web应用)           │     (系统管理界面)            │
└─────────────────────────────────────────────────────────────┘

<!-- 未来扩展计划 (待用户基础达到一定规模后考虑)
┌─────────────────────────────────────────────────────────────┐
│                     多端扩展 (Future)                        │
├─────────────────────────────────────────────────────────────┤
│        移动端H5        │        桌面端Electron              │
│     (移动设备支持)      │      (桌面应用体验)                │
└─────────────────────────────────────────────────────────────┘
-->
                              │
┌─────────────────────────────────────────────────────────────┐
│                      API网关层 (Gateway)                     │
├─────────────────────────────────────────────────────────────┤
│  Nginx/Traefik  │  负载均衡  │  SSL终止  │  限流防护        │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      应用服务层 (Services)                    │
├─────────────────────────────────────────────────────────────┤
│  用户服务  │  租户服务  │  MCP服务  │  监控服务  │  计费服务   │
│  认证服务  │  通知服务  │  文件服务  │  日志服务  │  工作流服务 │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      数据存储层 (Storage)                     │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL  │  Redis  │  MinIO  │  InfluxDB  │  Elasticsearch │
│  (主数据库)   │ (缓存)   │ (文件)   │ (监控)     │   (日志搜索)    │
└─────────────────────────────────────────────────────────────┘
```

### 微服务架构

#### 核心服务
1. **用户服务 (User Service)**
   - 用户注册、登录、资料管理
   - 权限控制、角色管理
   - SSO集成

2. **租户服务 (Tenant Service)**
   - 多租户管理
   - 组织架构管理
   - 数据隔离

3. **MCP服务 (MCP Service)**
   - MCP服务器管理
   - 服务编排
   - 负载均衡

4. **监控服务 (Monitor Service)**
   - 性能监控
   - 健康检查
   - 告警通知

5. **计费服务 (Billing Service)**
   - 订阅管理
   - 用量统计
   - 发票生成

#### 支撑服务
1. **认证服务 (Auth Service)**
2. **通知服务 (Notification Service)**
3. **文件服务 (File Service)**
4. **日志服务 (Log Service)**
5. **工作流服务 (Workflow Service)**

### 数据库设计

#### 多租户数据隔离策略
- **共享数据库，共享Schema**: 通过tenant_id字段隔离
- **行级安全策略**: PostgreSQL RLS (Row Level Security)
- **连接池隔离**: 不同租户使用不同连接池

#### 核心数据表
```sql
-- 租户表
CREATE TABLE tenants (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    plan_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100),
    role VARCHAR(50) DEFAULT 'member',
    created_at TIMESTAMP DEFAULT NOW()
);

-- MCP服务表
CREATE TABLE mcp_services (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    name VARCHAR(255) NOT NULL,
    config JSONB,
    status VARCHAR(20) DEFAULT 'stopped',
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 📅 开发计划

### 阶段一：MVP核心版 (1-6个月) 🎯

#### 目标
- **核心功能实现**: MCP服务管理和API集成
- **基础架构搭建**: 多租户SaaS平台基础
- **MVP产品交付**: 可用的最小功能集合

#### 调整后的里程碑

**M1.1 基础架构搭建 (1个月)**
- [ ] ~~微服务架构设计~~ → 单体应用架构（简化）
- [ ] Docker容器化
- [ ] 基础监控告警系统

**M1.2 多租户核心系统 (1.5个月)**
- [ ] 租户管理模块
- [ ] 数据隔离机制（PostgreSQL RLS）
- [ ] 用户认证系统（JWT）
- [ ] 基础权限控制
- [ ] 路径隔离路由

**M1.3 MCP服务管理 (2个月) 🔥**
- [ ] MCP服务创建、配置、管理
- [ ] 服务状态监控和日志查看
- [ ] 一键启停和重启
- [ ] 服务模板库（常用配置）
- [ ] 批量操作支持

**M1.4 开发者API集成 (1个月) 🔥**
- [ ] API Token认证系统
- [ ] MCP工具远程调用API
- [ ] Python SDK开发
- [ ] API文档和示例
- [ ] 基础速率限制

**M1.5 计费系统 (0.5个月)**
- [ ] 订阅计划管理
- [ ] API调用计费
- [ ] 支付集成 (Stripe)
- [ ] 试用期管理
- [ ] 基础发票生成

#### 技术栈
- **后端**: FastAPI + SQLAlchemy + Alembic
- **前端**: Vue 3 + TypeScript + Pinia
- **数据库**: PostgreSQL + Redis
- **部署**: Docker Compose
- **监控**: Prometheus + Grafana

#### 功能清单

**用户管理**
- [x] 用户注册/登录
- [ ] 邮箱验证
- [ ] 密码重置
- [ ] 个人资料管理
- [ ] 账户安全设置

**MCP服务管理**
- [ ] 无限MCP服务创建
- [ ] 服务配置管理
- [ ] 批量操作支持
- [ ] 服务模板库
- [ ] 一键部署功能

**监控与日志**
- [ ] 实时性能监控
- [ ] 详细日志查看
- [ ] 错误追踪系统
- [ ] 使用统计报告
- [ ] 自定义告警规则

**数据管理**
- [ ] 自动数据备份
- [ ] 版本历史管理
- [ ] 一键数据恢复
- [ ] 数据导出功能
- [ ] 数据同步机制

### 阶段二：成长优化版 (6-12个月) 🚀

#### 目标
- **用户体验优化**: 界面和交互流程改进
- **团队协作功能**: 多用户协作支持
- **性能稳定性**: 系统性能和可靠性提升

#### 调整后的里程碑

**M2.1 团队协作基础 (1个月) 📊**
- [ ] 团队创建和成员管理
- [ ] 基础角色权限（管理员、成员）
- [ ] 项目空间隔离
- [ ] 团队内配置共享
- [ ] ~~成员邀请系统~~ → 简化邀请流程
- [ ] ~~协作日志记录~~ → 后期功能

**M2.2 用户界面优化 (1个月) 🎨**
- [ ] 响应式设计优化
- [ ] 直观的仪表板设计
- [ ] 操作引导和帮助系统
- [ ] 多主题支持
- [ ] 用户体验优化

**M2.3 数据管理增强 (1个月) 💾**
- [ ] 自动数据备份
- [ ] 配置导入导出
- [ ] 版本历史管理
- [ ] 数据恢复功能
- [ ] 配置模板管理

**M2.4 高级API功能 (1个月) 🔌**
- [ ] JavaScript/Go SDK开发
- [ ] 批量操作API
- [ ] 异步任务API
- [ ] Webhook支持
- [ ] CLI工具增强
- [ ] 开发者控制台

**M2.5 性能优化 (2个月) ⚡**
- [ ] 数据库查询优化
- [ ] 缓存策略实施
- [ ] API响应时间优化
- [ ] 并发处理优化
- [ ] 监控系统完善

#### 功能清单

**团队协作**
- [ ] 团队创建管理
- [ ] 成员邀请加入
- [ ] 角色权限分配
- [ ] 项目空间管理
- [ ] 实时协作编辑
- [ ] 评论讨论功能
- [ ] 变更通知机制

**工作流管理**
- [ ] 可视化流程设计
- [ ] 自动化任务执行
- [ ] 条件分支逻辑
- [ ] 定时任务调度
- [ ] 错误处理机制
- [ ] 执行历史追踪

**开发者API集成**
- [ ] API Token生成管理
- [ ] MCP工具远程调用接口
- [ ] 批量操作API
- [ ] 异步任务API
- [ ] 实时状态查询
- [ ] API使用统计
- [ ] 速率限制配置
- [ ] 错误码标准化
- [ ] API版本管理
- [ ] 开发者控制台
- [ ] 在线API测试
- [ ] SDK代码生成

**高级监控**
- [ ] 多维度性能分析
- [ ] 自定义仪表板
- [ ] 智能告警规则
- [ ] 趋势分析报告
- [ ] 容量规划建议

### 阶段三：企业扩展版 (12-15个月) 🏢

#### 目标
- **企业级功能**: 差异化功能和企业级能力开发
- **企业用户支持**: 企业级功能和安全特性
- **生态系统基础**: 平台扩展性和集成能力

#### 调整后的里程碑

**M3.1 工作流引擎 (2个月) 🔄**
- [ ] 可视化流程设计器
- [ ] 自动化任务执行
- [ ] 定时任务调度
- [ ] 条件分支逻辑
- [ ] 执行历史追踪
- [ ] ~~复杂编排功能~~ → 简化版本

**M3.2 企业级安全 (2个月) 🔒**
- [ ] SSO集成 (SAML/OAuth)
- [ ] 审计日志系统
- [ ] IP白名单控制
- [ ] 数据加密传输
- [ ] 合规性报告
- [ ] 多因素认证

**M3.3 高级监控分析 (1个月) 📈**
- [ ] 自定义仪表板
- [ ] 趋势分析报告
- [ ] 容量规划建议
- [ ] 智能告警规则
- [ ] 性能分析洞察

**M3.4 生态系统基础 (1个月) 🌱**
- [ ] MCP工具市场基础
- [ ] 第三方集成框架
- [ ] 开发者文档平台
- [ ] 社区论坛基础
- [ ] ~~复杂合作伙伴计划~~ → 简化版本

#### 暂缓功能（根据市场反馈决定）
- ❌ **私有部署**: 开发成本高，市场需求待验证
- ❌ **AI智能化**: 噱头大于实用，用户不愿付费
- ❌ **复杂生态系统**: 需要大量用户基础支撑

#### 功能清单

**企业级安全**
- [ ] 企业SSO集成
- [ ] 多因素认证
- [ ] IP白名单控制
- [ ] 数据驻留选择
- [ ] 合规性认证
- [ ] 安全审计报告

**高级管理**
- [ ] 组织架构管理
- [ ] 成本中心分配
- [ ] 预算控制系统
- [ ] 使用配额管理
- [ ] 自定义报表
- [ ] 数据分析洞察

**平台扩展**
- [ ] 插件开发框架
- [ ] 第三方应用集成
- [ ] API网关管理
- [ ] 微服务治理
- [ ] 服务网格支持

## 🛠️ 技术实现细节

### 后端架构

#### 微服务通信
```python
# 服务间通信示例
from fastapi import FastAPI
from httpx import AsyncClient

class TenantService:
    async def get_tenant_info(self, tenant_id: str):
        async with AsyncClient() as client:
            response = await client.get(
                f"http://tenant-service/api/v1/tenants/{tenant_id}"
            )
            return response.json()

class MCPService:
    def __init__(self):
        self.tenant_service = TenantService()
    
    async def create_mcp_service(self, tenant_id: str, config: dict):
        # 验证租户权限
        tenant = await self.tenant_service.get_tenant_info(tenant_id)
        if not tenant or tenant['status'] != 'active':
            raise HTTPException(status_code=403, detail="Tenant not active")
        
        # 创建MCP服务逻辑
        # ...
```

#### 开发者API系统
```python
# API Token认证系统
from fastapi import HTTPException, Depends, Header
from fastapi.security import HTTPBearer
import jwt
from datetime import datetime, timedelta

class APITokenManager:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.security = HTTPBearer()
    
    def generate_api_token(self, user_id: str, tenant_id: str, permissions: list) -> str:
        """生成API Token"""
        payload = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "permissions": permissions,
            "exp": datetime.utcnow() + timedelta(days=365),
            "iat": datetime.utcnow(),
            "type": "api_token"
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")
    
    def verify_api_token(self, token: str) -> dict:
        """验证API Token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            if payload.get("type") != "api_token":
                raise HTTPException(status_code=401, detail="Invalid token type")
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

# MCP工具远程调用API
class MCPRemoteAPI:
    def __init__(self, token_manager: APITokenManager):
        self.token_manager = token_manager
    
    async def call_mcp_tool(self, 
                           token_payload: dict,
                           tool_name: str, 
                           method: str, 
                           params: dict) -> dict:
        """远程调用MCP工具"""
        # 验证权限
        if "mcp:execute" not in token_payload.get("permissions", []):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        tenant_id = token_payload["tenant_id"]
        
        # 获取租户的MCP服务实例
        mcp_service = await self.get_tenant_mcp_service(tenant_id, tool_name)
        if not mcp_service:
            raise HTTPException(status_code=404, detail="MCP tool not found")
        
        # 执行MCP工具调用
        try:
            result = await mcp_service.call_method(method, params)
            
            # 记录API调用日志
            await self.log_api_call(token_payload["user_id"], tenant_id, tool_name, method)
            
            return {
                "success": True,
                "data": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

# API路由定义
from fastapi import APIRouter, Depends

api_router = APIRouter(prefix="/api/v1")

@api_router.post("/mcp/{tool_name}/call")
async def call_mcp_tool_endpoint(
    tool_name: str,
    request: dict,
    token_payload: dict = Depends(verify_api_token)
):
    """MCP工具调用端点"""
    mcp_api = MCPRemoteAPI(token_manager)
    return await mcp_api.call_mcp_tool(
        token_payload=token_payload,
        tool_name=tool_name,
        method=request["method"],
        params=request.get("params", {})
    )

@api_router.get("/mcp/tools")
async def list_available_tools(
    token_payload: dict = Depends(verify_api_token)
):
    """获取可用的MCP工具列表"""
    tenant_id = token_payload["tenant_id"]
    tools = await get_tenant_mcp_tools(tenant_id)
    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "methods": tool.available_methods,
                "status": tool.status
            }
            for tool in tools
        ]
    }
```

#### 多租户数据隔离
```python
# 数据库会话管理
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text

class TenantSessionManager:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def get_tenant_session(self, tenant_id: str):
        session = self.SessionLocal()
        # 设置行级安全策略
        session.execute(text(f"SET app.current_tenant_id = '{tenant_id}'"))
        return session

# 行级安全策略
"""
CREATE POLICY tenant_isolation ON mcp_services
    FOR ALL TO application_role
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

ALTER TABLE mcp_services ENABLE ROW LEVEL SECURITY;
"""
```

### 客户端SDK使用示例

#### Python SDK
```python
# 安装SDK
# pip install mcps-one-sdk

from mcps_one import MCPSClient

# 初始化客户端
client = MCPSClient(
    api_token="your_api_token_here",
    base_url="https://api.mcps.one"
)

# 获取可用的MCP工具
tools = await client.get_available_tools()
print(f"Available tools: {[tool.name for tool in tools]}")

# 调用MCP工具
result = await client.call_tool(
    tool_name="file-manager",
    method="list_files",
    params={"path": "/workspace"}
)

if result.success:
    print(f"Files: {result.data}")
else:
    print(f"Error: {result.error}")

# 批量操作
batch_results = await client.batch_call([
    {"tool": "file-manager", "method": "read_file", "params": {"path": "config.json"}},
    {"tool": "database", "method": "query", "params": {"sql": "SELECT * FROM users"}}
])

for i, result in enumerate(batch_results):
    print(f"Batch {i}: {'Success' if result.success else 'Failed'}")
```

#### JavaScript/Node.js SDK
```javascript
// 安装SDK
// npm install @mcps-one/sdk

const { MCPSClient } = require('@mcps-one/sdk');

// 初始化客户端
const client = new MCPSClient({
    apiToken: 'your_api_token_here',
    baseUrl: 'https://api.mcps.one'
});

// 获取可用工具
async function listTools() {
    try {
        const tools = await client.getAvailableTools();
        console.log('Available tools:', tools.map(t => t.name));
        return tools;
    } catch (error) {
        console.error('Failed to get tools:', error.message);
    }
}

// 调用MCP工具
async function callTool() {
    try {
        const result = await client.callTool({
            toolName: 'web-scraper',
            method: 'scrape_page',
            params: {
                url: 'https://example.com',
                selector: '.content'
            }
        });
        
        if (result.success) {
            console.log('Scraped content:', result.data);
        } else {
            console.error('Scraping failed:', result.error);
        }
    } catch (error) {
        console.error('API call failed:', error.message);
    }
}

// 实时状态监听
client.onToolStatusChange((event) => {
    console.log(`Tool ${event.toolName} status: ${event.status}`);
});

// 执行
listTools().then(() => callTool());
```

#### Go SDK
```go
// go get github.com/mcps-one/go-sdk

package main

import (
    "context"
    "fmt"
    "log"
    
    "github.com/mcps-one/go-sdk"
)

func main() {
    // 初始化客户端
    client := mcps.NewClient(&mcps.Config{
        APIToken: "your_api_token_here",
        BaseURL:  "https://api.mcps.one",
    })
    
    ctx := context.Background()
    
    // 获取工具列表
    tools, err := client.GetAvailableTools(ctx)
    if err != nil {
        log.Fatalf("Failed to get tools: %v", err)
    }
    
    fmt.Printf("Available tools: %d\n", len(tools))
    
    // 调用工具
    result, err := client.CallTool(ctx, &mcps.ToolCallRequest{
        ToolName: "system-monitor",
        Method:   "get_cpu_usage",
        Params: map[string]interface{}{
            "interval": "1m",
        },
    })
    
    if err != nil {
        log.Fatalf("Tool call failed: %v", err)
    }
    
    if result.Success {
        fmt.Printf("CPU Usage: %v\n", result.Data)
    } else {
        fmt.Printf("Error: %s\n", result.Error)
    }
    
    // 异步调用
    go func() {
        asyncResult, err := client.CallToolAsync(ctx, &mcps.ToolCallRequest{
            ToolName: "data-processor",
            Method:   "process_large_dataset",
            Params: map[string]interface{}{
                "dataset_id": "12345",
                "operation":  "aggregate",
            },
        })
        
        if err != nil {
            log.Printf("Async call failed: %v", err)
            return
        }
        
        // 轮询结果
        for {
            status, err := client.GetAsyncResult(ctx, asyncResult.TaskID)
            if err != nil {
                log.Printf("Failed to get async result: %v", err)
                break
            }
            
            if status.Completed {
                fmt.Printf("Async task completed: %v\n", status.Result)
                break
            }
            
            time.Sleep(5 * time.Second)
        }
    }()
}
```

#### CLI工具使用
```bash
# 安装CLI工具
npm install -g @mcps-one/cli
# 或者
curl -sSL https://install.mcps.one | bash

# 配置API Token
mcps auth login --token your_api_token_here

# 查看可用工具
mcps tools list

# 调用工具
mcps tools call file-manager list_files --params '{"path": "/workspace"}'

# 批量操作
mcps tools batch --file batch_operations.json

# 实时监控
mcps monitor --tool web-scraper --follow

# 导出配置
mcps config export --output mcps-config.yaml

# 部署到本地
mcps deploy local --config mcps-config.yaml
```

#### REST API直接调用
```bash
# 获取工具列表
curl -H "Authorization: Bearer your_api_token" \
     https://api.mcps.one/api/v1/mcp/tools

# 调用MCP工具
curl -X POST \
     -H "Authorization: Bearer your_api_token" \
     -H "Content-Type: application/json" \
     -d '{
       "method": "search_files",
       "params": {
         "query": "*.py",
         "path": "/src"
       }
     }' \
     https://api.mcps.one/api/v1/mcp/file-manager/call

# 获取工具状态
curl -H "Authorization: Bearer your_api_token" \
     https://api.mcps.one/api/v1/mcp/tools/file-manager/status

# 获取调用历史
curl -H "Authorization: Bearer your_api_token" \
     "https://api.mcps.one/api/v1/mcp/history?limit=50&tool=file-manager"
```

### 前端架构

#### 多租户路由
```typescript
// 路由配置
import { createRouter, createWebHistory } from 'vue-router'
import { useTenantStore } from '@/stores/tenant'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/u/:username',
      component: () => import('@/layouts/PersonalLayout.vue'),
      children: [
        {
          path: 'dashboard',
          component: () => import('@/views/Dashboard.vue')
        }
      ]
    },
    {
      path: '/t/:teamSlug',
      component: () => import('@/layouts/TeamLayout.vue'),
      children: [
        {
          path: 'dashboard',
          component: () => import('@/views/TeamDashboard.vue')
        }
      ]
    }
  ]
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const tenantStore = useTenantStore()
  
  // 从路径提取租户信息
  const tenantInfo = extractTenantFromPath(to.path)
  if (tenantInfo) {
    await tenantStore.setCurrentTenant(tenantInfo)
  }
  
  next()
})
```

#### 状态管理
```typescript
// Pinia Store
import { defineStore } from 'pinia'

export const useTenantStore = defineStore('tenant', {
  state: () => ({
    currentTenant: null as Tenant | null,
    userRole: null as string | null,
    permissions: [] as string[]
  }),
  
  actions: {
    async setCurrentTenant(tenantInfo: TenantInfo) {
      // 获取租户详细信息
      const response = await api.get(`/tenants/${tenantInfo.id}`)
      this.currentTenant = response.data
      
      // 获取用户在该租户下的角色权限
      const roleResponse = await api.get(`/tenants/${tenantInfo.id}/user-role`)
      this.userRole = roleResponse.data.role
      this.permissions = roleResponse.data.permissions
    }
  }
})
```

### 部署架构

#### Kubernetes配置
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcps-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcps-backend
  template:
    metadata:
      labels:
        app: mcps-backend
    spec:
      containers:
      - name: backend
        image: mcps/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: mcps-secrets
              key: database-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: mcps-backend-service
spec:
  selector:
    app: mcps-backend
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```





## 📚 相关文档

- [技术架构设计](./architecture-design.md)
- [API接口文档](./api-documentation.md)
- [开发者SDK文档](./sdk-documentation.md)
- [数据库设计](./database-design.md)
- [部署运维指南](./deployment-guide.md)
- [安全设计方案](./security-design.md)
- [测试策略文档](./testing-strategy.md)
- [用户使用手册](./user-manual.md)

---

**文档版本**: v3.1（Web端专注版）  
**创建时间**: 2025年1月  
**更新时间**: 2025年1月  
**负责人**: 项目团队  
**审核人**: 技术架构师  
**变更说明**: 调整开发策略，暂时专注Web端开发，移动端和桌面端延后至用户基础建立后