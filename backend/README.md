# MCPS.ONE Backend

MCPS.ONE 后端服务 - MCP (Model Context Protocol) 服务器管理平台的后端 API。

## 项目简介

MCPS.ONE 是一个用于管理和监控 MCP 服务器的平台，提供了完整的工具管理、系统监控、日志记录和备份功能。

## 功能特性

### 核心功能
- 🔧 **工具管理**: MCP 工具的创建、配置、启动、停止和监控
- 📊 **系统监控**: 实时系统状态监控和性能指标
- 📝 **日志管理**: 系统日志、操作日志和 MCP 协议日志的记录和查询
- 💾 **数据备份**: 自动和手动数据库备份，支持压缩和恢复
- 🔐 **安全认证**: 用户认证和权限管理
- 🌐 **RESTful API**: 完整的 REST API 接口

### 技术特性
- ⚡ **高性能**: 基于 FastAPI 的异步架构
- 🗄️ **数据持久化**: SQLAlchemy ORM + SQLite/PostgreSQL
- 🔄 **自动迁移**: Alembic 数据库迁移管理
- 📈 **可扩展**: 模块化设计，易于扩展
- 🛡️ **异常处理**: 完善的错误处理和日志记录
- 🔍 **API 文档**: 自动生成的 OpenAPI 文档

## 项目结构

```
backend/
├── alembic/                 # 数据库迁移脚本
│   ├── env.py              # Alembic 环境配置
│   └── script.py.mako      # 迁移脚本模板
├── app/                     # 应用主目录
│   ├── api/                # API 路由
│   │   ├── __init__.py     # API 路由注册
│   │   ├── tools.py        # 工具管理 API
│   │   ├── system.py       # 系统管理 API
│   │   └── logs.py         # 日志管理 API
│   ├── core/               # 核心配置
│   │   ├── config.py       # 应用配置
│   │   └── database.py     # 数据库配置
│   ├── models/             # 数据模型
│   │   ├── __init__.py     # 模型注册
│   │   ├── tool.py         # 工具模型
│   │   ├── system.py       # 系统模型
│   │   └── log.py          # 日志模型
│   ├── schemas/            # Pydantic 模式
│   │   ├── __init__.py     # 模式注册
│   │   ├── tool.py         # 工具模式
│   │   ├── system.py       # 系统模式
│   │   └── log.py          # 日志模式
│   ├── services/           # 业务逻辑服务
│   │   ├── __init__.py     # 服务注册
│   │   ├── tool_service.py # 工具服务
│   │   ├── mcp_service.py  # MCP 协议服务
│   │   ├── system_service.py # 系统服务
│   │   ├── log_service.py  # 日志服务
│   │   └── backup_service.py # 备份服务
│   ├── utils/              # 工具函数
│   │   ├── __init__.py     # 工具函数注册
│   │   ├── exceptions.py   # 自定义异常
│   │   └── helpers.py      # 辅助函数
│   └── __init__.py         # 应用包初始化
├── alembic.ini             # Alembic 配置文件
├── main.py                 # 应用入口文件
├── requirements.txt        # 依赖包列表
└── README.md              # 项目说明文档
```

## 快速开始

### 环境要求

- Python 3.8+
- pip 或 poetry
- SQLite (默认) 或 PostgreSQL (可选)

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd MCPS.ONE/backend
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/macOS
   source venv/bin/activate
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **配置环境变量**
   ```bash
   # 复制环境变量模板
   cp .env.example .env
   
   # 编辑配置文件
   # 设置数据库连接、日志级别等配置
   ```

5. **初始化数据库**
   ```bash
   # 创建迁移
   alembic revision --autogenerate -m "Initial migration"
   
   # 执行迁移
   alembic upgrade head
   ```

6. **启动服务**
   ```bash
   # 开发模式
   python main.py
   
   # 或使用 uvicorn
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

### 访问服务

- **API 文档**: http://localhost:8000/docs
- **ReDoc 文档**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health
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

### 工具管理 API

- `GET /api/v1/tools` - 获取工具列表
- `POST /api/v1/tools` - 创建工具
- `GET /api/v1/tools/{tool_id}` - 获取工具详情
- `PUT /api/v1/tools/{tool_id}` - 更新工具
- `DELETE /api/v1/tools/{tool_id}` - 删除工具
- `POST /api/v1/tools/{tool_id}/start` - 启动工具
- `POST /api/v1/tools/{tool_id}/stop` - 停止工具
- `POST /api/v1/tools/{tool_id}/restart` - 重启工具
- `GET /api/v1/tools/{tool_id}/status` - 获取工具状态

### 系统管理 API

- `GET /api/v1/system/config` - 获取系统配置
- `PUT /api/v1/system/config` - 更新系统配置
- `GET /api/v1/system/info` - 获取系统信息
- `GET /api/v1/system/status` - 获取系统状态
- `GET /api/v1/system/health` - 健康检查
- `POST /api/v1/system/backups` - 创建备份
- `GET /api/v1/system/backups` - 获取备份列表

### 日志管理 API

- `GET /api/v1/logs/system` - 获取系统日志
- `GET /api/v1/logs/operations` - 获取操作日志
- `GET /api/v1/logs/mcp` - 获取 MCP 日志
- `GET /api/v1/logs/stats` - 获取日志统计
- `DELETE /api/v1/logs/cleanup` - 清理日志

## 开发指南

### 代码规范

- 使用 Black 进行代码格式化
- 使用 Flake8 进行代码检查
- 使用 MyPy 进行类型检查
- 遵循 PEP 8 编码规范

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_tools.py

# 运行测试并生成覆盖率报告
pytest --cov=app tests/
```

### 代码检查

```bash
# 代码格式化
black app/

# 代码检查
flake8 app/

# 类型检查
mypy app/
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