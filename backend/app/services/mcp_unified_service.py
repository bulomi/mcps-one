"""统一MCP服务管理器

这个模块提供了统一的MCP服务管理功能，支持同时运行MCP服务端和HTTP代理模式。
主要功能：
- 管理MCP服务端和HTTP代理的生命周期
- 协调两种模式的资源使用
- 提供统一的工具调用接口
- 处理配置变更和服务切换
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
from contextlib import asynccontextmanager

from ..core.config import settings
from .mcp_service import MCPService
from .mcp_server import MCPSServer
from ..utils.exceptions import MCPServiceError

logger = logging.getLogger(__name__)

class ServiceMode(Enum):
    """服务模式枚举"""
    PROXY_ONLY = "proxy"
    SERVER_ONLY = "server"
    BOTH = "both"
    DISABLED = "disabled"

@dataclass
class ServiceStatus:
    """服务状态信息"""
    mode: ServiceMode
    proxy_running: bool = False
    server_running: bool = False
    proxy_tools_count: int = 0
    server_connections: int = 0
    uptime: float = 0.0
    last_error: Optional[str] = None

class MCPUnifiedService:
    """统一MCP服务管理器
    
    负责管理MCP服务端和HTTP代理的生命周期，提供统一的服务接口。
    """
    
    def __init__(self):
        self._mode = ServiceMode.DISABLED
        self._proxy_service: Optional[MCPService] = None
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
    
    async def initialize(self) -> None:
        """初始化服务"""
        logger.info("初始化统一MCP服务管理器")
        
        # 根据配置确定服务模式
        if settings.ENABLE_MCP_SERVER and settings.MCP_SERVICE_MODE == "both":
            self._mode = ServiceMode.BOTH
        elif settings.ENABLE_MCP_SERVER and settings.MCP_SERVICE_MODE == "server":
            self._mode = ServiceMode.SERVER_ONLY
        elif settings.MCP_SERVICE_MODE == "proxy":
            self._mode = ServiceMode.PROXY_ONLY
        else:
            self._mode = ServiceMode.DISABLED
            
        logger.info(f"服务模式设置为: {self._mode.value}")
        
        # 初始化代理服务
        if self._mode in [ServiceMode.PROXY_ONLY, ServiceMode.BOTH]:
            self._proxy_service = MCPService()
            await self._proxy_service.initialize()
            logger.info("MCP代理服务已初始化")
        
        # 初始化服务端
        if self._mode in [ServiceMode.SERVER_ONLY, ServiceMode.BOTH]:
            self._server_service = MCPSServer()
            logger.info("MCP服务端已初始化")
    
    async def start_service(self, mode: Optional[str] = None) -> None:
        """启动服务
        
        Args:
            mode: 可选的服务模式覆盖 ("proxy", "server", "both")
        """
        async with self._lock:
            if self._running:
                logger.warning("服务已在运行中")
                return
            
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
                if self._mode in [ServiceMode.PROXY_ONLY, ServiceMode.BOTH]:
                    if self._proxy_service:
                        await self._proxy_service.start()
                        logger.info("MCP代理服务已启动")
                    else:
                        raise MCPServiceError("MCP代理服务未初始化")
                
                # 启动服务端
                if self._mode in [ServiceMode.SERVER_ONLY, ServiceMode.BOTH]:
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
    
    async def stop_service(self, mode: Optional[str] = None) -> None:
        """停止服务
        
        Args:
            mode: 可选的服务模式，指定要停止的服务 ("proxy", "server", "both")
        """
        async with self._lock:
            if not self._running:
                logger.warning("服务未在运行")
                return
            
            stop_mode = ServiceMode(mode) if mode else ServiceMode.BOTH
            
            logger.info(f"停止MCP统一服务，模式: {stop_mode.value}")
            
            try:
                # 停止代理服务
                if stop_mode in [ServiceMode.PROXY_ONLY, ServiceMode.BOTH]:
                    if self._proxy_service:
                        await self._proxy_service.stop()
                        logger.info("MCP代理服务已停止")
                
                # 停止服务端
                if stop_mode in [ServiceMode.SERVER_ONLY, ServiceMode.BOTH]:
                    if self._server_service:
                        await self._stop_mcp_server()
                        logger.info("MCP服务端已停止")
                
                # 如果停止所有服务，更新运行状态
                if stop_mode == ServiceMode.BOTH:
                    self._running = False
                    self._start_time = None
                
                logger.info("MCP统一服务停止完成")
                
            except Exception as e:
                logger.error(f"停止MCP统一服务失败: {e}")
                raise MCPServiceError(f"停止服务失败: {e}")
    
    async def switch_mode(self, enable_server: bool, enable_proxy: bool) -> None:
        """切换服务模式
        
        Args:
            enable_server: 是否启用MCP服务端
            enable_proxy: 是否启用HTTP代理
        """
        async with self._lock:
            # 确定新模式
            if enable_server and enable_proxy:
                new_mode = ServiceMode.BOTH
            elif enable_server:
                new_mode = ServiceMode.SERVER_ONLY
            elif enable_proxy:
                new_mode = ServiceMode.PROXY_ONLY
            else:
                new_mode = ServiceMode.DISABLED
            
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
                if was_running and new_mode != ServiceMode.DISABLED:
                    await self.start_service()
                
                logger.info(f"服务模式切换完成: {new_mode.value}")
                
            except Exception as e:
                logger.error(f"切换服务模式失败: {e}")
                raise MCPServiceError(f"切换服务模式失败: {e}")
    
    async def get_service_status(self) -> ServiceStatus:
        """获取服务状态"""
        status = ServiceStatus(mode=self._mode)
        
        # 代理服务状态
        if self._proxy_service:
            status.proxy_running = self._proxy_service.is_running
            status.proxy_tools_count = len(self._proxy_service.get_available_tools())
        
        # 服务端状态
        if self._server_service:
            status.server_running = hasattr(self._server_service, '_running') and self._server_service._running
            # TODO: 实现客户端连接数统计
            status.server_connections = 0
        
        # 运行时间
        if self._start_time:
            status.uptime = asyncio.get_event_loop().time() - self._start_time
        
        return status
    
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
            proxy_tools = self._proxy_service.get_available_tools()
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
        
        # 根据配置选择传输方式
        if settings.MCP_SERVER_TRANSPORT == "stdio":
            # stdio模式通常由外部客户端启动
            logger.info("MCP服务端配置为stdio模式，等待客户端连接")
        elif settings.MCP_SERVER_TRANSPORT == "http":
            # HTTP模式需要启动HTTP服务器
            logger.info(f"启动MCP服务端HTTP服务器: {settings.MCP_SERVER_HOST}:{settings.MCP_SERVER_PORT}")
            # TODO: 实现HTTP模式启动
        
        # 标记服务端为运行状态
        self._server_service._running = True
    
    async def _stop_mcp_server(self) -> None:
        """停止MCP服务端"""
        if not self._server_service:
            return
        
        logger.info("停止MCP服务端")
        # TODO: 实现服务端停止逻辑
        self._server_service._running = False
    
    async def _reinitialize_services(self, old_mode: ServiceMode, new_mode: ServiceMode) -> None:
        """重新初始化服务"""
        # 清理不需要的服务
        if old_mode in [ServiceMode.PROXY_ONLY, ServiceMode.BOTH] and \
           new_mode not in [ServiceMode.PROXY_ONLY, ServiceMode.BOTH]:
            if self._proxy_service:
                await self._proxy_service.cleanup()
                self._proxy_service = None
        
        if old_mode in [ServiceMode.SERVER_ONLY, ServiceMode.BOTH] and \
           new_mode not in [ServiceMode.SERVER_ONLY, ServiceMode.BOTH]:
            self._server_service = None
        
        # 初始化新需要的服务
        if new_mode in [ServiceMode.PROXY_ONLY, ServiceMode.BOTH] and not self._proxy_service:
            self._proxy_service = MCPService()
            await self._proxy_service.initialize()
        
        if new_mode in [ServiceMode.SERVER_ONLY, ServiceMode.BOTH] and not self._server_service:
            self._server_service = MCPSServer()
    
    async def _cleanup_services(self) -> None:
        """清理服务资源"""
        try:
            if self._proxy_service:
                await self._proxy_service.stop()
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
            if settings.MCP_AUTO_START and self._mode != ServiceMode.DISABLED:
                await self.start_service()
            yield self
        finally:
            if self._running:
                await self.stop_service()
            await self._cleanup_services()

# 全局实例
unified_service = MCPUnifiedService()