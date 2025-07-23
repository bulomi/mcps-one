"""统一错误处理系统"""

import traceback
import logging
import uuid
from typing import Dict, Any, Optional, List, Union, Type
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from contextlib import contextmanager
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """错误分类"""
    SYSTEM = "system"
    NETWORK = "network"
    DATABASE = "database"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    BUSINESS = "business"
    EXTERNAL_API = "external_api"
    MCP = "mcp"
    TOOL = "tool"
    SESSION = "session"
    USER = "user"
    UNKNOWN = "unknown"

@dataclass
class ErrorContext:
    """错误上下文信息"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    service_name: Optional[str] = None
    method_name: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ErrorInfo:
    """错误信息"""
    error_id: str
    error_code: str
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    timestamp: datetime
    context: ErrorContext
    stack_trace: Optional[str] = None
    inner_error: Optional['ErrorInfo'] = None
    resolution_steps: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class MCPSError(Exception):
    """MCPS系统基础异常类"""

    def __init__(self,
                 message: str,
                 error_code: str = "UNKNOWN_ERROR",
                 category: ErrorCategory = ErrorCategory.UNKNOWN,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 context: Optional[ErrorContext] = None,
                 inner_error: Optional[Exception] = None,
                 resolution_steps: Optional[List[str]] = None,
                 metadata: Optional[Dict[str, Any]] = None):

        super().__init__(message)
        self.error_id = str(uuid.uuid4())
        self.error_code = error_code
        self.message = message
        self.category = category
        self.severity = severity
        self.context = context or ErrorContext()
        self.inner_error = inner_error
        self.resolution_steps = resolution_steps or []
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()

    def to_error_info(self) -> ErrorInfo:
        """转换为ErrorInfo对象"""
        inner_error_info = None
        if self.inner_error:
            if isinstance(self.inner_error, MCPSError):
                inner_error_info = self.inner_error.to_error_info()
            else:
                inner_error_info = ErrorInfo(
                    error_id=str(uuid.uuid4()),
                    error_code="INNER_ERROR",
                    message=str(self.inner_error),
                    category=ErrorCategory.UNKNOWN,
                    severity=ErrorSeverity.LOW,
                    timestamp=datetime.utcnow(),
                    context=ErrorContext(),
                    stack_trace=traceback.format_exc()
                )

        return ErrorInfo(
            error_id=self.error_id,
            error_code=self.error_code,
            message=self.message,
            category=self.category,
            severity=self.severity,
            timestamp=self.timestamp,
            context=self.context,
            stack_trace=traceback.format_exc(),
            inner_error=inner_error_info,
            resolution_steps=self.resolution_steps,
            metadata=self.metadata
        )

# 具体异常类
class SystemError(MCPSError):
    """系统错误"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.SYSTEM, **kwargs)

class NetworkError(MCPSError):
    """网络错误"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.NETWORK, **kwargs)

class DatabaseError(MCPSError):
    """数据库错误"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.DATABASE, **kwargs)

class AuthenticationError(MCPSError):
    """认证错误"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.AUTHENTICATION, **kwargs)

class AuthorizationError(MCPSError):
    """授权错误"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.AUTHORIZATION, **kwargs)

class ValidationError(MCPSError):
    """验证错误"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.VALIDATION, **kwargs)

class BusinessError(MCPSError):
    """业务逻辑错误"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.BUSINESS, **kwargs)

class ExternalAPIError(MCPSError):
    """外部API错误"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.EXTERNAL_API, **kwargs)

class MCPError(MCPSError):
    """MCP相关错误"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.MCP, **kwargs)

class ToolError(MCPSError):
    """工具错误"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.TOOL, **kwargs)

# 会话管理功能已移除
# class SessionError(MCPSError):
#     """会话相关错误"""
#     def __init__(self, message: str, **kwargs):
#         super().__init__(message, category=ErrorCategory.SESSION, **kwargs)

class UserError(MCPSError):
    """用户错误"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.USER, **kwargs)

