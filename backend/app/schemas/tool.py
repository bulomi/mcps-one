"""工具相关的 Pydantic 模式定义"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ToolStatus(str, Enum):
    """工具状态枚举"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
    UNKNOWN = "unknown"

class ToolType(str, Enum):
    """工具类型枚举"""
    BUILTIN = "builtin"
    CUSTOM = "custom"
    EXTERNAL = "external"

class ConnectionType(str, Enum):
    """连接类型枚举"""
    STDIO = "stdio"
    HTTP = "http"
    WEBSOCKET = "websocket"

class ConnectionConfig(BaseModel):
    """连接配置模式"""
    type: ConnectionType = Field(ConnectionType.STDIO, description="连接类型")
    host: Optional[str] = Field(None, description="主机地址")
    port: Optional[int] = Field(None, description="端口号")
    path: Optional[str] = Field(None, description="路径")
    timeout: int = Field(30, description="连接超时时间")

class RuntimeConfig(BaseModel):
    """运行时配置模式"""
    auto_start: bool = Field(False, description="自动启动")
    auto_restart: bool = Field(True, description="自动重启")
    max_restarts: int = Field(3, description="最大重启次数")
    restart_delay: int = Field(5, description="重启延迟")
    health_check_interval: int = Field(30, description="健康检查间隔")
    timeout: int = Field(30, description="超时时间")

# 基础模式
class ToolBase(BaseModel):
    """工具基础模式"""
    name: str = Field(..., min_length=1, max_length=100, description="工具名称")
    display_name: str = Field(..., min_length=1, max_length=200, description="显示名称")
    description: Optional[str] = Field(None, description="工具描述")
    type: ToolType = Field(ToolType.CUSTOM, description="工具类型")
    category: Optional[str] = Field(None, max_length=50, description="工具分类")
    tags: List[str] = Field(default_factory=list, description="工具标签")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """验证工具名称"""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('工具名称只能包含字母、数字、下划线和连字符')
        return v

class ToolConfigBase(BaseModel):
    """工具配置基础模式"""
    command: str = Field(..., min_length=1, description="启动命令")
    working_directory: Optional[str] = Field(None, max_length=500, description="工作目录")
    environment_variables: Dict[str, str] = Field(default_factory=dict, description="环境变量")

    # 连接配置
    connection_type: ConnectionType = Field(ConnectionType.STDIO, description="连接类型")
    host: Optional[str] = Field(None, max_length=100, description="主机地址")
    port: Optional[int] = Field(None, ge=1, le=65535, description="端口号")
    path: Optional[str] = Field(None, max_length=200, description="路径")

    # 运行时配置
    auto_start: bool = Field(False, description="自动启动")
    restart_on_failure: bool = Field(True, description="失败时重启")
    max_restart_attempts: int = Field(3, ge=0, le=10, description="最大重启次数")
    timeout: int = Field(30, ge=5, le=300, description="超时时间（秒）")

    @field_validator('host')
    @classmethod
    def validate_host(cls, v, info):
        """验证主机地址"""
        connection_type = info.data.get('connection_type')
        if connection_type in [ConnectionType.HTTP, ConnectionType.WEBSOCKET] and not v:
            raise ValueError(f'{connection_type.value} 连接类型需要指定主机地址')
        return v

    @field_validator('port')
    @classmethod
    def validate_port(cls, v, info):
        """验证端口号"""
        connection_type = info.data.get('connection_type')
        if connection_type in [ConnectionType.HTTP, ConnectionType.WEBSOCKET] and not v:
            raise ValueError(f'{connection_type.value} 连接类型需要指定端口号')
        return v

class ToolMetadata(BaseModel):
    """工具元数据模式"""
    version: Optional[str] = Field(None, max_length=20, description="工具版本")
    author: Optional[str] = Field(None, max_length=100, description="作者")
    homepage: Optional[str] = Field(None, max_length=500, description="主页")

# 创建模式
class ToolCreate(ToolBase, ToolConfigBase, ToolMetadata):
    """创建工具模式"""
    enabled: bool = Field(True, description="是否启用")

# 更新模式
class ToolUpdate(BaseModel):
    """更新工具模式"""
    display_name: Optional[str] = Field(None, min_length=1, max_length=200, description="显示名称")
    description: Optional[str] = Field(None, description="工具描述")
    category: Optional[str] = Field(None, max_length=50, description="工具分类")
    tags: Optional[List[str]] = Field(None, description="工具标签")

    # 配置更新
    command: Optional[str] = Field(None, min_length=1, description="启动命令")
    working_directory: Optional[str] = Field(None, max_length=500, description="工作目录")
    environment_variables: Optional[Dict[str, str]] = Field(None, description="环境变量")

    connection_type: Optional[ConnectionType] = Field(None, description="连接类型")
    host: Optional[str] = Field(None, max_length=100, description="主机地址")
    port: Optional[int] = Field(None, ge=1, le=65535, description="端口号")
    path: Optional[str] = Field(None, max_length=200, description="路径")

    auto_start: Optional[bool] = Field(None, description="自动启动")
    restart_on_failure: Optional[bool] = Field(None, description="失败时重启")
    max_restart_attempts: Optional[int] = Field(None, ge=0, le=10, description="最大重启次数")
    timeout: Optional[int] = Field(None, ge=5, le=300, description="超时时间（秒）")

    # 元数据更新
    version: Optional[str] = Field(None, max_length=20, description="工具版本")
    author: Optional[str] = Field(None, max_length=100, description="作者")
    homepage: Optional[str] = Field(None, max_length=500, description="主页")

    enabled: Optional[bool] = Field(None, description="是否启用")

