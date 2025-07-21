"""错误处理和恢复机制模块

提供系统级别的错误处理、恢复策略和容错机制，包括：
- 错误分类和处理
- 自动恢复策略
- 熔断器模式
- 重试机制
- 错误监控和告警
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from functools import wraps
import traceback
import json

from app.utils.exceptions import MCPSException as MCPServiceError, MCPConnectionError, MCPTimeoutError
from app.core.unified_logging import get_logger


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """错误分类"""
    NETWORK = "network"
    TIMEOUT = "timeout"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    RESOURCE = "resource"
    SYSTEM = "system"
    EXTERNAL = "external"
    UNKNOWN = "unknown"


class RecoveryAction(Enum):
    """恢复动作"""
    RETRY = "retry"
    FALLBACK = "fallback"
    CIRCUIT_BREAK = "circuit_break"
    ESCALATE = "escalate"
    IGNORE = "ignore"
    RESTART = "restart"


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class ErrorInfo:
    """错误信息"""
    error_id: str
    timestamp: datetime
    error_type: str
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    context: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    recovery_attempted: bool = False
    recovery_successful: bool = False
    retry_count: int = 0


@dataclass
class RetryConfig:
    """重试配置"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retry_on: List[type] = field(default_factory=lambda: [Exception])
    stop_on: List[type] = field(default_factory=list)


@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exception: type = Exception
    name: str = "default"


@dataclass
class RecoveryStrategy:
    """恢复策略"""
    action: RecoveryAction
    retry_config: Optional[RetryConfig] = None
    fallback_function: Optional[Callable] = None
    escalation_target: Optional[str] = None
    conditions: Dict[str, Any] = field(default_factory=dict)


class CircuitBreaker:
    """熔断器实现"""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count = 0
        self._lock = asyncio.Lock()

        self.logger = logging.getLogger(f"{__name__}.CircuitBreaker.{config.name}")

    async def call(self, func: Callable, *args, **kwargs):
        """通过熔断器调用函数"""
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.logger.info(f"Circuit breaker {self.config.name} entering half-open state")
                else:
                    raise MCPServiceError(f"Circuit breaker {self.config.name} is open")

        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            await self._on_success()
            return result
        except self.config.expected_exception as e:
            await self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """检查是否应该尝试重置熔断器"""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.config.recovery_timeout

    async def _on_success(self):
        """成功时的处理"""
        async with self._lock:
            self.failure_count = 0
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= 3:  # 连续3次成功后关闭熔断器
                    self.state = CircuitState.CLOSED
                    self.success_count = 0
                    self.logger.info(f"Circuit breaker {self.config.name} closed")

    async def _on_failure(self):
        """失败时的处理"""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                self.success_count = 0
                self.logger.warning(f"Circuit breaker {self.config.name} opened from half-open")
            elif self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                self.logger.warning(f"Circuit breaker {self.config.name} opened due to {self.failure_count} failures")

    def get_state(self) -> Dict[str, Any]:
        """获取熔断器状态"""
        return {
            "name": self.config.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "failure_threshold": self.config.failure_threshold,
            "recovery_timeout": self.config.recovery_timeout
        }


