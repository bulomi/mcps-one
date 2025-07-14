"""系统相关的 Pydantic 模式定义"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

class ConfigValueType(str, Enum):
    """配置值类型枚举"""
    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    JSON = "json"

class MetricType(str, Enum):
    """指标类型枚举"""
    GAUGE = "gauge"
    COUNTER = "counter"
    HISTOGRAM = "histogram"

class BackupType(str, Enum):
    """备份类型枚举"""
    MANUAL = "manual"
    AUTO = "auto"
    SCHEDULED = "scheduled"

class BackupStatus(str, Enum):
    """备份状态枚举"""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

# 系统配置模式
class SystemConfigBase(BaseModel):
    """系统配置基础模式"""
    key: str = Field(..., min_length=1, max_length=100, description="配置键")
    value: Optional[str] = Field(None, description="配置值")
    value_type: ConfigValueType = Field(ConfigValueType.STRING, description="值类型")
    category: Optional[str] = Field(None, max_length=50, description="配置分类")
    description: Optional[str] = Field(None, description="配置描述")
    is_public: bool = Field(False, description="是否为公开配置")
    is_readonly: bool = Field(False, description="是否只读")
    
    @validator('key')
    def validate_key(cls, v):
        """验证配置键"""
        if not v.replace('_', '').replace('.', '').replace('-', '').isalnum():
            raise ValueError('配置键只能包含字母、数字、下划线、点号和连字符')
        return v

class SystemConfigCreate(SystemConfigBase):
    """创建系统配置模式"""
    pass

class SystemConfigUpdate(BaseModel):
    """更新系统配置模式"""
    value: Optional[str] = Field(None, description="配置值")
    value_type: Optional[ConfigValueType] = Field(None, description="值类型")
    category: Optional[str] = Field(None, max_length=50, description="配置分类")
    description: Optional[str] = Field(None, description="配置描述")
    is_public: Optional[bool] = Field(None, description="是否为公开配置")

class SystemConfigResponse(SystemConfigBase):
    """系统配置响应模式"""
    id: int = Field(..., description="配置ID")
    typed_value: Any = Field(..., description="类型化的值")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True

# 系统信息模式
class SystemInfoBase(BaseModel):
    """系统信息基础模式"""
    metric_name: str = Field(..., min_length=1, max_length=100, description="指标名称")
    metric_value: str = Field(..., description="指标值")
    metric_type: MetricType = Field(MetricType.GAUGE, description="指标类型")
    unit: Optional[str] = Field(None, max_length=20, description="单位")
    category: Optional[str] = Field(None, max_length=50, description="分类")
    tags: Dict[str, str] = Field(default_factory=dict, description="标签")

class SystemInfoCreate(SystemInfoBase):
    """创建系统信息模式"""
    pass

class SystemInfoResponse(SystemInfoBase):
    """系统信息响应模式"""
    id: int = Field(..., description="信息ID")
    timestamp: datetime = Field(..., description="时间戳")
    
    class Config:
        from_attributes = True

# 数据库备份模式
class DatabaseBackupBase(BaseModel):
    """数据库备份基础模式"""
    filename: str = Field(..., min_length=1, max_length=200, description="备份文件名")
    backup_type: BackupType = Field(BackupType.MANUAL, description="备份类型")

class DatabaseBackupCreate(DatabaseBackupBase):
    """创建数据库备份模式"""
    pass

class DatabaseBackupResponse(DatabaseBackupBase):
    """数据库备份响应模式"""
    id: int = Field(..., description="备份ID")
    file_path: str = Field(..., description="文件路径")
    file_size: Optional[int] = Field(None, description="文件大小（字节）")
    status: BackupStatus = Field(..., description="备份状态")
    error_message: Optional[str] = Field(None, description="错误信息")
    started_at: datetime = Field(..., description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    duration_seconds: Optional[float] = Field(None, description="备份耗时（秒）")
    
    class Config:
        from_attributes = True

# 系统状态模式
class SystemStatus(BaseModel):
    """系统状态模式"""
    status: str = Field(..., description="系统状态")
    uptime: float = Field(..., description="运行时间（秒）")
    version: str = Field(..., description="系统版本")
    
    # 资源使用情况
    cpu_usage: float = Field(..., description="CPU使用率（%）")
    memory_usage: float = Field(..., description="内存使用率（%）")
    disk_usage: float = Field(..., description="磁盘使用率（%）")
    
    # 工具统计
    total_tools: int = Field(..., description="工具总数")
    running_tools: int = Field(..., description="运行中的工具数")
    stopped_tools: int = Field(..., description="已停止的工具数")
    error_tools: int = Field(..., description="错误状态的工具数")
    
    # 数据库信息
    database_size: int = Field(..., description="数据库大小（字节）")
    last_backup_time: Optional[datetime] = Field(None, description="最后备份时间")
    
    timestamp: datetime = Field(..., description="状态时间戳")

class SystemStatusResponse(SystemStatus):
    """系统状态响应模式"""
    pass

# 系统操作模式
class SystemOperationBase(BaseModel):
    """系统操作基础模式"""
    operation: str = Field(..., description="操作类型")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="操作参数")
    
    @validator('operation')
    def validate_operation(cls, v):
        """验证操作类型"""
        allowed_operations = [
            'backup_database',
            'restore_database',
            'cleanup_logs',
            'restart_system',
            'update_config'
        ]
        if v not in allowed_operations:
            raise ValueError(f'操作类型必须是: {", ".join(allowed_operations)}')
        return v

class SystemOperationCreate(SystemOperationBase):
    """创建系统操作模式"""
    pass

class SystemOperation(SystemOperationBase):
    """系统操作模式"""
    pass

class SystemOperationResult(BaseModel):
    """系统操作结果模式"""
    operation: str = Field(..., description="操作类型")
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="结果消息")
    data: Optional[Dict[str, Any]] = Field(None, description="结果数据")
    error: Optional[str] = Field(None, description="错误信息")
    duration_ms: int = Field(..., description="操作耗时（毫秒）")
    timestamp: datetime = Field(..., description="操作时间")

# 配置批量操作模式
class ConfigBatchUpdate(BaseModel):
    """配置批量更新模式"""
    configs: List[Dict[str, Any]] = Field(..., min_items=1, description="配置列表")
    
    @validator('configs')
    def validate_configs(cls, v):
        """验证配置列表"""
        for config in v:
            if 'key' not in config:
                raise ValueError('每个配置必须包含 key 字段')
            if 'value' not in config:
                raise ValueError('每个配置必须包含 value 字段')
        return v

class ConfigBatchResult(BaseModel):
    """配置批量操作结果模式"""
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    errors: List[str] = Field(default_factory=list, description="错误列表")
    updated_configs: List[str] = Field(default_factory=list, description="已更新的配置键")

# 系统健康检查模式
class HealthCheck(BaseModel):
    """系统健康检查模式"""
    status: str = Field(..., description="健康状态: healthy, degraded, unhealthy")
    checks: Dict[str, Dict[str, Any]] = Field(..., description="检查项目")

class HealthCheckResponse(HealthCheck):
    """系统健康检查响应模式"""
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="检查时间")
    duration_ms: int = Field(..., description="检查耗时（毫秒）")
    
    class Config:
        from_attributes = True
    timestamp: datetime = Field(..., description="检查时间")
    
    @validator('status')
    def validate_status(cls, v):
        """验证健康状态"""
        allowed_statuses = ['healthy', 'degraded', 'unhealthy']
        if v not in allowed_statuses:
            raise ValueError(f'健康状态必须是: {", ".join(allowed_statuses)}')
        return v

# 系统设置模式
class SystemSettings(BaseModel):
    """系统设置模式"""
    # 基础设置
    app_name: str = Field(..., description="应用名称")
    debug_mode: bool = Field(..., description="调试模式")
    log_level: str = Field(..., description="日志级别")
    
    # MCP 设置
    max_processes: int = Field(..., ge=1, le=50, description="最大进程数")
    process_timeout: int = Field(..., ge=5, le=300, description="进程超时时间")
    restart_delay: int = Field(..., ge=1, le=60, description="重启延迟")
    
    # 数据库设置
    backup_enabled: bool = Field(..., description="启用自动备份")
    backup_interval: str = Field(..., description="备份间隔")
    
    # WebSocket 设置
    heartbeat_interval: int = Field(..., ge=10, le=300, description="心跳间隔")
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """验证日志级别"""
        allowed_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed_levels:
            raise ValueError(f'日志级别必须是: {", ".join(allowed_levels)}')
        return v.upper()
    
    @validator('backup_interval')
    def validate_backup_interval(cls, v):
        """验证备份间隔"""
        allowed_intervals = ['hourly', 'daily', 'weekly', 'monthly']
        if v not in allowed_intervals:
            raise ValueError(f'备份间隔必须是: {", ".join(allowed_intervals)}')
        return v