"""数据模型包"""

from app.core.database import Base
from .tool import MCPTool, ToolCategory, ToolStatus, ToolType
from .system import SystemConfig, SystemInfo
from .log import SystemLog, OperationLog, MCPLog, LogLevel, LogCategory
# 会话和任务管理功能已移除
from .proxy import MCPProxy, ProxyCategory, ProxyTestResult, ProxyStatus, ProxyType, ProxyProtocol
from .user import User



__all__ = [
    # 数据库基类
    "Base",

    # 工具模型
    "MCPTool",
    "ToolCategory",
    "ToolStatus",
    "ToolType",

    # 系统模型
    "SystemConfig",
    "SystemInfo",

    # 日志模型
    "SystemLog",
    "OperationLog",
    "MCPLog",
    "LogLevel",
    "LogCategory",

    # 会话模型
    # "MCPSession", # 会话管理功能已移除
    # "SessionStatus", # 会话管理功能已移除
    # "SessionType", # 会话管理功能已移除

    # 任务模型 - 任务管理功能已移除
    # "MCPTask", # 任务管理功能已移除
    # "TaskStatus", # 任务管理功能已移除
    # "TaskType", # 任务管理功能已移除
    # "TaskPriority", # 任务管理功能已移除

    # 代理模型
    "MCPProxy",
    "ProxyCategory",
    "ProxyTestResult",
    "ProxyStatus",
    "ProxyType",
    "ProxyProtocol",

    # 用户模型
    "User",
]
