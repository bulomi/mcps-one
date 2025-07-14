# MCP工具管理系统开发计划 - 单用户开源版本

## 项目概述

**技术栈：** FastAPI + Vue 3 + Naive UI + SQLite
**开发模式：** 前后端分离
**设计风格：** Naive UI 设计语言
**目标用户：** 个人开发者和小团队

## 核心功能模块

### 1. MCP 工具管理 (P0)
- **工具配置**：添加、编辑、删除 MCP 工具配置
- **工具分类**：标签和分组管理
- **状态监控**：实时监控工具连接和运行状态
- **导入导出**：工具配置的批量导入导出

### 2. MCP 代理服务 (P0)
- **协议实现**：完整的 MCP 协议支持
- **进程管理**：工具进程的启动、停止、重启
- **请求路由**：API 请求到 MCP 工具的路由
- **错误处理**：统一的错误处理和重试机制

### 3. 用户界面 (P0)
- **仪表板**：系统概览和工具状态
- **工具管理**：直观的工具配置和操作界面
- **工具详情**：详细的工具信息和日志
- **系统设置**：代理配置和界面设置

### 4. 系统管理 (P1)
- **日志管理**：操作日志和系统日志
- **数据管理**：SQLite 数据库备份和恢复
- **配置管理**：系统参数和环境配置
- **性能监控**：基础的性能指标监控

### 技术栈
- **后端**：FastAPI + SQLite + SQLAlchemy
- **前端**：Vue 3 + Naive UI + Vite + TypeScript
- **协议**：MCP (Model Context Protocol)
- **部署**：Docker + 本地部署
- **开发工具**：ESLint + Prettier + Black + pytest

## 技术实现细节

### 后端架构

#### FastAPI 应用结构
```
backend/
├── main.py              # FastAPI 应用入口
├── config.py            # 配置管理
├── database.py          # SQLite 数据库连接
├── models/              # SQLAlchemy 模型
│   ├── mcp_tool.py      # MCP 工具模型
│   ├── system_log.py    # 系统日志模型
│   └── system_config.py # 系统配置模型
├── schemas/             # Pydantic 模式
│   ├── tool_schemas.py
│   ├── log_schemas.py
│   └── config_schemas.py
├── api/                 # API 路由
│   ├── tools.py         # 工具管理 API
│   ├── mcp_proxy.py     # MCP 代理 API
│   ├── logs.py          # 日志管理 API
│   └── system.py        # 系统管理 API
├── core/                # 核心业务逻辑
│   ├── mcp_client.py    # MCP 协议客户端
│   ├── process_manager.py # 进程管理
│   ├── tool_monitor.py  # 工具监控
│   └── error_handler.py # 错误处理
└── utils/               # 工具函数
    ├── file_utils.py
    └── validation.py
```

#### MCP 协议实现
```python
# core/mcp_client.py
class MCPClient:
    """MCP 协议客户端实现"""
    
    def __init__(self, tool_config: dict):
        self.config = tool_config
        self.process = None
        self.transport = None
    
    async def start_tool(self):
        """启动 MCP 工具进程"""
        pass
    
    async def stop_tool(self):
        """停止 MCP 工具进程"""
        pass
    
    async def send_request(self, method: str, params: dict):
        """发送 MCP 请求"""
        pass
```

### 前端架构

#### Vue 3 + Naive UI 结构
```
frontend/
├── src/
│   ├── components/      # 通用组件
│   │   ├── ToolCard.vue
│   │   ├── StatusBadge.vue
│   │   └── LogViewer.vue
│   ├── views/           # 页面组件
│   │   ├── Dashboard.vue
│   │   ├── ToolManagement.vue
│   │   ├── ToolDetail.vue
│   │   └── SystemSettings.vue
│   ├── store/           # Pinia 状态管理
│   │   ├── tools.ts
│   │   ├── system.ts
│   │   └── logs.ts
│   ├── api/             # API 调用
│   │   ├── tools.ts
│   │   ├── mcp.ts
│   │   └── system.ts
│   ├── router/          # 路由配置
│   │   └── index.ts
│   ├── utils/           # 工具函数
│   │   ├── request.ts
│   │   └── format.ts
│   └── main.ts          # 应用入口
└── package.json
```

## 项目架构设计

