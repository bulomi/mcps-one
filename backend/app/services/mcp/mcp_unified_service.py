"""统一MCP服务管理器

这个模块提供了统一的MCP服务管理功能，支持同时运行MCP服务端和HTTP代理模式。
主要功能：
- 管理MCP服务端和HTTP代理的生命周期
- 协调两种模式的资源使用
- 提供统一的工具调用接口
- 处理配置变更和服务切换
"""

import asyncio
import subprocess
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
from contextlib import asynccontextmanager

from app.core import (
    get_unified_config_manager, get_logger, error_handler,
    MCPSError, LogLevel, LogCategory
)
from .mcp_service import MCPService
from .mcp_server import MCPSServer
from .mcp_proxy_server import MCPProxyServer
from app.services.base.base_service import BaseService
from app.utils.exceptions import MCPServiceError

logger = get_logger(__name__)

class ServiceMode(Enum):
    """服务模式枚举"""
    PROXY_ONLY = "proxy"
    SERVER_ONLY = "server"

@dataclass
class ServiceStatus:
    """服务状态信息"""
    mode: ServiceMode
    proxy_running: bool = False
    server_running: bool = False
    api_running: bool = False
    proxy_tools_count: int = 0
    server_connections: int = 0
    uptime: float = 0.0
    last_error: Optional[str] = None
    timestamp: Optional[str] = None

