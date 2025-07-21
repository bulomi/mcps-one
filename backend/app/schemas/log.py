"""日志相关的 Pydantic 模式定义"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class LogLevel(str, Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogCategory(str, Enum):
    """日志分类枚举"""
    SYSTEM = "SYSTEM"
    TOOL = "TOOL"
    API = "API"
    MCP = "MCP"
    AUTH = "AUTH"
    OPERATION = "OPERATION"

class OperationAction(str, Enum):
    """操作动作枚举"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    START = "start"
    STOP = "stop"
    RESTART = "restart"

class OperationStatus(str, Enum):
    """操作状态枚举"""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"

class MessageDirection(str, Enum):
    """消息方向枚举"""
    IN = "in"
    OUT = "out"

# 系统日志模式
class SystemLogBase(BaseModel):
    """系统日志基础模式"""
    level: LogLevel = Field(..., description="日志级别")
    category: LogCategory = Field(..., description="日志分类")
    message: str = Field(..., min_length=1, description="日志消息")
    source: Optional[str] = Field(None, max_length=100, description="日志来源")
    tool_id: Optional[int] = Field(None, description="关联工具ID")
    tool_name: Optional[str] = Field(None, max_length=100, description="工具名称")
    details: Optional[Dict[str, Any]] = Field(None, description="详细信息")
    stack_trace: Optional[str] = Field(None, description="堆栈跟踪")
    request_id: Optional[str] = Field(None, max_length=50, description="请求ID")
    user_agent: Optional[str] = Field(None, max_length=500, description="用户代理")
    ip_address: Optional[str] = Field(None, max_length=50, description="IP地址")

class SystemLogCreate(SystemLogBase):
    """创建系统日志模式"""
    pass

class SystemLogResponse(SystemLogBase):
    """系统日志响应模式"""
    id: int = Field(..., description="日志ID")
    timestamp: datetime = Field(..., description="时间戳")

    model_config = ConfigDict(from_attributes=True)

# 操作日志模式
class OperationLogBase(BaseModel):
    """操作日志基础模式"""
    operation: str = Field(..., min_length=1, max_length=100, description="操作类型")
    resource_type: Optional[str] = Field(None, max_length=50, description="资源类型")
    resource_id: Optional[str] = Field(None, max_length=100, description="资源ID")
    resource_name: Optional[str] = Field(None, max_length=200, description="资源名称")
    action: OperationAction = Field(..., description="具体动作")
    status: OperationStatus = Field(OperationStatus.SUCCESS, description="操作状态")
    description: Optional[str] = Field(None, description="操作描述")
    old_values: Optional[Dict[str, Any]] = Field(None, description="变更前的值")
    new_values: Optional[Dict[str, Any]] = Field(None, description="变更后的值")
    result: Optional[Dict[str, Any]] = Field(None, description="操作结果")
    error_message: Optional[str] = Field(None, description="错误信息")
    request_id: Optional[str] = Field(None, max_length=50, description="请求ID")
    ip_address: Optional[str] = Field(None, max_length=50, description="IP地址")
    user_agent: Optional[str] = Field(None, max_length=500, description="用户代理")
    duration_ms: Optional[int] = Field(None, ge=0, description="操作耗时（毫秒）")

class OperationLogCreate(OperationLogBase):
    """创建操作日志模式"""
    pass

class OperationLogResponse(OperationLogBase):
    """操作日志响应模式"""
    id: int = Field(..., description="日志ID")
    timestamp: datetime = Field(..., description="时间戳")

    model_config = ConfigDict(from_attributes=True)

# MCP 日志模式
class MCPLogBase(BaseModel):
    """MCP 日志基础模式"""
    tool_id: int = Field(..., description="工具ID")
    tool_name: Optional[str] = Field(None, max_length=100, description="工具名称")
    direction: MessageDirection = Field(..., description="消息方向")
    message_type: str = Field(..., max_length=50, description="消息类型")
    method: Optional[str] = Field(None, max_length=100, description="方法名")
    request_data: Optional[Dict[str, Any]] = Field(None, description="请求数据")
    response_data: Optional[Dict[str, Any]] = Field(None, description="响应数据")
    error_data: Optional[Dict[str, Any]] = Field(None, description="错误数据")
    processing_time_ms: Optional[int] = Field(None, ge=0, description="处理时间（毫秒）")

