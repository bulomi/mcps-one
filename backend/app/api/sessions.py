"""会话管理API路由"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.core.database import get_db
from app.services.session_service import SessionService
from app.schemas.session import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    SessionListResponse,
    SessionStatsResponse,
    SessionActivityRequest,
    SessionActivityResponse,
)
from app.utils.exceptions import (
    SessionNotFoundError,
    SessionOperationError,
)
from app.utils.response import success_response, error_response

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/", response_model=SessionListResponse)
async def get_sessions(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(50, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="会话状态过滤"),
    session_type: Optional[str] = Query(None, description="会话类型过滤"),
    tool_id: Optional[int] = Query(None, description="工具ID过滤"),
    user_id: Optional[int] = Query(None, description="用户ID过滤"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    created_after: Optional[datetime] = Query(None, description="创建时间起始"),
    created_before: Optional[datetime] = Query(None, description="创建时间结束"),
    db: Session = Depends(get_db)
):
    """获取会话列表"""
    try:
        service = SessionService(db)
        
        # 构建过滤条件
        filters = {}
        if status:
            filters['status'] = status
        if session_type:
            filters['session_type'] = session_type
        if tool_id:
            filters['tool_id'] = tool_id
        if user_id:
            filters['user_id'] = user_id
        if search:
            filters['search'] = search
        if created_after:
            filters['created_after'] = created_after
        if created_before:
            filters['created_before'] = created_before
        
        sessions, total = service.get_sessions(page, size, filters)
        
        return SessionListResponse(
            sessions=[SessionResponse.from_orm(session) for session in sessions],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")


@router.get("/stats", response_model=SessionStatsResponse)
async def get_session_stats(db: Session = Depends(get_db)):
    """获取会话统计信息"""
    try:
        service = SessionService(db)
        stats = service.get_session_stats()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话统计失败: {str(e)}")


@router.get("/recent")
async def get_recent_sessions(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db: Session = Depends(get_db)
):
    """获取最近的会话"""
    try:
        service = SessionService(db)
        sessions = service.get_recent_sessions(limit)
        
        return success_response(
            data=[SessionResponse.from_orm(session) for session in sessions],
            message="获取最近会话成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取最近会话失败: {str(e)}")


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """获取会话详情"""
    try:
        service = SessionService(db)
        session = service.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")
        
        return SessionResponse.from_orm(session)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话详情失败: {str(e)}")


@router.post("/", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    db: Session = Depends(get_db)
):
    """创建会话"""
    try:
        service = SessionService(db)
        session = service.create_session(session_data)
        
        return SessionResponse.from_orm(session)
        
    except SessionOperationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建会话失败: {str(e)}")


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    session_data: SessionUpdate,
    db: Session = Depends(get_db)
):
    """更新会话"""
    try:
        service = SessionService(db)
        session = service.update_session(session_id, session_data)
        
        return SessionResponse.from_orm(session)
        
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SessionOperationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新会话失败: {str(e)}")


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """删除会话"""
    try:
        service = SessionService(db)
        success = service.delete_session(session_id)
        
        if success:
            return success_response(message="会话删除成功")
        else:
            raise HTTPException(status_code=400, detail="删除会话失败")
        
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除会话失败: {str(e)}")


@router.post("/{session_id}/activate", response_model=SessionResponse)
async def activate_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """激活会话"""
    try:
        service = SessionService(db)
        session = service.activate_session(session_id)
        
        return SessionResponse.from_orm(session)
        
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SessionOperationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"激活会话失败: {str(e)}")


@router.post("/{session_id}/deactivate", response_model=SessionResponse)
async def deactivate_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """停用会话"""
    try:
        service = SessionService(db)
        session = service.deactivate_session(session_id)
        
        return SessionResponse.from_orm(session)
        
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SessionOperationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停用会话失败: {str(e)}")


@router.post("/{session_id}/terminate", response_model=SessionResponse)
async def terminate_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """终止会话"""
    try:
        service = SessionService(db)
        session = service.terminate_session(session_id)
        
        return SessionResponse.from_orm(session)
        
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SessionOperationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"终止会话失败: {str(e)}")


@router.post("/{session_id}/activity", response_model=SessionActivityResponse)
async def update_session_activity(
    session_id: str,
    activity_data: SessionActivityRequest,
    db: Session = Depends(get_db)
):
    """更新会话活动"""
    try:
        service = SessionService(db)
        
        # 更新活动时间
        session = service.update_session_activity(session_id)
        
        # 根据活动类型增加相应计数
        if activity_data.activity_type == "request":
            session = service.increment_session_request(session_id)
        elif activity_data.activity_type == "response":
            session = service.increment_session_response(session_id)
        elif activity_data.activity_type == "error":
            session = service.increment_session_error(session_id)
        
        return SessionActivityResponse(
            session_id=session.session_id,
            activity_type=activity_data.activity_type,
            timestamp=session.last_activity_at,
            request_count=session.request_count,
            response_count=session.response_count,
            error_count=session.error_count
        )
        
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新会话活动失败: {str(e)}")


@router.post("/cleanup")
async def cleanup_expired_sessions(db: Session = Depends(get_db)):
    """清理过期会话"""
    try:
        service = SessionService(db)
        count = service.cleanup_expired_sessions()
        
        return success_response(
            data={"cleaned_count": count},
            message=f"清理过期会话完成，共清理 {count} 个会话"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理过期会话失败: {str(e)}")