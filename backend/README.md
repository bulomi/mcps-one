# MCPS.ONE Backend

MCPS.ONE 后端服务 - MCP (Model Context Protocol) 工具管理平台的核心后端系统。

## 项目简介

MCPS.ONE 是一个现代化的 MCP 工具管理平台，提供统一的接口来管理、监控和代理各种 MCP 工具。通过模块化的架构设计，支持多种 MCP 协议传输方式和灵活的工具配置。

## 功能特性

### 核心功能
- 🔧 **工具管理**: MCP 工具的创建、配置、启动、停止和监控
- 🔄 **MCP 代理**: 支持 STDIO、HTTP 等多种传输协议的 MCP 代理服务
- 📊 **系统监控**: 实时系统状态监控和性能指标收集
- 📝 **日志管理**: 统一的日志记录、查询和分析系统
- 👥 **用户管理**: 完整的用户认证、授权和会话管理
- 🔐 **安全认证**: JWT 令牌认证和基于角色的权限控制
- 🌐 **RESTful API**: 完整的 REST API 接口和 WebSocket 支持
- 📋 **任务管理**: 异步任务调度和执行监控
- 🔗 **会话管理**: 自动会话创建和管理功能

### 技术特性
- ⚡ **高性能**: 基于 FastAPI 的异步架构
- 🗄️ **数据持久化**: SQLAlchemy ORM + SQLite 数据库
- 🔄 **自动迁移**: Alembic 数据库迁移管理
- 📈 **模块化设计**: 清晰的分层架构，易于扩展和维护
- 🛡️ **统一错误处理**: 完善的异常处理和错误追踪
- 📊 **统一配置管理**: 集中化的配置管理系统
- 🔍 **API 文档**: 自动生成的 OpenAPI/Swagger 文档
- 🔌 **插件化架构**: 支持自定义服务和集成扩展