class ErrorHandler:
    """统一错误处理器"""

    def __init__(self):
        self._error_callbacks: Dict[ErrorCategory, List[callable]] = {}
        self._global_callbacks: List[callable] = []
        self._error_history: List[ErrorInfo] = []
        self._max_history_size = 1000

    def register_callback(self, callback: callable, category: Optional[ErrorCategory] = None) -> None:
        """注册错误回调"""
        if category:
            if category not in self._error_callbacks:
                self._error_callbacks[category] = []
            self._error_callbacks[category].append(callback)
        else:
            self._global_callbacks.append(callback)

    def unregister_callback(self, callback: callable, category: Optional[ErrorCategory] = None) -> None:
        """注销错误回调"""
        if category and category in self._error_callbacks:
            if callback in self._error_callbacks[category]:
                self._error_callbacks[category].remove(callback)
        else:
            if callback in self._global_callbacks:
                self._global_callbacks.remove(callback)

    def handle_error(self, error: Union[Exception, ErrorInfo], context: Optional[ErrorContext] = None) -> ErrorInfo:
        """处理错误"""
        if isinstance(error, ErrorInfo):
            error_info = error
        elif isinstance(error, MCPSError):
            error_info = error.to_error_info()
            if context:
                error_info.context = context
        else:
            error_info = ErrorInfo(
                error_id=str(uuid.uuid4()),
                error_code="UNHANDLED_ERROR",
                message=str(error),
                category=ErrorCategory.UNKNOWN,
                severity=ErrorSeverity.MEDIUM,
                timestamp=datetime.utcnow(),
                context=context or ErrorContext(),
                stack_trace=traceback.format_exc()
            )

        # 记录错误
        self._record_error(error_info)

        # 执行回调
        self._execute_callbacks(error_info)

        # 记录日志
        self._log_error(error_info)

        return error_info

    def _record_error(self, error_info: ErrorInfo) -> None:
        """记录错误到历史"""
        self._error_history.append(error_info)

        # 保持历史记录大小
        if len(self._error_history) > self._max_history_size:
            self._error_history = self._error_history[-self._max_history_size:]

    def _execute_callbacks(self, error_info: ErrorInfo) -> None:
        """执行错误回调"""
        # 执行全局回调
        for callback in self._global_callbacks:
            try:
                callback(error_info)
            except Exception as e:
                logger.error(f"执行全局错误回调失败: {e}")

        # 执行分类回调
        category_callbacks = self._error_callbacks.get(error_info.category, [])
        for callback in category_callbacks:
            try:
                callback(error_info)
            except Exception as e:
                logger.error(f"执行分类错误回调失败: {e}")

    def _log_error(self, error_info: ErrorInfo) -> None:
        """记录错误日志"""
        log_level = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }.get(error_info.severity, logging.ERROR)

        log_message = (
            f"错误ID: {error_info.error_id} | "
            f"错误代码: {error_info.error_code} | "
            f"分类: {error_info.category.value} | "
            f"严重程度: {error_info.severity.value} | "
            f"消息: {error_info.message}"
        )

        if error_info.context.user_id:
            log_message += f" | 用户ID: {error_info.context.user_id}"
        if error_info.context.session_id:
            log_message += f" | 会话ID: {error_info.context.session_id}"

        logger.log(log_level, log_message)

        if error_info.stack_trace and error_info.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            logger.log(log_level, f"堆栈跟踪:\n{error_info.stack_trace}")

    def get_error_history(self,
                         category: Optional[ErrorCategory] = None,
                         severity: Optional[ErrorSeverity] = None,
                         limit: Optional[int] = None) -> List[ErrorInfo]:
        """获取错误历史"""
        filtered_errors = self._error_history

        if category:
            filtered_errors = [e for e in filtered_errors if e.category == category]

        if severity:
            filtered_errors = [e for e in filtered_errors if e.severity == severity]

        if limit:
            filtered_errors = filtered_errors[-limit:]

        return filtered_errors

    def get_error_stats(self) -> Dict[str, Any]:
        """获取错误统计"""
        total_errors = len(self._error_history)

        category_stats = {}
        severity_stats = {}

        for error in self._error_history:
            # 分类统计
            category = error.category.value
            category_stats[category] = category_stats.get(category, 0) + 1

            # 严重程度统计
            severity = error.severity.value
            severity_stats[severity] = severity_stats.get(severity, 0) + 1

        return {
            "total_errors": total_errors,
            "category_stats": category_stats,
            "severity_stats": severity_stats,
            "recent_errors": len([e for e in self._error_history
                                 if (datetime.utcnow() - e.timestamp).total_seconds() < 3600])
        }

    def clear_history(self) -> None:
        """清空错误历史"""
        self._error_history.clear()

