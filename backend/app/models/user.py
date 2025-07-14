"""用户相关数据模型"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, Any, Optional

from app.core.database import Base

class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False, comment="用户名")
    email = Column(String(100), unique=True, index=True, nullable=False, comment="邮箱")
    full_name = Column(String(100), comment="姓名")
    phone = Column(String(20), comment="电话号码")
    bio = Column(Text, comment="个人简介")
    avatar_url = Column(String(500), comment="头像URL")
    
    # 安全相关
    password_hash = Column(String(255), comment="密码哈希")
    is_active = Column(Boolean, default=True, comment="是否激活")
    
    # 偏好设置
    theme = Column(String(20), default="light", comment="主题设置")
    language = Column(String(10), default="zh-CN", comment="语言设置")
    timezone = Column(String(50), default="Asia/Shanghai", comment="时区设置")
    email_notifications = Column(Boolean, default=True, comment="邮件通知")
    
    # 系统字段
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    last_login_at = Column(DateTime, comment="最后登录时间")
    
    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "phone": self.phone,
            "bio": self.bio,
            "avatar_url": self.avatar_url,
            "is_active": self.is_active,
            "theme": self.theme,
            "language": self.language,
            "timezone": self.timezone,
            "email_notifications": self.email_notifications,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }
    
    def to_public_dict(self) -> Dict[str, Any]:
        """转换为公开字典（不包含敏感信息）"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "phone": self.phone,
            "bio": self.bio,
            "avatar_url": self.avatar_url,
            "theme": self.theme,
            "language": self.language,
            "timezone": self.timezone,
            "email_notifications": self.email_notifications,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }