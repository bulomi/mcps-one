"""数据模型包"""

from app.core.database import Base
from .tool import MCPTool, ToolCategory, ToolStatus, ToolType
from .system import SystemConfig, SystemInfo
from .log import SystemLog, OperationLog, MCPLog, LogLevel, LogCategory
from .session import MCPSession, SessionStatus, SessionType
from .task import MCPTask, TaskStatus, TaskType, TaskPriority
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
    "MCPSession",
    "SessionStatus",
    "SessionType",

    # 任务模型
    "MCPTask",
    "TaskStatus",
    "TaskType",
    "TaskPriority",

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
