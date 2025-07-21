"""MCP 代理服务管理器"""

import asyncio
from app.core import get_logger, LogLevel, LogCategory, create_log_context
from app.core.unified_error import error_handler
from app.core.unified_cache import cached
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor
import json
import time

from app.schemas.mcp_agent import (
    AgentConfig,
    AgentSessionCreate,
    AgentExecuteRequest,
    TaskStep,
    TaskResult,
    TaskStatus,
    AgentMode,
    ToolCallRequest
)
from .mcp_service import MCPService
from ..tools import ToolService
from app.utils.mcp_client import MCPClient
from app.models.tool import ToolStatus

logger = get_logger(__name__)

class AgentSession:
    """代理会话类"""

    @error_handler
    def __init__(self, session_id: str, config: AgentConfig, tools: List[int]):
        self.session_id = session_id
        self.config = config
        self.tools = tools
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.status = "active"
        self.tasks: Dict[str, 'AgentTask'] = {}
        self.context: Dict[str, Any] = {}

    @error_handler
    def update_activity(self):
        """更新最后活动时间"""
        self.last_activity = datetime.now()

    @error_handler
    def is_expired(self, timeout: int = 3600) -> bool:
        """检查会话是否过期"""
        return (datetime.now() - self.last_activity).total_seconds() > timeout

    @error_handler
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "config": self.config.model_dump(),
            "tools": self.tools,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "status": self.status,
            "task_count": len(self.tasks),
            "context": self.context
        }

class AgentTask:
    """代理任务类"""

    @error_handler
    def __init__(self, task_id: str, session_id: str, request: AgentExecuteRequest):
        self.task_id = task_id
        self.session_id = session_id
        self.request = request
        self.status = TaskStatus.PENDING
        self.progress = 0.0
        self.results: List[TaskResult] = []
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error: Optional[str] = None
        self.context: Dict[str, Any] = request.context or {}

    @error_handler
    def start(self):
        """开始任务"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()

    @error_handler
    def complete(self):
        """完成任务"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.progress = 100.0

    @error_handler
    def fail(self, error: str):
        """任务失败"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.error = error

    @error_handler
    def cancel(self):
        """取消任务"""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now()

    @error_handler
    def update_progress(self, progress: float):
        """更新进度"""
        self.progress = min(100.0, max(0.0, progress))

    @error_handler
    def add_result(self, result: TaskResult):
        """添加步骤结果"""
        self.results.append(result)

    @error_handler
    @cached(ttl=300)
    def get_execution_time(self) -> Optional[float]:
        """获取执行时间"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @error_handler
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "session_id": self.session_id,
            "status": self.status.value,
            "progress": self.progress,
            "results": [result.model_dump() for result in self.results],
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "execution_time": self.get_execution_time(),
            "error": self.error,
            "context": self.context
        }

