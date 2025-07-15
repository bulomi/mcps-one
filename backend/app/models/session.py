"""会话管理模型"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from datetime import datetime
from typing import Dict, Any

from app.core.database import Base


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


class MCPSession(Base):
    """MCP 会话模型"""
    __tablename__ = "mcp_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, index=True, nullable=False, comment="会话ID")
    session_type = Column(SQLEnum(SessionType), default=SessionType.USER, comment="会话类型")
    status = Column(SQLEnum(SessionStatus), default=SessionStatus.ACTIVE, comment="会话状态")
    
    # 会话信息
    name = Column(String(255), nullable=False, comment="会话名称")
    description = Column(Text, comment="会话描述")
    
    # 关联信息
    tool_id = Column(Integer, ForeignKey("mcp_tools.id"), nullable=True, comment="关联工具ID")
    user_id = Column(String(255), nullable=True, comment="用户ID")
    
    # 会话配置
    config = Column(Text, comment="会话配置(JSON)")
    session_metadata = Column(Text, comment="会话元数据(JSON)")
    
    # 统计信息
    request_count = Column(Integer, default=0, comment="请求次数")
    response_count = Column(Integer, default=0, comment="响应次数")
    error_count = Column(Integer, default=0, comment="错误次数")
    
    # 时间信息
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    last_activity_at = Column(DateTime, default=func.now(), comment="最后活动时间")
    expires_at = Column(DateTime, nullable=True, comment="过期时间")
    
    # 关联关系
    tool = relationship("MCPTool", back_populates="sessions")
    tasks = relationship("MCPTask", back_populates="session")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "session_type": self.session_type,
            "status": self.status,
            "name": self.name,
            "description": self.description,
            "tool_id": self.tool_id,
            "user_id": self.user_id,
            "config": self.config,
            "metadata": self.session_metadata,
            "request_count": self.request_count,
            "response_count": self.response_count,
            "error_count": self.error_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_activity_at": self.last_activity_at.isoformat() if self.last_activity_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }
    
    def is_active(self) -> bool:
        """检查会话是否活跃"""
        if self.status != SessionStatus.ACTIVE:
            return False
        
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        
        return True
    
    def update_activity(self):
        """更新最后活动时间"""
        self.last_activity_at = datetime.utcnow()
    
    def increment_request(self):
        """增加请求计数"""
        self.request_count += 1
        self.update_activity()
    
    def increment_response(self):
        """增加响应计数"""
        self.response_count += 1
        self.update_activity()
    
    def increment_error(self):
        """增加错误计数"""
        self.error_count += 1
        self.update_activity()