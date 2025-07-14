"""用户管理服务"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Optional, Dict, Any
from datetime import datetime
import hashlib
import secrets
import logging

from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserPasswordUpdate,
    UserPreferencesUpdate
)

logger = logging.getLogger(__name__)

class UserService:
    """用户服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _hash_password(self, password: str) -> str:
        """密码哈希"""
        # 生成随机盐
        salt = secrets.token_hex(16)
        # 使用 SHA-256 哈希
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """验证密码"""
        try:
            salt, hash_value = password_hash.split(':')
            return hashlib.sha256((password + salt).encode()).hexdigest() == hash_value
        except ValueError:
            return False
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return self.db.query(User).filter(User.email == email).first()
    
    def create_user(self, user_data: UserCreate) -> User:
        """创建用户"""
        try:
            # 检查用户名是否已存在
            if self.get_user_by_username(user_data.username):
                raise ValueError("用户名已存在")
            
            # 检查邮箱是否已存在
            if self.get_user_by_email(user_data.email):
                raise ValueError("邮箱已存在")
            
            # 创建用户
            user = User(
                username=user_data.username,
                email=user_data.email,
                full_name=user_data.full_name,
                phone=user_data.phone,
                bio=user_data.bio,
                avatar_url=user_data.avatar_url,
                password_hash=self._hash_password(user_data.password)
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"用户创建成功: {user.username}")
            return user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建用户失败: {str(e)}")
            raise
    
    def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """更新用户信息"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return None
            
            # 检查用户名是否已被其他用户使用
            if user_data.username and user_data.username != user.username:
                existing_user = self.get_user_by_username(user_data.username)
                if existing_user and existing_user.id != user_id:
                    raise ValueError("用户名已存在")
            
            # 检查邮箱是否已被其他用户使用
            if user_data.email and user_data.email != user.email:
                existing_user = self.get_user_by_email(user_data.email)
                if existing_user and existing_user.id != user_id:
                    raise ValueError("邮箱已存在")
            
            # 更新用户信息
            update_data = user_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(user, field, value)
            
            user.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"用户信息更新成功: {user.username}")
            return user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新用户信息失败: {str(e)}")
            raise
    
    def update_password(self, user_id: int, password_data: UserPasswordUpdate) -> bool:
        """更新用户密码"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            # 验证当前密码
            if not self._verify_password(password_data.current_password, user.password_hash):
                raise ValueError("当前密码不正确")
            
            # 更新密码
            user.password_hash = self._hash_password(password_data.new_password)
            user.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"用户密码更新成功: {user.username}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新用户密码失败: {str(e)}")
            raise
    
    def update_preferences(self, user_id: int, preferences_data: UserPreferencesUpdate) -> Optional[User]:
        """更新用户偏好设置"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return None
            
            # 更新偏好设置
            update_data = preferences_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(user, field, value)
            
            user.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"用户偏好设置更新成功: {user.username}")
            return user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新用户偏好设置失败: {str(e)}")
            raise
    
    def get_or_create_default_user(self) -> User:
        """获取或创建默认用户（单用户系统）"""
        try:
            # 查找现有用户
            user = self.db.query(User).first()
            if user:
                return user
            
            # 创建默认用户
            default_user = User(
                username="admin",
                email="admin@mcps.one",
                full_name="系统管理员",
                password_hash=self._hash_password("admin123"),
                is_active=True
            )
            
            self.db.add(default_user)
            self.db.commit()
            self.db.refresh(default_user)
            
            logger.info("默认用户创建成功")
            return default_user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"获取或创建默认用户失败: {str(e)}")
            raise
    
    def update_last_login(self, user_id: int) -> None:
        """更新最后登录时间"""
        try:
            user = self.get_user_by_id(user_id)
            if user:
                user.last_login_at = datetime.utcnow()
                self.db.commit()
        except Exception as e:
            logger.error(f"更新最后登录时间失败: {str(e)}")
    
    def get_user_stats(self) -> Dict[str, Any]:
        """获取用户统计信息"""
        try:
            total_users = self.db.query(User).count()
            active_users = self.db.query(User).filter(User.is_active == True).count()
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "inactive_users": total_users - active_users
            }
            
        except Exception as e:
            logger.error(f"获取用户统计信息失败: {str(e)}")
            return {
                "total_users": 0,
                "active_users": 0,
                "inactive_users": 0
            }