class ErrorHandler:
    """错误处理器"""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.error_history: List[ErrorInfo] = []
        self.recovery_strategies: Dict[str, RecoveryStrategy] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.error_patterns: Dict[str, int] = {}
        self.max_history_size = 1000

        # 默认恢复策略
        self._setup_default_strategies()

    def _setup_default_strategies(self):
        """设置默认恢复策略"""
        # 网络错误重试策略
        self.recovery_strategies["network_retry"] = RecoveryStrategy(
            action=RecoveryAction.RETRY,
            retry_config=RetryConfig(
                max_attempts=3,
                base_delay=1.0,
                exponential_base=2.0
            )
        )

        # 超时错误重试策略
        self.recovery_strategies["timeout_retry"] = RecoveryStrategy(
            action=RecoveryAction.RETRY,
            retry_config=RetryConfig(
                max_attempts=2,
                base_delay=0.5,
                max_delay=5.0
            )
        )

        # 系统错误熔断策略
        self.recovery_strategies["system_circuit_break"] = RecoveryStrategy(
            action=RecoveryAction.CIRCUIT_BREAK
        )

        # 关键错误升级策略
        self.recovery_strategies["critical_escalate"] = RecoveryStrategy(
            action=RecoveryAction.ESCALATE,
            escalation_target="admin"
        )

    def register_circuit_breaker(self, name: str, config: CircuitBreakerConfig):
        """注册熔断器"""
        self.circuit_breakers[name] = CircuitBreaker(config)
        self.logger.info(f"Registered circuit breaker: {name}")

    def register_recovery_strategy(self, name: str, strategy: RecoveryStrategy):
        """注册恢复策略"""
        self.recovery_strategies[name] = strategy
        self.logger.info(f"Registered recovery strategy: {name}")

    async def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> Optional[Any]:
        """处理错误"""
        error_info = self._create_error_info(error, context or {})
        self._record_error(error_info)

        # 选择恢复策略
        strategy = self._select_recovery_strategy(error_info)

        if strategy:
            try:
                result = await self._execute_recovery(error_info, strategy, context)
                error_info.recovery_attempted = True
                error_info.recovery_successful = result is not None
                return result
            except Exception as recovery_error:
                self.logger.error(f"Recovery failed: {recovery_error}")
                error_info.recovery_attempted = True
                error_info.recovery_successful = False

        # 如果没有恢复策略或恢复失败，重新抛出错误
        raise error

    def _create_error_info(self, error: Exception, context: Dict[str, Any]) -> ErrorInfo:
        """创建错误信息"""
        error_id = f"{int(time.time() * 1000)}_{id(error)}"
        category = self._categorize_error(error)
        severity = self._assess_severity(error, category)

        return ErrorInfo(
            error_id=error_id,
            timestamp=datetime.now(),
            error_type=type(error).__name__,
            message=str(error),
            category=category,
            severity=severity,
            context=context,
            stack_trace=traceback.format_exc()
        )

    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """错误分类"""
        if isinstance(error, MCPConnectionError):
            return ErrorCategory.NETWORK
        elif isinstance(error, MCPTimeoutError):
            return ErrorCategory.TIMEOUT
        elif isinstance(error, PermissionError):
            return ErrorCategory.AUTHORIZATION
        elif isinstance(error, ValueError):
            return ErrorCategory.VALIDATION
        elif isinstance(error, MemoryError):
            return ErrorCategory.RESOURCE
        elif isinstance(error, OSError):
            return ErrorCategory.SYSTEM
        else:
            return ErrorCategory.UNKNOWN

    def _assess_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """评估错误严重程度"""
        if isinstance(error, (MemoryError, SystemError)):
            return ErrorSeverity.CRITICAL
        elif category in [ErrorCategory.SYSTEM, ErrorCategory.RESOURCE]:
            return ErrorSeverity.HIGH
        elif category in [ErrorCategory.NETWORK, ErrorCategory.TIMEOUT]:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW

    def _select_recovery_strategy(self, error_info: ErrorInfo) -> Optional[RecoveryStrategy]:
        """选择恢复策略"""
        # 根据错误类别选择策略
        if error_info.category == ErrorCategory.NETWORK:
            return self.recovery_strategies.get("network_retry")
        elif error_info.category == ErrorCategory.TIMEOUT:
            return self.recovery_strategies.get("timeout_retry")
        elif error_info.severity == ErrorSeverity.CRITICAL:
            return self.recovery_strategies.get("critical_escalate")
        elif error_info.category == ErrorCategory.SYSTEM:
            return self.recovery_strategies.get("system_circuit_break")

        return None

    async def _execute_recovery(self, error_info: ErrorInfo, strategy: RecoveryStrategy, context: Dict[str, Any]) -> Optional[Any]:
        """执行恢复策略"""
        if strategy.action == RecoveryAction.RETRY:
            return await self._execute_retry(error_info, strategy, context)
        elif strategy.action == RecoveryAction.FALLBACK:
            return await self._execute_fallback(error_info, strategy, context)
        elif strategy.action == RecoveryAction.CIRCUIT_BREAK:
            await self._execute_circuit_break(error_info, strategy, context)
        elif strategy.action == RecoveryAction.ESCALATE:
            await self._execute_escalation(error_info, strategy, context)

        return None

    async def _execute_retry(self, error_info: ErrorInfo, strategy: RecoveryStrategy, context: Dict[str, Any]) -> Optional[Any]:
        """执行重试策略"""
        if not strategy.retry_config:
            return None

        retry_config = strategy.retry_config
        original_function = context.get('function')
        original_args = context.get('args', [])
        original_kwargs = context.get('kwargs', {})

        if not original_function:
            return None

        for attempt in range(retry_config.max_attempts):
            if attempt > 0:
                delay = min(
                    retry_config.base_delay * (retry_config.exponential_base ** (attempt - 1)),
                    retry_config.max_delay
                )

                if retry_config.jitter:
                    import random
                    delay *= (0.5 + random.random() * 0.5)

                self.logger.info(f"Retrying in {delay:.2f}s (attempt {attempt + 1}/{retry_config.max_attempts})")
                await asyncio.sleep(delay)

            try:
                if asyncio.iscoroutinefunction(original_function):
                    result = await original_function(*original_args, **original_kwargs)
                else:
                    result = original_function(*original_args, **original_kwargs)

                error_info.retry_count = attempt + 1
                self.logger.info(f"Retry successful after {attempt + 1} attempts")
                return result

            except Exception as retry_error:
                error_info.retry_count = attempt + 1

                # 检查是否应该停止重试
                if any(isinstance(retry_error, stop_type) for stop_type in retry_config.stop_on):
                    self.logger.info(f"Stopping retry due to {type(retry_error).__name__}")
                    break

                # 检查是否应该重试
                if not any(isinstance(retry_error, retry_type) for retry_type in retry_config.retry_on):
                    self.logger.info(f"Not retrying {type(retry_error).__name__}")
                    break

                if attempt == retry_config.max_attempts - 1:
                    self.logger.error(f"All retry attempts failed")
                    raise retry_error

        return None

    async def _execute_fallback(self, error_info: ErrorInfo, strategy: RecoveryStrategy, context: Dict[str, Any]) -> Optional[Any]:
        """执行降级策略"""
        if not strategy.fallback_function:
            return None

        try:
            if asyncio.iscoroutinefunction(strategy.fallback_function):
                return await strategy.fallback_function(error_info, context)
            else:
                return strategy.fallback_function(error_info, context)
        except Exception as fallback_error:
            self.logger.error(f"Fallback function failed: {fallback_error}")
            return None

    async def _execute_circuit_break(self, error_info: ErrorInfo, strategy: RecoveryStrategy, context: Dict[str, Any]):
        """执行熔断策略"""
        circuit_name = context.get('circuit_name', 'default')

        if circuit_name not in self.circuit_breakers:
            # 创建默认熔断器
            config = CircuitBreakerConfig(name=circuit_name)
            self.register_circuit_breaker(circuit_name, config)

        # 熔断器会在下次调用时生效
        self.logger.warning(f"Circuit breaker {circuit_name} activated due to error: {error_info.message}")

    async def _execute_escalation(self, error_info: ErrorInfo, strategy: RecoveryStrategy, context: Dict[str, Any]):
        """执行升级策略"""
        target = strategy.escalation_target or "system"

        escalation_data = {
            "error_id": error_info.error_id,
            "timestamp": error_info.timestamp.isoformat(),
            "severity": error_info.severity.value,
            "category": error_info.category.value,
            "message": error_info.message,
            "context": error_info.context,
            "target": target
        }

        # 这里可以集成告警系统
        self.logger.critical(f"Error escalated to {target}: {json.dumps(escalation_data, indent=2)}")

        # 可以发送邮件、短信、Webhook等
        await self._send_alert(escalation_data)

    async def _send_alert(self, alert_data: Dict[str, Any]):
        """发送告警"""
        # 这里可以实现具体的告警发送逻辑
        # 例如：发送邮件、调用Webhook、发送到消息队列等
        pass

    def _record_error(self, error_info: ErrorInfo):
        """记录错误"""
        self.error_history.append(error_info)

        # 限制历史记录大小
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size:]

        # 更新错误模式统计
        pattern_key = f"{error_info.category.value}:{error_info.error_type}"
        self.error_patterns[pattern_key] = self.error_patterns.get(pattern_key, 0) + 1

        # 记录日志
        log_level = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }.get(error_info.severity, logging.ERROR)

        self.logger.log(
            log_level,
            f"Error {error_info.error_id}: {error_info.message} (Category: {error_info.category.value}, Severity: {error_info.severity.value})"
        )

    def get_error_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """获取错误统计"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_errors = [e for e in self.error_history if e.timestamp >= cutoff_time]

        # 按类别统计
        category_stats = {}
        for error in recent_errors:
            category = error.category.value
            if category not in category_stats:
                category_stats[category] = {
                    "count": 0,
                    "severity_breakdown": {s.value: 0 for s in ErrorSeverity}
                }
            category_stats[category]["count"] += 1
            category_stats[category]["severity_breakdown"][error.severity.value] += 1

        # 按严重程度统计
        severity_stats = {s.value: 0 for s in ErrorSeverity}
        for error in recent_errors:
            severity_stats[error.severity.value] += 1

        # 恢复成功率
        recovery_attempted = len([e for e in recent_errors if e.recovery_attempted])
        recovery_successful = len([e for e in recent_errors if e.recovery_successful])
        recovery_rate = (recovery_successful / recovery_attempted * 100) if recovery_attempted > 0 else 0

        return {
            "time_range_hours": hours,
            "total_errors": len(recent_errors),
            "category_breakdown": category_stats,
            "severity_breakdown": severity_stats,
            "recovery_stats": {
                "attempted": recovery_attempted,
                "successful": recovery_successful,
                "success_rate_percent": round(recovery_rate, 2)
            },
            "top_error_patterns": dict(sorted(self.error_patterns.items(), key=lambda x: x[1], reverse=True)[:10]),
            "circuit_breaker_states": {name: cb.get_state() for name, cb in self.circuit_breakers.items()}
        }

    def get_recent_errors(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近的错误"""
        recent_errors = sorted(self.error_history, key=lambda x: x.timestamp, reverse=True)[:limit]

        return [
            {
                "error_id": error.error_id,
                "timestamp": error.timestamp.isoformat(),
                "error_type": error.error_type,
                "message": error.message,
                "category": error.category.value,
                "severity": error.severity.value,
                "context": error.context,
                "recovery_attempted": error.recovery_attempted,
                "recovery_successful": error.recovery_successful,
                "retry_count": error.retry_count
            }
            for error in recent_errors
        ]

    async def test_circuit_breaker(self, name: str) -> Dict[str, Any]:
        """测试熔断器"""
        if name not in self.circuit_breakers:
            raise ValueError(f"Circuit breaker {name} not found")

        circuit_breaker = self.circuit_breakers[name]

        async def test_function():
            raise Exception("Test exception")

        try:
            await circuit_breaker.call(test_function)
        except Exception:
            pass

        return circuit_breaker.get_state()


