"""任务管理服务"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
import uuid
import json
import logging

from app.models.task import MCPTask, TaskStatus, TaskType, TaskPriority
from app.models.session import MCPSession
from app.models.tool import MCPTool
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskStatsResponse,
    TaskProgressUpdate,
    TaskBatchOperation,
    TaskBatchOperationResponse,
)
from app.utils.exceptions import (
    TaskNotFoundError,
    TaskOperationError,
)
from app.core.unified_logging import get_logger

logger = get_logger(__name__)

# 常量定义
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200
DEFAULT_RECENT_LIMIT = 10
DEFAULT_CLEANUP_DAYS = 30
MAX_RETRY_COUNT = 3


class TaskService:
    """任务管理服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_tasks(
        self,
        page: int = 1,
        size: int = DEFAULT_PAGE_SIZE,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[MCPTask], int]:
        """获取任务列表"""
        query = self.db.query(MCPTask)

        # 应用过滤条件
        if filters:
            if filters.get('status'):
                if isinstance(filters['status'], list):
                    query = query.filter(MCPTask.status.in_(filters['status']))
                else:
                    query = query.filter(MCPTask.status == filters['status'])

            if filters.get('task_type'):
                query = query.filter(MCPTask.task_type == filters['task_type'])

            if filters.get('priority'):
                query = query.filter(MCPTask.priority == filters['priority'])

            if filters.get('session_id'):
                query = query.filter(MCPTask.session_id == filters['session_id'])

            if filters.get('tool_id'):
                query = query.filter(MCPTask.tool_id == filters['tool_id'])

            if filters.get('user_id'):
                query = query.filter(MCPTask.user_id == filters['user_id'])

            if filters.get('parent_task_id'):
                query = query.filter(MCPTask.parent_task_id == filters['parent_task_id'])

            if filters.get('search'):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        MCPTask.name.ilike(search_term),
                        MCPTask.description.ilike(search_term),
                        MCPTask.task_id.ilike(search_term)
                    )
                )

            if filters.get('created_after'):
                query = query.filter(MCPTask.created_at >= filters['created_after'])

            if filters.get('created_before'):
                query = query.filter(MCPTask.created_at <= filters['created_before'])

            if filters.get('scheduled_after'):
                query = query.filter(MCPTask.scheduled_at >= filters['scheduled_after'])

            if filters.get('scheduled_before'):
                query = query.filter(MCPTask.scheduled_at <= filters['scheduled_before'])

        # 获取总数
        total = query.count()

        # 限制页面大小
        size = min(size, MAX_PAGE_SIZE)

        # 分页和排序
        tasks = query.order_by(
            desc(MCPTask.created_at)
        ).offset((page - 1) * size).limit(size).all()

        return tasks, total

    def get_task(self, task_id: str) -> Optional[MCPTask]:
        """获取任务详情"""
        return self.db.query(MCPTask).filter(
            MCPTask.task_id == task_id
        ).first()

    def get_task_by_id(self, id: int) -> Optional[MCPTask]:
        """根据ID获取任务"""
        return self.db.query(MCPTask).filter(MCPTask.id == id).first()

    def create_task(self, task_data: TaskCreate) -> MCPTask:
        """创建任务"""
        try:
            # 生成唯一的任务ID
            task_id = str(uuid.uuid4())

            # 验证关联资源是否存在
            if task_data.session_id:
                session = self.db.query(MCPSession).filter(
                    MCPSession.id == task_data.session_id
                ).first()
                if not session:
                    raise TaskOperationError(f"会话不存在: {task_data.session_id}")

            if task_data.tool_id:
                tool = self.db.query(MCPTool).filter(
                    MCPTool.id == task_data.tool_id
                ).first()
                if not tool:
                    raise TaskOperationError(f"工具不存在: {task_data.tool_id}")

            if task_data.parent_task_id:
                parent_task = self.db.query(MCPTask).filter(
                    MCPTask.id == task_data.parent_task_id
                ).first()
                if not parent_task:
                    raise TaskOperationError(f"父任务不存在: {task_data.parent_task_id}")

            task = MCPTask(
                task_id=task_id,
                name=task_data.name,
                description=task_data.description,
                task_type=task_data.task_type,
                priority=task_data.priority or TaskPriority.MEDIUM,
                session_id=task_data.session_id,
                tool_id=task_data.tool_id,
                user_id=task_data.user_id,
                parent_task_id=task_data.parent_task_id,
                input_data=json.dumps(task_data.input_data) if task_data.input_data else None,
                config=json.dumps(task_data.config) if task_data.config else None,
                metadata=json.dumps(task_data.metadata) if task_data.metadata else None,
                scheduled_at=task_data.scheduled_at or datetime.utcnow(),
                timeout_at=task_data.timeout_at,
                status=TaskStatus.PENDING,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)

            logger.info(f"任务创建成功: {task.task_id}")
            return task

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建任务失败: {e}")
            raise TaskOperationError(f"创建任务失败: {e}")

    def update_task(self, task_id: str, task_data: TaskUpdate) -> MCPTask:
        """更新任务"""
        try:
            task = self.get_task(task_id)
            if not task:
                raise TaskNotFoundError(f"任务不存在: {task_id}")

            # 更新字段
            update_data = task_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                if field in ['input_data', 'output_data', 'config', 'metadata'] and value is not None:
                    value = json.dumps(value)
                setattr(task, field, value)

            task.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(task)

            logger.info(f"任务更新成功: {task.task_id}")
            return task

        except Exception as e:
            self.db.rollback()
            logger.error(f"更新任务失败: {e}")
            raise

    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        try:
            task = self.get_task(task_id)
            if not task:
                raise TaskNotFoundError(f"任务不存在: {task_id}")

            # 检查任务是否可以删除
            if task.status in [TaskStatus.RUNNING, TaskStatus.PENDING]:
                # 先取消任务
                task.cancel_task()
                task.updated_at = datetime.utcnow()

            self.db.delete(task)
            self.db.commit()

            logger.info(f"任务删除成功: {task_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"删除任务失败: {e}")
            raise

    def start_task(self, task_id: str) -> MCPTask:
        """开始执行任务"""
        try:
            task = self.get_task(task_id)
            if not task:
                raise TaskNotFoundError(f"任务不存在: {task_id}")

            if task.status != TaskStatus.PENDING:
                raise TaskOperationError(f"任务状态不允许开始执行: {task.status}")

            task.start_task()
            task.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(task)

            logger.info(f"任务开始执行: {task_id}")
            return task

        except Exception as e:
            self.db.rollback()
            logger.error(f"开始任务失败: {e}")
            raise

    def complete_task(self, task_id: str, output_data: Optional[Dict[str, Any]] = None) -> MCPTask:
        """完成任务"""
        try:
            task = self.get_task(task_id)
            if not task:
                raise TaskNotFoundError(f"任务不存在: {task_id}")

            if task.status != TaskStatus.RUNNING:
                raise TaskOperationError(f"任务状态不允许完成: {task.status}")

            task.complete_task()
            if output_data:
                task.output_data = json.dumps(output_data)
            task.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(task)

            logger.info(f"任务完成: {task_id}")
            return task

        except Exception as e:
            self.db.rollback()
            logger.error(f"完成任务失败: {e}")
            raise

    def fail_task(self, task_id: str, error_message: str) -> MCPTask:
        """任务失败"""
        try:
            task = self.get_task(task_id)
            if not task:
                raise TaskNotFoundError(f"任务不存在: {task_id}")

            if task.status not in [TaskStatus.RUNNING, TaskStatus.PENDING]:
                raise TaskOperationError(f"任务状态不允许设置为失败: {task.status}")

            task.fail_task(error_message)
            task.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(task)

            logger.info(f"任务失败: {task_id}, 错误: {error_message}")
            return task

        except Exception as e:
            self.db.rollback()
            logger.error(f"设置任务失败状态失败: {e}")
            raise

    def cancel_task(self, task_id: str) -> MCPTask:
        """取消任务"""
        try:
            task = self.get_task(task_id)
            if not task:
                raise TaskNotFoundError(f"任务不存在: {task_id}")

            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                raise TaskOperationError(f"任务状态不允许取消: {task.status}")

            task.cancel_task()
            task.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(task)

            logger.info(f"任务取消: {task_id}")
            return task

        except Exception as e:
            self.db.rollback()
            logger.error(f"取消任务失败: {e}")
            raise

    def retry_task(self, task_id: str) -> MCPTask:
        """重试任务"""
        try:
            task = self.get_task(task_id)
            if not task:
                raise TaskNotFoundError(f"任务不存在: {task_id}")

            if task.status != TaskStatus.FAILED:
                raise TaskOperationError(f"只有失败的任务才能重试: {task.status}")

            if task.retry_count >= MAX_RETRY_COUNT:
                raise TaskOperationError(f"任务重试次数已达上限: {task.retry_count}")

            task.retry_task()
            task.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(task)

            logger.info(f"任务重试: {task_id}")
            return task

        except Exception as e:
            self.db.rollback()
            logger.error(f"重试任务失败: {e}")
            raise

    def update_task_progress(self, task_id: str, progress_data: TaskProgressUpdate) -> MCPTask:
        """更新任务进度"""
        try:
            task = self.get_task(task_id)
            if not task:
                raise TaskNotFoundError(f"任务不存在: {task_id}")

            if task.status != TaskStatus.RUNNING:
                raise TaskOperationError(f"只有运行中的任务才能更新进度: {task.status}")

            task.update_progress(
                progress_data.progress_percentage,
                progress_data.current_step,
                progress_data.total_steps,
                progress_data.status_message
            )
            task.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(task)

            return task

        except Exception as e:
            self.db.rollback()
            logger.error(f"更新任务进度失败: {e}")
            raise

    def get_task_stats(self) -> TaskStatsResponse:
        """获取任务统计信息"""
        try:
            # 基础统计
            total_tasks = self.db.query(MCPTask).count()
            pending_tasks = self.db.query(MCPTask).filter(
                MCPTask.status == TaskStatus.PENDING
            ).count()
            running_tasks = self.db.query(MCPTask).filter(
                MCPTask.status == TaskStatus.RUNNING
            ).count()
            completed_tasks = self.db.query(MCPTask).filter(
                MCPTask.status == TaskStatus.COMPLETED
            ).count()
            failed_tasks = self.db.query(MCPTask).filter(
                MCPTask.status == TaskStatus.FAILED
            ).count()
            cancelled_tasks = self.db.query(MCPTask).filter(
                MCPTask.status == TaskStatus.CANCELLED
            ).count()

            # 按类型统计
            task_type_stats = {}
            for task_type in TaskType:
                count = self.db.query(MCPTask).filter(
                    MCPTask.task_type == task_type
                ).count()
                task_type_stats[task_type.value] = count

            # 按优先级统计
            priority_stats = {}
            for priority in TaskPriority:
                count = self.db.query(MCPTask).filter(
                    MCPTask.priority == priority
                ).count()
                priority_stats[priority.value] = count

            # 平均执行时间（分钟）
            completed_tasks_with_time = self.db.query(MCPTask).filter(
                and_(
                    MCPTask.status == TaskStatus.COMPLETED,
                    MCPTask.started_at.isnot(None),
                    MCPTask.completed_at.isnot(None)
                )
            ).all()

            if completed_tasks_with_time:
                total_execution_time = sum(
                    (task.completed_at - task.started_at).total_seconds() / 60
                    for task in completed_tasks_with_time
                )
                avg_execution_time = total_execution_time / len(completed_tasks_with_time)
            else:
                avg_execution_time = 0.0

            # 成功率
            if total_tasks > 0:
                success_rate = (completed_tasks / total_tasks) * 100
            else:
                success_rate = 0.0

            return TaskStatsResponse(
                total_tasks=total_tasks,
                pending_tasks=pending_tasks,
                running_tasks=running_tasks,
                completed_tasks=completed_tasks,
                failed_tasks=failed_tasks,
                cancelled_tasks=cancelled_tasks,
                task_type_stats=task_type_stats,
                priority_stats=priority_stats,
                avg_execution_time=round(avg_execution_time, 2),
                success_rate=round(success_rate, 2)
            )

        except Exception as e:
            logger.error(f"获取任务统计失败: {e}")
            raise

    def batch_operation(self, operation: TaskBatchOperation) -> TaskBatchOperationResponse:
        """批量操作任务"""
        try:
            results = []
            errors = []

            for task_id in operation.task_ids:
                try:
                    task = self.get_task(task_id)
                    if not task:
                        errors.append(f"任务不存在: {task_id}")
                        continue

                    if operation.operation == "cancel":
                        self.cancel_task(task_id)
                    elif operation.operation == "retry":
                        self.retry_task(task_id)
                    elif operation.operation == "delete":
                        self.delete_task(task_id)
                    else:
                        errors.append(f"不支持的操作: {operation.operation}")
                        continue

                    results.append(task_id)

                except Exception as e:
                    errors.append(f"操作任务 {task_id} 失败: {e}")

            return TaskBatchOperationResponse(
                operation=operation.operation,
                total_requested=len(operation.task_ids),
                successful_count=len(results),
                failed_count=len(errors),
                successful_task_ids=results,
                errors=errors
            )

        except Exception as e:
            logger.error(f"批量操作任务失败: {e}")
            raise

    def cleanup_old_tasks(self, days: int = DEFAULT_CLEANUP_DAYS) -> int:
        """清理旧任务"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # 删除已完成或已取消的旧任务
            old_tasks = self.db.query(MCPTask).filter(
                and_(
                    MCPTask.status.in_([TaskStatus.COMPLETED, TaskStatus.CANCELLED]),
                    MCPTask.completed_at < cutoff_date
                )
            ).all()

            count = len(old_tasks)
            for task in old_tasks:
                self.db.delete(task)

            if count > 0:
                self.db.commit()
                logger.info(f"清理旧任务: {count} 个")

            return count

        except Exception as e:
            self.db.rollback()
            logger.error(f"清理旧任务失败: {e}")
            raise

    def get_recent_tasks(self, limit: int = DEFAULT_RECENT_LIMIT) -> List[MCPTask]:
        """获取最近的任务"""
        return self.db.query(MCPTask).order_by(
            desc(MCPTask.created_at)
        ).limit(limit).all()

    def get_tasks_by_session(self, session_id: int, limit: int = DEFAULT_PAGE_SIZE) -> List[MCPTask]:
        """获取会话相关的任务"""
        return self.db.query(MCPTask).filter(
            MCPTask.session_id == session_id
        ).order_by(desc(MCPTask.created_at)).limit(limit).all()

    def get_tasks_by_tool(self, tool_id: int, limit: int = DEFAULT_PAGE_SIZE) -> List[MCPTask]:
        """获取工具相关的任务"""
        return self.db.query(MCPTask).filter(
            MCPTask.tool_id == tool_id
        ).order_by(desc(MCPTask.created_at)).limit(limit).all()
