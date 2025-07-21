"""自动会话管理服务"""

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
from dataclasses import dataclass
from enum import Enum

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
from ..mcp import MCPService, MCPAgentService
from ..mcp.mcp_agent_service import AgentSession
from ..tools import ToolService
from app.utils.mcp_client import MCPClient
from sqlalchemy.orm import Session

logger = get_logger(__name__)

class SessionLifecycleState(str, Enum):
    """会话生命周期状态"""
    CREATING = "creating"
    ACTIVE = "active"
    IDLE = "idle"
    HIBERNATING = "hibernating"
    DESTROYING = "destroying"
    DESTROYED = "destroyed"

@dataclass
class AutoSessionConfig:
    """自动会话配置"""
    # 会话超时配置
    idle_timeout: int = 300  # 空闲超时时间（秒）
    hibernation_timeout: int = 1800  # 休眠超时时间（秒）
    max_session_lifetime: int = 7200  # 最大会话生命周期（秒）

    # 会话池配置
    max_concurrent_sessions: int = 50  # 最大并发会话数
    session_pool_size: int = 10  # 预创建会话池大小

    # 自动工具选择配置
    enable_auto_tool_selection: bool = True
    tool_selection_strategy: str = "smart"  # smart, round_robin, load_balanced

    # 清理配置
    cleanup_interval: int = 60  # 清理间隔（秒）