class MCPUnifiedService(BaseService):
    """统一MCP服务管理器

    负责管理MCP服务端和HTTP代理的生命周期，提供统一的服务接口。
    """

    def __init__(self):
        super().__init__("MCPUnifiedService")
        self._mode = ServiceMode.SERVER_ONLY
        self._proxy_service: Optional[MCPService] = None
        self._proxy_server: Optional[MCPProxyServer] = None
        self._server_service: Optional[MCPSServer] = None

        self._running = False
        self._start_time: Optional[float] = None
        self._lock = asyncio.Lock()

    @property
    def mode(self) -> ServiceMode:
        """当前服务模式"""
        return self._mode

    @property
    def is_running(self) -> bool:
        """服务是否正在运行"""
        return self._running

    async def _initialize_impl(self) -> None:
        """具体的初始化实现"""
        # 根据配置确定服务模式
        config_manager = get_unified_config_manager()
        enable_mcp_server = config_manager.get("mcp.server.enabled", False)
        service_mode = config_manager.get("mcp.service.mode", "server")
        
        if enable_mcp_server or service_mode == "server":
            self._mode = ServiceMode.SERVER_ONLY
        elif service_mode == "proxy":
            self._mode = ServiceMode.PROXY_ONLY
        else:
            # 默认使用服务端模式
            self._mode = ServiceMode.SERVER_ONLY

        self.logger.info(f"服务模式设置为: {self._mode.value}")

        # 初始化代理服务
        if self._mode == ServiceMode.PROXY_ONLY:
            self._proxy_service = MCPService()
            await self._proxy_service.initialize()
            self._proxy_server = MCPProxyServer()
            await self._proxy_server.initialize()
            self.logger.info("MCP代理服务已初始化")

        # 初始化服务端
        if self._mode == ServiceMode.SERVER_ONLY:
            self._server_service = MCPSServer()
            self.logger.info("MCP服务端已初始化")

    async def _start_impl(self) -> None:
        """具体的启动实现"""
        self.logger.info(f"启动MCP统一服务，模式: {self._mode.value}")

        # 启动代理服务
        if self._mode == ServiceMode.PROXY_ONLY:
            if self._proxy_service and self._proxy_server:
                await self._proxy_service.start()
                await self._proxy_server.start()
                self.logger.info("MCP代理服务已启动")
            else:
                raise MCPServiceError("MCP代理服务未初始化")

        # 启动服务端
        if self._mode == ServiceMode.SERVER_ONLY:
            if self._server_service:
                await self._start_mcp_server()
                self.logger.info("MCP服务端已启动")
            else:
                raise MCPServiceError("MCP服务端未初始化")

        self._start_time = asyncio.get_event_loop().time()

    async def _stop_impl(self) -> None:
        """具体的停止实现"""
        # 停止代理服务
        if self._proxy_service:
            await self._proxy_service.stop()
        if self._proxy_server:
            await self._proxy_server.stop()

        # 停止服务端
        if self._server_service:
            await self._stop_mcp_server()
        
        # 停止API服务器


        self._start_time = None

    async def _cleanup_impl(self) -> None:
        """具体的清理实现"""
        # 清理代理服务
        if self._proxy_service:
            if hasattr(self._proxy_service, 'cleanup'):
                await self._proxy_service.cleanup()
        if self._proxy_server:
            if hasattr(self._proxy_server, 'cleanup'):
                await self._proxy_server.cleanup()

        # 清理服务端
        if self._server_service:
            if hasattr(self._server_service, 'cleanup'):
                await self._server_service.cleanup()

    @error_handler
    async def start_service(self, mode: Optional[str] = None) -> None:
        """启动服务

        Args:
            mode: 可选的服务模式覆盖 ("proxy", "server")
        """
        async with self._lock:
            if self._running:
                logger.warning("服务已在运行中")
                return

            # 确保服务已初始化
            if not hasattr(self, '_initialized') or not self._initialized:
                logger.info("服务未初始化，正在初始化...")
                await self.initialize()

            # 如果指定了模式，临时切换
            original_mode = self._mode
            if mode:
                try:
                    self._mode = ServiceMode(mode)
                except ValueError:
                    raise MCPServiceError(f"无效的服务模式: {mode}")

            try:
                logger.info(f"启动MCP统一服务，模式: {self._mode.value}")

                # 启动代理服务
                if self._mode == ServiceMode.PROXY_ONLY:
                    if self._proxy_service and self._proxy_server:
                        await self._proxy_service.start()
                        await self._proxy_server.start()
                        logger.info("MCP代理服务已启动")
                    else:
                        raise MCPServiceError("MCP代理服务未初始化")

                # 启动服务端
                if self._mode == ServiceMode.SERVER_ONLY:
                    if self._server_service:
                        await self._start_mcp_server()
                        logger.info("MCP服务端已启动")
                    else:
                        raise MCPServiceError("MCP服务端未初始化")
                


                self._running = True
                self._start_time = asyncio.get_event_loop().time()
                logger.info("MCP统一服务启动完成")

            except Exception as e:
                # 恢复原始模式
                self._mode = original_mode
                logger.error(f"启动MCP统一服务失败: {e}")
                # 清理已启动的服务
                await self._cleanup_services()
                raise MCPServiceError(f"启动服务失败: {e}")

    @error_handler
    async def stop_service(self, mode: Optional[str] = None) -> None:
        """停止服务

        Args:
            mode: 可选的服务模式，指定要停止的服务 ("proxy", "server")
        """
        async with self._lock:
            if not self._running:
                logger.warning("服务未在运行")
                return

            # 如果没有指定模式，则停止当前运行的模式
            stop_mode = ServiceMode(mode) if mode else self._mode

            logger.info(f"停止MCP统一服务，模式: {stop_mode.value}")

            try:
                # 停止代理服务
                if stop_mode == ServiceMode.PROXY_ONLY:
                    if self._proxy_service:
                        await self._proxy_service.stop()
                    if self._proxy_server:
                        await self._proxy_server.stop()
                    logger.info("MCP代理服务已停止")

                # 停止服务端
                if stop_mode == ServiceMode.SERVER_ONLY:
                    if self._server_service:
                        await self._stop_mcp_server()
                        logger.info("MCP服务端已停止")



                # 更新运行状态
                self._running = False
                self._start_time = None

                logger.info("MCP统一服务停止完成")

            except Exception as e:
                logger.error(f"停止MCP统一服务失败: {e}")
                raise MCPServiceError(f"停止服务失败: {e}")

    @error_handler
    async def switch_mode(self, enable_server: bool, enable_proxy: bool) -> None:
        """切换服务模式

        Args:
            enable_server: 是否启用MCP服务端
            enable_proxy: 是否启用HTTP代理
        """
        async with self._lock:
            # 确定新模式
            if enable_server:
                new_mode = ServiceMode.SERVER_ONLY
            elif enable_proxy:
                new_mode = ServiceMode.PROXY_ONLY
            else:
                # 默认使用服务端模式
                new_mode = ServiceMode.SERVER_ONLY

            if new_mode == self._mode:
                logger.info(f"服务模式已经是 {new_mode.value}，无需切换")
                return

            logger.info(f"切换服务模式: {self._mode.value} -> {new_mode.value}")

            was_running = self._running

            try:
                # 停止当前服务
                if was_running:
                    await self.stop_service()

                # 更新模式
                old_mode = self._mode
                self._mode = new_mode

                # 重新初始化需要的服务
                await self._reinitialize_services(old_mode, new_mode)

                # 如果之前在运行，重新启动
                if was_running:
                    await self.start_service()

                logger.info(f"服务模式切换完成: {new_mode.value}")

            except Exception as e:
                logger.error(f"切换服务模式失败: {e}")
                raise MCPServiceError(f"切换服务模式失败: {e}")

    async def get_service_status(self) -> ServiceStatus:
        """获取服务状态"""
        from datetime import datetime

        status = ServiceStatus(mode=self._mode)

        # 代理服务状态
        if self._proxy_service:
            status.proxy_running = self._proxy_service.is_running
            proxy_tools = await self._proxy_service.get_available_tools()
            status.proxy_tools_count = len(proxy_tools)

        # 服务端状态
        if self._server_service:
            status.server_running = hasattr(self._server_service, '_running') and self._server_service._running
            # TODO: 实现客户端连接数统计
            status.server_connections = 0

        # API服务状态（当前服务是否在运行）
        status.api_running = self._running

        # 运行时间
        if self._start_time:
            status.uptime = asyncio.get_event_loop().time() - self._start_time

        # 设置时间戳
        status.timestamp = datetime.now().isoformat()

        return status

    @error_handler
    async def reload_configuration(self) -> None:
        """重新加载配置"""
        logger.info("重新加载MCP服务配置")

        try:
            # 重新加载设置
            # TODO: 实现配置重新加载逻辑

            # 如果服务正在运行，需要重启以应用新配置
            if self._running:
                logger.info("重启服务以应用新配置")
                await self.stop_service()
                await self.initialize()
                await self.start_service()
            else:
                await self.initialize()

            logger.info("配置重新加载完成")

        except Exception as e:
            logger.error(f"重新加载配置失败: {e}")
            raise MCPServiceError(f"重新加载配置失败: {e}")

    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """获取可用工具列表"""
        tools = []

        if self._proxy_service:
            proxy_tools = await self._proxy_service.get_available_tools()
            for tool in proxy_tools:
                tools.append({
                    **tool,
                    "source": "proxy",
                    "available_via": ["http_api"]
                })

        if self._server_service:
            # TODO: 从MCP服务端获取工具列表
            pass

        return tools

    @error_handler
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any],
                       source: str = "auto") -> Dict[str, Any]:
        """调用工具

        Args:
            tool_name: 工具名称
            arguments: 工具参数
            source: 调用源 ("proxy", "server", "auto")
        """
        if source == "auto":
            # 自动选择可用的服务
            if self._proxy_service and self._proxy_service.is_running:
                source = "proxy"
            elif self._server_service:
                source = "server"
            else:
                raise MCPServiceError("没有可用的MCP服务")

        if source == "proxy" and self._proxy_service:
            return await self._proxy_service.call_tool(tool_name, arguments)
        elif source == "server" and self._server_service:
            # TODO: 实现服务端工具调用
            raise MCPServiceError("MCP服务端工具调用尚未实现")
        else:
            raise MCPServiceError(f"指定的服务源不可用: {source}")

    async def _start_mcp_server(self) -> None:
        """启动MCP服务端"""
        if not self._server_service:
            raise MCPServiceError("MCP服务端未初始化")

        # 启动MCP服务端
        await self._server_service.start()

        # 根据配置选择传输方式并启动服务器
        config_manager = get_unified_config_manager()
        transport = config_manager.get("mcp.server.transport", "stdio")
        
        if transport == "stdio":
            logger.info("MCP服务端配置为stdio模式，启动stdio服务器")
            # 在后台任务中启动stdio服务器
            asyncio.create_task(self._run_stdio_server())
        elif transport == "http":
            host = config_manager.get("mcp.server.host", "127.0.0.1")
            port = config_manager.get("mcp.server.port", 8001)
            logger.info(f"启动MCP服务端HTTP服务器: {host}:{port}")
            # 在后台任务中启动HTTP服务器
            asyncio.create_task(self._run_http_server())

    async def _run_stdio_server(self) -> None:
        """运行stdio服务器"""
        try:
            logger.info("启动stdio服务器")
            # 在独立线程中运行stdio服务器，避免阻塞FastAPI应用
            import threading
            import asyncio
            
            def run_in_thread():
                # 创建新的事件循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    # 在新的事件循环中运行stdio服务器
                    loop.run_until_complete(self._server_service.run_stdio())
                except Exception as e:
                    logger.error(f"线程中的stdio服务器运行失败: {e}")
                finally:
                    loop.close()
            
            # 创建并启动线程
            thread = threading.Thread(target=run_in_thread, daemon=True)
            thread.start()
            logger.info("stdio服务器已在独立线程中启动")
        except Exception as e:
            logger.error(f"stdio服务器启动失败: {e}")

    async def _run_http_server(self) -> None:
        """运行HTTP服务器"""
        try:
            config_manager = get_unified_config_manager()
            host = config_manager.get("mcp.server.host", "127.0.0.1")
            port = config_manager.get("mcp.server.port", 8001)
            
            # 在独立线程中运行HTTP服务器，避免阻塞FastAPI应用
            import threading
            import asyncio
            
            def run_in_thread():
                # 创建新的事件循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    # 在新的事件循环中运行HTTP服务器，添加超时处理
                    async def run_with_timeout():
                        try:
                            await asyncio.wait_for(
                                self._server_service.run_http(host=host, port=port),
                                timeout=60.0  # 60秒超时
                            )
                        except asyncio.TimeoutError:
                            logger.warning("MCP HTTP服务器启动超时，但可能已在后台运行")
                        except Exception as e:
                            logger.error(f"MCP HTTP服务器运行异常: {e}")
                            # 如果是端口占用，说明服务可能已经在运行
                            if "already in use" in str(e) or "Address already in use" in str(e):
                                logger.warning("端口已被占用，MCP服务可能已在运行")
                            else:
                                raise
                    
                    loop.run_until_complete(run_with_timeout())
                except Exception as e:
                    logger.error(f"线程中的HTTP服务器运行失败: {e}")
                finally:
                    loop.close()
            
            # 创建并启动线程
            thread = threading.Thread(target=run_in_thread, daemon=True)
            thread.start()
            logger.info(f"HTTP服务器已在独立线程中启动: {host}:{port}")
            
            # 给线程一些时间启动
            await asyncio.sleep(2.0)
            logger.info("HTTP服务器启动完成")
            
        except Exception as e:
            logger.error(f"HTTP服务器启动失败: {e}")



    async def _stop_mcp_server(self) -> None:
        """停止MCP服务端"""
        if not self._server_service:
            return

        logger.info("停止MCP服务端")
        await self._server_service.stop()
    


    async def _reinitialize_services(self, old_mode: ServiceMode, new_mode: ServiceMode) -> None:
        """重新初始化服务"""
        # 清理不需要的服务
        if old_mode == ServiceMode.PROXY_ONLY and new_mode != ServiceMode.PROXY_ONLY:
            if self._proxy_service:
                await self._proxy_service.cleanup()
                self._proxy_service = None

        if old_mode == ServiceMode.SERVER_ONLY and new_mode != ServiceMode.SERVER_ONLY:
            self._server_service = None

        # 初始化新需要的服务
        if new_mode == ServiceMode.PROXY_ONLY and not self._proxy_service:
            self._proxy_service = MCPService()
            await self._proxy_service.initialize()
            self._proxy_server = MCPProxyServer()
            await self._proxy_server.initialize()

        if new_mode == ServiceMode.SERVER_ONLY and not self._server_service:
            self._server_service = MCPSServer()
            await self._server_service.initialize()

    async def get_service_metrics(self) -> Dict[str, Any]:
        """获取服务指标"""
        import time
        import psutil
        import os

        try:
            # 获取系统指标
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()

            # 基础指标
            metrics = {
                "uptime": time.time() - self._start_time if self._start_time else 0,
                "total_tool_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "average_response_time": 0.0,
                "active_connections": 0,
                "memory_usage": memory_info.rss / 1024 / 1024,  # MB
                "cpu_usage": process.cpu_percent()
            }

            # 代理服务指标
            if self._proxy_service:
                # TODO: 从代理服务获取真实指标
                proxy_tools = await self._proxy_service.get_available_tools()
                proxy_metrics = {
                    "proxy_tools_count": len(proxy_tools),
                    "proxy_running": self._proxy_service.is_running
                }
                metrics.update(proxy_metrics)

            # 服务端指标
            if self._server_service:
                # TODO: 从服务端获取真实指标
                server_metrics = {
                    "server_running": hasattr(self._server_service, '_running') and self._server_service._running,
                    "server_connections": 0  # TODO: 实现连接数统计
                }
                metrics.update(server_metrics)

            return metrics

        except Exception as e:
            logger.error(f"获取服务指标失败: {e}")
            return {
                "error": str(e),
                "uptime": 0,
                "total_tool_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "average_response_time": 0.0,
                "active_connections": 0,
                "memory_usage": 0,
                "cpu_usage": 0
            }

    async def run_stdio(self) -> None:
        """以stdio模式运行统一服务
        
        这个方法主要用于MCP客户端连接，会根据当前模式选择合适的stdio服务
        """
        logger.info(f"启动统一服务stdio模式，当前模式: {self._mode.value}")
        
        try:
            # 确保服务已初始化
            if not self._initialized:
                await self.initialize()
            
            # 确保服务已启动
            if not self._running:
                await self.start_service()
            
            # 根据模式选择stdio服务
            if self._mode == ServiceMode.SERVER_ONLY:
                if self._server_service:
                    logger.info("使用MCP服务端stdio模式")
                    # 确保服务端已初始化
                    if not self._server_service._initialized:
                        await self._server_service.initialize()
                    # 确保服务端已启动
                    if not self._server_service._running:
                        await self._server_service.start()
                    # 使用异步方法运行stdio
                    logger.info("调用异步stdio方法...")
                    await self._server_service.run_stdio()
                else:
                    raise MCPServiceError("MCP服务端未初始化")
            
            elif self._mode == ServiceMode.PROXY_ONLY:
                if self._proxy_server:
                    logger.info("使用MCP代理stdio模式")
                    await self._proxy_server.run_stdio()
                else:
                    raise MCPServiceError("MCP代理服务未初始化")
            

            
            else:
                raise MCPServiceError(f"模式 {self._mode.value} 不支持stdio")
                
        except Exception as e:
            logger.error(f"stdio模式运行失败: {e}")
            raise MCPServiceError(f"stdio模式运行失败: {e}")

    async def _cleanup_services(self) -> None:
        """清理服务资源"""
        try:
            if self._proxy_service:
                await self._proxy_service.stop()
            if self._proxy_server:
                await self._proxy_server.stop()
        except Exception as e:
            logger.error(f"清理代理服务失败: {e}")

        try:
            if self._server_service:
                await self._stop_mcp_server()
        except Exception as e:
            logger.error(f"清理服务端失败: {e}")

    @asynccontextmanager
    async def lifespan_context(self):
        """生命周期上下文管理器"""
        try:
            await self.initialize()
            config_manager = get_unified_config_manager()
            if config_manager.get("mcp.auto_start", False):
                await self.start_service()
            yield self
        finally:
            if self._running:
                await self.stop_service()
            await self._cleanup_services()

# 全局实例
unified_service = MCPUnifiedService()
