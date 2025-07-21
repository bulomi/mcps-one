"""会话管理相关的 Pydantic 模型"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class SessionStatus(str, Enum):
    """会话状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class SessionType(str, Enum):
    """会话类型"""
    USER = "user"
    SYSTEM = "system"
    API = "api"
    MCP = "mcp"


class SessionBase(BaseModel):
    """会话基础模型"""
    name: str = Field(..., min_length=1, max_length=255, description="会话名称")
    description: Optional[str] = Field(None, description="会话描述")
    session_type: SessionType = Field(SessionType.USER, description="会话类型")
    tool_id: Optional[int] = Field(None, description="关联工具ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    config: Optional[Dict[str, Any]] = Field(None, description="会话配置")
    metadata: Optional[Dict[str, Any]] = Field(None, description="会话元数据")
    expires_at: Optional[datetime] = Field(None, description="过期时间")


class SessionCreate(SessionBase):
    """创建会话模型"""
    pass


class SessionUpdate(BaseModel):
    """更新会话模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="会话名称")
    description: Optional[str] = Field(None, description="会话描述")
    status: Optional[SessionStatus] = Field(None, description="会话状态")
    config: Optional[Dict[str, Any]] = Field(None, description="会话配置")
    metadata: Optional[Dict[str, Any]] = Field(None, description="会话元数据")
    expires_at: Optional[datetime] = Field(None, description="过期时间")


class SessionResponse(SessionBase):
    """会话响应模型"""
    id: int
    session_id: str
    status: SessionStatus
    request_count: int = 0
    response_count: int = 0
    error_count: int = 0
    created_at: datetime
    updated_at: datetime
    last_activity_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SessionListResponse(BaseModel):
    """会话列表响应模型"""
    items: List[SessionResponse]
    total: int
    page: int
    size: int
    pages: int


class SessionStatsResponse(BaseModel):
    """会话统计响应模型"""
    total_sessions: int
    active_sessions: int
    inactive_sessions: int
    expired_sessions: int
    terminated_sessions: int
    total_requests: int
    total_responses: int
    total_errors: int
    avg_session_duration: float  # 平均会话持续时间（分钟）


class SessionActivityRequest(BaseModel):
    """会话活动请求模型"""
    action: str = Field(..., description="活动类型")
    data: Optional[Dict[str, Any]] = Field(None, description="活动数据")


class SessionActivityResponse(BaseModel):
    """会话活动响应模型"""
    session_id: str
    action: str
    timestamp: datetime
    success: bool
    message: Optional[str] = None
