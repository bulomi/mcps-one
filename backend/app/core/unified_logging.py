"""统一日志系统"""

import logging
import logging.handlers
import json
import os
import sys
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timezone
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, asdict
import threading
from contextlib import contextmanager
import traceback
from functools import wraps

class LogLevel(Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogCategory(Enum):
    """日志分类"""
    SYSTEM = "system"
    API = "api"
    DATABASE = "database"
    MCP = "mcp"
    TOOL = "tool"
    SESSION = "session"
    USER = "user"
    SECURITY = "security"
    PERFORMANCE = "performance"
    INTEGRATION = "integration"
    BUSINESS = "business"
    DEBUG = "debug"

@dataclass
class LogContext:
    """日志上下文"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    service_name: Optional[str] = None
    method_name: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    additional_data: Dict[str, Any] = None

    def __post_init__(self):
        if self.additional_data is None:
            self.additional_data = {}

@dataclass
class LogEntry:
    """日志条目"""
    timestamp: datetime
    level: LogLevel
    category: LogCategory
    message: str
    logger_name: str
    context: LogContext
    exception_info: Optional[str] = None
    stack_trace: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""

    def __init__(self, include_context: bool = True, include_metadata: bool = True):
        super().__init__()
        self.include_context = include_context
        self.include_metadata = include_metadata

    def format(self, record: logging.LogRecord) -> str:
        # 基础日志信息
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # 添加分类信息
        if hasattr(record, 'category'):
            log_data["category"] = record.category

        # 添加上下文信息
        if self.include_context and hasattr(record, 'context'):
            context_data = asdict(record.context)
            # 过滤空值
            context_data = {k: v for k, v in context_data.items() if v is not None}
            if context_data:
                log_data["context"] = context_data

        # 添加元数据
        if self.include_metadata and hasattr(record, 'metadata'):
            if record.metadata:
                log_data["metadata"] = record.metadata

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }

        # 添加堆栈跟踪
        if hasattr(record, 'stack_info') and record.stack_info:
            log_data["stack_trace"] = record.stack_info

        return json.dumps(log_data, ensure_ascii=False, default=str)

class ColoredFormatter(logging.Formatter):
    """彩色控制台格式化器"""

    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
        'RESET': '\033[0m'        # 重置
    }

    def format(self, record: logging.LogRecord) -> str:
        # 获取颜色
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']

        # 格式化时间
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')

        # 构建基础消息
        message = f"{color}[{timestamp}] {record.levelname:8} {record.name:20} | {record.getMessage()}{reset}"

        # 添加上下文信息
        if hasattr(record, 'context') and record.context:
            context_parts = []
            if record.context.user_id:
                context_parts.append(f"user:{record.context.user_id}")
            if record.context.session_id:
                context_parts.append(f"session:{record.context.session_id[:8]}")
            if record.context.request_id:
                context_parts.append(f"req:{record.context.request_id[:8]}")

            if context_parts:
                message += f" [{', '.join(context_parts)}]"

        # 添加异常信息
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"

        return message

class UnifiedLogger:
    """统一日志器"""

    def __init__(self, name: str, category: LogCategory = LogCategory.SYSTEM):
        self.name = name
        self.category = category
        self.logger = logging.getLogger(name)
        self._context_stack: List[LogContext] = []
        self._local = threading.local()

    def _get_current_context(self) -> LogContext:
        """获取当前上下文"""
        # 尝试从线程本地存储获取
        if hasattr(self._local, 'context'):
            return self._local.context

        # 从上下文栈获取
        if self._context_stack:
            return self._context_stack[-1]

        return LogContext()

    def _set_current_context(self, context: LogContext) -> None:
        """设置当前上下文"""
        self._local.context = context

    def _create_log_record(self, level: LogLevel, message: str,
                          context: Optional[LogContext] = None,
                          metadata: Optional[Dict[str, Any]] = None,
                          exc_info: Optional[tuple] = None) -> logging.LogRecord:
        """创建日志记录"""
        # 获取调用者信息
        frame = sys._getframe(3)  # 跳过内部调用栈

        # 创建日志记录
        record = logging.LogRecord(
            name=self.name,
            level=getattr(logging, level.value),
            pathname=frame.f_code.co_filename,
            lineno=frame.f_lineno,
            msg=message,
            args=(),
            exc_info=exc_info
        )

        # 添加自定义属性
        record.category = self.category.value
        record.context = context or self._get_current_context()
        record.metadata = metadata or {}

        return record

    def debug(self, message: str, context: Optional[LogContext] = None,
             metadata: Optional[Dict[str, Any]] = None, category: Optional[LogCategory] = None) -> None:
        """记录调试日志"""
        if self.logger.isEnabledFor(logging.DEBUG):
            record = self._create_log_record(LogLevel.DEBUG, message, context, metadata)
            self.logger.handle(record)

    def info(self, message: str, context: Optional[LogContext] = None,
            metadata: Optional[Dict[str, Any]] = None, category: Optional[LogCategory] = None) -> None:
        """记录信息日志"""
        if self.logger.isEnabledFor(logging.INFO):
            record = self._create_log_record(LogLevel.INFO, message, context, metadata)
            self.logger.handle(record)

    def warning(self, message: str, context: Optional[LogContext] = None,
               metadata: Optional[Dict[str, Any]] = None, category: Optional[LogCategory] = None) -> None:
        """记录警告日志"""
        if self.logger.isEnabledFor(logging.WARNING):
            record = self._create_log_record(LogLevel.WARNING, message, context, metadata)
            self.logger.handle(record)

    def error(self, message: str, context: Optional[LogContext] = None,
             metadata: Optional[Dict[str, Any]] = None, exc_info: bool = False, category: Optional[LogCategory] = None) -> None:
        """记录错误日志"""
        if self.logger.isEnabledFor(logging.ERROR):
            exc_info_tuple = sys.exc_info() if exc_info else None
            record = self._create_log_record(LogLevel.ERROR, message, context, metadata, exc_info_tuple)
            self.logger.handle(record)

    def critical(self, message: str, context: Optional[LogContext] = None,
                metadata: Optional[Dict[str, Any]] = None, exc_info: bool = False, category: Optional[LogCategory] = None) -> None:
        """记录严重错误日志"""
        if self.logger.isEnabledFor(logging.CRITICAL):
            exc_info_tuple = sys.exc_info() if exc_info else None
            record = self._create_log_record(LogLevel.CRITICAL, message, context, metadata, exc_info_tuple)
            self.logger.handle(record)

    def exception(self, message: str, context: Optional[LogContext] = None,
                 metadata: Optional[Dict[str, Any]] = None) -> None:
        """记录异常日志"""
        self.error(message, context, metadata, exc_info=True)

    def setLevel(self, level: Union[str, int]) -> None:
        """设置日志级别"""
        self.logger.setLevel(level)

    def getEffectiveLevel(self) -> int:
        """获取有效日志级别"""
        return self.logger.getEffectiveLevel()

    def isEnabledFor(self, level: Union[str, int]) -> bool:
        """检查是否启用指定级别的日志"""
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        return self.logger.isEnabledFor(level)

    @contextmanager
    def context(self, **kwargs):
        """上下文管理器"""
        # 创建新的上下文
        current_context = self._get_current_context()
        new_context = LogContext(
            user_id=kwargs.get('user_id', current_context.user_id),
            session_id=kwargs.get('session_id', current_context.session_id),
            request_id=kwargs.get('request_id', current_context.request_id),
            service_name=kwargs.get('service_name', current_context.service_name),
            method_name=kwargs.get('method_name', current_context.method_name),
            trace_id=kwargs.get('trace_id', current_context.trace_id),
            span_id=kwargs.get('span_id', current_context.span_id),
            additional_data={**current_context.additional_data, **kwargs.get('additional_data', {})}
        )

        # 保存当前上下文
        old_context = getattr(self._local, 'context', None)
        self._set_current_context(new_context)

        try:
            yield new_context
        finally:
            # 恢复上下文
            if old_context:
                self._set_current_context(old_context)
            elif hasattr(self._local, 'context'):
                delattr(self._local, 'context')

class LoggingManager:
    """日志管理器"""

    def __init__(self, log_dir: Optional[str] = None):
        self.log_dir = Path(log_dir) if log_dir else Path("logs")
        self.log_dir.mkdir(exist_ok=True)

        self._loggers: Dict[str, UnifiedLogger] = {}
        self._handlers: Dict[str, logging.Handler] = {}
        self._configured = False

    def configure(self,
                 level: Union[str, int] = logging.INFO,
                 console_output: bool = True,
                 file_output: bool = True,
                 structured_format: bool = True,
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5) -> None:
        """配置日志系统"""
        if self._configured:
            return

        # 设置根日志级别
        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        # 清除现有处理器
        root_logger.handlers.clear()

        # 控制台处理器
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)

            if structured_format:
                console_formatter = StructuredFormatter()
            else:
                console_formatter = ColoredFormatter()

            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
            self._handlers['console'] = console_handler

        # 文件处理器
        if file_output:
            # 主日志文件
            main_log_file = self.log_dir / "mcps.log"
            file_handler = logging.handlers.RotatingFileHandler(
                main_log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(level)

            file_formatter = StructuredFormatter()
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
            self._handlers['file'] = file_handler

            # 错误日志文件
            error_log_file = self.log_dir / "error.log"
            error_handler = logging.handlers.RotatingFileHandler(
                error_log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(file_formatter)
            root_logger.addHandler(error_handler)
            self._handlers['error'] = error_handler

        self._configured = True

    def get_logger(self, name: str, category: LogCategory = LogCategory.SYSTEM) -> UnifiedLogger:
        """获取日志器"""
        if name not in self._loggers:
            self._loggers[name] = UnifiedLogger(name, category)
        return self._loggers[name]

    def add_handler(self, name: str, handler: logging.Handler) -> None:
        """添加处理器"""
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        self._handlers[name] = handler

    def remove_handler(self, name: str) -> None:
        """移除处理器"""
        if name in self._handlers:
            root_logger = logging.getLogger()
            root_logger.removeHandler(self._handlers[name])
            del self._handlers[name]

    def set_level(self, level: Union[str, int], logger_name: Optional[str] = None) -> None:
        """设置日志级别"""
        if logger_name:
            logger = logging.getLogger(logger_name)
            logger.setLevel(level)
        else:
            root_logger = logging.getLogger()
            root_logger.setLevel(level)

    def create_category_logger(self, category: LogCategory,
                              log_file: Optional[str] = None,
                              level: Union[str, int] = logging.INFO) -> UnifiedLogger:
        """为特定分类创建专用日志器"""
        logger_name = f"mcps.{category.value}"
        logger = self.get_logger(logger_name, category)

        if log_file:
            # 创建专用文件处理器
            file_path = self.log_dir / log_file
            handler = logging.handlers.RotatingFileHandler(
                file_path,
                maxBytes=10 * 1024 * 1024,
                backupCount=5,
                encoding='utf-8'
            )
            handler.setLevel(level)
            handler.setFormatter(StructuredFormatter())

            # 只添加到特定日志器
            specific_logger = logging.getLogger(logger_name)
            specific_logger.addHandler(handler)
            specific_logger.propagate = False  # 防止传播到根日志器

        return logger

# 装饰器
def log_function_call(logger: Optional[UnifiedLogger] = None,
                     level: LogLevel = LogLevel.DEBUG,
                     include_args: bool = False,
                     include_result: bool = False):
    """函数调用日志装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger(func.__module__)

            # 记录函数开始
            context = LogContext(
                service_name=func.__module__,
                method_name=func.__name__
            )

            metadata = {}
            if include_args:
                metadata['args'] = str(args)[:200]  # 限制长度
                metadata['kwargs'] = {k: str(v)[:100] for k, v in kwargs.items()}

            logger.debug(f"开始执行函数: {func.__name__}", context, metadata)

            try:
                result = func(*args, **kwargs)

                # 记录函数成功完成
                success_metadata = {}
                if include_result and result is not None:
                    success_metadata['result'] = str(result)[:200]

                logger.debug(f"函数执行成功: {func.__name__}", context, success_metadata)
                return result

            except Exception as e:
                # 记录函数异常
                logger.error(f"函数执行失败: {func.__name__} - {str(e)}", context, exc_info=True)
                raise

        return wrapper
    return decorator

# 全局日志管理器
_logging_manager: Optional[LoggingManager] = None

def get_logging_manager() -> LoggingManager:
    """获取全局日志管理器"""
    global _logging_manager
    if _logging_manager is None:
        _logging_manager = LoggingManager()
    return _logging_manager

def init_logging(log_dir: Optional[str] = None, **config_kwargs) -> LoggingManager:
    """初始化日志系统"""
    global _logging_manager
    _logging_manager = LoggingManager(log_dir)
    _logging_manager.configure(**config_kwargs)
    return _logging_manager

def get_logger(name: str, category: LogCategory = LogCategory.SYSTEM) -> UnifiedLogger:
    """获取日志器的便捷函数"""
    return get_logging_manager().get_logger(name, category)

def create_log_context(user_id: Optional[str] = None,
                      session_id: Optional[str] = None,
                      request_id: Optional[str] = None,
                      service_name: Optional[str] = None,
                      method_name: Optional[str] = None,
                      **additional_data) -> LogContext:
    """创建日志上下文的便捷函数"""
    return LogContext(
        user_id=user_id,
        session_id=session_id,
        request_id=request_id,
        service_name=service_name,
        method_name=method_name,
        additional_data=additional_data
    )
