"""会话管理服务"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
import uuid
import json
import logging

from app.models.session import MCPSession, SessionStatus, SessionType
from app.models.tool import MCPTool
from app.schemas.session import (
    SessionCreate,
    SessionUpdate,
    SessionStatsResponse,
)
from app.utils.exceptions import (
    SessionNotFoundError,
    SessionOperationError,
)
from app.core.unified_logging import get_logger

logger = get_logger(__name__)

# 常量定义
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200
DEFAULT_RECENT_LIMIT = 10


class SessionService:
    """会话管理服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_sessions(
        self,
        page: int = 1,
        size: int = DEFAULT_PAGE_SIZE,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[MCPSession], int]:
        """获取会话列表"""
        query = self.db.query(MCPSession)

        # 应用过滤条件
        if filters:
            if filters.get('status'):
                query = query.filter(MCPSession.status == filters['status'])

            if filters.get('session_type'):
                query = query.filter(MCPSession.session_type == filters['session_type'])

            if filters.get('tool_id'):
                query = query.filter(MCPSession.tool_id == filters['tool_id'])

            if filters.get('user_id'):
                query = query.filter(MCPSession.user_id == filters['user_id'])

            if filters.get('search'):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        MCPSession.name.ilike(search_term),
                        MCPSession.description.ilike(search_term),
                        MCPSession.session_id.ilike(search_term)
                    )
                )

            if filters.get('created_after'):
                query = query.filter(MCPSession.created_at >= filters['created_after'])

            if filters.get('created_before'):
                query = query.filter(MCPSession.created_at <= filters['created_before'])

        # 获取总数
        total = query.count()

        # 分页和排序
        sessions = query.order_by(
            desc(MCPSession.last_activity_at)
        ).offset((page - 1) * size).limit(size).all()

        return sessions, total

    def get_session(self, session_id: str) -> Optional[MCPSession]:
        """获取会话详情"""
        return self.db.query(MCPSession).filter(
            MCPSession.session_id == session_id
        ).first()

    def get_session_by_id(self, id: int) -> Optional[MCPSession]:
        """根据ID获取会话"""
        return self.db.query(MCPSession).filter(MCPSession.id == id).first()

    def create_session(self, session_data: SessionCreate) -> MCPSession:
        """创建会话"""
        try:
            # 生成唯一的会话ID
            session_id = str(uuid.uuid4())

            # 验证工具是否存在
            if session_data.tool_id:
                tool = self.db.query(MCPTool).filter(
                    MCPTool.id == session_data.tool_id
                ).first()
                if not tool:
                    raise SessionOperationError(f"工具不存在: {session_data.tool_id}")

            session = MCPSession(
                session_id=session_id,
                name=session_data.name,
                description=session_data.description,
                session_type=session_data.session_type,
                tool_id=session_data.tool_id,
                user_id=session_data.user_id,
                config=json.dumps(session_data.config) if session_data.config else None,
                metadata=json.dumps(session_data.metadata) if session_data.metadata else None,
                expires_at=session_data.expires_at,
                status=SessionStatus.ACTIVE,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                last_activity_at=datetime.utcnow()
            )

            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)

            logger.info(f"会话创建成功: {session.session_id}")
            return session

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建会话失败: {e}")
            raise SessionOperationError(f"创建会话失败: {e}")

    def update_session(self, session_id: str, session_data: SessionUpdate) -> MCPSession:
        """更新会话"""
        try:
            session = self.get_session(session_id)
            if not session:
                raise SessionNotFoundError(f"会话不存在: {session_id}")

            # 更新字段
            update_data = session_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                if field in ['config', 'metadata'] and value is not None:
                    value = json.dumps(value)
                setattr(session, field, value)

            session.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(session)

            logger.info(f"会话更新成功: {session.session_id}")
            return session

        except Exception as e:
            self.db.rollback()
            logger.error(f"更新会话失败: {e}")
            raise

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        try:
            session = self.get_session(session_id)
            if not session:
                raise SessionNotFoundError(f"会话不存在: {session_id}")

            # 检查会话是否可以删除
            if session.status == SessionStatus.ACTIVE:
                # 先终止会话
                session.status = SessionStatus.TERMINATED
                session.updated_at = datetime.utcnow()

            self.db.delete(session)
            self.db.commit()

            logger.info(f"会话删除成功: {session_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"删除会话失败: {e}")
            raise

    def activate_session(self, session_id: str) -> MCPSession:
        """激活会话"""
        try:
            session = self.get_session(session_id)
            if not session:
                raise SessionNotFoundError(f"会话不存在: {session_id}")

            session.status = SessionStatus.ACTIVE
            session.last_activity_at = datetime.utcnow()
            session.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(session)

            logger.info(f"会话激活成功: {session_id}")
            return session

        except Exception as e:
            self.db.rollback()
            logger.error(f"激活会话失败: {e}")
            raise

    def deactivate_session(self, session_id: str) -> MCPSession:
        """停用会话"""
        try:
            session = self.get_session(session_id)
            if not session:
                raise SessionNotFoundError(f"会话不存在: {session_id}")

            session.status = SessionStatus.INACTIVE
            session.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(session)

            logger.info(f"会话停用成功: {session_id}")
            return session

        except Exception as e:
            self.db.rollback()
            logger.error(f"停用会话失败: {e}")
            raise

    def terminate_session(self, session_id: str) -> MCPSession:
        """终止会话"""
        try:
            session = self.get_session(session_id)
            if not session:
                raise SessionNotFoundError(f"会话不存在: {session_id}")

            session.status = SessionStatus.TERMINATED
            session.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(session)

            logger.info(f"会话终止成功: {session_id}")
            return session

        except Exception as e:
            self.db.rollback()
            logger.error(f"终止会话失败: {e}")
            raise

    def update_session_activity(self, session_id: str) -> MCPSession:
        """更新会话活动时间"""
        try:
            session = self.get_session(session_id)
            if not session:
                raise SessionNotFoundError(f"会话不存在: {session_id}")

            session.update_activity()
            session.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(session)

            return session

        except Exception as e:
            self.db.rollback()
            logger.error(f"更新会话活动失败: {e}")
            raise

    def increment_session_request(self, session_id: str) -> MCPSession:
        """增加会话请求计数"""
        try:
            session = self.get_session(session_id)
            if not session:
                raise SessionNotFoundError(f"会话不存在: {session_id}")

            session.increment_request()
            session.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(session)

            return session

        except Exception as e:
            self.db.rollback()
            logger.error(f"增加会话请求计数失败: {e}")
            raise

    def increment_session_response(self, session_id: str) -> MCPSession:
        """增加会话响应计数"""
        try:
            session = self.get_session(session_id)
            if not session:
                raise SessionNotFoundError(f"会话不存在: {session_id}")

            session.increment_response()
            session.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(session)

            return session

        except Exception as e:
            self.db.rollback()
            logger.error(f"增加会话响应计数失败: {e}")
            raise

    def increment_session_error(self, session_id: str) -> MCPSession:
        """增加会话错误计数"""
        try:
            session = self.get_session(session_id)
            if not session:
                raise SessionNotFoundError(f"会话不存在: {session_id}")

            session.increment_error()
            session.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(session)

            return session

        except Exception as e:
            self.db.rollback()
            logger.error(f"增加会话错误计数失败: {e}")
            raise

    def get_session_stats(self) -> SessionStatsResponse:
        """获取会话统计信息"""
        try:
            # 基础统计
            total_sessions = self.db.query(MCPSession).count()
            active_sessions = self.db.query(MCPSession).filter(
                MCPSession.status == SessionStatus.ACTIVE
            ).count()
            inactive_sessions = self.db.query(MCPSession).filter(
                MCPSession.status == SessionStatus.INACTIVE
            ).count()
            expired_sessions = self.db.query(MCPSession).filter(
                MCPSession.status == SessionStatus.EXPIRED
            ).count()
            terminated_sessions = self.db.query(MCPSession).filter(
                MCPSession.status == SessionStatus.TERMINATED
            ).count()

            # 请求响应统计
            total_requests = self.db.query(func.sum(MCPSession.request_count)).scalar() or 0
            total_responses = self.db.query(func.sum(MCPSession.response_count)).scalar() or 0
            total_errors = self.db.query(func.sum(MCPSession.error_count)).scalar() or 0

            # 平均会话持续时间（分钟）
            completed_sessions = self.db.query(MCPSession).filter(
                and_(
                    MCPSession.status.in_([SessionStatus.TERMINATED, SessionStatus.EXPIRED]),
                    MCPSession.created_at.isnot(None),
                    MCPSession.updated_at.isnot(None)
                )
            ).all()

            if completed_sessions:
                total_duration = sum(
                    (session.updated_at - session.created_at).total_seconds() / 60
                    for session in completed_sessions
                )
                avg_session_duration = total_duration / len(completed_sessions)
            else:
                avg_session_duration = 0.0

            return SessionStatsResponse(
                total_sessions=total_sessions,
                active_sessions=active_sessions,
                inactive_sessions=inactive_sessions,
                expired_sessions=expired_sessions,
                terminated_sessions=terminated_sessions,
                total_requests=total_requests,
                total_responses=total_responses,
                total_errors=total_errors,
                avg_session_duration=round(avg_session_duration, 2)
            )

        except Exception as e:
            logger.error(f"获取会话统计失败: {e}")
            raise

    def cleanup_expired_sessions(self) -> int:
        """清理过期会话"""
        try:
            current_time = datetime.utcnow()

            # 查找过期的活跃会话
            expired_sessions = self.db.query(MCPSession).filter(
                and_(
                    MCPSession.status == SessionStatus.ACTIVE,
                    MCPSession.expires_at.isnot(None),
                    MCPSession.expires_at < current_time
                )
            ).all()

            count = 0
            for session in expired_sessions:
                session.status = SessionStatus.EXPIRED
                session.updated_at = current_time
                count += 1

            if count > 0:
                self.db.commit()
                logger.info(f"清理过期会话: {count} 个")

            return count

        except Exception as e:
            self.db.rollback()
            logger.error(f"清理过期会话失败: {e}")
            raise

    def get_recent_sessions(self, limit: int = DEFAULT_RECENT_LIMIT) -> List[MCPSession]:
        """获取最近的会话"""
        return self.db.query(MCPSession).order_by(
            desc(MCPSession.last_activity_at)
        ).limit(limit).all()