# 装饰器函数

def with_error_handling(error_handler: ErrorHandler, circuit_name: Optional[str] = None):
    """错误处理装饰器"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            context = {
                'function': func,
                'args': args,
                'kwargs': kwargs,
                'circuit_name': circuit_name
            }

            try:
                if circuit_name and circuit_name in error_handler.circuit_breakers:
                    circuit_breaker = error_handler.circuit_breakers[circuit_name]
                    return await circuit_breaker.call(func, *args, **kwargs)
                else:
                    return await func(*args, **kwargs)
            except Exception as e:
                return await error_handler.handle_error(e, context)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            context = {
                'function': func,
                'args': args,
                'kwargs': kwargs,
                'circuit_name': circuit_name
            }

            try:
                if circuit_name and circuit_name in error_handler.circuit_breakers:
                    circuit_breaker = error_handler.circuit_breakers[circuit_name]
                    return asyncio.run(circuit_breaker.call(func, *args, **kwargs))
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                return asyncio.run(error_handler.handle_error(e, context))

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


def with_retry(retry_config: RetryConfig):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            for attempt in range(retry_config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == retry_config.max_attempts - 1:
                        raise

                    if any(isinstance(e, stop_type) for stop_type in retry_config.stop_on):
                        raise

                    if not any(isinstance(e, retry_type) for retry_type in retry_config.retry_on):
                        raise

                    delay = min(
                        retry_config.base_delay * (retry_config.exponential_base ** attempt),
                        retry_config.max_delay
                    )

                    if retry_config.jitter:
                        import random
                        delay *= (0.5 + random.random() * 0.5)

                    await asyncio.sleep(delay)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            for attempt in range(retry_config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == retry_config.max_attempts - 1:
                        raise

                    if any(isinstance(e, stop_type) for stop_type in retry_config.stop_on):
                        raise

                    if not any(isinstance(e, retry_type) for retry_type in retry_config.retry_on):
                        raise

                    delay = min(
                        retry_config.base_delay * (retry_config.exponential_base ** attempt),
                        retry_config.max_delay
                    )

                    if retry_config.jitter:
                        import random
                        delay *= (0.5 + random.random() * 0.5)

                    time.sleep(delay)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


# 全局错误处理器实例
global_error_handler = ErrorHandler()
