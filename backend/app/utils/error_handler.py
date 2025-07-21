"""错误处理工具模块"""
import asyncio
import logging
import functools
from typing import Any, Callable, Dict, List, Optional, Type, Union
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError

from .exceptions import (
    MCPSException, ProcessError, ProcessStartError, ProcessStopError,
    ProcessTimeoutError, ProcessCrashError, MCPConnectionError, MCPTimeoutError
)

logger = logging.getLogger(__name__)

class RetryConfig:
    """重试配置"""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Optional[List[Type[Exception]]] = None
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or [
            ProcessStartError,
            ProcessTimeoutError,
            MCPConnectionError,
            MCPTimeoutError
        ]

    def calculate_delay(self, attempt: int) -> float:
        """计算延迟时间"""
        delay = self.base_delay * (self.exponential_base ** (attempt - 1))
        delay = min(delay, self.max_delay)

        if self.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)  # 添加50%的随机抖动

        return delay

    def is_retryable(self, exception: Exception) -> bool:
        """判断异常是否可重试"""
        return any(isinstance(exception, exc_type) for exc_type in self.retryable_exceptions)

class CircuitBreakerConfig:
    """熔断器配置"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

class CircuitBreaker:
    """熔断器实现"""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def can_execute(self) -> bool:
        """检查是否可以执行"""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if self.last_failure_time and (
                datetime.utcnow() - self.last_failure_time
            ).total_seconds() > self.config.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        else:  # HALF_OPEN
            return True

    def record_success(self):
        """记录成功"""
        self.failure_count = 0
        self.state = "CLOSED"
        self.last_failure_time = None

    def record_failure(self, exception: Exception):
        """记录失败"""
        if isinstance(exception, self.config.expected_exception):
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()

            if self.failure_count >= self.config.failure_threshold:
                self.state = "OPEN"
                logger.warning(f"熔断器开启，失败次数: {self.failure_count}")

class ErrorHandler:
    """错误处理器"""

    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}

    def get_circuit_breaker(self, name: str, config: CircuitBreakerConfig) -> CircuitBreaker:
        """获取熔断器"""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(config)
        return self.circuit_breakers[name]

    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker_name: Optional[str] = None,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
        **kwargs
    ) -> Any:
        """带重试和熔断的执行"""
        retry_config = retry_config or RetryConfig()

        # 熔断器检查
        circuit_breaker = None
        if circuit_breaker_name and circuit_breaker_config:
            circuit_breaker = self.get_circuit_breaker(circuit_breaker_name, circuit_breaker_config)
            if not circuit_breaker.can_execute():
                raise MCPSException(
                    f"熔断器开启，暂时无法执行: {circuit_breaker_name}",
                    code="CIRCUIT_BREAKER_OPEN"
                )

        last_exception = None

        for attempt in range(1, retry_config.max_attempts + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                # 记录成功
                if circuit_breaker:
                    circuit_breaker.record_success()

                if attempt > 1:
                    logger.info(f"重试成功，尝试次数: {attempt}")

                return result

            except Exception as e:
                last_exception = e

                # 记录失败
                if circuit_breaker:
                    circuit_breaker.record_failure(e)

                # 检查是否可重试
                if attempt == retry_config.max_attempts or not retry_config.is_retryable(e):
                    break

                # 计算延迟
                delay = retry_config.calculate_delay(attempt)
                logger.warning(
                    f"执行失败，{delay:.2f}秒后重试 (尝试 {attempt}/{retry_config.max_attempts}): {e}"
                )

                await asyncio.sleep(delay)

        # 所有重试都失败了
        if isinstance(last_exception, MCPSException):
            last_exception.add_context("retry_attempts", retry_config.max_attempts)
            raise last_exception
        else:
            raise MCPSException(
                f"执行失败，已重试 {retry_config.max_attempts} 次",
                code="RETRY_EXHAUSTED",
                context={"retry_attempts": retry_config.max_attempts},
                original_exception=last_exception
            )

    def handle_process_error(self, e: Exception, context: Dict[str, Any]) -> MCPSException:
        """处理进程相关错误"""
        if isinstance(e, PermissionError):
            return ProcessPermissionError(
                "进程权限不足",
                context=context,
                original_exception=e
            )
        elif isinstance(e, FileNotFoundError):
            return ProcessStartError(
                "可执行文件未找到",
                context=context,
                original_exception=e
            )
        elif isinstance(e, OSError) and e.errno == 8:  # Exec format error
            return ProcessStartError(
                "可执行文件格式错误",
                context=context,
                original_exception=e
            )
        elif isinstance(e, asyncio.TimeoutError):
            return ProcessTimeoutError(
                "进程操作超时",
                context=context,
                original_exception=e
            )
        else:
            return ProcessError(
                f"进程操作失败: {str(e)}",
                context=context,
                original_exception=e
            )

    def log_error(self, error: MCPSException, level: int = logging.ERROR):
        """记录错误日志"""
        error_dict = error.to_dict()
        logger.log(level, f"错误详情: {error_dict}")

        # 如果有原始异常的堆栈信息，也记录下来
        if error.original_traceback:
            logger.log(level, f"原始异常堆栈: {''.join(error.original_traceback)}")

# API错误处理
class APIErrorHandler:
    """API错误处理器"""

    @staticmethod
    def create_error_response(
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ) -> JSONResponse:
        """创建标准错误响应"""
        error_data = {
            "error": {
                "code": code,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "details": details or {}
            }
        }
        return JSONResponse(
            status_code=status_code,
            content=error_data
        )

    @staticmethod
    def handle_validation_error(error: ValidationError) -> JSONResponse:
        """处理Pydantic验证错误"""
        details = []
        for err in error.errors():
            details.append({
                "field": ".".join(str(x) for x in err["loc"]),
                "message": err["msg"],
                "type": err["type"]
            })

        return APIErrorHandler.create_error_response(
            message="请求参数验证失败",
            code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"validation_errors": details}
        )

    @staticmethod
    def handle_database_error(error: SQLAlchemyError) -> JSONResponse:
        """处理数据库错误"""
        if isinstance(error, IntegrityError):
            return APIErrorHandler.create_error_response(
                message="数据完整性约束违反",
                code="INTEGRITY_ERROR",
                status_code=status.HTTP_409_CONFLICT,
                details={"constraint": str(error.orig) if hasattr(error, 'orig') else None}
            )
        else:
            logger.error(f"数据库错误: {error}")
            return APIErrorHandler.create_error_response(
                message="数据库操作失败",
                code="DATABASE_ERROR",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @staticmethod
    def handle_mcps_error(error: MCPSException) -> JSONResponse:
        """处理MCPS自定义错误"""
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        # 根据错误类型设置状态码
        if isinstance(error, (ProcessStartError, ProcessStopError)):
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        elif isinstance(error, ProcessTimeoutError):
            status_code = status.HTTP_408_REQUEST_TIMEOUT
        elif isinstance(error, (MCPConnectionError, MCPTimeoutError)):
            status_code = status.HTTP_502_BAD_GATEWAY

        return APIErrorHandler.create_error_response(
            message=error.message,
            code=error.code,
            status_code=status_code,
            details=error.context
        )

def handle_api_errors(func):
    """API错误处理装饰器"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except ValidationError as e:
            return APIErrorHandler.handle_validation_error(e)
        except SQLAlchemyError as e:
            return APIErrorHandler.handle_database_error(e)
        except MCPSException as e:
            return APIErrorHandler.handle_mcps_error(e)
        except HTTPException:
            raise  # 让FastAPI处理
        except Exception as e:
            logger.exception(f"未处理的API错误: {e}")
            return APIErrorHandler.create_error_response(
                message="服务器内部错误",
                code="INTERNAL_ERROR",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    return wrapper

def safe_execute(func, *args, **kwargs):
    """安全执行函数，捕获异常并返回结果"""
    try:
        return {"success": True, "data": func(*args, **kwargs)}
    except Exception as e:
        logger.exception(f"执行失败: {func.__name__}")
        return {"success": False, "error": str(e)}

async def safe_execute_async(func, *args, **kwargs):
    """安全执行异步函数，捕获异常并返回结果"""
    try:
        result = await func(*args, **kwargs)
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception(f"异步执行失败: {func.__name__}")
        return {"success": False, "error": str(e)}

# 全局错误处理器实例
error_handler = ErrorHandler()
api_error_handler = APIErrorHandler()

# 装饰器
def with_retry(
    retry_config: Optional[RetryConfig] = None,
    circuit_breaker_name: Optional[str] = None,
    circuit_breaker_config: Optional[CircuitBreakerConfig] = None
):
    """重试装饰器"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await error_handler.execute_with_retry(
                func,
                *args,
                retry_config=retry_config,
                circuit_breaker_name=circuit_breaker_name,
                circuit_breaker_config=circuit_breaker_config,
                **kwargs
            )
        return wrapper
    return decorator

def handle_errors(func):
    """错误处理装饰器"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except MCPSException:
            raise  # 直接抛出MCPS异常
        except Exception as e:
            # 转换为MCPS异常
            mcps_error = error_handler.handle_process_error(e, {
                "function": func.__name__,
                "args": str(args),
                "kwargs": str(kwargs)
            })
            error_handler.log_error(mcps_error)
            raise mcps_error
    return wrapper
