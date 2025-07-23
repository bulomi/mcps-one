# 配置指南

本文档详细介绍 MCPS.ONE 的各种配置选项。

## 系统配置

### 基础配置

系统的基础配置位于 `backend/.env` 文件中：

```env
# 数据库配置
DATABASE_URL=sqlite:///./data/mcps.db

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=true

# 日志配置
LOG_LEVEL=INFO
LOG_DIR=./logs
```

### MCP 配置

MCP 相关配置位于 `backend/.env.mcp` 文件中：

```env
# MCP 服务配置
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT_START=8100
MCP_SERVER_PORT_END=8200

# FastMCP 代理配置
FASTMCP_PROXY_HOST=localhost
FASTMCP_PROXY_PORT=8080
FASTMCP_PROXY_TIMEOUT=30
```

## 工具配置

### 添加工具

通过 Web 界面添加工具时，需要配置以下信息：

- **工具名称**：唯一标识符，建议使用小写字母和连字符
- **显示名称**：在界面中显示的友好名称
- **描述**：工具功能的简要说明
- **分类**：工具的分类标签
- **启动命令**：工具的完整启动命令
- **工作目录**：工具运行时的工作目录

### 命令配置示例

#### Python 工具
```bash
python -m your_mcp_tool
```

#### Node.js 工具
```bash
node your-mcp-tool/index.js
```

#### 可执行文件
```bash
./your-mcp-tool
```

## 运行模式配置

### MCP 服务模式

在此模式下，每个工具运行在独立的端口上：

- 端口范围：8100-8200（可配置）
- 连接方式：直接连接到工具端口
- 适用场景：单一客户端连接



### FastMCP 代理模式

在此模式下，所有工具通过代理统一管理：

- 代理端口：8080（可配置）
- 连接方式：连接到代理端口
- 适用场景：多客户端连接，统一管理

## 高级配置

### 性能优化
`config/app.yaml`
```yaml
performance:
  max_workers: 10
  timeout: 30
  cache_enabled: true
  cache_ttl: 300
```

### 安全配置
`config/app.yaml`
```yaml
security:
  enable_auth: false
  cors_origins: ["*"]
  rate_limit: 100
```

### 监控配置
`config/app.yaml`
```yaml
monitoring:
  enable_metrics: true
  metrics_port: 9090
  health_check_interval: 30
```

## MCP客户端配置

### Claude Desktop 配置

在 Claude Desktop 中配置 MCPS.ONE 服务，需要修改配置文件：

**Windows 配置文件位置：**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**macOS 配置文件位置：**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**配置示例：**
```json
{
  "mcpServers": {
    "mcps-one": {
      "command": "D:/project/mcps-one/backend/.venv/Scripts/python.exe",
      "args": ["D:/project/mcps-one/backend/start_dynamic_mcp.py"],
      "env": {
        "PYTHONPATH": "D:/project/mcps-one/backend",
        "PYTHONIOENCODING": "utf-8",
        "MCP_SERVER_MODE": "server"
      }
    }
  }
}
```

### 配置参数说明

- **command**: Python 可执行文件路径（虚拟环境中的 Python）
- **args**: 启动脚本路径
- **env**: 环境变量配置
  - `PYTHONPATH`: Python 模块搜索路径
  - `PYTHONIOENCODING`: 字符编码设置
  - `MCP_SERVER_MODE`: 服务模式（server 或 proxy）,缺省默认 server

### 其他MCP客户端配置

#### Continue.dev 配置

在 Continue.dev 的配置文件中添加：

```json
{
  "mcpServers": [
    {
      "name": "mcps-one",
      "command": "python",
      "args": ["D:/project/mcps-one/backend/start_dynamic_mcp.py"],
      "cwd": "D:/project/mcps-one/backend",
      "env": {
        "PYTHONPATH": "D:/project/mcps-one/backend",
        "PYTHONIOENCODING": "utf-8",
        "MCP_SERVER_MODE": "server"
      }
    }
  ]
}
```

#### Cline 配置

在 Cline 的设置中配置 MCP 服务器：

```json
{
  "mcpServers": {
    "mcps-one": {
      "command": "python",
      "args": ["start_dynamic_mcp.py"],
      "cwd": "D:/project/mcps-one/backend",
      "env": {
        "PYTHONPATH": "D:/project/mcps-one/backend",
        "PYTHONIOENCODING": "utf-8",
        "MCP_SERVER_MODE": "server"
      }
    }
  }
}
```

### 配置验证

配置完成后，可以通过以下方式验证：

1. **检查服务启动**：查看客户端日志，确认 MCPS.ONE 服务正常启动
2. **测试工具调用**：尝试调用 MCPS.ONE 提供的工具
3. **查看错误日志**：如果出现问题，检查客户端和服务端的错误日志

### 常见配置问题

1. **路径问题**：确保所有路径使用绝对路径
2. **权限问题**：确保 Python 可执行文件有执行权限
3. **环境变量**：确保 PYTHONPATH 正确设置
4. **虚拟环境**：确保使用正确的虚拟环境中的 Python

## 故障排除

### 常见问题

1. **工具启动失败**
   - 检查启动命令是否正确
   - 确认工作目录路径
   - 查看工具日志

2. **端口冲突**
   - 修改端口配置
   - 检查端口占用情况

3. **连接超时**
   - 增加超时时间
   - 检查网络连接

### 日志查看

- 系统日志：`logs/system.log`
- 工具日志：`logs/tools/`
- 错误日志：`logs/error.log`