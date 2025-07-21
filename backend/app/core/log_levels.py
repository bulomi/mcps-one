"""日志级别常量定义

统一管理系统中使用的日志级别，避免重复定义。
"""

from enum import Enum
from typing import List


class LogLevel(str, Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# 日志级别列表
LOG_LEVELS: List[str] = [level.value for level in LogLevel]

# 有效的日志级别（用于验证）
VALID_LOG_LEVELS = LOG_LEVELS

# 允许的日志级别（用于配置验证）
ALLOWED_LOG_LEVELS = LOG_LEVELS