# 装饰器
def error_handler(func_or_category=None, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 reraise: bool = True,
                 context_factory: Optional[callable] = None):
    """错误处理装饰器
    
    支持两种使用方式:
    1. @error_handler  # 无参数
    2. @error_handler(category=ErrorCategory.SERVICE)  # 有参数
    """
    # 如果第一个参数是函数，说明是无参数调用
    if callable(func_or_category):
        func = func_or_category
        category = ErrorCategory.UNKNOWN
        
        def decorator_impl(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                try:
                    return f(*args, **kwargs)
                except MCPSError:
                    raise
                except Exception as e:
                    context = ErrorContext(
                        service_name=f.__module__,
                        method_name=f.__name__
                    )
                    error_info = get_error_handler().handle_error(e, context)
                    if reraise:
                        mcps_error = MCPSError(
                            message=str(e),
                            error_code="WRAPPED_ERROR",
                            category=category,
                            severity=severity,
                            context=context,
                            inner_error=e
                        )
                        mcps_error.error_id = error_info.error_id
                        raise mcps_error
                    return None

            @wraps(f)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await f(*args, **kwargs)
                except MCPSError:
                    raise
                except Exception as e:
                    context = ErrorContext(
                        service_name=f.__module__,
                        method_name=f.__name__
                    )
                    error_info = get_error_handler().handle_error(e, context)
                    if reraise:
                        mcps_error = MCPSError(
                            message=str(e),
                            error_code="WRAPPED_ERROR",
                            category=category,
                            severity=severity,
                            context=context,
                            inner_error=e
                        )
                        mcps_error.error_id = error_info.error_id
                        raise mcps_error
                    return None

            return async_wrapper if asyncio.iscoroutinefunction(f) else wrapper
        
        return decorator_impl(func)
    
    # 有参数调用
    category = func_or_category if isinstance(func_or_category, ErrorCategory) else ErrorCategory.UNKNOWN
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except MCPSError:
                # MCPS错误直接重新抛出
                raise
            except Exception as e:
                # 创建上下文
                context = ErrorContext(
                    service_name=func.__module__,
                    method_name=func.__name__
                )

                if context_factory:
                    try:
                        additional_context = context_factory(*args, **kwargs)
                        if isinstance(additional_context, ErrorContext):
                            context = additional_context
                        elif isinstance(additional_context, dict):
                            context.additional_data.update(additional_context)
                    except Exception:
                        pass

                # 处理错误
                error_info = get_error_handler().handle_error(e, context)

                if reraise:
                    # 转换为MCPS错误并重新抛出
                    mcps_error = MCPSError(
                        message=str(e),
                        error_code="WRAPPED_ERROR",
                        category=category,
                        severity=severity,
                        context=context,
                        inner_error=e
                    )
                    mcps_error.error_id = error_info.error_id
                    raise mcps_error

                return None

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except MCPSError:
                raise
            except Exception as e:
                context = ErrorContext(
                    service_name=func.__module__,
                    method_name=func.__name__
                )

                if context_factory:
                    try:
                        additional_context = context_factory(*args, **kwargs)
                        if isinstance(additional_context, ErrorContext):
                            context = additional_context
                        elif isinstance(additional_context, dict):
                            context.additional_data.update(additional_context)
                    except Exception:
                        pass

                error_info = get_error_handler().handle_error(e, context)

                if reraise:
                    mcps_error = MCPSError(
                        message=str(e),
                        error_code="WRAPPED_ERROR",
                        category=category,
                        severity=severity,
                        context=context,
                        inner_error=e
                    )
                    mcps_error.error_id = error_info.error_id
                    raise mcps_error

                return None

        return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper
    return decorator

@contextmanager
def error_context(context: ErrorContext):
    """错误上下文管理器"""
    # 这里可以实现上下文的线程本地存储
    # 暂时简单实现
    try:
        yield context
    except Exception as e:
        get_error_handler().handle_error(e, context)
        raise

# 全局错误处理器实例
_error_handler: Optional[ErrorHandler] = None

def get_error_handler() -> ErrorHandler:
    """获取全局错误处理器"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler

def init_error_handler() -> ErrorHandler:
    """初始化错误处理器"""
    global _error_handler
    _error_handler = ErrorHandler()
    return _error_handler

# 便捷函数
def handle_error(error: Union[Exception, ErrorInfo], context: Optional[ErrorContext] = None) -> ErrorInfo:
    """处理错误的便捷函数"""
    return get_error_handler().handle_error(error, context)

def create_error_context(user_id: Optional[str] = None,
                        session_id: Optional[str] = None,
                        request_id: Optional[str] = None,
                        service_name: Optional[str] = None,
                        method_name: Optional[str] = None,
                        **additional_data) -> ErrorContext:
    """创建错误上下文的便捷函数"""
    return ErrorContext(
        user_id=user_id,
        session_id=session_id,
        request_id=request_id,
        service_name=service_name,
        method_name=method_name,
        additional_data=additional_data
    )