class MCPLogCreate(MCPLogBase):
    """创建 MCP 日志模式"""
    pass

class MCPLogResponse(MCPLogBase):
    """MCP 日志响应模式"""
    id: int = Field(..., description="日志ID")
    timestamp: datetime = Field(..., description="时间戳")

    model_config = ConfigDict(from_attributes=True)

# 日志查询模式
class LogQueryParams(BaseModel):
    """日志查询参数模式"""
    # 分页参数
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页大小")

    # 过滤条件
    level: Optional[LogLevel] = Field(None, description="日志级别")
    category: Optional[LogCategory] = Field(None, description="日志分类")
    source: Optional[str] = Field(None, description="日志来源")
    tool_id: Optional[int] = Field(None, description="工具ID")
    tool_name: Optional[str] = Field(None, description="工具名称")

    # 时间范围
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")

# 日志统计模式
class LogStats(BaseModel):
    """日志统计模式"""
    total_logs: int = Field(..., description="总日志数")
    level_stats: Dict[str, int] = Field(..., description="按级别统计")
    category_stats: Dict[str, int] = Field(..., description="按分类统计")
    hourly_stats: List[Dict[str, Any]] = Field(..., description="按小时统计")
    daily_stats: List[Dict[str, Any]] = Field(..., description="按天统计")
    error_rate: float = Field(..., description="错误率")

class LogStatsResponse(BaseModel):
    """日志统计响应模式"""
    total_logs: int = Field(..., description="总日志数")
    level_stats: Dict[str, int] = Field(..., description="按级别统计")
    category_stats: Dict[str, int] = Field(..., description="按分类统计")
    hourly_stats: List[Dict[str, Any]] = Field(..., description="按小时统计")
    daily_stats: List[Dict[str, Any]] = Field(..., description="按天统计")
    error_rate: float = Field(..., description="错误率")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="统计时间")

    model_config = ConfigDict(from_attributes=True)

class LogQuery(BaseModel):
    """日志查询模式"""
    # 分页参数
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页大小")

    # 过滤条件
    level: Optional[LogLevel] = Field(None, description="日志级别")
    category: Optional[LogCategory] = Field(None, description="日志分类")
    source: Optional[str] = Field(None, description="日志来源")
    tool_id: Optional[int] = Field(None, description="工具ID")
    tool_name: Optional[str] = Field(None, description="工具名称")

    # 时间范围
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")

    # 搜索关键词
    keyword: Optional[str] = Field(None, min_length=1, description="搜索关键词")

    # 排序
    order_by: str = Field("timestamp", description="排序字段")
    order_desc: bool = Field(True, description="是否降序")

    @field_validator('end_time')
    @classmethod
    def validate_time_range(cls, v, info):
        """验证时间范围"""
        start_time = info.data.get('start_time')
        if start_time and v and v <= start_time:
            raise ValueError('结束时间必须大于开始时间')
        return v

class OperationLogQuery(BaseModel):
    """操作日志查询模式"""
    # 分页参数
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页大小")

    # 过滤条件
    operation: Optional[str] = Field(None, description="操作类型")
    resource_type: Optional[str] = Field(None, description="资源类型")
    resource_id: Optional[str] = Field(None, description="资源ID")
    action: Optional[OperationAction] = Field(None, description="具体动作")
    status: Optional[OperationStatus] = Field(None, description="操作状态")

    # 时间范围
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")

    # 搜索关键词
    keyword: Optional[str] = Field(None, min_length=1, description="搜索关键词")

    # 排序
    order_by: str = Field("timestamp", description="排序字段")
    order_desc: bool = Field(True, description="是否降序")

