"""认证相关工具函数"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.user import User
from app.services.user_service import UserService


def get_current_user(db: Session = Depends(get_db)) -> User:
    """
    获取当前用户
    在单用户系统中，直接返回默认用户
    """
    try:
        user_service = UserService(db)
        user = user_service.get_or_create_default_user()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户未找到"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户已被禁用"
            )
        
        return user
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户信息失败: {str(e)}"
        )


def get_optional_current_user(db: Session = Depends(get_db)) -> Optional[User]:
    """
    获取当前用户（可选）
    如果获取失败则返回None而不是抛出异常
    """
    try:
        return get_current_user(db)
    except HTTPException:
        return None