### 整体架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端 (Vue3)   │────│  后端 (FastAPI) │────│  数据库 (SQLite)│
│                 │    │                 │    │                 │
│ - 工具管理界面  │    │ - MCP 代理服务  │    │ - 工具配置      │
│ - 仪表板        │    │ - RESTful API   │    │ - 系统日志      │
│ - 状态监控      │    │ - 进程管理      │    │ - 系统配置      │
│ - 配置管理      │    │ - 错误处理      │    │ - 操作记录      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   MCP 工具进程  │
                    │                 │
                    │ - 文件操作工具  │
                    │ - 网络请求工具  │
                    │ - 数据处理工具  │
                    │ - 自定义工具    │
                    └─────────────────┘
```

### 目录结构
```
mcps-one/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── api/            # API 路由
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据模型
│   │   ├── schemas/        # Pydantic 模式
│   │   ├── services/       # 业务逻辑
│   │   ├── utils/          # 工具函数
│   │   └── main.py         # 应用入口
│   ├── alembic/            # 数据库迁移
│   ├── tests/              # 测试文件
│   └── requirements.txt    # Python 依赖
├── frontend/               # Vue 3 + Naive UI 前端
│   ├── src/
│   │   ├── components/     # 通用组件
│   │   ├── views/          # 页面组件
│   │   ├── store/          # Pinia 状态管理
│   │   ├── api/            # API 调用
│   │   ├── router/         # 路由配置
│   │   ├── utils/          # 工具函数
│   │   └── main.ts         # 应用入口
│   ├── public/             # 静态资源
│   └── package.json        # 前端依赖
├── DEVELOPMENT_PLAN.md     # 开发计划
└── README.md               # 项目说明
```

## 开发阶段规划

### 第1-2周：项目基础搭建 ✅ **已完成**
**目标**：搭建项目基础框架和开发环境

**后端任务**：
- [x] FastAPI 项目初始化和配置
- [x] SQLAlchemy 数据模型设计（工具配置、系统日志）
- [x] SQLite 数据库配置和迁移
- [x] 基础 API 路由结构
- [x] 开发环境配置（pytest、black、pre-commit）

**前端任务**：
- [x] Vue 3 + Vite + TypeScript 项目搭建
- [x] Naive UI 组件库集成和主题配置
- [x] Pinia 状态管理配置
- [x] ESLint + Prettier 配置
- [x] 基础布局组件开发（侧边栏、导航）

**交付物**：
- [x] 可运行的后端开发环境
- [x] 基础数据模型和API结构
- [x] 后端代码规范和质量工具配置
- [x] 前端开发环境和框架搭建

### 第3-4周：MCP 工具管理核心功能 🔄 **进行中**
**目标**：实现 MCP 工具的基础管理功能

**后端任务**：
- [x] MCP 工具配置数据模型
- [x] 工具 CRUD API 实现
- [x] 工具分类和标签系统
- [ ] 配置导入导出功能
- [x] 基础错误处理机制

**前端任务**：
- [x] 前端开发环境搭建
- [x] 基础布局和导航组件
- [ ] 工具管理界面开发
- [ ] 工具配置表单组件
- [ ] 工具列表和详情页面
- [ ] 分类管理界面
- [ ] 导入导出功能界面

**交付物**：
- [x] 基础工具配置管理功能（后端）
- [x] 工具分类和标签系统（后端）
- [x] 前端开发环境搭建
- [x] 前端管理界面
- [ ] 配置导入导出功能

### 第5-6周：MCP 代理服务实现 ✅ **已完成**
**目标**：实现 MCP 协议支持和进程管理

**后端任务**：
- [x] MCP 协议实现（JSON-RPC over stdio/HTTP/WebSocket）
- [x] 工具进程管理（启动、停止、重启）
- [x] 请求路由和代理功能
- [x] 工具状态监控和健康检查
- [x] 统一错误处理和重试机制
- [x] MCP 代理服务 API 接口
- [x] 代理会话管理和任务执行
- [x] 工具调用、资源管理、提示管理

**前端任务**：
- [ ] 仪表板页面开发
- [ ] 工具状态监控界面
- [ ] 实时状态更新（WebSocket）
- [ ] 工具操作控制面板
- [ ] 错误信息展示组件

**交付物**：
- [x] 完整的 MCP 代理服务（后端）
- [x] 工具进程管理功能
- [x] MCP 客户端连接管理
- [x] 代理服务 API 接口
- [ ] 实时状态监控界面（前端）

### 第7周：系统管理和日志功能 🔄 **部分完成**
**目标**：完善系统管理和监控功能

**后端任务**：
- [x] 系统日志记录和管理
- [x] 操作日志追踪
- [x] 系统配置管理 API
- [ ] 数据库备份和恢复功能
- [ ] 基础性能指标收集

**前端任务**：
- [ ] 日志查看和搜索界面
- [ ] 系统设置页面
- [ ] 数据管理界面
- [ ] 性能监控仪表板
- [ ] 系统信息展示

**交付物**：
- [x] 日志管理系统（后端API）
- [x] 系统配置管理功能（后端）
- [ ] 前端管理界面
- [ ] 基础性能监控

### 第8周：优化、测试和部署
**目标**：项目优化、测试完善和部署准备

**优化任务**：
- [ ] API 性能优化
- [ ] 前端代码分割和懒加载
- [ ] 数据库查询优化
- [ ] 错误处理完善

**测试任务**：
- [ ] 单元测试补充
- [ ] 集成测试编写
- [ ] 前端组件测试
- [ ] E2E 测试场景

**部署任务**：
- [ ] Docker 容器化配置
- [ ] 生产环境配置
- [ ] 部署文档编写
- [ ] 用户使用手册

**交付物**：
- [ ] 完整的测试覆盖
- [ ] 生产就绪的部署方案
- [ ] 项目文档和用户手册

## 技术实现细节

### 后端技术栈
```python
# 核心依赖
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.13.1
pydantic==2.5.0
pydantic-settings==2.1.0