## 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用主入口
│   ├── websocket.py         # WebSocket 连接处理
│   ├── api/                 # API 路由层
│   │   ├── __init__.py      # API 路由注册
│   │   ├── auth.py          # 认证相关 API
│   │   ├── tools.py         # 工具管理 API
│   │   ├── system.py        # 系统监控 API
│   │   ├── logs.py          # 日志管理 API
│   │   ├── user.py          # 用户管理 API
│   │   ├── sessions.py      # 会话管理 API
│   │   ├── tasks.py         # 任务管理 API
│   │   ├── monitoring.py    # 监控 API
│   │   ├── mcp_unified.py   # MCP 统一接口
│   │   ├── mcp_proxy.py     # MCP 代理服务
│   │   ├── mcp_agent.py     # MCP 代理 API
│   │   ├── mcp_http.py      # MCP HTTP 接口
│   │   ├── fastmcp_proxy.py # FastMCP 代理
│   │   ├── auto_session.py  # 自动会话管理
│   │   └── proxy.py         # 通用代理接口
│   ├── core/                # 核心基础设施
│   │   ├── __init__.py
│   │   ├── database.py      # 数据库连接和配置
│   │   ├── dependencies.py  # 依赖注入
│   │   ├── init_core.py     # 核心初始化
│   │   ├── setup_core.py    # 核心设置
│   │   ├── service_registry.py # 服务注册表
│   │   ├── unified_config_manager.py # 统一配置管理
│   │   ├── unified_logging.py # 统一日志系统
│   │   ├── unified_error.py # 统一错误处理
│   │   ├── unified_cache.py # 统一缓存系统
│   │   └── log_levels.py    # 日志级别定义
│   ├── models/              # 数据模型层
│   │   ├── __init__.py
│   │   ├── tool.py          # MCP 工具模型
│   │   ├── user.py          # 用户模型
│   │   ├── log.py           # 日志模型
│   │   ├── system.py        # 系统模型
│   │   ├── session.py       # 会话模型
│   │   ├── task.py          # 任务模型
│   │   └── proxy.py         # 代理模型
│   ├── schemas/             # Pydantic 数据模式
│   │   ├── __init__.py
│   │   ├── tool.py          # 工具数据模式
│   │   ├── user.py          # 用户数据模式
│   │   ├── auth.py          # 认证数据模式
│   │   ├── log.py           # 日志数据模式
│   │   ├── system.py        # 系统数据模式
│   │   ├── session.py       # 会话数据模式
│   │   ├── task.py          # 任务数据模式
│   │   ├── mcp_agent.py     # MCP 代理数据模式
│   │   └── mcp_proxy.py     # MCP 代理数据模式
│   ├── services/            # 业务逻辑服务层
│   │   ├── __init__.py      # 服务层初始化
│   │   ├── base/            # 基础服务
│   │   │   ├── base_service.py    # 服务基类
│   │   │   ├── cache_service.py   # 缓存服务
│   │   │   └── error_handler.py   # 错误处理服务
│   │   ├── mcp/             # MCP 相关服务
│   │   │   ├── mcp_service.py     # MCP 核心服务
│   │   │   ├── mcp_server.py      # MCP 服务器
│   │   │   ├── mcp_proxy_server.py # MCP 代理服务器
│   │   │   ├── mcp_agent_service.py # MCP 代理服务
│   │   │   └── mcp_unified_service.py # MCP 统一服务
│   │   ├── tools/           # 工具管理服务
│   │   │   ├── tool_service.py    # 工具服务
│   │   │   └── tool_registry.py   # 工具注册表
│   │   ├── users/           # 用户管理服务
│   │   │   ├── user_service.py    # 用户服务
│   │   │   └── email_service.py   # 邮件服务
│   │   ├── sessions/        # 会话管理服务
│   │   │   ├── session_service.py # 会话服务
│   │   │   └── auto_session_service.py # 自动会话服务
│   │   ├── tasks/           # 任务管理服务
│   │   │   └── task_service.py    # 任务服务
│   │   ├── system/          # 系统管理服务
│   │   │   ├── system_service.py  # 系统服务
│   │   │   ├── log_service.py     # 日志服务
│   │   │   └── process_manager.py # 进程管理
│   │   └── integrations/    # 集成服务
│   │       ├── proxy_service.py   # 代理服务
│   │       ├── request_router.py  # 请求路由
│   │       └── webhook_service.py # Webhook 服务
│   └── utils/               # 工具函数和辅助模块
│       ├── __init__.py
│       ├── helpers.py       # 辅助函数
│       ├── validators.py    # 数据验证器
│       ├── exceptions.py    # 自定义异常
│       ├── response.py      # 响应处理
│       ├── pagination.py    # 分页工具
│       ├── auth.py          # 认证工具
│       ├── jwt_utils.py     # JWT 工具
│       ├── mcp_client.py    # MCP 客户端
│       ├── process_manager.py # 进程管理工具
│       ├── process_monitor.py # 进程监控
│       ├── websocket_manager.py # WebSocket 管理
│       └── error_handler.py # 错误处理工具
├── alembic/                 # 数据库迁移
│   ├── versions/            # 迁移版本文件
│   ├── env.py              # 迁移环境配置
│   └── alembic.ini         # Alembic 配置文件
├── tests/                   # 测试文件目录
│   ├── __init__.py
│   ├── test_api/           # API 测试
│   ├── test_services/      # 服务测试
│   └── test_utils/         # 工具测试
├── data/                    # 数据存储目录
│   ├── mcps.db             # SQLite 数据库文件
│   ├── logs/               # 日志文件目录
│   └── backups/            # 数据备份目录
├── config/                  # 配置文件目录
│   ├── app.yaml            # 应用主配置
│   └── logging.yaml        # 日志配置
├── requirements.txt         # Python 依赖包列表
├── start_mcp_for_cursor.py  # Cursor MCP 服务启动脚本
├── .env.example            # 环境变量配置示例
└── README.md               # 项目文档
```

## 快速开始

### 环境要求

- Python 3.8+
- SQLite 3.x (默认数据库)
- 推荐使用虚拟环境

### 安装步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/bulomi/mcps-one.git
   cd mcps-one/backend
   ```

2. **创建虚拟环境**
   ```bash
   uv python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/macOS
   source venv/bin/activate
   ```

3. **安装依赖**
   ```bash
   uv pip install -r requirements.txt
   ```

4. **配置环境变量**
   ```bash
   # 复制环境变量模板
   cp .env.example .env
   
   # 编辑配置文件
   # 设置必要的环境变量
   ```

5. **初始化核心基础设施**
   ```bash
   # 从项目根目录运行
   cd ..
   python startup_core.py
   cd backend
   ```

6. **初始化数据库**
   ```bash
   # 创建迁移
   alembic revision --autogenerate -m "Initial migration"
   
   # 执行迁移
   alembic upgrade head
   ```

