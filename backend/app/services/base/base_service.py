"""基础服务类

提供所有服务类的通用功能和接口规范。
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import asynccontextmanager

from app.core import (
    get_logger, LogLevel, LogCategory, create_log_context,
    MCPSError, handle_error, error_handler, error_context,
    get_unified_config_manager
)
from app.utils.exceptions import MCPSException


class BaseService(ABC):
    """基础服务类

    所有服务类的基类，提供通用功能：
    - 生命周期管理
    - 错误处理
    - 日志记录
    - 状态管理
    """

    def __init__(self, name: str):
        self.name = name
        self._initialized = False
        self._running = False
        self._start_time: Optional[datetime] = None
        self._lock = asyncio.Lock()
        self._shutdown_event = asyncio.Event()

        # 配置日志
        self.logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    @property
    def is_initialized(self) -> bool:
        """是否已初始化"""
        return self._initialized

    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._running

    @property
    def uptime(self) -> float:
        """运行时间（秒）"""
        if self._start_time:
            return (datetime.utcnow() - self._start_time).total_seconds()
        return 0.0

    @abstractmethod
    async def _initialize_impl(self) -> None:
        """具体的初始化实现"""
        pass

    @abstractmethod
    async def _start_impl(self) -> None:
        """具体的启动实现"""
        pass

    @abstractmethod
    async def _stop_impl(self) -> None:
        """具体的停止实现"""
        pass

    @abstractmethod
    async def _cleanup_impl(self) -> None:
        """具体的清理实现"""
        pass

    @error_handler
    async def initialize(self) -> None:
        """初始化服务"""
        async with self._lock:
            if self._initialized:
                self.logger.info(f"服务 {self.name} 已经初始化")
                return

            self.logger.info(f"初始化服务: {self.name}")

            try:
                await self._initialize_impl()
                self._initialized = True
                self.logger.info(f"服务 {self.name} 初始化完成")
            except Exception as e:
                self.logger.error(f"服务 {self.name} 初始化失败: {e}")
                raise MCPSException(
                    f"服务 {self.name} 初始化失败",
                    code="SERVICE_INIT_FAILED",
                    context={"service": self.name, "error": str(e)},
                    original_exception=e
                )

    @error_handler
    async def start(self) -> None:
        """启动服务"""
        async with self._lock:
            if not self._initialized:
                await self.initialize()

            if self._running:
                self.logger.info(f"服务 {self.name} 已经在运行")
                return

            self.logger.info(f"启动服务: {self.name}")

            try:
                await self._start_impl()
                self._running = True
                self._start_time = datetime.utcnow()
                self._shutdown_event.clear()
                self.logger.info(f"服务 {self.name} 启动完成")
            except Exception as e:
                self.logger.error(f"服务 {self.name} 启动失败: {e}")
                raise MCPSException(
                    f"服务 {self.name} 启动失败",
                    code="SERVICE_START_FAILED",
                    context={"service": self.name, "error": str(e)},
                    original_exception=e
                )

    @error_handler
    async def stop(self) -> None:
        """停止服务"""
        async with self._lock:
            if not self._running:
                self.logger.info(f"服务 {self.name} 未在运行")
                return

            self.logger.info(f"停止服务: {self.name}")

            try:
                self._shutdown_event.set()
                await self._stop_impl()
                self._running = False
                self._start_time = None
                self.logger.info(f"服务 {self.name} 停止完成")
            except Exception as e:
                self.logger.error(f"服务 {self.name} 停止失败: {e}")
                raise MCPSException(
                    f"服务 {self.name} 停止失败",
                    code="SERVICE_STOP_FAILED",
                    context={"service": self.name, "error": str(e)},
                    original_exception=e
                )

    @error_handler
    async def restart(self) -> None:
        """重启服务"""
        self.logger.info(f"重启服务: {self.name}")
        await self.stop()
        await self.start()

    @error_handler
    async def cleanup(self) -> None:
        """清理资源"""
        self.logger.info(f"清理服务资源: {self.name}")

        try:
            if self._running:
                await self.stop()

            await self._cleanup_impl()
            self._initialized = False
            self.logger.info(f"服务 {self.name} 清理完成")
        except Exception as e:
            self.logger.error(f"服务 {self.name} 清理失败: {e}")
            raise MCPSException(
                f"服务 {self.name} 清理失败",
                code="SERVICE_CLEANUP_FAILED",
                context={"service": self.name, "error": str(e)},
                original_exception=e
            )

    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            "name": self.name,
            "initialized": self._initialized,
            "running": self._running,
            "uptime": self.uptime,
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "timestamp": datetime.utcnow().isoformat()
        }

    @asynccontextmanager
    @error_handler
    async def lifecycle(self):
        """服务生命周期上下文管理器"""
        try:
            await self.start()
            yield self
        finally:
            await self.cleanup()

    @error_handler
    async def wait_for_shutdown(self) -> None:
        """等待关闭信号"""
        await self._shutdown_event.wait()

class MCPBaseService(BaseService):
    """MCP相关服务的基类

    提供MCP服务的通用功能：
    - MCP客户端管理
    - 工具状态管理
    - 连接管理
    """

    def __init__(self, name: str):
        super().__init__(name)
        self.clients: Dict[int, Any] = {}  # tool_id -> client
        self.tool_statuses: Dict[int, str] = {}  # tool_id -> status

    @error_handler
    async def get_tool_status(self, tool_id: int) -> Optional[str]:
        """获取工具状态"""
        return self.tool_statuses.get(tool_id)

    @error_handler
    async def update_tool_status(self, tool_id: int, status: str) -> None:
        """更新工具状态"""
        self.tool_statuses[tool_id] = status
        self.logger.debug(f"工具 {tool_id} 状态更新为: {status}")

    @error_handler
    async def get_client(self, tool_id: int) -> Optional[Any]:
        """获取工具客户端"""
        return self.clients.get(tool_id)

    @error_handler
    async def add_client(self, tool_id: int, client: Any) -> None:
        """添加工具客户端"""
        self.clients[tool_id] = client
        self.logger.debug(f"添加工具 {tool_id} 的客户端")

    @error_handler
    async def remove_client(self, tool_id: int) -> None:
        """移除工具客户端"""
        if tool_id in self.clients:
            del self.clients[tool_id]
            self.logger.debug(f"移除工具 {tool_id} 的客户端")

    @error_handler
    async def cleanup_tool(self, tool_id: int) -> None:
        """清理工具资源"""
        await self.remove_client(tool_id)
        if tool_id in self.tool_statuses:
            del self.tool_statuses[tool_id]
        self.logger.debug(f"清理工具 {tool_id} 的资源")

    def get_tools_status(self) -> Dict[int, str]:
        """获取所有工具状态"""
        return self.tool_statuses.copy()

    def get_status(self) -> Dict[str, Any]:
        """获取服务状态（包含MCP特定信息）"""
        status = super().get_status()
        status.update({
            "tools_count": len(self.clients),
            "active_tools": list(self.clients.keys()),
            "tool_statuses": self.get_tools_status()
        })
        return status
