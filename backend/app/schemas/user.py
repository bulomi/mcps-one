"""用户相关的 Pydantic 模式定义"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """用户基础模式"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="姓名")
    phone: Optional[str] = Field(None, max_length=20, description="电话号码")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")
    avatar_url: Optional[str] = Field(None, max_length=500, description="头像URL")

class UserCreate(UserBase):
    """创建用户模式"""
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码长度至少6位')
        return v

class UserUpdate(BaseModel):
    """更新用户模式"""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="姓名")
    phone: Optional[str] = Field(None, max_length=20, description="电话号码")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")
    avatar_url: Optional[str] = Field(None, max_length=500, description="头像URL")

class UserPasswordUpdate(BaseModel):
    """更新密码模式"""
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")
    confirm_password: str = Field(..., description="确认密码")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('两次输入的密码不一致')
        return v
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码长度至少6位')
        return v

class UserPreferencesUpdate(BaseModel):
    """更新用户偏好设置模式"""
    theme: Optional[str] = Field(None, description="主题设置")
    language: Optional[str] = Field(None, description="语言设置")
    timezone: Optional[str] = Field(None, description="时区设置")
    email_notifications: Optional[bool] = Field(None, description="邮件通知")
    
    @validator('theme')
    def validate_theme(cls, v):
        if v and v not in ['light', 'dark', 'auto']:
            raise ValueError('主题设置必须是 light、dark 或 auto')
        return v

class UserResponse(BaseModel):
    """用户响应模式"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    theme: str
    language: str
    timezone: str
    email_notifications: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserPublicResponse(BaseModel):
    """用户公开信息响应模式"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    theme: str
    language: str
    timezone: str
    email_notifications: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True