class AutoSessionManager:
    """自动会话管理器"""

    @error_handler
    def __init__(self, config: AutoSessionConfig = None):
        self.config = config or AutoSessionConfig()
        self.sessions: Dict[str, AgentSession] = {}
        self.session_states: Dict[str, SessionLifecycleState] = {}
        self.session_pool: List[str] = []  # 预创建的会话池
        self.pending_requests: Dict[str, Any] = {}  # 待处理的请求

        self.mcp_service = None  # 延迟初始化
        self.agent_service = None  # 延迟初始化
        self.executor = ThreadPoolExecutor(max_workers=10)

        # 后台任务状态
        self._cleanup_task: Optional[asyncio.Task] = None
        self._pool_manager_task: Optional[asyncio.Task] = None
        self._initialized = False

    @error_handler
    def _ensure_initialized(self):
        """确保管理器已初始化"""
        if not self._initialized:
            # 延迟初始化服务
            self.mcp_service = MCPService()
            self.agent_service = MCPAgentService()

            # 启动后台任务
            self._start_background_tasks()
            self._initialized = True

    @error_handler
    def _start_background_tasks(self):
        """启动后台任务"""
        try:
            if self._cleanup_task is None or self._cleanup_task.done():
                self._cleanup_task = asyncio.create_task(self._cleanup_loop())

            if self._pool_manager_task is None or self._pool_manager_task.done():
                self._pool_manager_task = asyncio.create_task(self._pool_manager_loop())
        except RuntimeError as e:
            if "no running event loop" in str(e):
                logger.warning("没有运行的事件循环，后台任务将在首次使用时启动", category=LogCategory.SYSTEM)
            else:
                raise

    @error_handler
    async def _cleanup_loop(self):
        """清理循环"""
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval)
                await self._cleanup_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理任务失败: {e}", category=LogCategory.SYSTEM)

    @error_handler
    async def _pool_manager_loop(self):
        """会话池管理循环"""
        while True:
            try:
                await asyncio.sleep(30)  # 每30秒检查一次
                # 不再预先创建会话池，改为按需创建
                # await self._manage_session_pool()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"会话池管理失败: {e}", category=LogCategory.SYSTEM)

    @error_handler
    async def _cleanup_sessions(self):
        """清理会话"""
        current_time = datetime.now()
        sessions_to_cleanup = []

        for session_id, session in self.sessions.items():
            state = self.session_states.get(session_id, SessionLifecycleState.ACTIVE)

            # 检查空闲超时
            idle_time = (current_time - session.last_activity).total_seconds()

            if state == SessionLifecycleState.ACTIVE and idle_time > self.config.idle_timeout:
                # 转为空闲状态
                await self._transition_to_idle(session_id)

            elif state == SessionLifecycleState.IDLE and idle_time > self.config.hibernation_timeout:
                # 转为休眠状态
                await self._transition_to_hibernation(session_id)

            elif idle_time > self.config.max_session_lifetime:
                # 超过最大生命周期，销毁会话
                sessions_to_cleanup.append(session_id)

        # 销毁过期会话
        for session_id in sessions_to_cleanup:
            await self._destroy_session(session_id)

    @error_handler
    async def _manage_session_pool(self):
        """管理会话池"""
        # 清理池中的无效会话
        valid_pool_sessions = []
        for session_id in self.session_pool:
            if session_id in self.sessions:
                valid_pool_sessions.append(session_id)

        self.session_pool = valid_pool_sessions

        # 补充会话池 - 改为按需创建策略，不再预先创建
        # needed_sessions = self.config.session_pool_size - len(self.session_pool)
        # if needed_sessions > 0:
        #     for _ in range(needed_sessions):
        #         try:
        #             session_id = await self._create_pool_session()
        #             if session_id:
        #                 self.session_pool.append(session_id)
        #         except Exception as e:
        #             logger.error(f"创建池会话失败: {e}", category=LogCategory.SYSTEM)
        logger.debug(f"当前会话池大小: {len(self.session_pool)}，采用按需创建策略", category=LogCategory.SYSTEM)

    @error_handler
    async def _create_pool_session(self) -> Optional[str]:
        """创建池会话"""
        try:
            # 确保已初始化
            await self._ensure_initialized()

            # 选择合适的工具
            tools = self._select_default_tools()
            if not tools:
                logger.warning("没有可用工具，跳过创建池会话", category=LogCategory.SYSTEM)
                return None

            # 创建默认配置
            config = AgentConfig(
                mode=AgentMode.MULTI_TOOL,
                max_iterations=10,
                timeout=300,
                parallel_execution=False
            )

            request = AgentSessionCreate(
                name=f"auto_pool_session_{uuid.uuid4().hex[:8]}",
                description="自动创建的池会话",
                config=config,
                tools=tools
            )

            session = await self.agent_service.create_session(request)
            self.sessions[session.session_id] = session
            self.session_states[session.session_id] = SessionLifecycleState.IDLE

            logger.info(f"创建池会话成功: {session.session_id}，使用工具: {tools}", category=LogCategory.SYSTEM)
            return session.session_id

        except Exception as e:
            logger.error(f"创建池会话失败: {e}", category=LogCategory.SYSTEM)
            return None

    @error_handler
    async def _select_default_tools(self) -> List[int]:
        """选择默认工具"""
        try:
            # 获取所有可用工具
            available_tools = self._get_available_tools()

            if not available_tools:
                logger.warning("没有可用的工具，无法创建会话", category=LogCategory.SYSTEM)
                return []

            # 选择前3个可用工具作为默认工具
            selected_tools = available_tools[:3]
            logger.info(f"选择的默认工具: {selected_tools}", category=LogCategory.SYSTEM)
            return selected_tools

        except Exception as e:
            logger.error(f"选择默认工具失败: {e}", category=LogCategory.SYSTEM)
            return []

    @error_handler
    async def _get_available_tools(self) -> List[int]:
        """获取可用工具列表"""
        try:
            from app.services.tools import ToolService
            from app.core.database import get_db

            # 获取数据库会话
            db = next(get_db())
            try:
                tool_service = ToolService(db)
                # 获取启用且运行中的工具ID列表（仅使用数据库状态）
                available_tool_ids = tool_service.get_available_tool_ids()
                logger.info(f"数据库中可用工具ID: {available_tool_ids}", category=LogCategory.SYSTEM)

                # 如果没有数据库中的可用工具，直接返回空列表
                if not available_tool_ids:
                    logger.warning("数据库中没有可用工具", category=LogCategory.SYSTEM)
                    return []

                # 注意：这里只使用数据库状态，不检查实时状态
                # 因为实时状态检查可能因为进程未启动而失败
                # 在实际使用工具时再进行实时状态检查
                return available_tool_ids

            finally:
                db.close()

        except Exception as e:
            logger.error(f"获取可用工具失败: {e}", category=LogCategory.SYSTEM)
            return []

    async def auto_create_session(
        self,
        request_context: Dict[str, Any],
        db: Session = None
    ) -> str:
        """自动创建会话"""
        try:
            # 确保已初始化
            await self._ensure_initialized()

            # 检查是否可以从池中获取会话
            if self.session_pool:
                session_id = self.session_pool.pop(0)
                session = self.sessions.get(session_id)

                if session and session_id in self.session_states:
                    # 唤醒会话
                    await self._wake_up_session(session_id, request_context)
                    return session_id

            # 检查并发限制
            if len(self.sessions) >= self.config.max_concurrent_sessions:
                # 尝试清理一些会话
                await self._force_cleanup_sessions()

                if len(self.sessions) >= self.config.max_concurrent_sessions:
                    raise MCPSError("达到最大并发会话限制")

            # 智能选择工具
            tools = await self._smart_select_tools(request_context, db)

            # 如果没有可用工具，记录警告但仍然创建会话
            if not tools:
                logger.warning("没有可用工具，但仍创建会话以响应请求", category=LogCategory.SYSTEM)
                tools = []  # 创建空工具列表的会话

            # 创建会话配置
            config = self._create_session_config(request_context)

            # 生成会话名称
            session_name = self._generate_session_name(request_context)

            request = AgentSessionCreate(
                name=session_name,
                description=f"自动创建的会话 - {datetime.now().isoformat()}",
                config=config,
                tools=tools
            )

            session = await self.agent_service.create_session(request)
            self.sessions[session.session_id] = session
            self.session_states[session.session_id] = SessionLifecycleState.ACTIVE

            logger.info(f"自动创建会话成功: {session.session_id}", category=LogCategory.SYSTEM)
            return session.session_id

        except Exception as e:
            logger.error(f"自动创建会话失败: {e}", category=LogCategory.SYSTEM)
            raise

    async def _smart_select_tools(
        self,
        request_context: Dict[str, Any],
        db: Session = None
    ) -> List[int]:
        """智能选择工具"""
        try:
            if not self.config.enable_auto_tool_selection:
                return self._get_available_tools()

            # 分析请求上下文
            message = request_context.get("message", "")
            task_type = request_context.get("task_type", "general")

            # 基于内容的工具选择逻辑
            selected_tools = []

            # 文件操作相关
            if any(keyword in message.lower() for keyword in ["file", "read", "write", "create", "delete"]):
                # 添加文件操作工具
                file_tools = await self._get_tools_by_category("file", db)
                selected_tools.extend(file_tools)

            # 网络请求相关
            if any(keyword in message.lower() for keyword in ["http", "api", "request", "fetch", "download"]):
                # 添加网络工具
                network_tools = await self._get_tools_by_category("network", db)
                selected_tools.extend(network_tools)

            # 数据处理相关
            if any(keyword in message.lower() for keyword in ["data", "json", "csv", "parse", "process"]):
                # 添加数据处理工具
                data_tools = await self._get_tools_by_category("data", db)
                selected_tools.extend(data_tools)

            # 如果没有匹配到特定工具，尝试获取默认工具
            if not selected_tools:
                available_tools = self._get_available_tools()
                if available_tools:
                    selected_tools = available_tools
                else:
                    # 没有可用工具时返回空列表，让上层处理
                    return []

            # 去重并限制数量
            unique_tools = list(set(selected_tools))
            return unique_tools[:5]  # 最多选择5个工具

        except Exception as e:
            logger.error(f"智能选择工具失败: {e}", category=LogCategory.SYSTEM)
            # 异常情况下也返回空列表，让上层处理
            return []

    async def _get_tools_by_category(
        self,
        category: str,
        db: Session = None
    ) -> List[int]:
        """根据类别获取工具"""
        # 这里需要实际的数据库查询逻辑
        # 暂时返回模拟数据
        category_tools = {
            "file": [1],
            "network": [2],
            "data": [3]
        }
        return category_tools.get(category, [])

    @error_handler
    def _create_session_config(self, request_context: Dict[str, Any]) -> AgentConfig:
        """创建会话配置"""
        # 根据请求上下文动态配置
        parallel = request_context.get("parallel", False)
        max_iterations = request_context.get("max_iterations", 10)
        timeout = request_context.get("timeout", 300)

        return AgentConfig(
            mode=AgentMode.MULTI_TOOL,
            max_iterations=max_iterations,
            timeout=timeout,
            parallel_execution=parallel
        )

    @error_handler
    def _generate_session_name(self, request_context: Dict[str, Any]) -> str:
        """生成会话名称"""
        task_type = request_context.get("task_type", "general")
        timestamp = datetime.now().strftime("%H%M%S")
        return f"auto_{task_type}_{timestamp}"

    @error_handler
    async def _transition_to_idle(self, session_id: str):
        """转换为空闲状态"""
        self.session_states[session_id] = SessionLifecycleState.IDLE
        logger.info(f"会话转为空闲状态: {session_id}", category=LogCategory.SYSTEM)

    @error_handler
    async def _transition_to_hibernation(self, session_id: str):
        """转换为休眠状态"""
        self.session_states[session_id] = SessionLifecycleState.HIBERNATING

        # 可以在这里实现会话数据的序列化保存
        session = self.sessions.get(session_id)
        if session:
            # 保存会话上下文到持久化存储
            await self._save_session_context(session_id, session.context)

        logger.info(f"会话转为休眠状态: {session_id}", category=LogCategory.SYSTEM)

    @error_handler
    async def _wake_up_session(self, session_id: str, request_context: Dict[str, Any]):
        """唤醒会话"""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"会话不存在: {session_id}")

        # 恢复会话上下文
        saved_context = await self._load_session_context(session_id)
        if saved_context:
            session.context.update(saved_context)

        # 更新活动时间
        session.update_activity()
        self.session_states[session_id] = SessionLifecycleState.ACTIVE

        logger.info(f"会话已唤醒: {session_id}", category=LogCategory.SYSTEM)

    @error_handler
    async def _destroy_session(self, session_id: str):
        """销毁会话"""
        try:
            # 确保已初始化
            await self._ensure_initialized()

            self.session_states[session_id] = SessionLifecycleState.DESTROYING

            # 关闭代理会话
            await self.agent_service.close_session(session_id)

            # 清理本地状态
            if session_id in self.sessions:
                del self.sessions[session_id]
            if session_id in self.session_states:
                del self.session_states[session_id]
            if session_id in self.session_pool:
                self.session_pool.remove(session_id)

            # 清理持久化数据
            await self._cleanup_session_context(session_id)

            logger.info(f"会话已销毁: {session_id}", category=LogCategory.SYSTEM)

        except Exception as e:
            logger.error(f"销毁会话失败: {session_id}, {e}", category=LogCategory.SYSTEM)

    @error_handler
    async def _force_cleanup_sessions(self):
        """强制清理会话"""
        # 优先清理空闲和休眠状态的会话
        cleanup_candidates = []

        for session_id, state in self.session_states.items():
            if state in [SessionLifecycleState.IDLE, SessionLifecycleState.HIBERNATING]:
                cleanup_candidates.append(session_id)

        # 清理一半的候选会话
        cleanup_count = max(1, len(cleanup_candidates) // 2)
        for session_id in cleanup_candidates[:cleanup_count]:
            await self._destroy_session(session_id)

    @error_handler
    async def _save_session_context(self, session_id: str, context: Dict[str, Any]):
        """保存会话上下文"""
        # 这里可以实现到Redis或数据库的持久化
        # 暂时跳过实现
        pass

    @error_handler
    async def _load_session_context(self, session_id: str) -> Dict[str, Any]:
        """加载会话上下文"""
        # 这里可以实现从Redis或数据库的加载
        # 暂时返回空字典
        return {}

    @error_handler
    async def _cleanup_session_context(self, session_id: str):
        """清理会话上下文"""
        # 这里可以实现持久化数据的清理
        # 暂时跳过实现
        pass

    @error_handler
    @cached(ttl=300)
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        session = self.sessions.get(session_id)
        if not session:
            return None

        state = self.session_states.get(session_id, SessionLifecycleState.ACTIVE)

        return {
            "session_id": session_id,
            "state": state.value,
            "session_info": session.to_dict(),
            "idle_time": (datetime.now() - session.last_activity).total_seconds()
        }

    @error_handler
    @cached(ttl=300)
    async def get_all_sessions_info(self) -> List[Dict[str, Any]]:
        """获取所有会话信息"""
        sessions_info = []

        for session_id in self.sessions.keys():
            info = await self.get_session_info(session_id)
            if info:
                sessions_info.append(info)

        return sessions_info

    @error_handler
    async def shutdown(self):
        """关闭自动会话管理器"""
        # 取消后台任务
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._pool_manager_task:
            self._pool_manager_task.cancel()

        # 关闭所有会话
        session_ids = list(self.sessions.keys())
        for session_id in session_ids:
            await self._destroy_session(session_id)

        logger.info("自动会话管理器已关闭", category=LogCategory.SYSTEM)

# 全局实例
_auto_session_manager: Optional[AutoSessionManager] = None

def get_auto_session_manager() -> AutoSessionManager:
    """获取自动会话管理器实例"""
    global _auto_session_manager
    if _auto_session_manager is None:
        _auto_session_manager = AutoSessionManager()
    return _auto_session_manager

# 为了兼容性，提供 AutoSessionService 别名
AutoSessionService = AutoSessionManager