7. **启动主服务**
   ```bash
   # 开发模式（推荐）
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # 生产模式
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
   
   # 或使用 Gunicorn（生产环境）
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```


### 访问服务

- **API 文档**: http://localhost:8000/docs
- **ReDoc 文档**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/api/v1/system/health
- **系统状态**: http://localhost:8000/api/v1/system/status
- **API 根路径**: http://localhost:8000/api/v1

## 配置说明

### 环境变量

创建 `.env` 文件并配置以下变量：

```env
# 应用配置
PROJECT_NAME="MCPS.ONE"
ENVIRONMENT="development"
DEBUG=true
HOST="0.0.0.0"
PORT=8000

# API 配置
API_V1_STR="/api/v1"

# 数据库配置
DATABASE_URL="sqlite:///./data/mcps.db"
# DATABASE_URL="postgresql://user:password@localhost/mcps_db"  # PostgreSQL

# 安全配置
SECRET_KEY="your-secret-key-here"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS 配置
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
ALLOWED_HOSTS=["localhost", "127.0.0.1"]

# 日志配置
LOG_LEVEL="INFO"
LOG_FILE="./logs/app.log"
LOG_DIR="./logs"

# 数据目录
DATA_DIR="./data"
BACKUP_DIR="./data/backups"
STATIC_DIR="./static"

# MCP 配置
MCP_TIMEOUT=30
MCP_MAX_RETRIES=3
```

### 数据库配置

#### SQLite (默认)
```env
DATABASE_URL="sqlite:///./data/mcps.db"
```

#### PostgreSQL
```env
DATABASE_URL="postgresql://username:password@localhost:5432/mcps_db"
```

## API 接口

