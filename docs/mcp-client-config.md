# MCP客户端配置示例

本文档提供mcps-one项目的MCP客户端配置示例，支持Windows和macOS平台。

> **重要提示**: 请将示例中的路径占位符（如 `/path/to/your/project/`、`your-username` 等）替换为您的实际项目路径。

## 📋 配置说明

MCP客户端配置文件通常位于以下位置：
- **Claude Desktop**: `~/.config/claude/claude_desktop_config.json`
- **其他MCP客户端**: 根据具体客户端文档确定配置文件位置

## 🖥️ Windows平台配置

### 基本配置

```json
{
  "mcpServers": {
    "mcps-one": {
      "command": "/path/to/your/project/mcps-one/backend/.venv/Scripts/python.exe",
      "args": ["/path/to/your/project/mcps-one/backend/start_dynamic_mcp.py"],
      "env": {
        "PYTHONPATH": "/path/to/your/project/mcps-one/backend",
        "PYTHONIOENCODING": "utf-8",
        "MCP_SERVER_MODE": "server"
      }
    }
  }
}
```

### PowerShell路径配置

如果使用PowerShell风格的路径：

```json
{
  "mcpServers": {
    "mcps-one": {
      "command": "C:\\path\\to\\your\\project\\mcps-one\\backend\\.venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\your\\project\\mcps-one\\backend\\start_dynamic_mcp.py"],
      "env": {
        "PYTHONPATH": "C:\\path\\to\\your\\project\\mcps-one\\backend",
        "PYTHONIOENCODING": "utf-8",
        "MCP_SERVER_MODE": "server"
      }
    }
  }
}
```

## 🍎 macOS平台配置

### 基本配置

```json
{
  "mcpServers": {
    "mcps-one": {
      "command": "/Users/your-username/path/to/mcps-one/backend/.venv/bin/python",
      "args": ["/Users/your-username/path/to/mcps-one/backend/start_dynamic_mcp.py"],
      "env": {
        "PYTHONPATH": "/Users/your-username/path/to/mcps-one/backend",
        "PYTHONIOENCODING": "utf-8",
        "MCP_SERVER_MODE": "server"
      }
    }
  }
}
```

### 使用相对路径（推荐）

```json
{
  "mcpServers": {
    "mcps-one": {
      "command": "~/path/to/mcps-one/backend/.venv/bin/python",
      "args": ["~/path/to/mcps-one/backend/start_dynamic_mcp.py"],
      "env": {
        "PYTHONPATH": "~/path/to/mcps-one/backend",
        "PYTHONIOENCODING": "utf-8",
        "MCP_SERVER_MODE": "server"
      }
    }
  }
}
```

## 🔧 配置参数说明

| 参数 | 说明 | 必需 |
|------|------|------|
| `command` | Python解释器路径 | ✅ |
| `args` | MCP服务器启动脚本路径 | ✅ |
| `PYTHONPATH` | Python模块搜索路径 | ✅ |
| `PYTHONIOENCODING` | Python I/O编码设置 | ✅ |
| `MCP_SERVER_MODE` | MCP服务器运行模式 | ✅ |

## 📝 配置步骤

### 1. 确认项目路径

首先确认mcps-one项目的实际安装路径，并相应调整配置中的路径。

### 2. 检查虚拟环境

确保Python虚拟环境已正确创建并激活：

**Windows:**
```powershell
cd /path/to/your/project/mcps-one/backend
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS:**
```bash
cd ~/path/to/mcps-one/backend
python -m venv .venv
source .venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 测试配置

手动运行MCP服务器以验证配置：

```bash
python start_dynamic_mcp.py
```

## 🚨 常见问题

### 路径问题

- **Windows**: 使用正斜杠 `/` 或双反斜杠 `\\`
- **macOS**: 使用正斜杠 `/`，支持 `~` 表示用户目录

### 权限问题

- 确保Python解释器和脚本文件具有执行权限
- macOS可能需要：`chmod +x start_dynamic_mcp.py`

### 编码问题

- 设置 `PYTHONIOENCODING: "utf-8"` 确保中文字符正确处理

## 🔄 配置更新

修改配置后，需要重启MCP客户端以使配置生效。

---

**注意**: 请根据实际项目路径调整配置中的路径信息。