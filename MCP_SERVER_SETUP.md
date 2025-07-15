# MCPS.ONE MCP 服务端配置指南

## 概述

MCPS.ONE MCP 服务端是一个功能强大的 Model Context Protocol (MCP) 服务端实现，支持多种传输协议、健康检查、指标收集和容器化部署。

## 🚀 新功能特性

### ✅ 已实现的改进

1. **增强的配置管理**
   - 完整的环境变量支持
   - 配置验证和错误处理
   - 灵活的传输协议配置
   - 新增 MCP 服务端核心配置项
   - 实现 `validate_mcp_server_config()` 配置验证
   - 实现 `get_mcp_server_config()` 配置获取

2. **健康检查和监控**
   - 内置健康检查端点
   - 详细的性能指标收集
   - 实时状态监控
   - 新增 `health_check` MCP 工具
   - 新增 `get_metrics` MCP 工具
   - 服务器运行时间、请求统计、错误计数

3. **改进的错误处理**
   - 结构化错误日志
   - 详细的异常追踪
   - 优雅的错误恢复
   - 使用 `traceback` 模块记录详细错误
   - 用户友好的错误消息

4. **容器化支持**
   - Docker 配置文件
   - Docker Compose 编排
   - 生产就绪的部署配置
   - 多阶段构建优化
   - 健康检查配置

5. **测试覆盖**
   - 单元测试框架
   - 配置验证测试
   - 模拟测试环境
   - 使用 `pytest` 和 `pytest-asyncio`
   - 测试覆盖率达到核心功能

### 📊 改进成果

#### 配置管理新增项
- `MCP_SERVER_LOG_LEVEL`: 日志级别控制
- `MCP_SERVER_SHOW_BANNER`: 启动横幅显示
- `MCP_SERVER_STATELESS_HTTP`: 无状态 HTTP 模式
- `HEALTH_CHECK_ENABLED`: 启用健康检查
- `METRICS_ENABLED`: 启用指标收集
- `PROMETHEUS_ENABLED`: Prometheus 集成

#### 监控能力提升
- 实时健康检查提供服务状态可见性
- 详细指标收集支持性能分析（CPU、内存、磁盘使用）
- 错误计数帮助识别问题
- 工具状态分布统计

#### 测试结果
```
=============================== 10 passed, 36 warnings in 0.36s ===============================
```

#### 配置验证测试
```
✓ 配置验证通过
✓ 传输协议: stdio
✓ 主机地址: 127.0.0.1
✓ 端口: 8001
✓ 日志级别: INFO
```

## 📋 快速开始

### 1. 环境配置

```bash
# 复制环境变量配置文件
cp backend/.env.mcp.example backend/.env

# 编辑配置文件
nano backend/.env
```

### 2. 验证配置

```bash
cd backend
python start_mcp_server.py --validate-config
```

### 3. 启动服务端

#### 开发模式
```bash
# stdio 模式
python start_mcp_server.py --transport stdio

# HTTP 模式
python start_mcp_server.py --transport http --host 127.0.0.1 --port 8001
```

#### 生产模式 (Docker)
```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f mcp-server

# 健康检查
curl http://localhost:8001/health
```

## 🔧 配置选项

### 核心配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `MCP_SERVER_TRANSPORT` | `stdio` | 传输协议 (stdio/http) |
| `MCP_SERVER_HOST` | `127.0.0.1` | HTTP 模式主机地址 |
| `MCP_SERVER_PORT` | `8001` | HTTP 模式端口 |
| `MCP_SERVER_LOG_LEVEL` | `INFO` | 日志级别 |

### 高级配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `MCP_MAX_CONNECTIONS` | `10` | 最大连接数 |
| `MCP_CONNECTION_TIMEOUT` | `30` | 连接超时(秒) |
| `HEALTH_CHECK_ENABLED` | `true` | 启用健康检查 |
| `METRICS_ENABLED` | `true` | 启用指标收集 |

## 🔍 监控和调试

### 健康检查

```bash
# 检查服务状态
curl http://localhost:8000/health

# 使用 MCP 工具检查
python -c "from app.services.mcp_server import get_mcp_server; import asyncio; server = get_mcp_server(); print('Server ready')"
```

### 指标收集

```bash
# 获取详细指标
curl http://localhost:8000/metrics

# 查看服务端统计
python start_mcp_server.py --transport http &
sleep 5
curl -s http://localhost:8000 | jq '.server_info'
```

