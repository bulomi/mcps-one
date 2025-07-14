"""自定义异常类"""

class MCPSException(Exception):
    """MCPS 基础异常类"""
    
    def __init__(self, message: str, code: str = None, details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

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
    """进程异常"""
    pass