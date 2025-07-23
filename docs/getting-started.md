# 快速开始

欢迎使用 MCPS.ONE！这是一个强大的 MCP 工具管理平台。

## 什么是 MCPS.ONE？

MCPS.ONE 是一个专为 MCP (Model Context Protocol) 工具设计的管理平台，提供：

- 🛠️ **工具管理**：轻松添加、配置和管理 MCP 工具
- 🔄 **多种模式**：支持 MCP 服务模式和 FastMCP 代理模式
- 🌐 **Web 界面**：直观的 Web 管理界面
- 📊 **实时监控**：工具状态和性能监控
- 🔧 **API 接口**：完整的 RESTful API

## 快速安装

### 1. 克隆项目

```bash
git clone https://github.com/your-repo/MCPS.ONE.git
cd MCPS.ONE
```

### 2. 启动服务

#### Windows
```bash
.\start.bat
```

#### Linux/macOS
```bash
./start.sh
```

### 3. 访问界面

打开浏览器访问：http://localhost:3000

## 基本使用

### 添加 MCP 工具

1. 点击「添加工具」按钮
2. 填写工具基本信息
3. 配置启动命令
4. 保存并启动工具

### 选择运行模式

- **MCP 服务模式**：每个工具独立运行在不同端口
- **FastMCP 代理模式**：通过代理统一管理所有工具

## 下一步

- [详细配置指南](./configuration.md)
- [API 使用说明](./api-guide.md)
- [常见问题](./faq.md)