### 日志调试

```bash
# 启用调试日志
python start_mcp_server.py --log-level DEBUG

# 查看 Docker 日志
docker-compose logs -f --tail=100 mcp-server
```

## 🧪 测试

### 运行单元测试

```bash
cd backend
pip install pytest pytest-asyncio
pytest tests/test_mcp_server.py -v
```

### 集成测试

```bash
# 启动测试环境
docker-compose -f docker-compose.test.yml up -d

# 运行集成测试
pytest tests/integration/ -v
```

## 🐳 Docker 部署

### 开发环境

```bash
# 启动开发环境
docker-compose up -d

# 查看服务状态
docker-compose ps
```

### 生产环境

```bash
# 启动生产环境 (包含 Nginx)
docker-compose --profile production up -d

# 启动监控环境 (包含 Prometheus + Grafana)
docker-compose --profile monitoring up -d
```

## 🔒 安全配置

### 生产环境安全检查清单

- [ ] 更改默认的 `SECRET_KEY`
- [ ] 设置适当的 `ALLOWED_HOSTS`
- [ ] 启用 HTTPS (通过 Nginx)
- [ ] 配置防火墙规则
- [ ] 定期更新依赖包
- [ ] 启用访问日志
- [ ] 配置备份策略

## 📊 性能优化

### 推荐的生产配置

```env
# 性能优化配置
MCP_MAX_CONNECTIONS=50
MCP_CONNECTION_TIMEOUT=60
MCP_TOOL_STARTUP_TIMEOUT=120
MCP_HEALTH_CHECK_INTERVAL=60

# 日志优化
LOG_LEVEL="WARNING"
MCP_SERVER_LOG_LEVEL="WARNING"

# 资源限制
MCP_MAX_PROCESSES=20
```

## 🚨 故障排除

### 常见问题

1. **端口冲突**
   ```bash
   # 检查端口占用
   netstat -tulpn | grep :8000
   
   # 更改端口
   export MCP_SERVER_PORT=8002
   ```

2. **配置验证失败**
   ```bash
   # 验证配置
   python start_mcp_server.py --validate-config
   
   # 查看详细错误
   python start_mcp_server.py --log-level DEBUG --validate-config
   ```

3. **数据库连接问题**
   ```bash
   # 检查数据库文件权限
   ls -la data/mcps.db
   
   # 重新初始化数据库
   rm data/mcps.db
   python start_mcp_server.py --transport stdio
   ```

### 日志分析

```bash
# 查看错误日志
grep "ERROR" data/logs/*.log

# 分析性能指标
grep "metrics" data/logs/*.log | tail -10

# 监控连接状态
grep "connection" data/logs/*.log | tail -20
```

## 📈 下一步计划

### 优先级 1 (已完成)
- [x] 配置管理优化
- [x] 健康检查和监控
- [x] 错误处理改进
- [x] 单元测试
- [x] Docker 支持

### 优先级 2 (计划中)
- [ ] 自定义 host/port 支持
- [ ] 集成测试套件
- [ ] 性能基准测试
- [ ] API 文档生成
- [ ] 安全审计

### 优先级 3 (未来)
- [ ] 分布式部署支持
- [ ] 高可用配置
- [ ] 自动扩缩容
- [ ] 监控告警
- [ ] 备份恢复

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 编写测试
4. 提交更改
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

本指南将帮助您将 MCPS.ONE 配置为 MCP 服务端，让 Cursor、Claude Desktop 等支持 MCP 协议的客户端能够连接并自动发现已配置的 MCP 工具。

## 功能特性

- **统一入口**: 只需在客户端配置 MCPS.ONE 一个 MCP 服务，即可访问所有已配置的 MCP 工具
- **自动发现**: 客户端可以自动发现 MCPS.ONE 中已配置的所有 MCP 工具
- **动态代理**: MCPS.ONE 作为代理，将客户端请求转发给相应的 MCP 工具
- **工具管理**: 支持启动、停止、重启 MCP 工具
- **能力查询**: 可以查询每个工具的具体功能和参数

## 安装依赖

首先确保安装了必要的 MCP 协议依赖：

```bash
cd backend
pip install -r requirements.txt
```

## 启动 MCP 服务端

### 方法 1: 直接启动

```bash
cd backend
python start_mcp_server.py
```

### 方法 2: 使用模块启动

```bash
cd backend
python -m app.services.mcp_server --transport stdio
```