class MCPAgentService:
    """MCP 代理服务管理器"""

    @error_handler
    def __init__(self):
        self.sessions: Dict[str, AgentSession] = {}
        self.mcp_service = MCPService()
        self.executor = ThreadPoolExecutor(max_workers=10)
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()

    @error_handler
    def _start_cleanup_task(self):
        """启动清理任务"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    @error_handler
    def _cleanup_loop(self):
        """清理循环"""
        while True:
            try:
                time.sleep(300)  # 每5分钟清理一次
                self._cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理任务失败: {e}", category=LogCategory.SYSTEM)

    @error_handler
    async def _cleanup_expired_sessions(self):
        """清理过期会话"""
        expired_sessions = []
        for session_id, session in self.sessions.items():
            if session.is_expired():
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            logger.info(f"清理过期会话: {session_id}", category=LogCategory.SYSTEM)
            await self.close_session(session_id)

    async def create_session(
        self,
        request: AgentSessionCreate
    ) -> AgentSession:
        """创建代理会话"""
        try:
            session_id = str(uuid.uuid4())
            session = AgentSession(session_id, request.config, request.tools)

            # 验证工具是否可用
            for tool_id in request.tools:
                tool_status = await self.mcp_service.get_tool_status(tool_id)
                if not tool_status or tool_status != ToolStatus.RUNNING:
                    logger.warning(f"工具 {tool_id} 状态为 {tool_status}，尝试启动工具", category=LogCategory.SYSTEM)
                    try:
                        # 尝试启动工具
                        success = await self.mcp_service.start_tool(tool_id)
                        if not success:
                            raise ValueError(f"工具 {tool_id} 启动失败")

                        # 重新检查状态
                        tool_status = await self.mcp_service.get_tool_status(tool_id)
                        if tool_status != ToolStatus.RUNNING:
                            raise ValueError(f"工具 {tool_id} 启动后状态仍为 {tool_status}")

                        logger.info(f"工具 {tool_id} 启动成功", category=LogCategory.SYSTEM)
                    except Exception as e:
                        logger.error(f"启动工具 {tool_id} 失败: {e}", category=LogCategory.SYSTEM)
                        raise ValueError(f"工具 {tool_id} 不可用: {e}")

            self.sessions[session_id] = session
            logger.info(f"创建代理会话成功: {session_id}", category=LogCategory.SYSTEM)
            return session

        except Exception as e:
            logger.error(f"创建代理会话失败: {e}", category=LogCategory.SYSTEM)
            raise

    @error_handler
    @cached(ttl=300)
    def get_session(self, session_id: str) -> Optional[AgentSession]:
        """获取代理会话"""
        session = self.sessions.get(session_id)
        if session:
            session.update_activity()
        return session

    @error_handler
    def close_session(self, session_id: str) -> bool:
        """关闭代理会话"""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return False

            # 取消所有运行中的任务
            for task in session.tasks.values():
                if task.status == TaskStatus.RUNNING:
                    task.cancel()

            session.status = "closed"
            del self.sessions[session_id]
            logger.info(f"关闭代理会话: {session_id}", category=LogCategory.SYSTEM)
            return True

        except Exception as e:
            logger.error(f"关闭代理会话失败: {e}", category=LogCategory.SYSTEM)
            return False

    async def execute_task(
        self,
        session_id: str,
        request: AgentExecuteRequest
    ) -> AgentTask:
        """执行代理任务"""
        try:
            session = await self.get_session(session_id)
            if not session:
                raise ValueError(f"会话不存在: {session_id}")

            task_id = str(uuid.uuid4())
            task = AgentTask(task_id, session_id, request)
            session.tasks[task_id] = task

            # 异步执行任务
            asyncio.create_task(self._execute_task_async(task, session))

            logger.info(f"提交代理任务: {task_id}", category=LogCategory.SYSTEM)
            return task

        except Exception as e:
            logger.error(f"执行代理任务失败: {e}", category=LogCategory.SYSTEM)
            raise

    @error_handler
    def _execute_task_async(self, task: AgentTask, session: AgentSession):
        """异步执行任务"""
        try:
            task.start()
            logger.info(f"开始执行任务: {task.task_id}", category=LogCategory.SYSTEM)

            if session.config.mode == AgentMode.SINGLE_TOOL:
                self._execute_single_tool_mode(task, session)
            elif session.config.mode == AgentMode.MULTI_TOOL:
                self._execute_multi_tool_mode(task, session)
            elif session.config.mode == AgentMode.PIPELINE:
                self._execute_pipeline_mode(task, session)
            elif session.config.mode == AgentMode.AUTONOMOUS:
                self._execute_autonomous_mode(task, session)
            else:
                raise ValueError(f"不支持的代理模式: {session.config.mode}")

            task.complete()
            logger.info(f"任务执行完成: {task.task_id}", category=LogCategory.SYSTEM)

        except Exception as e:
            error_msg = f"任务执行失败: {e}"
            logger.error(error_msg, category=LogCategory.SYSTEM)
            task.fail(error_msg)

    @error_handler
    def _execute_single_tool_mode(self, task: AgentTask, session: AgentSession):
        """执行单工具模式"""
        if not task.request.steps:
            raise ValueError("单工具模式需要至少一个步骤")

        step = task.request.steps[0]
        result = self._execute_step(step, session, task)
        task.add_result(result)
        task.update_progress(100.0)

    @error_handler
    def _execute_multi_tool_mode(self, task: AgentTask, session: AgentSession):
        """执行多工具模式"""
        total_steps = len(task.request.steps)

        if session.config.parallel_execution:
            # 并行执行
            tasks = []
            for step in task.request.steps:
                step_task = asyncio.create_task(self._execute_step(step, session, task))
                tasks.append(step_task)

            results = asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    step_result = TaskResult(
                        step_id=task.request.steps[i].step_id,
                        status=TaskStatus.FAILED,
                        error=str(result),
                        execution_time=0.0
                    )
                else:
                    step_result = result

                task.add_result(step_result)
                task.update_progress((i + 1) / total_steps * 100)
        else:
            # 串行执行
            for i, step in enumerate(task.request.steps):
                result = self._execute_step(step, session, task)
                task.add_result(result)
                task.update_progress((i + 1) / total_steps * 100)

    @error_handler
    def _execute_pipeline_mode(self, task: AgentTask, session: AgentSession):
        """执行流水线模式"""
        # 构建依赖图
        dependency_graph = self._build_dependency_graph(task.request.steps)

        # 按依赖顺序执行
        executed_steps = set()
        step_results = {}

        while len(executed_steps) < len(task.request.steps):
            ready_steps = []

            for step in task.request.steps:
                if step.step_id in executed_steps:
                    continue

                # 检查依赖是否已完成
                if not step.depends_on or all(dep in executed_steps for dep in step.depends_on):
                    ready_steps.append(step)

            if not ready_steps:
                raise ValueError("检测到循环依赖")

            # 执行就绪的步骤
            for step in ready_steps:
                # 合并依赖步骤的结果到上下文
                if step.depends_on:
                    for dep_id in step.depends_on:
                        if dep_id in step_results:
                            task.context[f"step_{dep_id}_result"] = step_results[dep_id].result

                result = self._execute_step(step, session, task)
                task.add_result(result)
                step_results[step.step_id] = result
                executed_steps.add(step.step_id)

                progress = len(executed_steps) / len(task.request.steps) * 100
                task.update_progress(progress)

    @error_handler
    def _execute_autonomous_mode(self, task: AgentTask, session: AgentSession):
        """执行自主模式"""
        # TODO: 实现自主代理逻辑
        # 这里可以集成LLM来实现智能决策
        raise NotImplementedError("自主模式尚未实现")

    @error_handler
    def _build_dependency_graph(self, steps: List[TaskStep]) -> Dict[str, List[str]]:
        """构建依赖图"""
        graph = {}
        for step in steps:
            graph[step.step_id] = step.depends_on or []
        return graph

    async def _execute_step(
        self,
        step: TaskStep,
        session: AgentSession,
        task: AgentTask
    ) -> TaskResult:
        """执行单个步骤"""
        start_time = time.time()

        try:
            # 检查工具是否在会话中
            if step.tool_id not in session.tools:
                raise ValueError(f"工具 {step.tool_id} 不在会话工具列表中")

            # 调用工具
            result = await self.mcp_service.call_tool(
                tool_id=step.tool_id,
                name=step.tool_name,
                arguments=step.arguments
            )

            execution_time = time.time() - start_time

            return TaskResult(
                step_id=step.step_id,
                status=TaskStatus.COMPLETED,
                result=result,
                execution_time=execution_time,
                started_at=datetime.fromtimestamp(start_time),
                completed_at=datetime.now()
            )

        except Exception as e:
            execution_time = time.time() - start_time

            return TaskResult(
                step_id=step.step_id,
                status=TaskStatus.FAILED,
                error=str(e),
                execution_time=execution_time,
                started_at=datetime.fromtimestamp(start_time),
                completed_at=datetime.now()
            )

    @error_handler
    @cached(ttl=300)
    def get_task_status(self, session_id: str, task_id: str) -> Optional[AgentTask]:
        """获取任务状态"""
        session = self.sessions.get(session_id)
        if not session:
            return None

        return session.tasks.get(task_id)

    @error_handler
    def cancel_task(self, session_id: str, task_id: str) -> bool:
        """取消任务"""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return False

            task = session.tasks.get(task_id)
            if not task:
                return False

            if task.status == TaskStatus.RUNNING:
                task.cancel()
                logger.info(f"取消任务: {task_id}", category=LogCategory.SYSTEM)
                return True

            return False

        except Exception as e:
            logger.error(f"取消任务失败: {e}", category=LogCategory.SYSTEM)
            return False

    @error_handler
    @cached(ttl=300)
    def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话统计信息"""
        session = self.sessions.get(session_id)
        if not session:
            return None

        total_tasks = len(session.tasks)
        completed_tasks = sum(1 for task in session.tasks.values() if task.status == TaskStatus.COMPLETED)
        failed_tasks = sum(1 for task in session.tasks.values() if task.status == TaskStatus.FAILED)
        running_tasks = sum(1 for task in session.tasks.values() if task.status == TaskStatus.RUNNING)

        avg_execution_time = 0.0
        if completed_tasks > 0:
            total_time = sum(
                task.get_execution_time() or 0
                for task in session.tasks.values()
                if task.status == TaskStatus.COMPLETED
            )
            avg_execution_time = total_time / completed_tasks

        return {
            "session_id": session_id,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "running_tasks": running_tasks,
            "success_rate": completed_tasks / total_tasks if total_tasks > 0 else 0,
            "avg_execution_time": avg_execution_time,
            "session_duration": (datetime.now() - session.created_at).total_seconds(),
            "last_activity": session.last_activity.isoformat()
        }

    @error_handler
    def shutdown(self):
        """关闭服务"""
        try:
            # 取消清理任务
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    self._cleanup_task
                except asyncio.CancelledError:
                    pass

            # 关闭所有会话
            for session_id in list(self.sessions.keys()):
                self.close_session(session_id)

            # 关闭线程池
            self.executor.shutdown(wait=True)

            logger.info("MCP代理服务已关闭", category=LogCategory.SYSTEM)

        except Exception as e:
            logger.error(f"关闭MCP代理服务失败: {e}", category=LogCategory.SYSTEM)

# 全局代理服务实例
_agent_service: Optional[MCPAgentService] = None

def get_agent_service() -> MCPAgentService:
    """获取代理服务实例"""
    global _agent_service
    if _agent_service is None:
        _agent_service = MCPAgentService()
    return _agent_service
