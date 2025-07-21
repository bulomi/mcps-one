"""MCPS.ONE 核心模块

这个模块包含了MCPS.ONE系统的核心基础设施组件：
- 统一配置管理系统
- 统一错误处理系统
- 统一日志系统
- 统一缓存系统
"""

# 统一配置管理
from .unified_config_manager import (
    get_unified_config_manager
)

# 统一错误处理
from .unified_error import (
    ErrorSeverity,
    ErrorCategory,
    ErrorContext,
    ErrorInfo,
    ErrorHandler,
    MCPSError,
    SystemError,
    NetworkError,
    DatabaseError,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    BusinessError,
    ExternalAPIError,
    MCPError,
    ToolError,
    SessionError,
    UserError,
    error_handler,
    error_context,
    get_error_handler,
    init_error_handler,
    handle_error,
    create_error_context
)

# 统一日志系统
from .unified_logging import (
    LogLevel,
    LogCategory,
    LogContext,
    LogEntry,
    StructuredFormatter,
    ColoredFormatter,
    UnifiedLogger,
    LoggingManager,
    log_function_call,
    get_logging_manager,
    init_logging,
    get_logger,
    create_log_context
)

# 统一缓存系统
from .unified_cache import (
    CacheBackend,
    SerializationMethod,
    CacheEntry,
    CacheStats,
    CacheBackendInterface,
    MemoryCacheBackend,
    RedisCacheBackend,
    UnifiedCacheManager,
    CacheFactory,
    get_cache_manager,
    init_cache,
    cache_get,
    cache_set,
    cache_delete,
    cached
)

__all__ = [
    # 配置管理
    "get_unified_config_manager",

    # 错误处理
    "ErrorSeverity",
    "ErrorCategory",
    "ErrorContext",
    "ErrorInfo",
    "ErrorHandler",
    "MCPSError",
    "SystemError",
    "NetworkError",
    "DatabaseError",
    "AuthenticationError",
    "AuthorizationError",
    "ValidationError",
    "BusinessError",
    "ExternalAPIError",
    "MCPError",
    "ToolError",
    "SessionError",
    "UserError",
    "error_handler",
    "error_context",
    "get_error_handler",
    "init_error_handler",
    "handle_error",
    "create_error_context",

    # 日志系统
    "LogLevel",
    "LogCategory",
    "LogContext",
    "LogEntry",
    "StructuredFormatter",
    "ColoredFormatter",
    "UnifiedLogger",
    "LoggingManager",
    "log_function_call",
    "get_logging_manager",
    "init_logging",
    "get_logger",
    "create_log_context",

    # 缓存系统
    "CacheBackend",
    "SerializationMethod",
    "CacheEntry",
    "CacheStats",
    "CacheBackendInterface",
    "MemoryCacheBackend",
    "RedisCacheBackend",
    "UnifiedCacheManager",
    "CacheFactory",
    "get_cache_manager",
    "init_cache",
    "cache_get",
    "cache_set",
    "cache_delete",
    "cached"
]

# 版本信息
__version__ = "1.0.0"
__author__ = "MCPS.ONE Team"
__description__ = "MCPS.ONE 统一核心基础设施"
