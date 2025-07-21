"""MCP代理服务器相关数据模型

定义MCP代理服务器API接口的请求和响应数据模型。
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum


class ProxyStatus(str, Enum):
    """代理服务器状态"""
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class ToolStatus(str, Enum):
    """工具状态"""
    NOT_RUNNING = "not_running"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    RESTARTING = "restarting"


class LogLevel(str, Enum):
    """日志级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ProxyServerStatus(BaseModel):
    """代理服务器状态信息"""
    status: ProxyStatus
    host: str
    port: int
    uptime: Optional[float] = None
    start_time: Optional[datetime] = None
    request_count: int = 0
    error_count: int = 0
    active_requests: int = 0
    max_concurrent_tools: int
    cache_enabled: bool
    cache_valid: bool

    model_config = ConfigDict()


class ToolConfig(BaseModel):
    """工具配置信息"""
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    command: Union[str, List[str]]
    enabled: bool = True
    auto_start: bool = False
    instances: int = 1
    timeout: int = 30
    restart_on_failure: bool = True
    max_restart_attempts: int = 3
    health_check: Optional[Dict[str, Any]] = None
    environment: Optional[Dict[str, str]] = None
    working_directory: Optional[str] = None

    @field_validator('instances')
    @classmethod
    def validate_instances(cls, v):
        if v < 1:
            raise ValueError('instances must be at least 1')
        return v

    @field_validator('timeout')
    @classmethod
    def validate_timeout(cls, v):
        if v < 1:
            raise ValueError('timeout must be at least 1 second')
        return v


class ProcessInfo(BaseModel):
    """进程信息"""
    process_id: str
    tool_name: str
    pid: Optional[int] = None
    status: ToolStatus
    start_time: Optional[datetime] = None
    uptime: Optional[float] = None
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    restart_count: int = 0
    last_error: Optional[str] = None

    model_config = ConfigDict()


class ToolInfo(BaseModel):
    """工具信息"""
    name: str
    config: ToolConfig
    process_info: Optional[ProcessInfo] = None
    capabilities: Optional[Dict[str, Any]] = None
    last_health_check: Optional[datetime] = None
    health_status: Optional[str] = None

    model_config = ConfigDict()


class ProxyMetrics(BaseModel):
    """代理服务器性能指标"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    active_tools: int = 0
    total_tools: int = 0
    cache_hit_rate: float = 0.0
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    uptime: Optional[float] = None

    @property
    def success_rate(self) -> float:
        """计算成功率"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    @property
    def error_rate(self) -> float:
        """计算错误率"""
        if self.total_requests == 0:
            return 0.0
        return (self.failed_requests / self.total_requests) * 100


class ProxyLogEntry(BaseModel):
    """代理服务器日志条目"""
    timestamp: datetime
    level: LogLevel
    message: str
    source: Optional[str] = None
    tool_name: Optional[str] = None
    request_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    model_config = ConfigDict()


class ConfigUpdateRequest(BaseModel):
    """配置更新请求"""
    config: Dict[str, Any] = Field(..., description="要更新的配置项")

    @field_validator('config')
    @classmethod
    def validate_config(cls, v):
        if not v:
            raise ValueError('config cannot be empty')
        return v


class ToolStartRequest(BaseModel):
    """工具启动请求"""
    tool_name: str = Field(..., description="工具名称")
    force: bool = Field(False, description="是否强制启动")
    timeout: Optional[int] = Field(None, description="启动超时时间（秒）")


class ToolStopRequest(BaseModel):
    """工具停止请求"""
    tool_name: str = Field(..., description="工具名称")
    force: bool = Field(False, description="是否强制停止")
    timeout: Optional[int] = Field(None, description="停止超时时间（秒）")


class ToolDiscoveryResult(BaseModel):
    """工具发现结果"""
    discovered_tools: List[str] = Field(default_factory=list, description="发现的工具列表")
    new_tools: List[str] = Field(default_factory=list, description="新发现的工具")
    updated_tools: List[str] = Field(default_factory=list, description="更新的工具")
    errors: List[str] = Field(default_factory=list, description="发现过程中的错误")

    @property
    def total_discovered(self) -> int:
        """总发现数量"""
        return len(self.discovered_tools)

    @property
    def total_new(self) -> int:
        """新工具数量"""
        return len(self.new_tools)


class ProxyHealthCheck(BaseModel):
    """代理服务器健康检查"""
    status: str
    timestamp: datetime
    checks: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict()


class ToolHealthCheck(BaseModel):
    """工具健康检查"""
    tool_name: str
    status: str
    timestamp: datetime
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    model_config = ConfigDict()


class ProxyConfigSchema(BaseModel):
    """代理服务器配置模式"""
    host: str = Field(default="localhost", description="服务器主机")
    port: int = Field(default=8000, description="服务器端口")
    max_concurrent_tools: int = Field(default=10, description="最大并发工具数")
    tool_timeout: int = Field(default=30, description="工具超时时间（秒）")
    enable_caching: bool = Field(default=True, description="是否启用缓存")
    cache_ttl: int = Field(default=300, description="缓存TTL（秒）")
    log_level: LogLevel = Field(default=LogLevel.INFO, description="日志级别")
    health_check_interval: int = Field(default=60, description="健康检查间隔（秒）")
    auto_discovery: bool = Field(default=True, description="是否自动发现工具")
    discovery_interval: int = Field(default=300, description="工具发现间隔（秒）")

    @field_validator('port')
    @classmethod
    def validate_port(cls, v):
        if not (1 <= v <= 65535):
            raise ValueError('port must be between 1 and 65535')
        return v

    @field_validator('max_concurrent_tools')
    @classmethod
    def validate_max_concurrent_tools(cls, v):
        if v < 1:
            raise ValueError('max_concurrent_tools must be at least 1')
        return v


class ToolListResponse(BaseModel):
    """工具列表响应"""
    tools: List[ToolInfo]
    total: int
    enabled_count: int
    running_count: int

    @field_validator('total')
    @classmethod
    def validate_total(cls, v, info):
        if hasattr(info, 'data') and 'tools' in info.data and v != len(info.data['tools']):
            raise ValueError('total must match the number of tools')
        return v


class ProxyStatsResponse(BaseModel):
    """代理服务器统计响应"""
    status: ProxyServerStatus
    metrics: ProxyMetrics
    tool_stats: Dict[str, int] = Field(default_factory=dict)
    recent_errors: List[ProxyLogEntry] = Field(default_factory=list)

    model_config = ConfigDict()
