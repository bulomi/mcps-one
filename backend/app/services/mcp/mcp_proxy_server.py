"""基于 FastMCP 2.0 最佳实践的 MCP 代理服务器实现"

使用 FastMCP 的 Client 和代理功能实现会话隔离和并发安全的 MCP 代理服务。
核心特性：
- 会话隔离：每个请求获得独立的后端会话
- 并发安全：支持多客户端同时访问
- 传输桥接：支持不同传输协议之间的桥接
- 高级 MCP 功能：自动转发采样、引导、日志和进度
- 零配置代理：自动发现和代理后端 MCP 工具
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from fastmcp import FastMCP, Client
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core import get_unified_config_manager, get_logger
from app.models.tool import MCPTool, ToolStatus, ToolType
from .mcp_service import MCPService
from app.utils.exceptions import MCPConnectionError, MCPTimeoutError

logger = get_logger(__name__)

class MCPProxyServer:
    """MCPS.ONE MCP 代理服务器"

    基于 FastMCP 2.0 最佳实践实现的代理服务器，提供：
    - 会话隔离：每个请求获得独立的后端会话
    - 并发安全：支持多客户端同时访问
    - 传输桥接：支持不同传输协议之间的桥接
    - 高级 MCP 功能：自动转发采样、引导、日志和进度
    """

    def __init__(self, name: str = "MCPS.ONE-Proxy"):
        self.name = name
        self.mcp_service = MCPService()
        self.proxy_servers: Dict[str, FastMCP] = {}  # tool_name -> proxy_server
        self.main_server = FastMCP(name)
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self._initialized = False

        # 配置日志级别
        try:
            from app.core.unified_config_manager import init_unified_config_manager
            config_manager = init_unified_config_manager()
            if config_manager:
                log_level = getattr(logging, config_manager.get("mcp.server.log_level", "INFO").upper(), logging.INFO)
                logger.setLevel(log_level)
            else:
                logger.setLevel(logging.INFO)
        except Exception as e:
            logger.warning(f"配置管理器初始化失败，使用默认日志级别: {e}")
            logger.setLevel(logging.INFO)

        # 设置主服务器
        self._setup_main_server()

    async def initialize(self) -> None:
        """初始化 MCP 代理服务器"""
        if self._initialized:
            return

        try:
            logger.info("初始化 MCP 代理服务器...")

            # 初始化 MCP 服务
            await self.mcp_service.initialize()

            # 创建代理服务器实例
            await self._create_proxy_servers()

            self._initialized = True
            logger.info("MCP 代理服务器初始化完成")

        except Exception as e:
            logger.error(f"MCP 代理服务器初始化失败: {e}")
            raise

    async def start(self) -> None:
        """启动 MCP 代理服务器"""
        try:
            if not self._initialized:
                await self.initialize()

            logger.info("启动 MCP 代理服务器...")

            # 启动 MCP 服务
            await self.mcp_service.start()

            logger.info("MCP 代理服务器启动完成")

        except Exception as e:
            logger.error(f"MCP 代理服务器启动失败: {e}")
            raise

    async def stop(self) -> None:
        """停止 MCP 代理服务器"""
        try:
            logger.info("停止 MCP 代理服务器...")

            # 停止 MCP 服务
            if hasattr(self.mcp_service, 'stop'):
                await self.mcp_service.stop()

            # 清理代理服务器
            self.proxy_servers.clear()

            logger.info("MCP 代理服务器停止完成")

        except Exception as e:
            logger.error(f"MCP 代理服务器停止失败: {e}")
            raise

    def _setup_main_server(self):
        """设置主服务器的管理工具"""

        @self.main_server.tool()
        async def list_available_tools() -> str:
            """列出所有可用的 MCP 工具"""
            self.request_count += 1
            try:
                db = SessionLocal()
                tools = db.query(MCPTool).filter(
                    MCPTool.status == ToolStatus.RUNNING
                ).all()
                db.close()

                tool_list = []
                for tool in tools:
                    tool_info = {
                        "name": tool.name,
                        "description": tool.description,
                        "category": tool.category,
                        "status": tool.status.value,
                        "proxy_available": tool.name in self.proxy_servers
                    }
                    tool_list.append(tool_info)

                return json.dumps(tool_list, ensure_ascii=False, indent=2)
            except Exception as e:
                self.error_count += 1
                logger.error(f"列出工具失败: {e}")
                return f"获取工具列表失败: {str(e)}"

        @self.main_server.tool()
        async def get_proxy_status() -> str:
            """获取代理服务器状态"""
            self.request_count += 1
            try:
                uptime = time.time() - self.start_time

                status_info = {
                    "server_name": self.name,
                    "uptime_seconds": round(uptime, 2),
                    "total_requests": self.request_count,
                    "total_errors": self.error_count,
                    "error_rate": round(self.error_count / max(self.request_count, 1) * 100, 2),
                    "active_proxies": len(self.proxy_servers),
                    "proxy_tools": list(self.proxy_servers.keys()),
                    "timestamp": datetime.now().isoformat()
                }

                return json.dumps(status_info, ensure_ascii=False, indent=2)
            except Exception as e:
                self.error_count += 1
                logger.error(f"获取代理状态失败: {e}")
                return f"获取代理状态失败: {str(e)}"

        @self.main_server.tool()
        async def refresh_proxies() -> str:
            """刷新代理服务器配置"""
            self.request_count += 1
            try:
                logger.info("刷新代理服务器配置...")

                # 重新创建代理服务器
                await self._create_proxy_servers()

                return f"代理服务器配置已刷新，当前活跃代理数量: {len(self.proxy_servers)}"
            except Exception as e:
                self.error_count += 1
                logger.error(f"刷新代理配置失败: {e}")
                return f"刷新代理配置失败: {str(e)}"

    async def _create_proxy_servers(self) -> None:
        """创建代理服务器实例"""
        try:
            # 清理现有代理
            self.proxy_servers.clear()

            # 获取运行中的工具
            db = SessionLocal()
            tools = db.query(MCPTool).filter(
                MCPTool.status == ToolStatus.RUNNING
            ).all()
            db.close()

            logger.info(f"找到 {len(tools)} 个运行中的工具，创建代理服务器...")

            for tool in tools:
                try:
                    await self._create_tool_proxy(tool)
                except Exception as e:
                    logger.error(f"为工具 {tool.name} 创建代理失败: {e}")
                    continue

            logger.info(f"成功创建 {len(self.proxy_servers)} 个代理服务器")

        except Exception as e:
            logger.error(f"创建代理服务器失败: {e}")
            raise

    async def _create_tool_proxy(self, tool: MCPTool) -> None:
        """为单个工具创建代理服务器"""
        try:
            # 构建工具命令
            command = self._build_tool_command(tool)
            if not command:
                logger.warning(f"无法为工具 {tool.name} 构建命令")
                return

            # 创建 Client 连接到工具
            from fastmcp.client.transports import StdioTransport
            
            # 解析命令和参数
            command_parts = command.split()
            if len(command_parts) == 0:
                logger.error(f"工具 {tool.name} 命令为空")
                return
            
            cmd = command_parts[0]
            args = command_parts[1:] if len(command_parts) > 1 else []
            
            transport = StdioTransport(cmd, args)
            client = Client(transport)

            # 创建代理服务器实例
            proxy_server = FastMCP.as_proxy(
                client,
                name=f"{tool.name}-Proxy"
            )

            # 将代理服务器挂载到主服务器
            self.main_server.mount(proxy_server, tool.name)

            # 保存代理服务器引用
            self.proxy_servers[tool.name] = proxy_server

            logger.info(f"为工具 {tool.name} 创建代理服务器成功")

        except Exception as e:
            logger.error(f"为工具 {tool.name} 创建代理服务器失败: {e}")
            raise

    def _build_tool_command(self, tool: MCPTool) -> Optional[str]:
        """构建工具启动命令"""
        try:
            if not tool.command:
                return None

            # 构建基础命令
            command = tool.command

            # 处理不同类型的工具（基于工具类型字段）
            if tool.type == ToolType.EXTERNAL:
                # 外部工具，检查是否为常见类型
                if "npx" in command or "npm" in command:
                    # NPM 工具
                    if not command.startswith("npx"):
                        command = f"npx {command}"
                elif "python" in command or command.endswith(".py"):
                    # Python 工具
                    if not command.startswith("python"):
                        command = f"python {command}"
                elif not Path(command.split()[0]).is_absolute():
                    # 相对路径的可执行文件，添加工具目录前缀
                    try:
                        config_manager = get_unified_config_manager()
                        if config_manager:
                            tool_dir = Path(config_manager.get("data.dir", "./data")) / "tools" / tool.name
                            command = str(tool_dir / command)
                    except Exception:
                        # 如果配置管理器不可用，使用原始命令
                        pass

            return command

        except Exception as e:
            logger.error(f"构建工具 {tool.name} 命令失败: {e}")
            return None

    async def run_stdio(self) -> None:
        """以 stdio 模式运行代理服务器"""
        logger.info(f"启动 {self.name} MCP 代理服务器 (stdio 模式)")
        try:
            # 确保已初始化
            if not self._initialized:
                await self.initialize()

            # 启动服务
            await self.start()

            # 运行主服务器 - 在异步上下文中使用 run_stdio_async
            await self.main_server.run_stdio_async()

        except Exception as e:
            self.error_count += 1
            logger.error(f"stdio 模式运行失败: {e}")
            raise

    async def run_http(self, host: str = "127.0.0.1", port: int = 8000) -> None:
        """以 HTTP 模式运行代理服务器"""
        logger.info(f"启动 {self.name} MCP 代理服务器 (HTTP 模式) - {host}:{port}")
        try:
            # 确保已初始化
            if not self._initialized:
                await self.initialize()

            # 启动服务
            await self.start()

            # 运行主服务器
            await self.main_server.run_streamable_http_async()

        except Exception as e:
            self.error_count += 1
            logger.error(f"HTTP 模式运行失败: {e}")
            raise

    def run_sync_stdio(self) -> None:
        """同步方式运行 stdio 模式"""
        asyncio.run(self.run_stdio())

    def run_sync_http(self, host: str = "127.0.0.1", port: int = 8000) -> None:
        """同步方式运行 HTTP 模式"""
        asyncio.run(self.run_http(host, port))

# 全局代理服务器实例
_proxy_server_instance: Optional[MCPProxyServer] = None

def get_mcp_proxy_server() -> MCPProxyServer:
    """获取 MCP 代理服务器实例"""
    global _proxy_server_instance
    if _proxy_server_instance is None:
        _proxy_server_instance = MCPProxyServer()
    return _proxy_server_instance

if __name__ == "__main__":
    # 命令行运行模式
    import argparse

    parser = argparse.ArgumentParser(description="MCPS.ONE MCP 代理服务器")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="传输协议 (默认: stdio)"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="HTTP 模式的主机地址 (默认: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="HTTP 模式的端口号 (默认: 8000)"
    )
    parser.add_argument(
        "--name",
        default="MCPS.ONE-Proxy",
        help="代理服务器名称 (默认: MCPS.ONE-Proxy)"
    )

    args = parser.parse_args()

    proxy_server = MCPProxyServer(args.name)

    if args.transport == "stdio":
        proxy_server.run_sync_stdio()
    else:
        proxy_server.run_sync_http(args.host, args.port)
