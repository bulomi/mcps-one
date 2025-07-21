"""自动会话管理API路由"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.sessions import AutoSessionService
from app.services.sessions.auto_session_service import AutoSessionConfig, SessionLifecycleState
from app.schemas.mcp_agent import (
    AgentExecuteRequest,
    AgentExecuteResponse
)
from app.utils.response import success_response, error_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auto-session", tags=["自动会话管理"])

# 请求模型
class AutoSessionRequest(BaseModel):
    """自动会话请求"""
    message: str = Field(..., description="任务消息")
    task_type: str = Field("general", description="任务类型")
    context: Optional[Dict[str, Any]] = Field(None, description="请求上下文")
    parallel: bool = Field(False, description="是否并行执行")
    max_iterations: int = Field(10, description="最大迭代次数")
    timeout: int = Field(300, description="超时时间（秒）")

class AutoSessionConfigUpdate(BaseModel):
    """自动会话配置更新"""
    idle_timeout: Optional[int] = Field(None, description="空闲超时时间（秒）")
    hibernation_timeout: Optional[int] = Field(None, description="休眠超时时间（秒）")
    max_session_lifetime: Optional[int] = Field(None, description="最大会话生命周期（秒）")
    max_concurrent_sessions: Optional[int] = Field(None, description="最大并发会话数")
    session_pool_size: Optional[int] = Field(None, description="会话池大小")
    enable_auto_tool_selection: Optional[bool] = Field(None, description="启用自动工具选择")
    tool_selection_strategy: Optional[str] = Field(None, description="工具选择策略")
    cleanup_interval: Optional[int] = Field(None, description="清理间隔（秒）")

class SessionActionRequest(BaseModel):
    """会话操作请求"""
    action: str = Field(..., description="操作类型: wake_up, hibernate, destroy")
    force: bool = Field(False, description="是否强制执行")

# API路由
@router.post("/execute", response_model=dict, summary="自动执行任务")
async def auto_execute_task(
    request: AutoSessionRequest,
    db: Session = Depends(get_db)
):
    """自动创建会话并执行任务"""
    try:
        manager = AutoSessionService()

        # 构建请求上下文
        request_context = {
            "message": request.message,
            "task_type": request.task_type,
            "parallel": request.parallel,
            "max_iterations": request.max_iterations,
            "timeout": request.timeout
        }

        if request.context:
            request_context.update(request.context)

        # 自动创建会话
        session_id = await manager.auto_create_session(request_context, db)

        # 构建执行请求
        execute_request = AgentExecuteRequest(
            message=request.message,
            context=request_context
        )

        # 执行任务
        from app.services.mcp import get_agent_service
        agent_service = get_agent_service()
        task = await agent_service.execute_task(session_id, execute_request)

        return success_response(
            data={
                "session_id": session_id,
                "task_id": task.task_id,
                "status": task.status.value,
                "message": "任务已自动提交执行",
                "auto_created": True
            },
            message="自动会话创建并执行任务成功"
        )

    except Exception as e:
        logger.error(f"自动执行任务失败: {e}")
        return error_response(message="自动执行任务失败", error_code=str(e))

@router.get("/sessions/", response_model=dict, summary="获取所有自动会话")
async def get_auto_sessions():
    """获取所有自动管理的会话信息"""
    try:
        manager = AutoSessionService()
        sessions_info = await manager.get_all_sessions_info()

        return success_response(
            data={
                "sessions": sessions_info,
                "total": len(sessions_info)
            },
            message="获取自动会话列表成功"
        )

    except Exception as e:
        logger.error(f"获取自动会话失败: {e}")
        return error_response(message="获取自动会话失败", error_code=str(e))

@router.get("/sessions/{session_id}", response_model=dict, summary="获取会话详情")
async def get_auto_session_info(session_id: str):
    """获取指定会话的详细信息"""
    try:
        manager = AutoSessionService()
        session_info = await manager.get_session_info(session_id)

        if not session_info:
            return error_response(message="会话不存在", status_code=404)

        return success_response(
            data=session_info,
            message="获取会话信息成功"
        )

    except Exception as e:
        logger.error(f"获取会话信息失败: {e}")
        return error_response(message="获取会话信息失败", error_code=str(e))

@router.post("/sessions/{session_id}/action", response_model=dict, summary="会话操作")
async def session_action(
    session_id: str,
    request: SessionActionRequest
):
    """对会话执行操作（唤醒、休眠、销毁）"""
    try:
        manager = AutoSessionService()

        if request.action == "wake_up":
            await manager._wake_up_session(session_id, {})
            message = "会话已唤醒"

        elif request.action == "hibernate":
            await manager._transition_to_hibernation(session_id)
            message = "会话已休眠"

        elif request.action == "destroy":
            await manager._destroy_session(session_id)
            message = "会话已销毁"

        else:
            return error_response(message="不支持的操作类型", status_code=400)

        return success_response(
            data={
                "session_id": session_id,
                "action": request.action,
                "success": True
            },
            message=message
        )

    except Exception as e:
        logger.error(f"会话操作失败: {e}")
        return error_response(message="会话操作失败", error_code=str(e))

@router.get("/stats/", response_model=dict, summary="获取自动会话统计")
async def get_auto_session_stats():
    """获取自动会话管理统计信息"""
    try:
        manager = AutoSessionService()
        sessions_info = await manager.get_all_sessions_info()

        # 统计各状态的会话数量
        stats = {
            "total_sessions": len(sessions_info),
            "active_sessions": 0,
            "idle_sessions": 0,
            "hibernating_sessions": 0,
            "pool_size": len(manager.session_pool),
            "max_concurrent": manager.config.max_concurrent_sessions,
            "config": {
                "idle_timeout": manager.config.idle_timeout,
                "hibernation_timeout": manager.config.hibernation_timeout,
                "max_session_lifetime": manager.config.max_session_lifetime,
                "session_pool_size": manager.config.session_pool_size,
                "auto_tool_selection": manager.config.enable_auto_tool_selection,
                "tool_selection_strategy": manager.config.tool_selection_strategy
            }
        }

        for session_info in sessions_info:
            state = session_info.get("state", "active")
            if state == SessionLifecycleState.ACTIVE.value:
                stats["active_sessions"] += 1
            elif state == SessionLifecycleState.IDLE.value:
                stats["idle_sessions"] += 1
            elif state == SessionLifecycleState.HIBERNATING.value:
                stats["hibernating_sessions"] += 1

        return success_response(
            data=stats,
            message="获取自动会话统计成功"
        )

    except Exception as e:
        logger.error(f"获取自动会话统计失败: {e}")
        return error_response(message="获取自动会话统计失败", error_code=str(e))

@router.put("/config", response_model=dict, summary="更新自动会话配置")
async def update_auto_session_config(
    config_update: AutoSessionConfigUpdate
):
    """更新自动会话管理配置"""
    try:
        manager = AutoSessionService()

        # 更新配置
        if config_update.idle_timeout is not None:
            manager.config.idle_timeout = config_update.idle_timeout
        if config_update.hibernation_timeout is not None:
            manager.config.hibernation_timeout = config_update.hibernation_timeout
        if config_update.max_session_lifetime is not None:
            manager.config.max_session_lifetime = config_update.max_session_lifetime
        if config_update.max_concurrent_sessions is not None:
            manager.config.max_concurrent_sessions = config_update.max_concurrent_sessions
        if config_update.session_pool_size is not None:
            manager.config.session_pool_size = config_update.session_pool_size
        if config_update.enable_auto_tool_selection is not None:
            manager.config.enable_auto_tool_selection = config_update.enable_auto_tool_selection
        if config_update.tool_selection_strategy is not None:
            manager.config.tool_selection_strategy = config_update.tool_selection_strategy
        if config_update.cleanup_interval is not None:
            manager.config.cleanup_interval = config_update.cleanup_interval

        return success_response(
            data={
                "config": {
                    "idle_timeout": manager.config.idle_timeout,
                    "hibernation_timeout": manager.config.hibernation_timeout,
                    "max_session_lifetime": manager.config.max_session_lifetime,
                    "max_concurrent_sessions": manager.config.max_concurrent_sessions,
                    "session_pool_size": manager.config.session_pool_size,
                    "enable_auto_tool_selection": manager.config.enable_auto_tool_selection,
                    "tool_selection_strategy": manager.config.tool_selection_strategy,
                    "cleanup_interval": manager.config.cleanup_interval
                }
            },
            message="自动会话配置更新成功"
        )

    except Exception as e:
        logger.error(f"更新自动会话配置失败: {e}")
        return error_response(message="更新自动会话配置失败", error_code=str(e))

@router.get("/config/", response_model=dict, summary="获取自动会话配置")
async def get_auto_session_config():
    """获取当前自动会话管理配置"""
    try:
        manager = AutoSessionService()

        return success_response(
            data={
                "config": {
                    "idle_timeout": manager.config.idle_timeout,
                    "hibernation_timeout": manager.config.hibernation_timeout,
                    "max_session_lifetime": manager.config.max_session_lifetime,
                    "max_concurrent_sessions": manager.config.max_concurrent_sessions,
                    "session_pool_size": manager.config.session_pool_size,
                    "enable_auto_tool_selection": manager.config.enable_auto_tool_selection,
                    "tool_selection_strategy": manager.config.tool_selection_strategy,
                    "cleanup_interval": manager.config.cleanup_interval
                }
            },
            message="获取自动会话配置成功"
        )

    except Exception as e:
        logger.error(f"获取自动会话配置失败: {e}")
        return error_response(message="获取自动会话配置失败", error_code=str(e))

@router.post("/cleanup", response_model=dict, summary="手动清理会话")
async def manual_cleanup_sessions(
    force: bool = Query(False, description="是否强制清理")
):
    """手动触发会话清理"""
    try:
        manager = AutoSessionService()

        if force:
            await manager._force_cleanup_sessions()
            message = "强制清理会话完成"
        else:
            await manager._cleanup_sessions()
            message = "常规清理会话完成"

        # 获取清理后的统计信息
        sessions_info = await manager.get_all_sessions_info()

        return success_response(
            data={
                "cleanup_type": "force" if force else "normal",
                "remaining_sessions": len(sessions_info),
                "pool_size": len(manager.session_pool)
            },
            message=message
        )

    except Exception as e:
        logger.error(f"手动清理会话失败: {e}")
        return error_response(message="手动清理会话失败", error_code=str(e))

@router.post("/pool/refill", response_model=dict, summary="补充会话池")
async def refill_session_pool():
    """手动补充会话池"""
    try:
        manager = AutoSessionService()
        await manager._manage_session_pool()

        return success_response(
            data={
                "pool_size": len(manager.session_pool),
                "target_size": manager.config.session_pool_size
            },
            message="会话池补充完成"
        )

    except Exception as e:
        logger.error(f"补充会话池失败: {e}")
        return error_response(message="补充会话池失败", error_code=str(e))

@router.get("/health", response_model=dict, summary="自动会话管理健康检查")
async def auto_session_health_check():
    """自动会话管理服务健康检查"""
    try:
        manager = AutoSessionService()

        # 检查后台任务状态
        cleanup_task_running = manager._cleanup_task and not manager._cleanup_task.done()
        pool_manager_running = manager._pool_manager_task and not manager._pool_manager_task.done()

        sessions_info = await manager.get_all_sessions_info()

        health_data = {
            "status": "healthy",
            "cleanup_task_running": cleanup_task_running,
            "pool_manager_running": pool_manager_running,
            "total_sessions": len(sessions_info),
            "pool_size": len(manager.session_pool),
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }

        return success_response(
            data=health_data,
            message="自动会话管理服务运行正常"
        )

    except Exception as e:
        logger.error(f"自动会话管理健康检查失败: {e}")
        return error_response(message="自动会话管理健康检查失败", error_code=str(e))
