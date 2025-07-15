# MCPS.ONE

<div align="center">

![Version](https://img.shields.io/badge/version-v1.0.1-brightgreen)
![MCPS.ONE](https://img.shields.io/badge/MCPS.ONE-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![Vue](https://img.shields.io/badge/vue-3.x-green)
![FastAPI](https://img.shields.io/badge/fastapi-latest-teal)

**一个简洁、现代化的 MCP (Model Context Protocol) 工具管理系统**

专为个人开发者设计，提供可视化的 MCP 工具配置和管理界面

[功能特性](#功能特性) • [快速开始](#快速开始) • [文档](#文档) • [贡献](#贡献)

</div>

## 🎯 项目简介

MCPS.ONE是一个专为个人开发者设计的轻量级工具，用于管理和使用 MCP (Model Context Protocol) 工具。它提供了一个直观的 Web 界面，让您可以轻松配置、监控和使用各种 MCP 工具，无需复杂的命令行操作。

### 为什么选择这个项目？

- 🚀 **开箱即用**: 无需复杂配置，快速启动和使用
- 🎨 **现代化界面**: 基于 Vue 3 + Naive UI 的简洁美观界面
- 🔧 **可视化管理**: 图形化的工具配置和状态监控
- 📦 **轻量级部署**: SQLite 数据库，单文件部署
- 🔒 **安全可靠**: 进程隔离和完善的错误处理
- 🌟 **开源友好**: MIT 许可证，欢迎社区贡献

## ✨ 功能特性

### 🚀 MCP 统一服务架构 (v1.0.1 新增)
- **双模式运行**: 支持代理模式和服务端模式无缝切换
- **协议支持**: 完整的 MCP 协议实现，支持 stdio/http 传输
- **Cursor 集成**: 直接支持 Cursor IDE 的 MCP 服务端集成
- **HTTP API**: 提供 RESTful API 接口，支持第三方集成

### 🛠️ MCP 工具管理
- **工具配置**: 添加、编辑、删除 MCP 工具配置
- **分类管理**: 使用标签和分组组织工具
- **批量操作**: 导入导出工具配置
- **模板支持**: 预设常用工具模板
- **进程管理**: 自动启动、停止、重启工具进程

### 📊 健康检查和监控 (v1.0.1 新增)
- **实时监控**: 系统资源使用情况和服务状态
- **健康检查**: 自动检测服务健康状态和可用性
- **性能指标**: CPU、内存、磁盘使用率监控
- **服务状态**: MCP 服务端和代理服务状态跟踪
- **告警机制**: 异常状态自动告警和恢复

### 🔄 实时通信 (v1.0.1 新增)
- **WebSocket 支持**: 实时数据更新和状态同步
- **事件推送**: 系统事件和状态变化实时推送
- **双向通信**: 客户端与服务端实时交互
- **连接管理**: 自动重连和连接状态监控

### 📋 会话和任务管理
- **会话管理**: 创建、管理和跟踪 MCP 会话
- **任务调度**: 任务创建、执行和状态监控
- **历史记录**: 完整的会话和任务执行历史
- **状态跟踪**: 实时的执行状态和进度监控

### 🔧 配置管理优化 (v1.0.1 改进)
- **环境变量支持**: 完善的环境变量配置和验证
- **配置验证**: 自动配置文件格式和内容验证
- **热重载**: 配置更改无需重启服务
- **备份恢复**: 配置文件自动备份和恢复机制

### 🎨 用户界面
- **仪表板**: 系统概览和快速操作
- **统一管理**: MCP 统一服务管理界面
- **实时数据**: 基于 WebSocket 的实时数据展示
- **响应式设计**: 支持桌面和移动端
- **简洁设计**: 专注核心功能的简化界面

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- Git

### 方式一：Docker 部署（推荐）

```bash
# 克隆项目
git clone https://github.com/BuloMi/MCPS.ONE.git
cd MCPS.ONE

# 使用 Docker Compose 启动
docker-compose up -d

# 访问应用
open http://localhost:8000
```

### 方式二：MCP 统一服务模式（推荐）

```bash
# 克隆项目
git clone https://github.com/BuloMi/MCPS.ONE.git
cd MCPS.ONE

# 后端设置
cd backend
pip install -r requirements.txt

# 启动 MCP 统一服务（支持双模式）
python start_mcp_server.py --transport http --host 127.0.0.1 --port 8001

# 前端设置（新终端）
cd frontend
npm install
npm run dev

# 访问应用
open http://localhost:5173/mcp-unified
```

### 方式三：本地开发部署

```bash
# 克隆项目
git clone https://github.com/BuloMi/MCPS.ONE.git
cd MCPS.ONE

# 后端设置
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 前端设置（新终端）
cd frontend
npm install
npm run dev

# 访问应用
open http://localhost:5173
```

### 方式四：生产环境部署

```bash
# 构建前端
cd frontend
npm run build

# 启动 MCP 统一服务（生产模式）
cd backend
python start_mcp_server.py --transport http --host 0.0.0.0 --port 8001 --production

# 或启动传统后端服务
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# 访问应用
open http://localhost:8001  # MCP 统一服务
# 或
open http://localhost:8000  # 传统服务
```

## 📖 使用指南

### 添加第一个 MCP 工具

1. 打开应用并进入「工具管理」页面
2. 点击「添加工具」按钮
3. 填写工具信息：
   - **名称**: 工具的显示名称
   - **命令**: 启动工具的命令（如 `python tool.py`）
   - **工作目录**: 工具的工作目录路径
   - **环境变量**: 需要的环境变量（可选）
4. 点击「保存」完成添加
5. 在工具列表中点击「启动」按钮启动工具

### 使用 API 调用工具

```bash
# 获取可用工具列表
curl http://localhost:8000/api/mcp/tools

# 调用特定工具
curl -X POST http://localhost:8000/api/mcp/tools/my-tool \
  -H "Content-Type: application/json" \
  -d '{"method": "list_files", "params": {"path": "/"}}'
```

### 配置管理

```bash
# 导出工具配置
curl http://localhost:8000/api/tools/export > tools-config.json

# 导入工具配置
curl -X POST http://localhost:8000/api/tools/import \
  -H "Content-Type: application/json" \
  -d @tools-config.json
```

## 🏗️ 项目结构

```
MCPS.ONE/
├── backend/                 # FastAPI 后端
│   ├── api/                # API 路由
│   │   ├── tools.py        # 工具管理 API
│   │   ├── system.py       # 系统信息 API
│   │   ├── sessions.py     # 会话管理 API
│   │   ├── tasks.py        # 任务管理 API
│   │   └── logs.py         # 日志管理 API
│   ├── core/               # 核心业务逻辑
│   ├── models/             # 数据模型
│   ├── services/           # 业务服务层
│   └── main.py             # 应用入口
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── components/     # 组件
│   │   ├── views/          # 页面视图
│   │   │   ├── DashboardView.vue    # 仪表板
│   │   │   ├── ToolsView.vue        # 工具管理
│   │   │   ├── SessionsView.vue     # 会话管理
│   │   │   ├── TasksView.vue        # 任务管理
│   │   │   ├── LogsView.vue         # 日志查看
│   │   │   └── SystemSettingsView.vue # 系统设置
│   │   ├── stores/         # 状态管理
│   │   └── api/            # API 调用
│   └── package.json
├── docs/                   # 项目文档
│   ├── MENU_OPTIMIZATION_PLAN.md   # 菜单优化计划
│   └── MENU_CLEANUP_REPORT.md      # 清理报告
├── docker-compose.yml      # Docker 配置
├── README.md              # 项目说明

```

## 🔧 配置说明

### 环境变量

```bash
# 数据库配置
DATABASE_URL=sqlite:///./data/mcps.db

# 服务器配置
HOST=0.0.0.0
PORT=8000
DEBUG=false

# MCP 配置
MCP_TOOLS_DIR=./data/tools
MCP_LOGS_DIR=./data/logs
MAX_PROCESSES=10
```

### 配置文件

创建 `config.yaml` 文件进行详细配置：

```yaml
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
  timeout: 30
```

## 🧪 开发指南

### 开发环境设置

```bash
# 安装开发依赖
cd backend
pip install -r requirements-dev.txt

cd frontend
npm install
```

### 运行测试

```bash
# 后端测试
cd backend
pytest

# 前端测试
cd frontend
npm run test
```

### 代码格式化

```bash
# 后端代码格式化
cd backend
black .
isort .

# 前端代码格式化
cd frontend
npm run lint:fix
```

## 📚 API 文档

启动应用后，访问以下地址查看 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 主要 API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/tools` | GET | 获取工具列表 |
| `/api/v1/tools` | POST | 创建新工具 |
| `/api/v1/tools/{id}` | PUT | 更新工具配置 |
| `/api/v1/tools/{id}/start` | POST | 启动工具 |
| `/api/v1/tools/{id}/stop` | POST | 停止工具 |
| `/api/v1/sessions` | GET | 获取会话列表 |
| `/api/v1/sessions` | POST | 创建新会话 |
| `/api/v1/tasks` | GET | 获取任务列表 |
| `/api/v1/tasks` | POST | 创建新任务 |
| `/api/v1/system/stats` | GET | 获取系统统计信息 |
| `/api/v1/logs` | GET | 获取系统日志 |

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 如何贡献

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 贡献类型

- 🐛 Bug 修复
- ✨ 新功能开发
- 📝 文档改进
- 🎨 UI/UX 优化
- ⚡ 性能优化
- 🧪 测试用例

### 开发规范

- 遵循现有的代码风格
- 添加适当的测试用例
- 更新相关文档
- 使用 Conventional Commits 规范

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Python Web 框架
- [Vue 3](https://vuejs.org/) - 渐进式 JavaScript 框架
- [Naive UI](https://www.naiveui.com/) - Vue 3 组件库
- [MCP Protocol](https://modelcontextprotocol.io/) - 模型上下文协议

## 📞 支持

如果您遇到问题或有建议，请：

- 📋 [提交 Issue](https://github.com/BuloMi/MCPS.ONE/issues)
- 💬 [参与讨论](https://github.com/BuloMi/MCPS.ONE/discussions)
- 📧 发送邮件至 bulomi@example.com

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给我们一个 Star！**

[⬆ 回到顶部](#mcp工具管理系统---单用户开源版本)

</div>