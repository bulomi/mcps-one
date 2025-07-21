"""认证相关工具函数"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.user import User
from app.services.users import UserService
from app.utils.jwt_utils import verify_token
from app.schemas.auth import TokenData

# HTTP Bearer 认证方案
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前用户（基于JWT认证）
    """
    try:
        # 验证JWT令牌
        token_data: TokenData = verify_token(credentials.credentials)

        # 根据令牌中的用户ID获取用户
        user_service = UserService(db)
        user = user_service.get_user_by_id(token_data.user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户未找到",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户已被禁用",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户信息失败: {str(e)}"
        )


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    获取当前用户（可选）
    如果获取失败则返回None而不是抛出异常
    """
    try:
        if not credentials:
            return None
        return get_current_user(credentials, db)
    except HTTPException:
        return None

def get_current_user_legacy(db: Session = Depends(get_db)) -> User:
    """
    获取当前用户（兼容模式）
    在单用户系统中，直接返回默认用户
    用于向后兼容不需要认证的API
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
