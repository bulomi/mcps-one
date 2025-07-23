
<div align="center">
<img src="frontend\src\assets\logo.png" align="center" alt="MCPS.ONE" width="200" height="200">
<br>

![Version](https://img.shields.io/badge/version-v2.0.1-blue)
![mcps-one](https://img.shields.io/badge/mcps-one-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![Vue](https://img.shields.io/badge/vue-3.x-green)
![FastAPI](https://img.shields.io/badge/fastapi-latest-teal)
![FastMCP](https://img.shields.io/badge/fastmcp-2.10.6-blue)

让 MCP 工具管理变得简单高效的可视化统一平台

</div>

## 🎯 功能介绍

MCPS.ONE 是一个 MCP 工具管理平台，解决 MCP 工具分散管理、配置复杂、监控困难等问题：

- **🔧 工具管理**: 统一管理各种 MCP 工具的配置、启停和监控
- **🌐 可视化界面**: 提供直观的 Web 管理界面
- **🔗 统一代理**: 提供统一的 HTTP 代理和 MCP 服务接入
- **⚡ 高性能**: 基于现代化技术栈构建
- **🛡️ 稳定可靠**: 具备自动重启和健康检查机制

## 🚀 安装部署

### 环境要求

- **Python**: 3.11+
- **Node.js**: 18+
- **操作系统**: Windows 10+, macOS 10.15+, Linux

### 快速启动

```bash
# 1. 克隆项目
git clone https://github.com/bulomi/mcps-one.git
cd mcps-one

# 2. 一键启动
# Windows
start.bat

# Linux/macOS
./start.sh

# 3. 访问应用
# 前端界面: http://localhost:5174
# 后端API: http://localhost:8000
# API文档: http://localhost:8000/docs
```

### Docker 部署

```bash
# 使用 Docker Compose 启动
docker-compose up -d
```

## ⚙️ 配置说明

系统配置文件位于以下位置：

- **后端配置**: `backend/config/app.yaml`
- **环境变量**: `backend/.env`
- **前端配置**: `frontend/vite.config.ts`

详细配置说明请参考 [配置指南](docs/configuration.md)


## 📚 相关文档

- **API 文档**: http://localhost:8000/docs
- **配置指南**: [docs/configuration.md](docs/configuration.md)
- **快速入门**: [docs/getting-started.md](docs/getting-started.md)
- **API 指南**: [docs/api-guide.md](docs/api-guide.md)
- **后端说明**: [backend/README.md](backend/README.md)
- **前端 API**: [frontend/src/api/README.md](frontend/src/api/README.md)

## 🙏 感谢名单

感谢以下开源项目和社区的支持：

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Python Web 框架
- [Vue.js](https://vuejs.org/) - 渐进式 JavaScript 框架
- [Naive UI](https://www.naiveui.com/) - Vue 3 组件库
- [MCP](https://modelcontextprotocol.io/) - Model Context Protocol 规范
- [FastMCP](https://github.com/jlowin/fastmcp) - 快速构建 MCP 服务器的 Python 库

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给我们一个 Star！**

项目地址: [https://github.com/bulomi/mcps-one](https://github.com/bulomi/mcps-one)

</div>