### 认证接口
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/logout` - 用户登出
- `POST /api/v1/auth/refresh` - 刷新令牌
- `GET /api/v1/auth/me` - 获取当前用户信息
- `POST /api/v1/auth/register` - 用户注册

### 用户管理
- `GET /api/v1/users` - 获取用户列表
- `POST /api/v1/users` - 创建新用户
- `GET /api/v1/users/{user_id}` - 获取用户详情
- `PUT /api/v1/users/{user_id}` - 更新用户信息
- `DELETE /api/v1/users/{user_id}` - 删除用户
- `POST /api/v1/users/{user_id}/reset-password` - 重置用户密码

### 工具管理
- `GET /api/v1/tools` - 获取工具列表
- `POST /api/v1/tools` - 创建新工具
- `GET /api/v1/tools/{tool_id}` - 获取工具详情
- `PUT /api/v1/tools/{tool_id}` - 更新工具配置
- `DELETE /api/v1/tools/{tool_id}` - 删除工具
- `POST /api/v1/tools/{tool_id}/start` - 启动工具
- `POST /api/v1/tools/{tool_id}/stop` - 停止工具
- `POST /api/v1/tools/{tool_id}/restart` - 重启工具
- `GET /api/v1/tools/{tool_id}/status` - 获取工具状态
- `GET /api/v1/tools/{tool_id}/logs` - 获取工具日志
- `GET /api/v1/tools/available` - 获取可用工具列表

### MCP 服务接口
- `POST /api/v1/mcp/unified/call` - MCP 统一调用接口
- `GET /api/v1/mcp/proxy/status` - MCP 代理状态
- `POST /api/v1/mcp/proxy/start` - 启动 MCP 代理
- `POST /api/v1/mcp/proxy/stop` - 停止 MCP 代理
- `GET /api/v1/mcp/agent/tools` - 获取 MCP 代理工具
- `POST /api/v1/mcp/agent/execute` - 执行 MCP 代理命令
- `GET /api/v1/mcp/http/tools` - HTTP MCP 工具列表
- `POST /api/v1/mcp/http/call` - HTTP MCP 调用

### 会话管理
- `GET /api/v1/sessions` - 获取会话列表
- `POST /api/v1/sessions` - 创建新会话
- `GET /api/v1/sessions/{session_id}` - 获取会话详情
- `PUT /api/v1/sessions/{session_id}` - 更新会话
- `DELETE /api/v1/sessions/{session_id}` - 删除会话
- `POST /api/v1/sessions/auto` - 自动创建会话
- `GET /api/v1/sessions/{session_id}/messages` - 获取会话消息

### 任务管理
- `GET /api/v1/tasks` - 获取任务列表
- `POST /api/v1/tasks` - 创建新任务
- `GET /api/v1/tasks/{task_id}` - 获取任务详情
- `PUT /api/v1/tasks/{task_id}` - 更新任务
- `DELETE /api/v1/tasks/{task_id}` - 删除任务
- `POST /api/v1/tasks/{task_id}/start` - 启动任务
- `POST /api/v1/tasks/{task_id}/stop` - 停止任务
- `GET /api/v1/tasks/{task_id}/status` - 获取任务状态

### 系统监控
- `GET /api/v1/system/config` - 获取系统配置
- `PUT /api/v1/system/config` - 更新系统配置
- `GET /api/v1/system/info` - 获取系统信息
- `GET /api/v1/system/status` - 获取系统状态
- `GET /api/v1/system/health` - 健康检查
- `GET /api/v1/system/metrics` - 获取系统指标
- `GET /api/v1/system/processes` - 获取进程信息
- `POST /api/v1/system/restart` - 重启系统服务
- `POST /api/v1/system/backups` - 创建备份
- `GET /api/v1/system/backups` - 获取备份列表

### 日志管理
- `GET /api/v1/logs` - 获取日志列表
- `GET /api/v1/logs/{log_id}` - 获取日志详情
- `DELETE /api/v1/logs/{log_id}` - 删除日志
- `POST /api/v1/logs/clear` - 清空日志
- `GET /api/v1/logs/system` - 获取系统日志
- `GET /api/v1/logs/operations` - 获取操作日志
- `GET /api/v1/logs/mcp` - 获取 MCP 日志
- `GET /api/v1/logs/stats` - 获取日志统计
- `DELETE /api/v1/logs/cleanup` - 清理日志
- `GET /api/v1/logs/search` - 搜索日志
- `GET /api/v1/logs/export` - 导出日志

### 监控接口
- `GET /api/v1/monitoring/metrics` - 获取监控指标
- `GET /api/v1/monitoring/alerts` - 获取告警信息
- `POST /api/v1/monitoring/alerts` - 创建告警规则
- `GET /api/v1/monitoring/dashboard` - 获取监控面板数据

### 代理服务
- `GET /api/v1/proxy/status` - 获取代理状态
- `POST /api/v1/proxy/start` - 启动代理服务
- `POST /api/v1/proxy/stop` - 停止代理服务
- `GET /api/v1/proxy/config` - 获取代理配置

## 开发指南

### 代码规范

- 使用 Black 进行代码格式化
- 使用 Flake8 进行代码检查
- 使用 MyPy 进行类型检查
- 遵循 PEP 8 编码规范
- 使用类型注解和 Pydantic 模型
- 统一的错误处理和日志记录

### 架构设计原则

#### 分层架构
- **API 层**: 处理 HTTP 请求，参数验证，响应格式化
- **服务层**: 业务逻辑实现，数据处理，外部集成
- **模型层**: 数据库模型，关系映射，数据验证
- **核心层**: 基础设施，配置管理，统一组件

#### 统一基础设施
- **配置管理**: 统一的配置管理器，支持多环境配置
- **日志系统**: 统一的日志记录，支持多级别和多输出
- **错误处理**: 统一的异常处理和错误追踪
- **缓存系统**: 统一的缓存接口，支持多种后端

#### 服务注册与发现
- 服务注册表管理所有服务实例
- 依赖注入支持服务解耦
- 插件化架构支持功能扩展

### 核心组件说明

#### 统一配置管理器 (`core/unified_config_manager.py`)
- 集中管理所有配置项
- 支持环境变量覆盖
- 配置验证和类型转换
- 热重载配置支持

#### MCP 服务架构 (`services/mcp/`)
- **MCP Server**: 核心 MCP 协议服务器
- **MCP Proxy**: 多协议代理服务
- **MCP Agent**: 智能代理服务
- **MCP Unified**: 统一接口服务

#### 进程管理 (`utils/process_manager.py`)
- 进程生命周期管理
- 进程监控和重启
- 资源使用统计

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_api/test_tools.py

# 运行测试并生成覆盖率报告
pytest --cov=app tests/

# 运行异步测试
pytest -v tests/test_services/
```

### 代码检查

```bash
# 代码格式化
black app/ tests/

# 代码检查
flake8 app/ tests/

# 类型检查
mypy app/

# 预提交钩子
pre-commit run --all-files
```

### 数据库迁移

