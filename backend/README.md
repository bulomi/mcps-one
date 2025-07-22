# MCPS.ONE Backend

基于 FastAPI 的 MCP 工具管理平台后端，提供统一的 MCP 服务聚合和管理能力。

## 技术栈

- **框架**: FastAPI + SQLAlchemy
- **数据库**: SQLite/PostgreSQL
- **协议**: MCP (STDIO/HTTP/WebSocket)
- **部署**: Docker + uv

## 项目结构

```
backend/
├── app/                    # 应用核心
│   ├── api/               # API 接口层
│   ├── core/              # 核心配置
│   ├── models/            # 数据模型
│   ├── schemas/           # 数据模式
│   ├── services/          # 业务逻辑
│   │   └── mcp/          # MCP 服务
│   ├── utils/             # 工具函数
│   └── main.py           # 应用入口
├── config/app.yaml        # 配置文件
├── data/                  # 数据目录
├── tests/                 # 测试代码
└── requirements.txt       # 依赖包
```

## 快速开始

### 环境要求
- Python 3.11+
- uv (推荐)

### 启动服务

```bash
# 安装依赖
uv sync

# 启动开发服务
uv run python -m app.main

# 生产环境
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### 服务端点

- **API 文档**: http://localhost:8000/docs
- **ReDoc 文档**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/api/v1/system/health
- **系统状态**: http://localhost:8000/api/v1/system/status
- **WebSocket**: ws://localhost:8000/ws

## 配置管理

### 配置文件结构

```
backend/
├── config/
│   └── app.yaml          # 主配置文件
├── .env.example          # 环境变量模板
└── .env                  # 本地环境变量（需创建）
```

### 环境变量配置

```bash
# 复制配置模板
cp .env.example .env

# 编辑环境变量
vim .env
```

**核心环境变量：**

```env
# 应用基础配置
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key-here

# 服务器配置
HOST=0.0.0.0
PORT=8000

# 数据库配置
DATABASE_URL=sqlite:///./data/mcps.db
# DATABASE_URL=postgresql://user:pass@localhost/mcps_db

# 日志配置
LOG_LEVEL=INFO
LOG_DIR=./data/logs

# MCP 服务配置
MCP_TIMEOUT=30
MCP_MAX_CONNECTIONS=100
```

### 主配置文件 (config/app.yaml)

系统使用 YAML 格式的主配置文件，支持环境变量覆盖：

```yaml
app:
  name: "MCPS.ONE"
  version: "2.0.0"
  environment: "${ENVIRONMENT:development}"
  debug: "${DEBUG:true}"

server:
  host: "${HOST:0.0.0.0}"
  port: "${PORT:8000}"
  workers: 1
  reload: true

database:
  url: "${DATABASE_URL:sqlite:///./data/mcps.db}"
  echo: false
  pool_size: 5

logging:
  level: "${LOG_LEVEL:INFO}"
  dir: "${LOG_DIR:./data/logs}"

mcp:
  timeout: "${MCP_TIMEOUT:30}"
  max_connections: "${MCP_MAX_CONNECTIONS:100}"
```

## API 接口

### 核心接口

#### 认证
```http
# 用户登录
POST /api/v1/auth/login
{
  "username": "admin",
  "password": "admin123"
}

# 获取用户信息
GET /api/v1/auth/me
Authorization: Bearer <token>
```

#### MCP 工具管理
```http
# 获取工具列表
GET /api/v1/tools

# 调用工具
POST /api/v1/tools/call
{
  "tool_name": "file_reader",
  "arguments": {"path": "./example-file.txt"}
}

# 添加工具
POST /api/v1/tools
{
  "name": "custom_tool",
  "description": "自定义工具",
  "command": "python script.py"
}
```

#### MCP 服务管理
```http
# 获取 MCP 服务列表
GET /api/v1/mcp/services

# MCP 代理请求
POST /api/v1/mcp/proxy
{
  "method": "tools/call",
  "params": {
    "name": "tool_name",
    "arguments": {}
  }
}
```

#### 系统管理
```http
# 系统状态
GET /api/v1/system/status

# 文件上传
POST /api/v1/system/upload
Content-Type: multipart/form-data
```

### WebSocket 接口

```javascript
// MCP 实时通信
const ws = new WebSocket('ws://localhost:8000/ws/mcp');

ws.send(JSON.stringify({
  "jsonrpc": "2.0",
  "method": "tools/list",
  "params": {}
}));
```

### API 文档

启动服务后访问：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 开发指南

### 开发环境设置

```bash
# 1. 安装开发依赖
uv pip install -r requirements.txt
uv pip install -e .

# 2. 安装代码质量工具
uv pip install black flake8 mypy pytest pytest-asyncio

# 3. 设置预提交钩子
pre-commit install
```

### 代码规范

```bash
# 代码格式化
black app/ tests/

# 代码检查
flake8 app/ tests/

# 类型检查
mypy app/

# 运行测试
pytest tests/ -v
```

### 架构设计

#### 分层架构
```
API Layer (app/api/)
├── 路由定义和请求处理
├── 参数验证和响应格式化
└── 权限控制和中间件

Service Layer (app/services/)
├── 业务逻辑实现
├── 数据处理和转换
└── 外部服务集成

Model Layer (app/models/)
├── 数据库模型定义
├── 关系映射配置
└── 数据验证规则

Core Layer (app/core/)
├── 基础设施组件
├── 配置和依赖管理
└── 统一工具和中间件
```

#### 核心组件

**统一配置管理器**
```python
from app.core.unified_config_manager import config_manager

# 获取配置
db_url = config_manager.get("database.url")
log_level = config_manager.get("logging.level")

# 环境变量覆盖
config_manager.set_env_override("DEBUG", "true")
```

**服务注册表**
```python
from app.core.service_registry import service_registry

# 注册服务
service_registry.register("mcp_service", MCPService())

# 获取服务
mcp_service = service_registry.get("mcp_service")
```

**统一日志系统**
```python
from app.core.unified_logging import get_logger

logger = get_logger(__name__)
logger.info("Service started", extra={"service": "mcp"})
```

### 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定模块测试
pytest tests/test_api/ -v
pytest tests/test_services/ -v

# 生成覆盖率报告
pytest --cov=app --cov-report=html tests/

# 异步测试
pytest -v tests/test_services/test_mcp_service.py
```

### 数据库管理

```bash
# 创建迁移文件
alembic revision --autogenerate -m "Add new table"

# 执行迁移
alembic upgrade head

# 回滚到上一版本
alembic downgrade -1

# 查看迁移状态
alembic current
alembic history

# 重置数据库（开发环境）
rm data/mcps.db
alembic upgrade head
```

## MCP 服务架构

### 协议支持
- **STDIO**: 标准输入输出
- **HTTP**: RESTful API
- **WebSocket**: 实时通信

### 核心组件
- **统一服务**: 聚合多个 MCP 服务
- **代理服务**: 多协议转换和路由
- **工具管理**: 动态工具注册和调用

## 部署指南

### Docker 部署（推荐）
```bash
# 完整部署
docker-compose up -d

# 单独后端
docker build -t mcps-one-backend .
docker run -p 8000:8000 mcps-one-backend
```

### 生产环境
```bash
# 系统服务
sudo systemctl enable mcps-one
sudo systemctl start mcps-one

# Nginx 代理
location /api/ {
    proxy_pass http://127.0.0.1:8000;
}
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