# 数据库
psycopg2-binary==2.9.9  # PostgreSQL (可选)

# 认证和安全
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# 工具库
python-dotenv==1.0.0
requests==2.31.0
```

### 前端技术栈
```json
{
  "dependencies": {
    "vue": "^3.3.11",
    "naive-ui": "^2.35.0",
    "@vicons/ionicons5": "^0.12.0",
    "vue-router": "^4.2.5",
    "pinia": "^2.1.7",
    "axios": "^1.6.7",
    "echarts": "^5.5.0",
    "vue-echarts": "^6.6.9",
    "typescript": "^5.2.2"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^4.5.2",
    "vite": "^5.0.8",
    "@types/node": "^20.11.20",
    "eslint": "^8.57.0",
    "prettier": "^3.2.5",
    "vitest": "^1.3.1"
  }
}
```

## 部署和运维

### 部署架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端静态文件   │    │  FastAPI 应用   │    │   SQLite 数据库 │
│                 │    │                 │    │                 │
│ - Vue 3 构建产物│    │ - API 服务      │    │ - 本地文件      │
│ - 静态资源服务  │    │ - MCP 代理      │    │ - 自动备份      │
│ - 开发/生产模式 │    │ - 进程管理      │    │ - 数据持久化    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   MCP 工具进程  │
                    │                 │
                    │ - 独立进程      │
                    │ - 进程监控      │
                    │ - 自动重启      │
                    └─────────────────┘
```

### 部署方案

#### 开发环境部署
```bash
# 后端开发服务器
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 前端开发服务器
cd frontend
npm install
npm run dev
```

#### 生产环境部署

**Docker 部署（推荐）**
```dockerfile
# Dockerfile
FROM node:18-alpine as frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app

# 安装 Python 依赖
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ ./backend/

# 复制前端构建产物
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# 创建数据目录
RUN mkdir -p /app/data

EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**本地部署**
```bash
# 构建前端
cd frontend
npm run build

# 启动后端（包含静态文件服务）
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 数据管理

#### SQLite 数据库
- **位置**: `./data/mcps.db`
- **备份**: 自动每日备份到 `./data/backups/`
- **迁移**: Alembic 数据库版本管理

#### 配置文件
```yaml
# config.yaml
database:
  url: "sqlite:///./data/mcps.db"
  backup_enabled: true
  backup_interval: "daily"

server:
  host: "0.0.0.0"
  port: 8000
  debug: false

mcp:
  tools_dir: "./data/tools"
  logs_dir: "./data/logs"
  max_processes: 10
```

## 开发规范

### 代码规范
- **Python**: 遵循 PEP 8，使用 Black 格式化
- **TypeScript**: 遵循 ESLint 规则，使用 Prettier 格式化
- **Git**: 使用 Conventional Commits 规范
- **文档**: 使用 Markdown，保持简洁清晰
- **注释**: 关键业务逻辑必须有注释说明

### 测试规范
- **后端**: pytest + coverage，覆盖率 > 80%
- **前端**: Vitest + Vue Test Utils，覆盖率 > 70%
- **组件**: 关键组件必须有单元测试
- **API**: 所有 API 端点必须有测试用例

