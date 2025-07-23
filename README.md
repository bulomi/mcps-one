# MCPS.ONE

<div align="center">

![Version](https://img.shields.io/badge/version-v1.0.0-blue)
![mcps-one](https://img.shields.io/badge/mcps-one-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![Vue](https://img.shields.io/badge/vue-3.x-green)
![FastAPI](https://img.shields.io/badge/fastapi-latest-teal)

**现代化 MCP 工具管理平台**

基于 FastAPI + Vue 3 的 MCP (Model Context Protocol) 工具统一管理系统，提供可视化界面来管理、监控和使用各种 MCP 工具。

</div>

## 🎯 项目简介

MCPS.ONE 是一个现代化的 MCP 工具管理平台，提供完整的 MCP 工具生命周期管理解决方案：

- **🔧 工具管理**: 可视化添加、配置、启动和停止 MCP 工具
- **🌐 Web 界面**: 基于 Naive UI 的现代化响应式管理界面
- **📚 文档系统**: 内置文档管理，支持 Markdown 渲染和目录导航
- **🔗 统一代理**: HTTP 代理和 MCP 服务端统一接入
- **⚡ 高性能**: 基于 FastAPI + Vue 3 + TypeScript 的现代化架构
- **🛡️ 稳定可靠**: 自动重启、健康检查、错误恢复机制

## 🚀 快速开始

### 环境要求

- **Python**: 3.11+ (推荐 3.11 或 3.12)
- **Node.js**: 18+ (推荐 LTS 版本)
- **包管理器**: uv (Python) + npm (Node.js)
- **操作系统**: Windows 10+, macOS 10.15+, Linux (Ubuntu 20.04+)

### 部署方式

#### 方式一：一键启动（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/bulomi/mcps-one.git
cd mcps-one

# 2. 一键启动（Windows）
start.bat

# 或者一键启动（Linux/macOS）
./start.sh

# 3. 访问应用
# 前端界面: http://localhost:5174
# 后端API: http://localhost:8000
# API文档: http://localhost:8000/docs
```

#### 方式二：手动启动

```bash
# 1. 后端设置
cd backend

# 安装 uv（如果尚未安装）
pip install uv

# 创建虚拟环境并安装依赖
uv venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
uv pip install -r requirements.txt

# 初始化数据库
alembic upgrade head

# 启动后端服务
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 2. 前端设置（新终端）
cd frontend
npm install
npm run dev
```

#### 方式三：Docker 部署

```bash
# 克隆项目
git clone https://github.com/bulomi/mcps-one.git
cd mcps-one

# 使用 Docker Compose 启动
docker-compose up -d

# 访问应用
# 前端界面: http://localhost:5174
# 后端API: http://localhost:8000
```

## 🏗️ 技术架构

### 后端架构

```
backend/
├── app/
│   ├── api/              # API 路由层
│   │   ├── tools.py      # 工具管理 API
│   │   ├── mcp_unified.py # MCP 统一服务 API
│   │   ├── mcp_proxy.py  # MCP 代理服务 API
│   │   └── docs.py       # 文档系统 API
│   ├── services/         # 业务逻辑层
│   │   ├── mcp/         # MCP 服务
│   │   ├── tools/       # 工具服务
│   │   └── system/      # 系统服务
│   ├── models/          # 数据模型
│   ├── schemas/         # 数据模式
│   └── core/           # 核心配置
└── requirements.txt     # 依赖管理
```

### 前端架构

```
frontend/
├── src/
│   ├── views/           # 页面组件
│   │   ├── ToolsView.vue      # 工具管理页面
│   │   ├── DocsView.vue       # 文档系统页面
│   │   ├── SystemSettingsView.vue # 系统设置页面
│   │   └── TutorialView.vue   # 教程页面
│   ├── components/      # 通用组件
│   ├── api/            # API 接口
│   ├── stores/         # 状态管理
│   └── utils/          # 工具函数
└── package.json        # 依赖管理
```


## 📚 文档和资源

- **API 文档**: http://localhost:8000/docs (Swagger UI)
- **后端详细说明**: [backend/README.md](backend/README.md)
- **前端 API 说明**: [frontend/src/api/README.md](frontend/src/api/README.md)
- **配置指南**: [docs/configuration.md](docs/configuration.md)
- **快速入门**: [docs/getting-started.md](docs/getting-started.md)
- **API 指南**: [docs/api-guide.md](docs/api-guide.md)


## 🛠️ 开发指南

### 开发环境设置

```bash
# 克隆项目
git clone https://github.com/bulomi/mcps-one.git
cd mcps-one

# 后端开发环境
cd backend
uv venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows
uv pip install -r requirements.txt

# 前端开发环境
cd frontend
npm install
npm run dev
```

### 代码规范

- **Python**: 使用 Black + isort 进行代码格式化
- **TypeScript**: 使用 ESLint + Prettier 进行代码检查
- **提交规范**: 使用 Conventional Commits 格式

### 测试

```bash
# 后端测试
cd backend
pytest

# 前端测试
cd frontend
npm test
```

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📞 联系方式

- 项目地址: [https://github.com/bulomi/mcps-one](https://github.com/bulomi/mcps-one)
- 问题反馈: [Issues](https://github.com/bulomi/mcps-one/issues)

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给我们一个 Star！**

</div>