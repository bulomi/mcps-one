# MCP工具自动发现与动态加载系统

## 概述

本系统实现了完整的MCP（Model Context Protocol）工具自动发现、动态加载和管理功能。通过智能扫描、配置监控、健康检查和数据库同步，实现了工具的全生命周期自动化管理。

## 核心功能

### 1. 工具自动发现

- **智能扫描**: 自动扫描指定目录，识别潜在的MCP工具
- **多格式支持**: 支持Python、Node.js、Shell脚本等多种工具格式
- **元数据提取**: 自动提取工具描述、版本信息等元数据
- **增量发现**: 只处理新增和变更的工具，提高效率

### 2. 动态加载与管理

- **热加载**: 无需重启服务即可加载新发现的工具
- **实例管理**: 支持工具的启动、停止、重启操作
- **状态跟踪**: 实时监控工具运行状态和健康状况
- **自动重启**: 工具异常时自动重启，确保服务可用性

### 3. 配置文件监控

- **实时监控**: 监控多个配置文件的变化
- **自动重载**: 配置变更时自动重新加载
- **触发发现**: 配置变更时自动触发工具发现
- **错误处理**: 配置错误时提供详细的错误信息

### 4. 健康检查机制

- **进程监控**: 检查工具进程是否正常运行
- **状态评估**: 评估工具的健康状态
- **自动恢复**: 检测到问题时自动尝试恢复
- **性能监控**: 监控CPU、内存使用情况

### 5. 数据库同步

- **持久化存储**: 工具配置存储在数据库中
- **启动加载**: 服务启动时自动从数据库加载工具
- **双向同步**: 内存和数据库之间的双向同步
- **事务安全**: 确保数据一致性

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP代理服务                              │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   工具注册中心   │  │   配置监控器     │  │   健康检查器     │ │
│  │                │  │                │  │                │ │
│  │ • 工具发现      │  │ • 文件监控      │  │ • 进程检查      │ │
│  │ • 动态加载      │  │ • 自动重载      │  │ • 状态评估      │ │
│  │ • 实例管理      │  │ • 触发发现      │  │ • 自动恢复      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   数据库服务     │  │   API接口       │  │   日志系统      │ │
│  │                │  │                │  │                │ │
│  │ • 配置存储      │  │ • RESTful API  │  │ • 结构化日志    │ │
│  │ • 状态持久化    │  │ • WebSocket     │  │ • 错误追踪      │ │
│  │ • 事务管理      │  │ • 事件通知      │  │ • 性能监控      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 使用指南

### 1. 基本配置

```python
from app.services.tool_registry import ToolRegistry

# 创建工具注册中心
tool_registry = ToolRegistry(
    auto_discovery_enabled=True,  # 启用自动发现
    discovery_interval=300        # 发现间隔（秒）
)

# 初始化并启动
await tool_registry.initialize()
await tool_registry.start()
```

### 2. 手动触发工具发现

```python
# 发现指定路径的工具
discovery_result = await tool_registry.discover_tools(
    scan_paths=["/path/to/tools", "/another/path"],
    recursive=True
)

print(f"发现 {len(discovery_result.new_tools)} 个新工具")
print(f"更新 {len(discovery_result.updated_tools)} 个工具")
```

### 3. 工具管理操作

```python
# 获取所有工具
all_tools = tool_registry.get_all_tools()

# 获取活跃工具
active_tools = tool_registry.get_active_tools()

# 获取工具状态
status = tool_registry.get_status()

# 同步工具到数据库
await tool_registry.sync_tool_to_database("tool_name")
```

### 4. API接口使用

```bash
# 触发工具发现
curl -X POST http://localhost:8000/api/tools/discover

# 获取工具列表
curl http://localhost:8000/api/tools

# 获取工具状态
curl http://localhost:8000/api/tools/status

# 启动工具
curl -X POST http://localhost:8000/api/tools/start \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "example_tool"}'
```

## 配置文件格式

### 工具配置文件 (mcp_tools.json)

```json
{
  "tools": {
    "example_tool": {
      "name": "example_tool",
      "display_name": "示例工具",
      "description": "这是一个示例MCP工具",
      "command": "python /path/to/tool.py",
      "enabled": true,
      "auto_start": false,
      "tags": ["example", "demo"],
      "health_check": {
        "enabled": true,
        "interval": 30,
        "timeout": 10
      },
      "environment": {
        "TOOL_ENV": "production"
      }
    }
  }
}
```

### 扫描路径配置

默认扫描路径：
- `{DATA_DIR}/tools`
- `./tools`
- `~/.mcp/tools`
- `/usr/local/bin` (Linux/macOS)
- `/opt/mcp/tools` (Linux)

## 工具识别规则

系统使用以下规则识别MCP工具：

