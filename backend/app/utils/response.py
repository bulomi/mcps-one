"""响应工具模块"""

from typing import Any, Dict, Optional, List, Union
from fastapi import status
from fastapi.responses import JSONResponse
from datetime import datetime
import json

def success_response(
    data: Any = None,
    message: str = "操作成功",
    status_code: int = status.HTTP_200_OK,
    headers: Optional[Dict[str, str]] = None
) -> JSONResponse:
    """成功响应"""
    response_data = {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return JSONResponse(
        content=response_data,
        status_code=status_code,
        headers=headers
    )

def error_response(
    message: str = "操作失败",
    error_code: Optional[str] = None,
    details: Any = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    headers: Optional[Dict[str, str]] = None
) -> JSONResponse:
    """错误响应"""
    response_data = {
        "success": False,
        "message": message,
        "error_code": error_code,
        "details": details,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return JSONResponse(
        content=response_data,
        status_code=status_code,
        headers=headers
    )

def paginated_response(
    data: List[Any],
    total: int,
    page: int,
    size: int,
    message: str = "获取成功",
    status_code: int = status.HTTP_200_OK
) -> JSONResponse:
    """分页响应"""
    total_pages = (total + size - 1) // size  # 向上取整
    
    response_data = {
        "success": True,
        "message": message,
        "data": data,
        "pagination": {
            "total": total,
            "page": page,
            "size": size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return JSONResponse(
        content=response_data,
        status_code=status_code
    )

def validation_error_response(
    errors: Union[List[Dict[str, Any]], Dict[str, Any]],
    message: str = "数据验证失败",
    status_code: int = status.HTTP_422_UNPROCESSABLE_ENTITY
) -> JSONResponse:
    """验证错误响应"""
    response_data = {
        "success": False,
        "message": message,
        "error_code": "VALIDATION_ERROR",
        "details": errors,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return JSONResponse(
        content=response_data,
        status_code=status_code
    )

def not_found_response(
    resource: str = "资源",
    message: Optional[str] = None,
    status_code: int = status.HTTP_404_NOT_FOUND
) -> JSONResponse:
    """资源未找到响应"""
    if message is None:
        message = f"{resource}未找到"
    
    response_data = {
        "success": False,
        "message": message,
        "error_code": "NOT_FOUND",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return JSONResponse(
        content=response_data,
        status_code=status_code
    )

def unauthorized_response(
    message: str = "未授权访问",
    status_code: int = status.HTTP_401_UNAUTHORIZED
) -> JSONResponse:
    """未授权响应"""
    response_data = {
        "success": False,
        "message": message,
        "error_code": "UNAUTHORIZED",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return JSONResponse(
        content=response_data,
        status_code=status_code
    )

def forbidden_response(
    message: str = "禁止访问",
    status_code: int = status.HTTP_403_FORBIDDEN
) -> JSONResponse:
    """禁止访问响应"""
    response_data = {
        "success": False,
        "message": message,
        "error_code": "FORBIDDEN",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return JSONResponse(
        content=response_data,
        status_code=status_code
    )

def server_error_response(
    message: str = "服务器内部错误",
    error_id: Optional[str] = None,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
) -> JSONResponse:
    """服务器错误响应"""
    response_data = {
        "success": False,
        "message": message,
        "error_code": "INTERNAL_SERVER_ERROR",
        "error_id": error_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return JSONResponse(
        content=response_data,
        status_code=status_code
    )

def rate_limit_response(
    message: str = "请求过于频繁",
    retry_after: Optional[int] = None,
    status_code: int = status.HTTP_429_TOO_MANY_REQUESTS
) -> JSONResponse:
    """限流响应"""
    response_data = {
        "success": False,
        "message": message,
        "error_code": "RATE_LIMIT_EXCEEDED",
        "retry_after": retry_after,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    headers = {}
    if retry_after:
        headers["Retry-After"] = str(retry_after)
    
    return JSONResponse(
        content=response_data,
        status_code=status_code,
        headers=headers
    )

def created_response(
    data: Any = None,
    message: str = "创建成功",
    location: Optional[str] = None,
    status_code: int = status.HTTP_201_CREATED
) -> JSONResponse:
    """创建成功响应"""
    response_data = {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    headers = {}
    if location:
        headers["Location"] = location
    
    return JSONResponse(
        content=response_data,
        status_code=status_code,
        headers=headers
    )

def no_content_response(
    message: str = "操作成功",
    status_code: int = status.HTTP_204_NO_CONTENT
) -> JSONResponse:
    """无内容响应"""
    return JSONResponse(
        content=None,
        status_code=status_code
    )

def accepted_response(
    data: Any = None,
    message: str = "请求已接受",
    task_id: Optional[str] = None,
    status_code: int = status.HTTP_202_ACCEPTED
) -> JSONResponse:
    """请求已接受响应（异步处理）"""
    response_data = {
        "success": True,
        "message": message,
        "data": data,
        "task_id": task_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return JSONResponse(
        content=response_data,
        status_code=status_code
    )

class ResponseFormatter:
    """响应格式化器"""
    
    @staticmethod
    def format_model_response(model_instance: Any) -> Dict[str, Any]:
        """格式化模型响应"""
        if hasattr(model_instance, '__dict__'):
            data = {}
            for key, value in model_instance.__dict__.items():
                if not key.startswith('_'):
                    if isinstance(value, datetime):
                        data[key] = value.isoformat()
                    elif hasattr(value, '__dict__'):
                        data[key] = ResponseFormatter.format_model_response(value)
                    else:
                        data[key] = value
            return data
        return model_instance
    
    @staticmethod
    def format_list_response(items: List[Any]) -> List[Dict[str, Any]]:
        """格式化列表响应"""
        return [ResponseFormatter.format_model_response(item) for item in items]
    
    @staticmethod
    def sanitize_response_data(data: Any) -> Any:
        """清理响应数据，移除敏感信息"""
        if isinstance(data, dict):
            sanitized = {}
            sensitive_fields = ['password', 'token', 'secret', 'key', 'private']
            
            for key, value in data.items():
                if any(field in key.lower() for field in sensitive_fields):
                    sanitized[key] = "[REDACTED]"
                elif isinstance(value, (dict, list)):
                    sanitized[key] = ResponseFormatter.sanitize_response_data(value)
                else:
                    sanitized[key] = value
            return sanitized
        elif isinstance(data, list):
            return [ResponseFormatter.sanitize_response_data(item) for item in data]
        else:
            return data

def custom_json_encoder(obj: Any) -> Any:
    """自定义JSON编码器"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, '__dict__'):
        return ResponseFormatter.format_model_response(obj)
    else:
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

# 响应状态码常量
class ResponseStatus:
    """响应状态码常量"""
    SUCCESS = status.HTTP_200_OK
    CREATED = status.HTTP_201_CREATED
    ACCEPTED = status.HTTP_202_ACCEPTED
    NO_CONTENT = status.HTTP_204_NO_CONTENT
    
    BAD_REQUEST = status.HTTP_400_BAD_REQUEST
    UNAUTHORIZED = status.HTTP_401_UNAUTHORIZED
    FORBIDDEN = status.HTTP_403_FORBIDDEN
    NOT_FOUND = status.HTTP_404_NOT_FOUND
    METHOD_NOT_ALLOWED = status.HTTP_405_METHOD_NOT_ALLOWED
    CONFLICT = status.HTTP_409_CONFLICT
    UNPROCESSABLE_ENTITY = status.HTTP_422_UNPROCESSABLE_ENTITY
    TOO_MANY_REQUESTS = status.HTTP_429_TOO_MANY_REQUESTS
    
    INTERNAL_SERVER_ERROR = status.HTTP_500_INTERNAL_SERVER_ERROR
    BAD_GATEWAY = status.HTTP_502_BAD_GATEWAY
    SERVICE_UNAVAILABLE = status.HTTP_503_SERVICE_UNAVAILABLE
    GATEWAY_TIMEOUT = status.HTTP_504_GATEWAY_TIMEOUT

# 错误代码常量
class ErrorCode:
    """错误代码常量"""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    CONFLICT = "CONFLICT"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    
    # 业务错误代码
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    TOOL_ALREADY_EXISTS = "TOOL_ALREADY_EXISTS"
    TOOL_OPERATION_FAILED = "TOOL_OPERATION_FAILED"
    MCP_CONNECTION_FAILED = "MCP_CONNECTION_FAILED"
    INVALID_CONFIGURATION = "INVALID_CONFIGURATION"
    DATABASE_ERROR = "DATABASE_ERROR"