class MCPLogQuery(BaseModel):
    """MCP 日志查询模式"""
    # 分页参数
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页大小")

    # 过滤条件
    tool_id: Optional[int] = Field(None, description="工具ID")
    tool_name: Optional[str] = Field(None, description="工具名称")
    direction: Optional[MessageDirection] = Field(None, description="消息方向")
    message_type: Optional[str] = Field(None, description="消息类型")
    method: Optional[str] = Field(None, description="方法名")

    # 时间范围
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")

    # 排序
    order_by: str = Field("timestamp", description="排序字段")
    order_desc: bool = Field(True, description="是否降序")

# 日志统计模式
class LogStatistics(BaseModel):
    """日志统计模式"""
    total_count: int = Field(..., description="总数量")
    level_counts: Dict[str, int] = Field(..., description="按级别统计")
    category_counts: Dict[str, int] = Field(..., description="按分类统计")
    hourly_counts: List[Dict[str, Any]] = Field(..., description="按小时统计")
    top_sources: List[Dict[str, Any]] = Field(..., description="主要来源")
    error_rate: float = Field(..., description="错误率")

class OperationStatistics(BaseModel):
    """操作统计模式"""
    total_count: int = Field(..., description="总数量")
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    success_rate: float = Field(..., description="成功率")
    action_counts: Dict[str, int] = Field(..., description="按动作统计")
    resource_counts: Dict[str, int] = Field(..., description="按资源类型统计")
    avg_duration_ms: float = Field(..., description="平均耗时（毫秒）")

class MCPStatistics(BaseModel):
    """MCP 统计模式"""
    total_count: int = Field(..., description="总数量")
    tool_counts: Dict[str, int] = Field(..., description="按工具统计")
    message_type_counts: Dict[str, int] = Field(..., description="按消息类型统计")
    direction_counts: Dict[str, int] = Field(..., description="按方向统计")
    avg_processing_time_ms: float = Field(..., description="平均处理时间（毫秒）")
    error_count: int = Field(..., description="错误数量")
    error_rate: float = Field(..., description="错误率")

# 日志清理模式
class LogCleanupParams(BaseModel):
    """日志清理参数模式"""
    days_to_keep: int = Field(..., ge=1, le=365, description="保留天数")
    categories: Optional[List[LogCategory]] = Field(None, description="清理的分类")
    levels: Optional[List[LogLevel]] = Field(None, description="清理的级别")
    dry_run: bool = Field(False, description="是否为试运行")

class LogCleanup(BaseModel):
    """日志清理模式"""
    days_to_keep: int = Field(..., ge=1, le=365, description="保留天数")
    categories: Optional[List[LogCategory]] = Field(None, description="清理的分类")
    levels: Optional[List[LogLevel]] = Field(None, description="清理的级别")
    dry_run: bool = Field(False, description="是否为试运行")

class LogCleanupResult(BaseModel):
    """日志清理结果模式"""
    deleted_count: int = Field(..., description="删除数量")
    freed_space_bytes: int = Field(..., description="释放空间（字节）")
    categories_cleaned: List[str] = Field(..., description="清理的分类")
    oldest_remaining: Optional[datetime] = Field(None, description="最旧的剩余日志时间")
    duration_ms: int = Field(..., description="清理耗时（毫秒）")

# 分页响应模式
class PaginatedResponse(BaseModel):
    """通用分页响应模式"""
    items: List[Any] = Field(..., description="数据列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")

class LogPageResponse(BaseModel):
    """日志分页响应模式"""
    items: List[SystemLogResponse] = Field(..., description="日志列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")

class OperationLogPageResponse(BaseModel):
    """操作日志分页响应模式"""
    items: List[OperationLogResponse] = Field(..., description="日志列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")

class MCPLogPageResponse(BaseModel):
    """MCP 日志分页响应模式"""
    items: List[MCPLogResponse] = Field(..., description="日志列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")