```bash
# 创建新迁移
alembic revision --autogenerate -m "描述迁移内容"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1

# 查看迁移历史
alembic history

# 查看当前版本
alembic current
```

## 配置说明

### 环境变量

```bash
# 数据库配置
DATABASE_URL=sqlite:///./backend/data/mcps.db

# 安全配置
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256

# 应用配置
APP_NAME=MCPS.ONE
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true

# 服务器配置
HOST=0.0.0.0
PORT=8000
WORKERS=1

# 日志配置
LOG_LEVEL=INFO
LOG_DIR=./data/logs
LOG_MAX_SIZE=10MB
LOG_BACKUP_COUNT=5

# MCP 配置
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=3000
MCP_TIMEOUT=30
MCP_MAX_CONNECTIONS=100

# 缓存配置
CACHE_BACKEND=memory
CACHE_TTL=3600

# 监控配置
MONITORING_ENABLED=true
METRICS_INTERVAL=60
```

### 主配置文件

#### `config/app.yaml`
```yaml
# MCPS.ONE 应用配置
app:
  name: "MCPS.ONE"
  version: "1.0.0"
  description: "MCP 工具管理平台"
  environment: "development"
  debug: true

# 服务器配置
server:
  host: "0.0.0.0"
  port: 8000
  workers: 1
  reload: true
  access_log: true

# 数据库配置
database:
  url: "sqlite:///./data/mcps.db"
  echo: false
  pool_size: 5
  max_overflow: 10
  pool_timeout: 30
  pool_recycle: 3600

# 日志配置
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  handlers:
    - type: "file"
      filename: "./data/logs/app.log"
      max_size: "10MB"
      backup_count: 5
    - type: "console"
      level: "DEBUG"

# MCP 服务配置
mcp:
  server:
    host: "localhost"
    port: 3000
    timeout: 30
    max_connections: 100
  proxy:
    enabled: true
    protocols: ["stdio", "http"]
  agent:
    enabled: true
    max_workers: 4

# 功能开关
features:
  auto_session: true
  monitoring: true
  webhooks: false
  email_notifications: false

# 通知配置
notifications:
  email:
    enabled: false
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    username: ""
    password: ""
  webhook:
    enabled: false
    urls: []

# 安全配置
security:
  secret_key: "your-secret-key-here"
  algorithm: "HS256"
  access_token_expire_minutes: 30
  refresh_token_expire_days: 7
  password_min_length: 8
  max_login_attempts: 5

# 性能配置
performance:
  cache:
    backend: "memory"
    ttl: 3600
    max_size: 1000
  rate_limiting:
    enabled: true
    requests_per_minute: 60
  pagination:
    default_page_size: 20
    max_page_size: 100

# 数据管理
data:
  backup:
    enabled: true
    interval: "daily"
    retention_days: 30
    compression: true
  cleanup:
    logs_retention_days: 7
    temp_files_retention_hours: 24

# 监控配置
monitoring:
  enabled: true
  metrics:
    interval: 60
    retention_days: 30
  alerts:
    enabled: false
    thresholds:
      cpu_usage: 80
      memory_usage: 85
      disk_usage: 90
```

## 部署指南

### Docker 部署

```dockerfile
# Dockerfile 示例
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 生产环境部署

```bash
# 使用 Gunicorn + Uvicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# 使用 Supervisor 管理进程
sudo supervisorctl start mcps-backend
```

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库配置
   - 确保数据库服务正在运行
   - 验证连接字符串格式

2. **端口占用**
   - 检查端口是否被其他进程占用
   - 修改配置文件中的端口号

3. **依赖包安装失败**
   - 更新 pip: `pip install --upgrade pip`
   - 使用国内镜像源
   - 检查 Python 版本兼容性

### 日志查看

```bash
# 查看应用日志
tail -f logs/app.log

# 查看错误日志
grep ERROR logs/app.log

# 查看最近的日志
tail -n 100 logs/app.log
```

## 贡献指南

1. Fork 项目
2. 创建功能分支: `git checkout -b feature/new-feature`
3. 提交更改: `git commit -am 'Add new feature'`
4. 推送分支: `git push origin feature/new-feature`
5. 提交 Pull Request

## 许可证

MIT License - 详见 [LICENSE](../LICENSE) 文件

## 联系方式

- 项目主页: [GitHub Repository]
- 问题反馈: [GitHub Issues]
- 文档: [项目文档]

---

**MCPS.ONE** - 让 MCP 服务器管理变得简单高效！