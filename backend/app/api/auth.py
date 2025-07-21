"""认证 API 路由"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging
from datetime import timedelta

from app.core.database import get_db
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    ChangePasswordRequest,
    RefreshTokenRequest
)
from app.schemas.user import UserPublicResponse
from app.services.users import UserService
from app.utils.jwt_utils import (
    create_access_token,
    create_refresh_token,
    verify_token,
    get_token_expire_time
)
from app.utils.auth import get_current_user
from app.utils.response import success_response, error_response

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/auth", tags=["认证"])

@router.post("/login/", response_model=dict, summary="用户登录")
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """用户登录"""
    try:
        user_service = UserService(db)

        # 验证用户凭据
        user = user_service.authenticate_user(login_data.username, login_data.password)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户账户已被禁用",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 创建访问令牌
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"user_id": user.id, "username": user.username},
            expires_delta=access_token_expires
        )

        # 创建刷新令牌
        refresh_token = create_refresh_token(
            data={"user_id": user.id, "username": user.username}
        )

        # 更新最后登录时间
        user_service.update_last_login(user.id)

        return success_response(
            data={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": get_token_expire_time(),
                "user": user.to_public_dict()
            },
            message="登录成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败"
        )

@router.post("/refresh/", response_model=dict, summary="刷新令牌")
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """刷新访问令牌"""
    try:
        # 验证刷新令牌
        token_data = verify_token(refresh_data.refresh_token, token_type="refresh")

        # 获取用户信息
        user_service = UserService(db)
        user = user_service.get_user_by_id(token_data.user_id)

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在或已被禁用",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 创建新的访问令牌
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"user_id": user.id, "username": user.username},
            expires_delta=access_token_expires
        )

        return success_response(
            data={
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": get_token_expire_time()
            },
            message="令牌刷新成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刷新令牌失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="刷新令牌失败"
        )

@router.post("/logout/", response_model=dict, summary="用户登出")
async def logout(
    current_user = Depends(get_current_user)
):
    """用户登出"""
    try:
        # 在实际应用中，这里可以将令牌加入黑名单
        # 目前只是返回成功响应
        return success_response(
            data={},
            message="登出成功"
        )

    except Exception as e:
        logger.error(f"登出失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登出失败"
        )

@router.get("/me/", response_model=dict, summary="获取当前用户信息")
async def get_current_user_info(
    current_user = Depends(get_current_user)
):
    """获取当前用户信息"""
    try:
        return success_response(
            data=current_user.to_public_dict(),
            message="获取用户信息成功"
        )

    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户信息失败"
        )

@router.post("/change-password", response_model=dict, summary="修改密码")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """修改密码"""
    try:
        user_service = UserService(db)

        # 验证旧密码
        if not user_service._verify_password(password_data.old_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="旧密码不正确"
            )

        # 创建密码更新对象
        from app.schemas.user import UserPasswordUpdate
        password_update = UserPasswordUpdate(
            current_password=password_data.old_password,
            new_password=password_data.new_password,
            confirm_password=password_data.new_password
        )

        # 更新密码
        success = user_service.update_password(current_user.id, password_update)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="密码更新失败"
            )

        return success_response(
            data={},
            message="密码修改成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"修改密码失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="修改密码失败"
        )
