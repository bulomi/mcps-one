# API 使用指南
MCPS.ONE 提供完整的 RESTful API 接口，支持所有核心功能的编程访问。

## API 基础信息

- **基础 URL**：`http://localhost:8000/api/v1`
- **数据格式**：JSON
- **认证方式**：暂无（开发阶段）

## 工具管理 API

### 获取工具列表

```http
GET /api/v1/tools/
```

**查询参数：**
- `page`：页码（默认：1）
- `size`：每页大小（默认：20）
- `category`：工具分类
- `status`：工具状态
- `search`：搜索关键词

**响应示例：**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "name": "file-manager",
        "display_name": "文件管理器",
        "description": "文件操作工具",
        "category": "utility",
        "status": "running",
        "port": 8101,
        "enabled": true
      }
    ],
    "total": 1,
    "page": 1,
    "size": 20
  }
}
```

### 添加工具

```http
POST /api/v1/tools/
```

**请求体：**
```json
{
  "name": "my-tool",
  "display_name": "我的工具",
  "description": "工具描述",
  "category": "utility",
  "command": "python -m my_tool",
  "working_directory": "/path/to/tool",
  "enabled": true
}
```

### 启动工具

```http
POST /api/v1/tools/{tool_id}/start
```

### 停止工具

```http
POST /api/v1/tools/{tool_id}/stop
```

### 删除工具

```http
DELETE /api/v1/tools/{tool_id}
```

## MCP 代理 API

### 获取代理状态

```http
GET /api/v1/mcp-proxy/status
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "running": true,
    "port": 8080,
    "connected_tools": 3,
    "active_connections": 1,
    "uptime": 3600
  }
}
```

### 启动代理服务

```http
POST /api/v1/mcp-proxy/start
```

### 停止代理服务

```http
POST /api/v1/mcp-proxy/stop
```

## MCP 统一服务 API

### 获取服务状态

```http
GET /api/v1/mcp-unified/service/status
```

### 切换服务模式

```http
POST /api/v1/mcp-unified/service/mode
```

**请求体：**
```json
{
  "enable_server": true,
  "enable_proxy": false
}
```

## 工具调用 API

### 调用工具

```http
POST /api/v1/mcp-agent/tools/{tool_name}/call
```

**请求体：**
```json
{
  "name": "function_name",
  "arguments": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

### 获取工具信息

```http
GET /api/v1/mcp-agent/tools/{tool_name}/info
```

## 配置管理 API

### 获取配置

```http
GET /api/v1/config
```

### 更新配置

```http
PUT /api/v1/config
```

**请求体：**
```json
{
  "mcp": {
    "server": {
      "host": "localhost",
      "port_start": 8100,
      "port_end": 8200
    },
    "proxy": {
      "host": "localhost",
      "port": 8080,
      "timeout": 30
    }
  }
}
```

## 错误处理

所有 API 都遵循统一的错误响应格式：

```json
{
  "success": false,
  "message": "错误描述",
  "error_code": "ERROR_CODE",
  "details": {
    "field": "具体错误信息"
  }
}
```

### 常见错误码

- `TOOL_NOT_FOUND`：工具不存在
- `TOOL_ALREADY_RUNNING`：工具已在运行
- `TOOL_START_FAILED`：工具启动失败
- `INVALID_PARAMETERS`：参数无效
- `SERVICE_UNAVAILABLE`：服务不可用

## SDK 示例

### JavaScript/TypeScript

```typescript
class MCPSClient {
  private baseURL: string;

  constructor(baseURL: string = 'http://localhost:8000/api/v1') {
    this.baseURL = baseURL;
  }

  async getTools() {
    const response = await fetch(`${this.baseURL}/tools/`);
    return response.json();
  }

  async startTool(toolId: number) {
    const response = await fetch(`${this.baseURL}/tools/${toolId}/start`, {
      method: 'POST'
    });
    return response.json();
  }
}
```

### Python

```python
import requests

class MCPSClient:
    def __init__(self, base_url="http://localhost:8000/api/v1"):
        self.base_url = base_url
    
    def get_tools(self):
        response = requests.get(f"{self.base_url}/tools/")
        return response.json()
    
    def start_tool(self, tool_id):
        response = requests.post(f"{self.base_url}/tools/{tool_id}/start")
        return response.json()
```

## 限制和注意事项

1. **并发限制**：同时最多支持 100 个并发请求
2. **超时设置**：API 请求超时时间为 30 秒
3. **数据大小**：请求体最大 10MB
4. **认证**：当前版本暂不需要认证，生产环境请配置适当的安全措施