# MCPS.ONE MCP 客户端配置指南

## 概述

MCPS.ONE 现在支持作为 MCP (Model Context Protocol) 服务端运行，允许支持 MCP 的客户端（如 Cursor、Claude Desktop 等）直接连接并使用已配置的 MCP 工具。

**重要说明**: MCPS.ONE MCP服务端不需要认证，可以直接连接使用。

## 功能特性

- **双模式运行**: 同时支持代理模式和服务端模式
- **自动启动**: 应用启动时自动启动 MCP 服务端
- **stdio 传输**: 支持标准输入输出协议，兼容大多数 MCP 客户端
- **工具聚合**: 将所有已配置的 MCP 工具统一暴露给客户端
- **动态发现**: 客户端可以动态发现和调用可用工具

## 配置步骤

### 1. 启动 MCPS.ONE 服务

确保 MCPS.ONE 后端服务正在运行：

```bash
cd d:\project\MCPS.ONE\backend
$env:PYTHONPATH="d:\project\MCPS.ONE\backend"
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. 配置 MCP 客户端

#### Cursor IDE 配置

在 Cursor 的设置中，添加以下 MCP 服务器配置：

```json
{
  "mcpServers": {
    "mcps-one": {
      "command": "python",
      "args": [
        "d:\\project\\MCPS.ONE\\backend\\start_mcp_server_standalone.py",
        "--transport",
        "stdio"
      ],
      "env": {
        "PYTHONPATH": "d:\\project\\MCPS.ONE\\backend"
      }
    }
  }
}```

#### Claude Desktop 配置

在 Claude Desktop 的配置文件中添加：

```json
{
  "mcpServers": {
    "mcps-one": {
      "command": "python",
      "args": [
        "d:\\project\\mcps-one\\backend\\start_mcp_server_standalone.py",
        "--transport",
        "stdio"
      ],
      "env": {
        "PYTHONPATH": "d:\\project\\mcps-one\\backend",
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}```

### 3. 认证说明

**MCPS.ONE MCP服务端无需认证**：

- 不需要API密钥或访问令牌
- 不需要用户名和密码
- 直接通过stdio协议连接即可
- 所有已配置的MCP工具都会自动暴露给客户端

这是因为MCPS.ONE MCP服务端设计为本地工具聚合器，主要用于简化多个MCP工具的管理和使用。

### 4. 验证连接

配置完成后，重启 MCP 客户端。客户端应该能够：

1. 连接到 MCPS.ONE MCP 服务端
2. 发现可用的工具
3. 调用工具功能

## 可用工具

MCPS.ONE MCP 服务端提供以下工具：

### 核心工具

- **list_available_tools**: 列出所有可用的 MCP 工具
- **call_tool**: 调用指定的 MCP 工具功能
- **get_tool_capabilities**: 获取特定工具的能力
- **start_tool**: 启动指定的 MCP 工具
- **stop_tool**: 停止指定的 MCP 工具
- **get_service_metrics**: 获取服务性能指标

### 工具管理

所有在 MCPS.ONE 中配置的 MCP 工具都会自动暴露给客户端，包括：

- 文件系统工具
- 网络请求工具
- 数据库工具
- API 集成工具
- 自定义工具

## 配置选项

### 环境变量

可以通过以下环境变量调整 MCP 服务端行为：

- `MCP_SERVICE_MODE`: 服务模式 (proxy, server, both, disabled)
- `MCP_SERVER_TRANSPORT`: 传输协议 (stdio, http)
- `MCP_AUTO_START`: 是否自动启动 (true, false)
- `MCP_SERVER_LOG_LEVEL`: 日志级别 (DEBUG, INFO, WARNING, ERROR)

### 配置文件

也可以在 `app/core/config.py` 中修改默认配置：

```python
# MCP统一服务配置
MCP_SERVICE_MODE: str = "both"  # 双模式
MCP_AUTO_START: bool = True     # 自动启动
MCP_SERVER_TRANSPORT: str = "stdio"  # stdio传输
```

## 故障排除

### 常见问题

1. **连接失败**
   - 确保 MCPS.ONE 后端服务正在运行
   - 检查 PYTHONPATH 环境变量设置
   - 验证 Python 路径是否正确

2. **工具不可用**
   - 检查工具是否在 MCPS.ONE 中正确配置
   - 确认工具状态为 "运行中"
   - 查看服务端日志获取详细错误信息

3. **权限问题**
   - 确保 Python 有执行权限
   - 检查文件路径访问权限

### 调试模式

启用调试模式获取更多日志信息：

```bash
# 设置日志级别为 DEBUG
python start_mcp_server_standalone.py --transport stdio --log-level DEBUG
```

## 高级用法

### HTTP 模式

如果需要使用 HTTP 传输协议：

```json
{
  "mcpServers": {
    "mcps-one-http": {
      "command": "python",
      "args": [
        "d:\\project\\MCPS.ONE\\backend\\start_mcp_server_standalone.py",
        "--transport",
        "http",
        "--host",
        "127.0.0.1",
        "--port",
        "8001"
      ],
      "env": {
        "PYTHONPATH": "d:\\project\\MCPS.ONE\\backend"
      }
    }
  }
}```

### 自定义配置

可以通过修改配置文件自定义 MCP 服务端行为：

- 调整连接超时时间
- 设置最大连接数
- 配置健康检查间隔
- 启用性能指标收集

## 总结

通过以上配置，您可以在支持 MCP 的客户端中直接使用 MCPS.ONE 作为统一的工具服务提供者，无需单独配置每个 MCP 工具。这大大简化了工具管理和使用流程。

如有问题，请查看 MCPS.ONE 的日志输出或联系技术支持。