### 1. 文件扩展名
- `.py` - Python脚本
- `.js`, `.ts` - Node.js脚本
- `.sh` - Shell脚本
- `.exe` - Windows可执行文件
- `.jar` - Java应用

### 2. 文件名模式
包含以下关键词的文件：
- `mcp`
- `server`
- `tool`
- `agent`

### 3. 文件内容检查
文件内容包含以下关键词：
- `mcp`
- `Model Context Protocol`
- `stdio`
- `tools/list`

### 4. 可执行权限
具有可执行权限的文件

## 健康检查机制

### 检查项目

1. **进程存在性**: 检查工具进程是否在运行
2. **响应性测试**: 发送ping请求测试工具响应
3. **资源使用**: 监控CPU和内存使用情况
4. **错误计数**: 跟踪工具错误次数
5. **运行时间**: 检查工具运行时长

### 状态定义

- `HEALTHY`: 工具运行正常
- `UNHEALTHY`: 工具存在问题
- `STARTING`: 工具正在启动
- `UNKNOWN`: 无法确定状态
- `FAILED`: 工具启动失败

### 自动恢复策略

1. **重启限制**: 最多重启3次
2. **重启间隔**: 指数退避策略
3. **失败处理**: 超过重启限制后标记为失败
4. **通知机制**: 发送状态变更通知

## 性能优化

### 1. 扫描优化
- 使用异步I/O减少阻塞
- 并行扫描多个目录
- 缓存扫描结果
- 增量扫描策略

### 2. 内存管理
- 工具实例池化
- 定期清理无用实例
- 内存使用监控
- 垃圾回收优化

### 3. 数据库优化
- 批量操作减少I/O
- 连接池管理
- 索引优化
- 事务合并

## 监控与日志

### 日志级别
- `DEBUG`: 详细调试信息
- `INFO`: 一般信息
- `WARNING`: 警告信息
- `ERROR`: 错误信息
- `CRITICAL`: 严重错误

### 监控指标
- 工具发现数量
- 工具启动成功率
- 健康检查通过率
- 平均响应时间
- 资源使用情况

### 告警机制
- 工具启动失败告警
- 健康检查失败告警
- 资源使用过高告警
- 配置错误告警

## 测试

### 运行测试

```bash
# 运行工具发现测试
python test_tool_discovery.py

# 运行单元测试
pytest tests/test_tool_registry.py

# 运行集成测试
pytest tests/test_integration.py
```

### 测试覆盖
- 工具发现功能
- 配置文件监控
- 健康检查机制
- 数据库同步
- API接口
- 错误处理

## 故障排除

### 常见问题

1. **工具发现失败**
   - 检查扫描路径是否存在
   - 确认文件权限设置
   - 查看日志错误信息

2. **工具启动失败**
   - 检查工具命令是否正确
   - 确认依赖环境是否安装
   - 查看工具错误输出

3. **健康检查失败**
   - 检查工具进程状态
   - 确认网络连接正常
   - 调整健康检查参数

4. **数据库同步问题**
   - 检查数据库连接
   - 确认权限设置
   - 查看事务日志

### 调试技巧

1. **启用详细日志**
   ```python
   logging.getLogger('app.services.tool_registry').setLevel(logging.DEBUG)
   ```

2. **手动测试工具**
   ```bash
   python /path/to/tool.py --help
   ```

3. **检查配置文件**
   ```bash
   python -m json.tool config.json
   ```

## 扩展开发

### 自定义工具识别器

```python
class CustomToolDetector:
    async def is_mcp_tool(self, file_path: Path) -> bool:
        # 自定义识别逻辑
        return True
    
    async def extract_metadata(self, file_path: Path) -> dict:
        # 自定义元数据提取
        return {}

# 注册自定义识别器
tool_registry.register_detector(CustomToolDetector())
```

### 自定义健康检查

```python
class CustomHealthChecker:
    async def check_health(self, instance: ToolInstance) -> ToolHealthStatus:
        # 自定义健康检查逻辑
        return ToolHealthStatus.HEALTHY

# 注册自定义健康检查器
tool_registry.register_health_checker(CustomHealthChecker())
```

## 版本历史

- **v1.0.0**: 基础工具管理功能
- **v1.1.0**: 添加自动发现功能
- **v1.2.0**: 完善健康检查机制
- **v1.3.0**: 增加配置文件监控
- **v1.4.0**: 实现数据库同步
- **v1.5.0**: 性能优化和错误处理改进

## 贡献指南

1. Fork项目仓库
2. 创建功能分支
3. 编写测试用例
4. 提交代码变更
5. 创建Pull Request

## 许可证

MIT License - 详见LICENSE文件

## 联系方式

- 项目主页: https://github.com/your-org/mcps-one
- 问题反馈: https://github.com/your-org/mcps-one/issues
- 邮箱: support@mcps-one.com