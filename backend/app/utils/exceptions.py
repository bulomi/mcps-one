"""自定义异常类"""
import traceback
from typing import Dict, Any, Optional
from datetime import datetime

class MCPSException(Exception):
    """MCPS 基础异常类"""

    def __init__(
        self,
        message: str,
        code: str = None,
        details: dict = None,
        context: dict = None,
        original_exception: Exception = None
    ):
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        self.context = context or {}
        self.original_exception = original_exception
        self.timestamp = datetime.utcnow()

        # 如果有原始异常，保存其堆栈信息
        if original_exception:
            self.original_traceback = traceback.format_exception(
                type(original_exception),
                original_exception,
                original_exception.__traceback__
            )
        else:
            self.original_traceback = None

        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "code": self.code,
            "details": self.details,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "original_exception": str(self.original_exception) if self.original_exception else None
        }

    def add_context(self, key: str, value: Any) -> 'MCPSException':
        """添加上下文信息"""
        self.context[key] = value
        return self

class ToolError(MCPSException):
    """工具相关异常"""
    pass

class ToolNotFoundError(ToolError):
    """工具未找到异常"""
    pass

class ToolConfigError(ToolError):
    """工具配置异常"""
    pass

class ToolOperationError(ToolError):
    """工具操作异常"""
    pass

class ToolValidationError(ToolError):
    """工具验证异常"""
    pass

class CategoryNotFoundError(ToolError):
    """分类未找到异常"""
    pass

class MCPProtocolError(MCPSException):
    """MCP 协议异常"""
    pass

class MCPConnectionError(MCPProtocolError):
    """MCP 连接异常"""
    pass

class MCPTimeoutError(MCPProtocolError):
    """MCP 超时异常"""
    pass

class MCPMethodError(MCPProtocolError):
    """MCP 方法调用异常"""
    pass

class SystemConfigError(MCPSException):
    """系统配置异常"""
    pass

class SystemOperationError(MCPSException):
    """系统操作异常"""
    pass

class DatabaseError(MCPSException):
    """数据库异常"""
    pass

class LogServiceError(MCPSException):
    """日志服务异常"""
    pass

class ValidationError(MCPSException):
    """数据验证异常"""
    pass

class AuthenticationError(MCPSException):
    """认证异常"""
    pass

class AuthorizationError(MCPSException):
    """授权异常"""
    pass

class RateLimitError(MCPSException):
    """频率限制异常"""
    pass

class ProcessError(MCPSException):
    """进程异常基类"""
    pass

class ProcessStartError(ProcessError):
    """进程启动异常"""
    pass

class ProcessStopError(ProcessError):
    """进程停止异常"""
    pass

class ProcessTimeoutError(ProcessError):
    """进程操作超时异常"""
    pass

class ProcessCrashError(ProcessError):
    """进程崩溃异常"""
    pass

class ProcessPermissionError(ProcessError):
    """进程权限异常"""
    pass

class ProcessResourceError(ProcessError):
    """进程资源异常（内存、文件句柄等）"""
    pass

class ProcessManagementError(ProcessError):
    """进程管理异常"""
    pass

# 会话相关异常
# 会话管理功能已移除
# class SessionError(MCPSException):
#     """会话异常基类"""
#     pass
# 
# class SessionNotFoundError(SessionError):
#     """会话不存在异常"""
#     pass
# 
# class SessionExpiredError(SessionError):
#     """会话过期异常"""
#     pass
# 
# class SessionOperationError(SessionError):
#     """会话操作异常"""
#     pass

# 任务管理功能已移除
# class TaskError(MCPSException):
#     """任务异常基类"""
#     pass
# 
# class TaskNotFoundError(TaskError):
#     """任务不存在异常"""
#     pass
# 
# class TaskExecutionError(TaskError):
#     """任务执行异常"""
#     pass
# 
# class TaskOperationError(TaskError):
#     """任务操作异常"""
#     pass
# 
# class TaskTimeoutError(TaskError):
#     """任务超时异常"""
#     pass

class ServiceException(MCPSException):
    """服务异常"""
    pass

class MCPServiceError(ServiceException):
    """MCP 服务异常"""
    pass

class BusinessException(MCPSException):
    """业务异常"""

# 配置相关异常
class ConfigurationError(MCPSException):
    """配置异常"""
    pass

class ConfigValidationError(ConfigurationError):
    """配置验证异常"""
    pass

class ConfigLoadError(ConfigurationError):
    """配置加载异常"""
    pass

class ConfigSaveError(ConfigurationError):
    """配置保存异常"""
    pass

# 路由相关异常
class RequestRoutingError(MCPSException):
    """请求路由异常"""
    pass

class RouteNotFoundError(RequestRoutingError):
    """路由未找到异常"""
    pass

class LoadBalancerError(RequestRoutingError):
    """负载均衡器异常"""
    pass

class CircuitBreakerError(RequestRoutingError):
    """熔断器异常"""
    pass

# 注册中心相关异常
class RegistryError(MCPSException):
    """注册中心异常"""
    pass

class ToolRegistrationError(RegistryError):
    """工具注册异常"""
    pass

class HealthCheckError(RegistryError):
    """健康检查异常"""
    pass

# 代理相关异常
class ProxyError(MCPSException):
    """代理异常基类"""
    pass

class ProxyNotFoundError(ProxyError):
    """代理不存在异常"""
    pass

class ProxyValidationError(ProxyError):
    """代理验证异常"""
    pass

class ProxyConnectionError(ProxyError):
    """代理连接异常"""
    pass

class ProxyTestError(ProxyError):
    """代理测试异常"""
    pass

class ProxyOperationError(ProxyError):
    """代理操作异常"""
    pass
    pass
