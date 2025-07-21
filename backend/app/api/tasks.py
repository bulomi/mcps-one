"""任务管理API路由"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.core.database import get_db
from app.services.tasks import TaskService
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
    TaskStatsResponse,
    TaskExecutionRequest,
    TaskExecutionResponse,
    TaskProgressUpdate,
    TaskBatchOperation,
    TaskBatchOperationResponse,
)
from app.utils.exceptions import (
    TaskNotFoundError,
    TaskOperationError,
    TaskExecutionError,
)
from app.utils.response import success_response, error_response

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/", response_model=TaskListResponse)
async def get_tasks(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(50, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="任务状态过滤"),
    task_type: Optional[str] = Query(None, description="任务类型过滤"),
    priority: Optional[str] = Query(None, description="任务优先级过滤"),
    session_id: Optional[int] = Query(None, description="会话ID过滤"),
    tool_id: Optional[int] = Query(None, description="工具ID过滤"),
    user_id: Optional[int] = Query(None, description="用户ID过滤"),
    parent_task_id: Optional[int] = Query(None, description="父任务ID过滤"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    created_after: Optional[datetime] = Query(None, description="创建时间起始"),
    created_before: Optional[datetime] = Query(None, description="创建时间结束"),
    scheduled_after: Optional[datetime] = Query(None, description="计划时间起始"),
    scheduled_before: Optional[datetime] = Query(None, description="计划时间结束"),
    db: Session = Depends(get_db)
):
    """获取任务列表"""
    try:
        service = TaskService(db)

        # 构建过滤条件
        filters = {}
        if status:
            filters['status'] = status
        if task_type:
            filters['task_type'] = task_type
        if priority:
            filters['priority'] = priority
        if session_id:
            filters['session_id'] = session_id
        if tool_id:
            filters['tool_id'] = tool_id
        if user_id:
            filters['user_id'] = user_id
        if parent_task_id:
            filters['parent_task_id'] = parent_task_id
        if search:
            filters['search'] = search
        if created_after:
            filters['created_after'] = created_after
        if created_before:
            filters['created_before'] = created_before
        if scheduled_after:
            filters['scheduled_after'] = scheduled_after
        if scheduled_before:
            filters['scheduled_before'] = scheduled_before

        tasks, total = service.get_tasks(page, size, filters)

        return TaskListResponse(
            items=[TaskResponse.from_orm(task) for task in tasks],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")


@router.get("/stats", response_model=TaskStatsResponse)
async def get_task_stats(db: Session = Depends(get_db)):
    """获取任务统计信息"""
    try:
        service = TaskService(db)
        stats = service.get_task_stats()
        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务统计失败: {str(e)}")


@router.get("/recent/")
async def get_recent_tasks(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db: Session = Depends(get_db)
):
    """获取最近的任务"""
    try:
        service = TaskService(db)
        tasks = service.get_recent_tasks(limit)

        return success_response(
            data=[TaskResponse.from_orm(task) for task in tasks],
            message="获取最近任务成功"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取最近任务失败: {str(e)}")


@router.get("/session/{session_id}")
async def get_tasks_by_session(
    session_id: int,
    limit: int = Query(50, ge=1, le=100, description="返回数量"),
    db: Session = Depends(get_db)
):
    """获取会话相关的任务"""
    try:
        service = TaskService(db)
        tasks = service.get_tasks_by_session(session_id, limit)

        return success_response(
            data=[TaskResponse.from_orm(task) for task in tasks],
            message="获取会话任务成功"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话任务失败: {str(e)}")


@router.get("/tool/{tool_id}")
async def get_tasks_by_tool(
    tool_id: int,
    limit: int = Query(50, ge=1, le=100, description="返回数量"),
    db: Session = Depends(get_db)
):
    """获取工具相关的任务"""
    try:
        service = TaskService(db)
        tasks = service.get_tasks_by_tool(tool_id, limit)

        return success_response(
            data=[TaskResponse.from_orm(task) for task in tasks],
            message="获取工具任务成功"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工具任务失败: {str(e)}")


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """获取任务详情"""
    try:
        service = TaskService(db)
        task = service.get_task(task_id)

        if not task:
            raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")

        return TaskResponse.from_orm(task)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务详情失败: {str(e)}")


@router.post("/", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db)
):
    """创建任务"""
    try:
        service = TaskService(db)
        task = service.create_task(task_data)

        return TaskResponse.from_orm(task)

    except TaskOperationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    db: Session = Depends(get_db)
):
    """更新任务"""
    try:
        service = TaskService(db)
        task = service.update_task(task_id, task_data)

        return TaskResponse.from_orm(task)

    except TaskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TaskOperationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新任务失败: {str(e)}")


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """删除任务"""
    try:
        service = TaskService(db)
        success = service.delete_task(task_id)

        if success:
            return success_response(message="任务删除成功")
        else:
            raise HTTPException(status_code=400, detail="删除任务失败")

    except TaskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除任务失败: {str(e)}")


@router.post("/{task_id}/start", response_model=TaskResponse)
async def start_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """开始执行任务"""
    try:
        service = TaskService(db)
        task = service.start_task(task_id)

        return TaskResponse.from_orm(task)

    except TaskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TaskOperationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"开始任务失败: {str(e)}")


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: str,
    execution_data: Optional[TaskExecutionRequest] = None,
    db: Session = Depends(get_db)
):
    """完成任务"""
    try:
        service = TaskService(db)
        output_data = execution_data.output_data if execution_data else None
        task = service.complete_task(task_id, output_data)

        return TaskResponse.from_orm(task)

    except TaskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TaskOperationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"完成任务失败: {str(e)}")


@router.post("/{task_id}/fail", response_model=TaskResponse)
async def fail_task(
    task_id: str,
    execution_data: TaskExecutionRequest,
    db: Session = Depends(get_db)
):
    """任务失败"""
    try:
        service = TaskService(db)
        error_message = execution_data.error_message or "任务执行失败"
        task = service.fail_task(task_id, error_message)

        return TaskResponse.from_orm(task)

    except TaskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TaskOperationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"设置任务失败状态失败: {str(e)}")


@router.post("/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """取消任务"""
    try:
        service = TaskService(db)
        task = service.cancel_task(task_id)

        return TaskResponse.from_orm(task)

    except TaskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TaskOperationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取消任务失败: {str(e)}")


@router.post("/{task_id}/retry", response_model=TaskResponse)
async def retry_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """重试任务"""
    try:
        service = TaskService(db)
        task = service.retry_task(task_id)

        return TaskResponse.from_orm(task)

    except TaskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TaskOperationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重试任务失败: {str(e)}")


@router.put("/{task_id}/progress", response_model=TaskResponse)
async def update_task_progress(
    task_id: str,
    progress_data: TaskProgressUpdate,
    db: Session = Depends(get_db)
):
    """更新任务进度"""
    try:
        service = TaskService(db)
        task = service.update_task_progress(task_id, progress_data)

        return TaskResponse.from_orm(task)

    except TaskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TaskOperationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新任务进度失败: {str(e)}")


@router.post("/batch", response_model=TaskBatchOperationResponse)
async def batch_operation(
    operation: TaskBatchOperation,
    db: Session = Depends(get_db)
):
    """批量操作任务"""
    try:
        service = TaskService(db)
        result = service.batch_operation(operation)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量操作任务失败: {str(e)}")


@router.post("/cleanup")
async def cleanup_old_tasks(
    days: int = Query(30, ge=1, le=365, description="清理多少天前的任务"),
    db: Session = Depends(get_db)
):
    """清理旧任务"""
    try:
        service = TaskService(db)
        count = service.cleanup_old_tasks(days)

        return success_response(
            data={"cleaned_count": count},
            message=f"清理旧任务完成，共清理 {count} 个任务"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理旧任务失败: {str(e)}")
