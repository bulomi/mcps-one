"""MCP 协议服务"""

import asyncio
import json
import logging
import subprocess
import signal
import os
import sys
import platform
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import psutil
from contextlib import asynccontextmanager
import shlex

from app.models.tool import MCPTool, ToolStatus, ToolType
from app.schemas.tool import ConnectionConfig
from app.core.config import settings
from app.utils.exceptions import (
    MCPConnectionError,
    MCPTimeoutError,
    ToolNotFoundError,
    ProcessError,
)
from app.utils.mcp_client import MCPClient
from app.utils.process_manager import ProcessManager

logger = logging.getLogger(__name__)

class MCPService:
    """MCP 协议服务"""
    
    def __init__(self):
        self.process_manager = ProcessManager()
        self.clients: Dict[int, MCPClient] = {}  # tool_id -> MCPClient
        self.processes: Dict[int, subprocess.Popen] = {}  # tool_id -> Process
        self._shutdown_event = asyncio.Event()
    
    async def start_tool(self, tool_id: int, force: bool = False) -> bool:
        """启动工具"""
        try:
            from app.services.tool_service import ToolService
            from app.core.database import get_db
            
            # 获取数据库会话
            db = next(get_db())
            tool_service = ToolService(db)
            
            # 获取工具信息
            tool = tool_service.get_tool(tool_id)
            if not tool:
                raise ToolNotFoundError(f"工具不存在: {tool_id}")
            
            # 检查工具状态
            if tool.status == ToolStatus.RUNNING and not force:
                logger.warning(f"工具已在运行: {tool.name}")
                return True
            
            if not tool.enabled and not force:
                raise ProcessError(f"工具已禁用: {tool.name}")
            
            # 停止现有进程（如果存在）
            if tool_id in self.processes:
                await self.stop_tool(tool_id, force=True)
            
            # 更新状态为启动中
            tool_service.update_tool_status(tool_id, ToolStatus.STARTING)
            
            # 启动进程
            process = await self._start_process(tool)
            if not process:
                tool_service.update_tool_status(
                    tool_id, 
                    ToolStatus.ERROR, 
                    error_message="进程启动失败"
                )
                return False
            
            # 保存进程信息
            self.processes[tool_id] = process
            
            # 创建 MCP 客户端
            client = await self._create_client(tool, process)
            if not client:
                await self._cleanup_process(tool_id)
                tool_service.update_tool_status(
                    tool_id, 
                    ToolStatus.ERROR, 
                    error_message="MCP 客户端创建失败"
                )
                return False
            
            self.clients[tool_id] = client
            
            # 更新状态为运行中
            tool_service.update_tool_status(
                tool_id, 
                ToolStatus.RUNNING, 
                process_id=process.pid
            )
            
            logger.info(f"工具启动成功: {tool.name} (PID: {process.pid})")
            
            # 启动健康检查
            asyncio.create_task(self._health_check_loop(tool_id))
            
            return True
            
        except Exception as e:
            logger.error(f"启动工具失败: {e}")
            await self._cleanup_tool(tool_id)
            raise
        finally:
            db.close()
    
    async def stop_tool(self, tool_id: int, force: bool = False) -> bool:
        """停止工具"""
        try:
            from app.services.tool_service import ToolService
            from app.core.database import get_db
            
            # 获取数据库会话
            db = next(get_db())
            tool_service = ToolService(db)
            
            # 获取工具信息
            tool = tool_service.get_tool(tool_id)
            if not tool:
                raise ToolNotFoundError(f"工具不存在: {tool_id}")
            
            # 检查工具状态
            if tool.status == ToolStatus.STOPPED and not force:
                logger.warning(f"工具已停止: {tool.name}")
                return True
            
            # 更新状态为停止中
            tool_service.update_tool_status(tool_id, ToolStatus.STOPPING)
            
            # 关闭 MCP 客户端
            if tool_id in self.clients:
                try:
                    await self.clients[tool_id].close()
                except Exception as e:
                    logger.warning(f"关闭 MCP 客户端失败: {e}")
                finally:
                    del self.clients[tool_id]
            
            # 停止进程
            success = await self._stop_process(tool_id, force)
            
            # 更新状态
            if success:
                tool_service.update_tool_status(tool_id, ToolStatus.STOPPED)
                logger.info(f"工具停止成功: {tool.name}")
            else:
                tool_service.update_tool_status(
                    tool_id, 
                    ToolStatus.ERROR, 
                    error_message="进程停止失败"
                )
            
            return success
            
        except Exception as e:
            logger.error(f"停止工具失败: {e}")
            raise
        finally:
            db.close()
    
    async def restart_tool(self, tool_id: int, force: bool = False) -> bool:
        """重启工具"""
        try:
            from app.services.tool_service import ToolService
            from app.core.database import get_db
            
            # 获取数据库会话
            db = next(get_db())
            tool_service = ToolService(db)
            
            # 增加重启计数
            tool = tool_service.increment_restart_count(tool_id)
            
            # 检查重启次数限制
            if tool.restart_count > tool.max_restart_attempts and not force:
                tool_service.update_tool_status(
                    tool_id, 
                    ToolStatus.ERROR, 
                    error_message=f"重启次数超过限制 ({tool.max_restart_attempts})"
                )
                return False
            
            # 停止工具
            await self.stop_tool(tool_id, force=True)
            
            # 等待1秒后重启
            await asyncio.sleep(1)
            
            # 启动工具
            return await self.start_tool(tool_id, force)
            
        except Exception as e:
            logger.error(f"重启工具失败: {e}")
            raise
        finally:
            db.close()
    
    async def get_tool_status(self, tool_id: int) -> Optional[ToolStatus]:
        """获取工具实时状态"""
        try:
            # 检查进程是否存在
            if tool_id not in self.processes:
                return ToolStatus.STOPPED
            
            process = self.processes[tool_id]
            
            # 检查进程是否还在运行
            if process.poll() is not None:
                # 进程已结束
                await self._cleanup_process(tool_id)
                return ToolStatus.STOPPED
            
            # 检查 MCP 客户端连接
            if tool_id in self.clients:
                client = self.clients[tool_id]
                if await client.is_connected():
                    return ToolStatus.RUNNING
                else:
                    return ToolStatus.ERROR
            
            return ToolStatus.STARTING
            
        except Exception as e:
            logger.error(f"获取工具状态失败: {e}")
            return ToolStatus.ERROR
    
    async def execute_tool_method(
        self, 
        tool_id: int, 
        method: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """执行工具方法"""
        try:
            if tool_id not in self.clients:
                raise MCPConnectionError(f"工具未连接: {tool_id}")
            
            client = self.clients[tool_id]
            result = await client.call_method(method, params or {})
            
            return result
            
        except Exception as e:
            logger.error(f"执行工具方法失败: {e}")
            raise
    
    async def get_tool_capabilities(self, tool_id: int) -> Dict[str, Any]:
        """获取工具能力"""
        try:
            if tool_id not in self.clients:
                raise MCPConnectionError(f"工具未连接: {tool_id}")
            
            client = self.clients[tool_id]
            capabilities = await client.get_capabilities()
            
            return capabilities
            
        except Exception as e:
            logger.error(f"获取工具能力失败: {e}")
            raise
    
    async def list_tools(self, tool_id: int) -> List[Dict[str, Any]]:
        """列出工具提供的工具"""
        try:
            if tool_id not in self.clients:
                raise MCPConnectionError(f"工具未连接: {tool_id}")
            
            client = self.clients[tool_id]
            tools = await client.list_tools()
            
            return tools
            
        except Exception as e:
            logger.error(f"列出工具失败: {e}")
            raise
    
    async def call_tool(
        self, 
        tool_id: int, 
        tool_name: str, 
        arguments: Optional[Dict[str, Any]] = None
    ) -> Any:
        """调用工具"""
        try:
            if tool_id not in self.clients:
                raise MCPConnectionError(f"工具未连接: {tool_id}")
            
            client = self.clients[tool_id]
            result = await client.call_tool(tool_name, arguments or {})
            
            return result
            
        except Exception as e:
            logger.error(f"调用工具失败: {e}")
            raise
    
    def get_client(self, tool_id: int) -> Optional[MCPClient]:
        """获取指定工具的MCP客户端"""
        return self.clients.get(tool_id)
    
    async def shutdown(self) -> None:
        """关闭服务"""
        try:
            logger.info("正在关闭 MCP 服务...")
            
            self._shutdown_event.set()
            
            # 关闭所有客户端
            for tool_id, client in list(self.clients.items()):
                try:
                    await client.close()
                except Exception as e:
                    logger.warning(f"关闭客户端失败 {tool_id}: {e}")
            
            self.clients.clear()
            
            # 停止所有进程
            for tool_id in list(self.processes.keys()):
                try:
                    await self._stop_process(tool_id, force=True)
                except Exception as e:
                    logger.warning(f"停止进程失败 {tool_id}: {e}")
            
            self.processes.clear()
            
            logger.info("MCP 服务已关闭")
            
        except Exception as e:
            logger.error(f"关闭 MCP 服务失败: {e}")
    
    # 私有方法
    def _start_process_sync(self, tool: MCPTool) -> Optional[subprocess.Popen]:
        """同步启动工具进程（在线程中运行）"""
        try:
            # 构建环境变量
            env = os.environ.copy()
            if tool.environment_variables:
                env.update(tool.environment_variables)
            
            logger.info(f"启动工具进程: {tool.name}, 命令: {tool.command}")
            
            # 启动进程
            # 如果working_directory为空，则不设置cwd参数
            kwargs = {
                "stdin": subprocess.PIPE,
                "stdout": subprocess.PIPE,
                "stderr": subprocess.PIPE,
                "env": env
            }
            
            # 只有当working_directory不为空时才设置cwd
            if tool.working_directory and tool.working_directory.strip():
                kwargs["cwd"] = tool.working_directory
            
            # Windows平台特殊处理
            if platform.system() == "Windows":
                # 在Windows上使用shell=True来执行命令，这样可以执行内置命令如echo
                kwargs["shell"] = True
                kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
                process = subprocess.Popen(tool.command, **kwargs)
            else:
                # 在非Windows平台上解析命令和参数
                cmd_parts = shlex.split(tool.command)
                kwargs["start_new_session"] = True
                process = subprocess.Popen(cmd_parts, **kwargs)
            
            # 等待一小段时间确保进程启动
            import time
            time.sleep(0.1)
            
            # 检查进程是否还在运行
            if process.poll() is not None:
                logger.error(f"进程启动后立即退出，退出码: {process.returncode}")
                return None
            
            logger.info(f"工具进程启动成功: {tool.name}, PID: {process.pid}")
            return process
            
        except Exception as e:
            import traceback
            error_details = f"启动进程失败: {e}\n命令: {tool.command}\n工作目录: {tool.working_directory or '未设置'}\n异常详情: {traceback.format_exc()}"
            logger.error(error_details)
            return None
    
    async def _start_process(self, tool: MCPTool) -> Optional[subprocess.Popen]:
        """异步启动工具进程"""
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(executor, self._start_process_sync, tool)
    
    async def _stop_process(self, tool_id: int, force: bool = False) -> bool:
        """停止进程"""
        try:
            if tool_id not in self.processes:
                return True
            
            process = self.processes[tool_id]
            
            # 检查进程是否已结束
            if process.returncode is not None:
                del self.processes[tool_id]
                return True
            
            # 优雅关闭
            if not force:
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                    del self.processes[tool_id]
                    return True
                except asyncio.TimeoutError:
                    logger.warning(f"进程优雅关闭超时，强制终止: {process.pid}")
            
            # 强制终止
            try:
                process.kill()
                await asyncio.wait_for(process.wait(), timeout=3.0)
            except asyncio.TimeoutError:
                logger.error(f"强制终止进程超时: {process.pid}")
                return False
            
            del self.processes[tool_id]
            return True
            
        except Exception as e:
            logger.error(f"停止进程失败: {e}")
            return False
    
    async def _create_client(self, tool: MCPTool, process: subprocess.Popen) -> Optional[MCPClient]:
        """创建 MCP 客户端"""
        try:
            if tool.connection_type == "stdio":
                # STDIO 连接
                client = MCPClient(
                    connection_type="stdio",
                    process=process
                )
            elif tool.connection_type in ["http", "websocket"]:
                # 服务器连接
                client = MCPClient(
                    connection_type=tool.connection_type,
                    host=tool.host or "localhost",
                    port=tool.port or 8080
                )
            else:
                logger.error(f"不支持的连接类型: {tool.connection_type}")
                return None
            
            # 连接客户端
            success = await client.connect(timeout=tool.timeout or 30)
            if not success:
                logger.error(f"MCP 客户端连接失败: {tool.name}")
                return None
            
            return client
            
        except Exception as e:
            logger.error(f"创建 MCP 客户端失败: {e}")
            return None
    
    async def _cleanup_process(self, tool_id: int) -> None:
        """清理进程"""
        if tool_id in self.processes:
            del self.processes[tool_id]
        
        if tool_id in self.clients:
            try:
                await self.clients[tool_id].close()
            except Exception:
                pass
            del self.clients[tool_id]
    
    async def _cleanup_tool(self, tool_id: int) -> None:
        """清理工具资源"""
        await self._cleanup_process(tool_id)
        
        # 更新数据库状态
        try:
            from app.services.tool_service import ToolService
            from app.core.database import get_db
            
            db = next(get_db())
            tool_service = ToolService(db)
            tool_service.update_tool_status(tool_id, ToolStatus.ERROR)
            db.close()
        except Exception as e:
            logger.error(f"更新工具状态失败: {e}")
    
    async def _health_check_loop(self, tool_id: int) -> None:
        """健康检查循环"""
        try:
            from app.services.tool_service import ToolService
            from app.core.database import get_db
            
            while not self._shutdown_event.is_set():
                try:
                    # 获取工具信息
                    db = next(get_db())
                    tool_service = ToolService(db)
                    tool = tool_service.get_tool(tool_id)
                    
                    if not tool or tool.status != ToolStatus.RUNNING:
                        break
                    
                    # 检查进程状态
                    if tool_id not in self.processes:
                        tool_service.update_tool_status(tool_id, ToolStatus.STOPPED)
                        break
                    
                    process = self.processes[tool_id]
                    if process.poll() is not None:
                        # 进程已结束
                        await self._cleanup_process(tool_id)
                        
                        # 检查是否需要自动重启
                        if tool.restart_on_failure and tool.restart_count < tool.max_restart_attempts:
                            logger.info(f"工具异常退出，自动重启: {tool.name}")
                            asyncio.create_task(self.restart_tool(tool_id))
                        else:
                            tool_service.update_tool_status(
                                tool_id, 
                                ToolStatus.ERROR, 
                                error_message="进程异常退出"
                            )
                        break
                    
                    # 检查 MCP 连接
                    if tool_id in self.clients:
                        client = self.clients[tool_id]
                        if not await client.is_connected():
                            logger.warning(f"MCP 连接断开: {tool.name}")
                            tool_service.update_tool_status(
                                tool_id, 
                                ToolStatus.ERROR, 
                                error_message="MCP 连接断开"
                            )
                            break
                    
                    db.close()
                    
                    # 等待下次检查
                    await asyncio.sleep(30)  # 固定30秒检查间隔
                    
                except Exception as e:
                    logger.error(f"健康检查失败 {tool_id}: {e}")
                    await asyncio.sleep(30)
                    
        except Exception as e:
            logger.error(f"健康检查循环异常 {tool_id}: {e}")

# 全局 MCP 服务实例
mcp_service = MCPService()