### 方法 3: HTTP 模式启动（用于调试）

```bash
cd backend
python -m app.services.mcp_server --transport http --host 127.0.0.1 --port 8001
```

## 客户端配置

### Cursor 配置

1. 打开 Cursor 设置
2. 找到 MCP 服务器配置部分
3. 添加以下配置：

```json
{
  "mcpServers": {
    "mcps-one": {
      "command": "python",
      "args": [
        "D:\\project\\MCPS.ONE\\backend\\start_mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "D:\\project\\MCPS.ONE\\backend"
      }
    }
  }
}
```

**注意**: 请将路径 `D:\\project\\MCPS.ONE\\backend` 替换为您的实际项目路径。

### Claude Desktop 配置

在 Claude Desktop 的配置文件中添加：

```json
{
  "mcpServers": {
    "mcps-one": {
      "command": "python",
      "args": [
        "/path/to/MCPS.ONE/backend/start_mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "/path/to/MCPS.ONE/backend"
      }
    }
  }
}
```

## 可用功能

配置完成后，客户端可以使用以下功能：

### 1. 查看所有可用工具

```
list_available_tools()
```

返回所有已配置且正在运行的 MCP 工具列表，包括每个工具的能力。

### 2. 调用工具功能

```
call_tool(tool_name="playwright-mcp", tool_function="playwright_navigate", arguments='{"url": "https://google.com"}')
```

### 3. 获取工具能力

```
get_tool_capabilities(tool_name="playwright-mcp")
```

### 4. 管理工具

```
# 启动工具
start_tool(tool_name="playwright-mcp")

# 停止工具
stop_tool(tool_name="playwright-mcp")
```

## 使用示例

### 示例 1: 使用 Playwright 进行网页操作

假设您已经在 MCPS.ONE 中配置了 `playwright-mcp` 工具，您可以在 Cursor 中这样使用：

```
用户: 帮我打开 Google 搜索 "AI" 关键词

助手: 我来帮您使用 Playwright 工具打开 Google 并搜索 "AI"。

首先，让我查看可用的工具：
call_tool(tool_name="playwright-mcp", tool_function="playwright_navigate", arguments='{"url": "https://google.com"}')

然后搜索 "AI"：
call_tool(tool_name="playwright-mcp", tool_function="playwright_fill", arguments='{"selector": "input[name=q]", "value": "AI"}')

最后点击搜索：
call_tool(tool_name="playwright-mcp", tool_function="playwright_click", arguments='{"selector": "input[type=submit]"}')
```

### 示例 2: 查看工具状态

```
用户: 显示所有可用的 MCP 工具

助手: 让我为您查看所有可用的 MCP 工具：
list_available_tools()
```

## 故障排除

### 1. 服务端启动失败

- 检查 Python 环境和依赖是否正确安装
- 确保数据库连接正常
- 查看错误日志

### 2. 客户端连接失败

- 检查配置文件中的路径是否正确
- 确保 Python 可执行文件路径正确
- 检查环境变量设置

### 3. 工具调用失败

- 确保目标 MCP 工具已启动
- 检查工具配置是否正确
- 查看 MCPS.ONE 后端日志

### 4. 权限问题

- 确保 Python 脚本有执行权限
- 检查文件路径访问权限

## 日志和调试

### 查看服务端日志

服务端日志会输出到 stderr，您可以重定向到文件：

```bash
python start_mcp_server.py 2> mcp_server.log
```

### 启用详细日志

在启动脚本中修改日志级别：

```python
logging.basicConfig(level=logging.DEBUG)
```

## 高级配置

### 自定义端口（HTTP 模式）

```bash
python -m app.services.mcp_server --transport http --port 8002
```

### 环境变量配置

您可以通过环境变量配置数据库连接等：

```bash
export DATABASE_URL="sqlite:///./mcps.db"
python start_mcp_server.py
```

## 注意事项

1. **路径配置**: 确保所有路径使用绝对路径
2. **Python 环境**: 确保客户端能够找到正确的 Python 环境
3. **依赖安装**: 确保所有必要的依赖都已安装
4. **工具状态**: 只有状态为 "running" 的工具才能被调用
5. **并发限制**: 注意工具的并发调用限制

## 支持的客户端

- Cursor
- Claude Desktop
- 其他支持 MCP 协议的 AI 客户端

通过这种方式，您只需要在客户端配置一次 MCPS.ONE，就可以访问所有已配置的 MCP 工具，大大简化了配置过程。