# 响应模式
class ToolResponse(ToolBase, ToolConfigBase, ToolMetadata):
    """工具响应模式"""
    id: int = Field(..., description="工具ID")
    status: ToolStatus = Field(..., description="当前状态")
    process_id: Optional[int] = Field(None, description="进程ID")
    last_started_at: Optional[datetime] = Field(None, description="最后启动时间")
    last_stopped_at: Optional[datetime] = Field(None, description="最后停止时间")
    restart_count: int = Field(0, description="重启次数")
    enabled: bool = Field(True, description="是否启用")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(from_attributes=True)

# 工具操作模式
class ToolAction(BaseModel):
    """工具操作模式"""
    action: str = Field(..., description="操作类型: start, stop, restart")
    force: bool = Field(False, description="是否强制执行")

    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        """验证操作类型"""
        allowed_actions = ['start', 'stop', 'restart']
        if v not in allowed_actions:
            raise ValueError(f'操作类型必须是: {", ".join(allowed_actions)}')
        return v

# 工具状态模式
class ToolStatusResponse(BaseModel):
    """工具状态响应模式"""
    id: int = Field(..., description="工具ID")
    name: str = Field(..., description="工具名称")
    status: ToolStatus = Field(..., description="当前状态")
    process_id: Optional[int] = Field(None, description="进程ID")
    last_started_at: Optional[datetime] = Field(None, description="最后启动时间")
    last_stopped_at: Optional[datetime] = Field(None, description="最后停止时间")
    restart_count: int = Field(0, description="重启次数")
    is_running: bool = Field(..., description="是否正在运行")
    can_start: bool = Field(..., description="是否可以启动")
    can_stop: bool = Field(..., description="是否可以停止")

    model_config = ConfigDict(from_attributes=True)

# 工具分类模式
class CategoryBase(BaseModel):
    """工具分类基础模式"""
    name: str = Field(..., min_length=1, max_length=50, description="分类名称")
    display_name: str = Field(..., min_length=1, max_length=100, description="显示名称")
    description: Optional[str] = Field(None, description="分类描述")
    icon: Optional[str] = Field(None, max_length=50, description="图标")
    color: Optional[str] = Field(None, max_length=20, description="颜色")
    sort_order: int = Field(0, description="排序")

class CategoryCreate(CategoryBase):
    """创建工具分类模式"""
    pass

class CategoryUpdate(BaseModel):
    """更新工具分类模式"""
    display_name: Optional[str] = Field(None, min_length=1, max_length=100, description="显示名称")
    description: Optional[str] = Field(None, description="分类描述")
    icon: Optional[str] = Field(None, max_length=50, description="图标")
    color: Optional[str] = Field(None, max_length=20, description="颜色")
    sort_order: Optional[int] = Field(None, description="排序")

class CategoryResponse(CategoryBase):
    """工具分类响应模式"""
    id: int = Field(..., description="分类ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(from_attributes=True)

# 批量操作模式
class ToolBatchAction(BaseModel):
    """工具批量操作模式"""
    tool_ids: List[int] = Field(..., min_length=1, description="工具ID列表")
    action: str = Field(..., description="操作类型: start, stop, restart, delete")
    force: bool = Field(False, description="是否强制执行")

    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        """验证操作类型"""
        allowed_actions = ['start', 'stop', 'restart', 'delete']
        if v not in allowed_actions:
            raise ValueError(f'操作类型必须是: {", ".join(allowed_actions)}')
        return v

# 导入导出模式
class ToolExport(BaseModel):
    """工具导出模式"""
    tools: List[ToolResponse] = Field(..., description="工具列表")
    categories: List[CategoryResponse] = Field(default_factory=list, description="分类列表")
    export_time: datetime = Field(..., description="导出时间")
    version: str = Field("1.0", description="导出格式版本")

class ToolImport(BaseModel):
    """工具导入模式"""
    tools: List[ToolCreate] = Field(..., description="工具列表")
    categories: List[CategoryCreate] = Field(default_factory=list, description="分类列表")
    overwrite_existing: bool = Field(False, description="是否覆盖已存在的工具")
