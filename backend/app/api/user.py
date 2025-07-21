"""用户管理 API 路由"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from app.core.database import get_db
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserPasswordUpdate,
    UserPreferencesUpdate,
    UserResponse,
    UserPublicResponse
)
from app.services.users import UserService

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/user", tags=["用户管理"])

@router.get("/profile", response_model=UserPublicResponse, summary="获取用户资料")
async def get_user_profile(
    db: Session = Depends(get_db)
):
    """获取当前用户资料"""
    try:
        user_service = UserService(db)

        # 在单用户系统中，获取或创建默认用户
        user = user_service.get_or_create_default_user()

        return UserPublicResponse.from_orm(user)

    except Exception as e:
        logger.error(f"获取用户资料失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户资料失败"
        )

@router.put("/profile", response_model=UserPublicResponse, summary="更新用户资料")
async def update_user_profile(
    user_data: UserUpdate,
    db: Session = Depends(get_db)
):
    """更新用户资料"""
    try:
        user_service = UserService(db)

        # 获取当前用户
        current_user = user_service.get_or_create_default_user()

        # 更新用户信息
        updated_user = user_service.update_user(current_user.id, user_data)

        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        return UserPublicResponse.from_orm(updated_user)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"更新用户资料失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户资料失败"
        )

@router.put("/password", response_model=dict, summary="修改密码")
async def update_password(
    password_data: UserPasswordUpdate,
    db: Session = Depends(get_db)
):
    """修改用户密码"""
    try:
        user_service = UserService(db)

        # 获取当前用户
        current_user = user_service.get_or_create_default_user()

        # 更新密码
        success = user_service.update_password(current_user.id, password_data)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        return {
            "success": True,
            "message": "密码修改成功"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"修改密码失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="修改密码失败"
        )

@router.put("/preferences", response_model=UserPublicResponse, summary="更新用户偏好设置")
async def update_user_preferences(
    preferences_data: UserPreferencesUpdate,
    db: Session = Depends(get_db)
):
    """更新用户偏好设置"""
    try:
        user_service = UserService(db)

        # 获取当前用户
        current_user = user_service.get_or_create_default_user()

        # 更新偏好设置
        updated_user = user_service.update_preferences(current_user.id, preferences_data)

        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        return UserPublicResponse.from_orm(updated_user)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"更新用户偏好设置失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户偏好设置失败"
        )

@router.post("/create", response_model=UserResponse, summary="创建用户")
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """创建新用户（管理员功能）"""
    try:
        user_service = UserService(db)

        # 创建用户
        user = user_service.create_user(user_data)

        return UserResponse.from_orm(user)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"创建用户失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建用户失败"
        )

@router.get("/stats", response_model=dict, summary="获取用户统计信息")
async def get_user_stats(
    db: Session = Depends(get_db)
):
    """获取用户统计信息"""
    try:
        user_service = UserService(db)
        stats = user_service.get_user_stats()

        return {
            "success": True,
            "data": stats
        }

    except Exception as e:
        logger.error(f"获取用户统计信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户统计信息失败"
        )
