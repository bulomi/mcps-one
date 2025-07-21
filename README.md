# mcps-one

<div align="center">

![Version](https://img.shields.io/badge/version-v2.0.0--dev-orange)
![mcps-one](https://img.shields.io/badge/mcps-one-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![Vue](https://img.shields.io/badge/vue-3.x-green)
![FastAPI](https://img.shields.io/badge/fastapi-latest-teal)

**现代化 MCP 工具管理平台**

一个基于 Web 的 MCP (Model Context Protocol) 工具管理系统，提供可视化界面来管理、监控和使用各种 MCP 工具。

</div>

## 🎯 项目简介

mcps-one 是一个现代化的 MCP 工具管理平台，主要功能包括：

- **🔧 工具管理**: 添加、配置、启动和停止 MCP 工具
- **📊 实时监控**: 监控工具状态、系统资源使用情况
- **🌐 Web 界面**: 直观的管理界面，支持实时数据更新
- **🔄 会话管理**: 管理 MCP 工具的会话和任务
- **⚡ 高性能**: 基于 FastAPI + Vue 3 的现代化架构
- **🛡️ 稳定可靠**: 自动重启、健康检查、错误恢复

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- uv (推荐的 Python 包管理器)

### 部署方式

#### 方式一：本地开发

```bash
# 1. 安装 uv（如果尚未安装）
pip install uv

# 2. 克隆项目
git clone https://github.com/bulomi/mcps-one.git
cd mcps-one

# 3. 后端设置
cd backend

# 方式一：使用自动化脚本（推荐）
python setup_uv.py
# 然后按照提示激活虚拟环境并启动服务

# 方式二：手动设置
uv venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
uv pip install -r requirements.txt

# 4. 启动后端服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 5. 前端设置（新终端）
cd frontend
npm install
npm run dev

# 6. 访问应用
# 前端界面: http://localhost:5173
# 后端API: http://localhost:8000
# API文档: http://localhost:8000/docs
```

#### 方式二：Docker 部署

```bash
# 克隆项目
git clone https://github.com/bulomi/mcps-one.git
cd mcps-one

# 使用 Docker Compose 启动
docker-compose up -d

# 访问应用
# http://localhost:8000
```

## ✨ 主要功能

### 🔧 工具管理
- 添加、编辑、删除 MCP 工具配置
- 一键启动、停止工具进程
- 工具状态实时监控
- 支持批量操作和配置导入导出

### 📊 系统监控
- 实时系统资源监控（CPU、内存、磁盘）
- 工具进程状态和健康检查
- 性能指标统计和历史记录
- 异常告警和自动恢复

### 🌐 Web 界面
- 现代化的响应式设计
- 实时数据更新（WebSocket）
- 直观的操作界面
- 支持桌面和移动端访问

### 🔄 会话管理
- MCP 会话创建和管理
- 任务执行状态跟踪
- 会话历史记录
- 并发会话支持

## 📖 使用指南

### 客户端 MCP 配置

#### Cursor 客户端配置

在 Cursor 的设置中添加以下 MCP 服务器配置：

```json
{
  "mcpServers": {
    "mcps-one-server": {
      "command": "<YOUR_PROJECT_PATH>/venv/Scripts/python.exe",
      "args": ["<YOUR_PROJECT_PATH>/backend/start_mcp_server.py"],
      "cwd": "<YOUR_PROJECT_PATH>/backend",
      "env": {
        "PYTHONPATH": "<YOUR_PROJECT_PATH>/backend",
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

**重要说明：**
- `<YOUR_PROJECT_PATH>`: 请替换为你的实际项目路径（如：`D:/project/mcps-one`）
- `PYTHONIOENCODING`: 在 Windows 操作系统下必须设置为 `utf-8`，否则会出现中文乱码问题
- `command`: 请根据实际的虚拟环境路径调整 Python 解释器路径
- `cwd`: 工作目录必须设置为 `backend` 目录
- `PYTHONPATH`: 确保 Python 能正确导入项目模块

#### Claude Desktop 客户端配置

在 Claude Desktop 的配置文件中添加：

```json
{
  "mcpServers": {
    "mcps-one-server": {
      "command": "<YOUR_PROJECT_PATH>/venv/Scripts/python.exe",
      "args": ["<YOUR_PROJECT_PATH>/backend/start_mcp_server.py"],
      "cwd": "<YOUR_PROJECT_PATH>/backend",
      "env": {
        "PYTHONPATH": "<YOUR_PROJECT_PATH>/backend",
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

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

### 基本配置

```bash
# 复制环境变量配置文件
cp backend/.env.example backend/.env

# 编辑配置文件
# 设置数据库路径、日志级别等
```

### API 使用示例

```bash
# 获取可用工具列表
curl http://localhost:8000/api/v1/tools/

# 获取系统状态
curl http://localhost:8000/api/v1/system/stats/

# 查看 API 文档
# http://localhost:8000/docs
```


## ❓ 常见问题

### Q: 启动后端服务时提示找不到模块？

**A:** 确保在 `backend/` 目录下运行启动命令，并且已安装所有依赖：

```bash
cd backend
# 激活虚拟环境
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 安装依赖
uv pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Q: 前端无法连接到后端 API？

**A:** 检查以下几点：
1. 后端服务是否正常启动（默认端口 8000）
2. 前端配置的 API 地址是否正确
3. 防火墙是否阻止了端口访问

### Q: MCP 工具启动失败？

**A:** 常见原因及解决方案：
1. **命令路径错误**: 确保工具的启动命令和工作目录正确
2. **环境变量缺失**: 检查工具所需的环境变量是否已配置
3. **权限问题**: 确保工具文件有执行权限
4. **依赖缺失**: 确保工具的运行环境和依赖已安装

### Q: 如何查看详细的错误日志？

**A:** 日志文件位置：
- 应用日志: `backend/logs/app.log`
- MCP 工具日志: `backend/logs/mcp_tools.log`
- 系统日志: `backend/logs/system.log`

可以通过以下命令实时查看日志：

```bash
# 查看应用日志
tail -f backend/logs/app.log

# 查看 MCP 工具日志
tail -f backend/logs/mcp_tools.log
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

## 📚 更多信息

- **API 文档**: 启动应用后访问 http://localhost:8000/docs
- **详细配置**: 查看 `backend/README.md` 了解完整配置选项
- **开发指南**: 查看 `backend/README.md` 了解开发规范和测试方法

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