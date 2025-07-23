"""服务层模块 - 重构后的模块化结构"""

# 新的模块化导入
from .base import BaseService, MCPBaseService, CacheService, ErrorHandler
from .mcp import MCPService, MCPSServer, MCPProxyServer, MCPUnifiedService, MCPAgentService
from .system import SystemService, LogService  # ConfigManager 已弃用
from .tools import ToolService, ToolRegistry
# 任务和会话管理功能已移除
from .users import UserService, EmailService
from .integrations import ProxyService, RequestRouter, WebhookService

# 向后兼容性导入（保持原有导入路径可用）
try:
    # 如果有其他模块仍在使用旧的导入路径，这些导入将继续工作
    pass
except ImportError:
    pass

__all__ = [
    # 基础服务
    'BaseService',
    'MCPBaseService',
    'CacheService',
    'ErrorHandler',
    # MCP服务
    'MCPService',
    'MCPSServer',
    'MCPProxyServer',
    'MCPUnifiedService',
    'MCPAgentService',
    # 系统服务
    'SystemService',
    'LogService',
    # 'ConfigManager',  # 已弃用
    # 工具服务
    'ToolService',
    'ToolRegistry',
    # 任务和会话管理功能已移除
    # 用户服务
    'UserService',
    'EmailService',
    # 集成服务
    'ProxyService',
    'RequestRouter',
    'WebhookService'
]