### 质量保证
- **代码审查**: 所有 PR 必须经过代码审查
- **自动化测试**: CI/CD 流水线自动运行测试
- **性能监控**: 关键接口响应时间监控
- **错误处理**: 完善的错误处理和用户友好提示

### 安全规范
- **输入验证**: Pydantic 数据验证和清理
- **SQL 注入**: SQLAlchemy ORM 防护
- **XSS**: 前端输入转义和内容安全策略
- **文件安全**: 上传文件类型和大小限制
- **进程安全**: MCP 工具进程隔离和权限控制

### API 设计规范
- RESTful API 设计
- OpenAPI 3.0 文档
- 统一错误处理
- 请求/响应日志

### UI/UX 规范
- Naive UI 设计语言
- 响应式设计（桌面优先）
- 深色/浅色主题支持
- 简洁直观的用户界面

## 质量保证

### 测试策略
- **后端**: pytest + 单元测试 + 集成测试
- **前端**: Vitest + 组件测试
- **E2E**: Playwright 端到端测试
- **API**: Postman 自动化测试

### 部署策略
- **开发环境**: Docker Compose
- **测试环境**: 自动化部署
- **生产环境**: Docker Swarm 或 Kubernetes
- **监控**: Prometheus + Grafana

## 里程碑和交付物

### 第一阶段交付物 ✅ **已完成**
- [x] 项目架构文档
- [x] 后端开发环境搭建完成
- [x] 基础数据模型和API结构
- [x] 前端开发环境和管理界面框架

### 第二阶段交付物 🔄 **进行中**
- [x] MCP 工具管理功能（后端API）
- [x] 系统日志管理功能（后端API）
- [x] 系统配置管理模块（后端API）
- [x] API 文档（自动生成）
- [ ] 前端管理界面
- [ ] MCP 代理服务实现

### 第三阶段交付物
- [ ] 应用市场功能
- [ ] 个人服务端点
- [ ] 通知系统
- [ ] 完整功能演示

### 第四阶段交付物
- [ ] 性能优化报告
- [ ] 安全审计报告
- [ ] 部署文档
- [ ] 用户手册

## 风险评估和应对

### 技术风险
- **Docker 管理复杂性**: 使用成熟的 Docker SDK
- **前后端集成**: 早期建立 API 契约
- **性能瓶颈**: 定期性能测试

### 进度风险
- **功能范围蔓延**: 严格按照 MVP 原则
- **技术学习曲线**: 提供充分的技术支持
- **集成问题**: 持续集成和测试

## 当前项目状态总结

### ✅ 已完成功能
- **后端基础架构**: FastAPI + SQLAlchemy + SQLite 完整搭建
- **数据模型**: MCP工具、系统日志、系统配置等核心模型
- **API接口**: 工具管理、日志管理、系统配置等完整API
- **数据库**: 自动迁移和初始化机制
- **配置管理**: 环境配置和应用设置
- **日志系统**: 完整的日志记录和管理
- **开发环境**: 后端开发服务器正常运行
- **前端环境**: Vue 3 + Naive UI + TypeScript 开发环境搭建
- **前端界面**: 基础布局、导航组件和工具管理界面

### 🔄 进行中功能
- **前端框架**: Vue 3 + Naive UI 环境搭建
- **MCP代理服务**: 协议实现和进程管理
- **配置导入导出**: 工具配置批量管理

### 📋 下一步优先级
1. **高优先级**: 基础布局和导航组件开发
2. **高优先级**: MCP协议实现和代理服务
3. **中优先级**: 工具进程管理和状态监控
4. **中优先级**: 前端工具管理界面开发
5. **低优先级**: 配置导入导出功能

## 下一步行动计划

### 本周目标
1. **MCP代理服务**: 协议实现和进程管理核心逻辑
2. **工具配置验证**: 配置验证机制和错误处理
3. **前后端集成**: API调用封装和状态管理完善

### 下周目标
1. **工具管理界面**: 工具列表、添加、编辑、删除功能
2. **MCP代理服务**: 基础协议实现和工具进程管理
3. **状态监控**: 实时工具状态展示

### 本月目标
1. **完整前端界面**: 所有核心功能的前端实现
2. **MCP协议支持**: 完整的MCP工具代理功能
3. **系统集成测试**: 前后端完整功能测试

---

**最后更新**: 2025年7月14日
**当前状态**: 后端基础完成，前端开发中
**服务器状态**: ✅ 运行中 (http://localhost:8000)
**下次更新**: 前端环境搭建完成后