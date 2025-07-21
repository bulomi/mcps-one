import asyncio
import json
from app.core import get_logger, LogLevel, LogCategory, create_log_context
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
from app.schemas.log import SystemLogCreate, LogLevel, LogCategory
from app.core import get_unified_config_manager
from app.core import MCPSError, handle_error, error_handler, error_context
from app.utils.exceptions import (
    MCPConnectionError,
    MCPTimeoutError,
    ToolNotFoundError,
    ProcessError,
    ProcessStartError,
    ProcessStopError,
    ProcessTimeoutError,
    ProcessCrashError
)
from app.utils.error_handler import (
    RetryConfig, CircuitBreakerConfig, with_retry, handle_errors
)
from app.core.unified_cache import cached
from app.utils.process_monitor import process_monitor, ProcessConfig, ProcessState
from app.utils.mcp_client import MCPClient
from app.utils.process_manager import ProcessManager
from app.services.base.base_service import MCPBaseService

logger = get_logger(__name__)

class MCPService(MCPBaseService):
    """MCP 协议服务"""

    def __init__(self):
        super().__init__("MCP Service")
        self.process_manager = ProcessManager()
        self.processes: Dict[int, subprocess.Popen] = {}  # tool_id -> Process
        self.clients: Dict[int, Any] = {}  # tool_id -> Client

        # 配置进程监控器
        self._setup_process_monitor()

    @error_handler
    def _setup_process_monitor(self):
        """设置进程监控器"""
        # 设置回调函数
        process_monitor.on_process_crash = self._handle_process_crash
        process_monitor.on_resource_limit_exceeded = self._handle_resource_limit_exceeded
        process_monitor.on_process_restart = self._handle_process_restart

    @error_handler
    async def _handle_process_crash(self, tool_id: int, metrics):
        """处理进程崩溃"""
        try:
            logger.error(f"检测到进程崩溃: tool_id={tool_id}", category=LogCategory.SYSTEM)

            # 清理资源
            await self._cleanup_process(tool_id)

            # 更新数据库状态
            from app.services.tools import ToolService
            from app.services.system import LogService
            from app.core.database import get_db

            db = next(get_db())
            tool_service = ToolService(db)
            log_service = LogService(db)
            tool = tool_service.get_tool(tool_id)

            # 记录系统日志
            log_data = SystemLogCreate(
                level=LogLevel.ERROR,
                category=LogCategory.MCP,
                message=f"MCP工具进程崩溃: {tool.name if tool else f'tool_id={tool_id}'}",
                source="mcp_service",
                tool_id=tool_id,
                tool_name=tool.name if tool else None,
                details={"metrics": metrics.__dict__ if hasattr(metrics, '__dict__') else str(metrics)}
            )
            log_service.create_system_log(log_data)

            if tool and tool.restart_on_failure:
                # 尝试重启
                restart_count = process_monitor.restart_counts.get(tool_id, 0)
                if restart_count < tool.max_restart_attempts:
                    logger.info(f"自动重启崩溃的工具: {tool.name}", category=LogCategory.SYSTEM)

                    # 记录重启日志
                    restart_log = SystemLogCreate(
                        level=LogLevel.INFO,
                        category=LogCategory.MCP,
                        message=f"自动重启崩溃的MCP工具: {tool.name}",
                        source="mcp_service",
                        tool_id=tool_id,
                        tool_name=tool.name,
                        details={"restart_count": restart_count + 1, "max_attempts": tool.max_restart_attempts}
                    )
                    log_service.create_system_log(restart_log)

                    asyncio.create_task(self.restart_tool(tool_id, force=True))
                else:
                    tool_service.update_tool_status(
                        tool_id,
                        ToolStatus.ERROR,
                        error_message=f"进程崩溃，重启次数已达上限 ({tool.max_restart_attempts})"
                    )
            else:
                tool_service.update_tool_status(
                    tool_id,
                    ToolStatus.ERROR,
                    error_message="进程崩溃"
                )

            db.close()

        except Exception as e:
            logger.error(f"处理进程崩溃失败: {e}", category=LogCategory.SYSTEM)

    @error_handler
    async def _handle_resource_limit_exceeded(self, tool_id: int, metrics):
        """处理资源使用超限"""
        try:
            logger.warning(
                f"工具资源使用超限: tool_id={tool_id}, "
                f"内存={metrics.memory_mb:.2f}MB, CPU={metrics.cpu_percent:.2f}%"
            , category=LogCategory.SYSTEM)

            # 更新数据库状态
            from app.services.tools import ToolService
            from app.core.database import get_db

            db = next(get_db())
            tool_service = ToolService(db)

            error_msg = f"资源使用超限: 内存={metrics.memory_mb:.2f}MB, CPU={metrics.cpu_percent:.2f}%"
            tool_service.update_tool_status(
                tool_id,
                ToolStatus.ERROR,
                error_message=error_msg
            )

            db.close()

        except Exception as e:
            logger.error(f"处理资源超限失败: {e}", category=LogCategory.SYSTEM)

    @error_handler
    async def _handle_process_restart(self, tool_id: int):
        """处理进程重启"""
        try:
            logger.info(f"进程监控器触发重启: tool_id={tool_id}", category=LogCategory.SYSTEM)

            # 更新数据库状态
            from app.services.tools import ToolService
            from app.core.database import get_db

            db = next(get_db())
            tool_service = ToolService(db)
            tool_service.update_tool_status(tool_id, ToolStatus.STARTING)
            db.close()

        except Exception as e:
            logger.error(f"处理进程重启失败: {e}", category=LogCategory.SYSTEM)

    @error_handler
    async def _initialize_impl(self) -> None:
        """具体的初始化实现"""
        # 这里可以添加初始化逻辑，比如：
        # - 加载配置
        # - 初始化连接池
        # - 预加载工具等
        pass

    @error_handler
    async def _start_impl(self) -> None:
        """具体的启动实现"""
        # 启动MCP代理服务的具体逻辑
        pass

    @error_handler
    async def _stop_impl(self) -> None:
        """具体的停止实现"""
        # 停止所有工具
        for tool_id in list(self.clients.keys()):
            await self.stop_tool(tool_id)

    @error_handler
    async def _cleanup_impl(self) -> None:
        """具体的清理实现"""
        # 清理所有资源
        for tool_id in list(self.clients.keys()):
            await self.cleanup_tool(tool_id)

        # 清理进程
        for tool_id, process in list(self.processes.items()):
            try:
                if process.poll() is None:
                    process.terminate()
                    await asyncio.sleep(1)
                    if process.poll() is None:
                        process.kill()
            except Exception as e:
                self.logger.error(f"清理进程失败: {e}", category=LogCategory.SYSTEM)
            finally:
                del self.processes[tool_id]

    @error_handler
    async def _auto_start_tools(self) -> None:
        """自动启动设置了auto_start=true的工具"""
        try:
            logger.info("MCP代理服务启动完成", category=LogCategory.SYSTEM)
        except Exception as e:
            self.logger.error(f"MCP代理服务启动失败: {e}", category=LogCategory.SYSTEM)
            raise

    @error_handler
    async def stop(self) -> None:
        """停止MCP代理服务"""
        try:
            logger.info("停止MCP代理服务...", category=LogCategory.SYSTEM)

            # 停止所有工具
            for tool_id in list(self.processes.keys()):
                try:
                    await self.stop_tool(tool_id, force=True)
                except Exception as e:
                    logger.warning(f"停止工具 {tool_id} 失败: {e}", category=LogCategory.SYSTEM)

            # 关闭所有客户端
            for tool_id, client in list(self.clients.items()):
                try:
                    await client.close()
                except Exception as e:
                    logger.warning(f"关闭客户端 {tool_id} 失败: {e}", category=LogCategory.SYSTEM)

            self.clients.clear()
            self.processes.clear()

            logger.info("MCP代理服务停止完成", category=LogCategory.SYSTEM)

        except Exception as e:
            logger.error(f"MCP代理服务停止失败: {e}", category=LogCategory.SYSTEM)
            raise

    @property
    @error_handler
    def is_running(self) -> bool:
        """检查服务是否正在运行"""
        return self._initialized and len(self.processes) > 0
    
    @error_handler
    @cached(ttl=300)
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """获取可用工具列表"""
        tools = []

        try:
            from app.services.tools import ToolService
            from app.core.database import get_db

            db = next(get_db())
            tool_service = ToolService(db)

            # 获取所有启用的工具
            db_tools, _ = tool_service.get_tools(filters={'enabled': True})

            for tool in db_tools:
                tool_info = {
                    "id": tool.id,
                    "name": tool.name,
                    "description": tool.description,
                    "category": tool.category,
                    "status": tool.status.value,
                    "enabled": tool.enabled,
                    "capabilities": None
                }
                tools.append(tool_info)

            db.close()

        except Exception as e:
            logger.error(f"获取可用工具列表失败: {e}", category=LogCategory.SYSTEM)

        return tools

    @error_handler
    @cached(ttl=300)
    async def get_available_tools_with_capabilities(self) -> List[Dict[str, Any]]:
        """获取可用工具列表（包含capabilities信息）"""
        tools = []

        try:
            from app.services.tools import ToolService
            from app.core.database import get_db

            db = next(get_db())
            tool_service = ToolService(db)

            # 获取所有启用的工具
            db_tools, _ = tool_service.get_tools(filters={'enabled': True})

            for tool in db_tools:
                tool_info = {
                    "id": tool.id,
                    "name": tool.name,
                    "description": tool.description,
                    "category": tool.category,
                    "status": tool.status.value,
                    "enabled": tool.enabled,
                    "capabilities": None
                }

                # 如果工具正在运行，尝试获取其capabilities
                if tool.status == ToolStatus.RUNNING and tool.id in self.clients:
                    try:
                        client = self.clients[tool.id]
                        logger.info(f"检查工具 {tool.name} (ID: {tool.id}) 的客户端连接状态", category=LogCategory.SYSTEM)
                        if client:
                            is_connected = await client.is_connected()
                            logger.info(f"工具 {tool.name} 客户端连接状态: {is_connected}", category=LogCategory.SYSTEM)
                            if is_connected:
                                capabilities = await client.list_tools()
                                tool_info["capabilities"] = capabilities
                                logger.info(f"获取工具 {tool.name} 的capabilities成功，共 {len(capabilities, category=LogCategory.SYSTEM)} 个函数")
                            else:
                                logger.warning(f"工具 {tool.name} 的客户端未连接", category=LogCategory.SYSTEM)
                        else:
                            logger.warning(f"工具 {tool.name} 的客户端不存在", category=LogCategory.SYSTEM)
                    except Exception as e:
                        logger.error(f"获取工具 {tool.name} 的capabilities失败: {e}", exc_info=True, category=LogCategory.SYSTEM)
                else:
                    logger.info(f"工具 {tool.name} 状态: {tool.status.value}, 客户端存在: {tool.id in self.clients}", category=LogCategory.SYSTEM)

                tools.append(tool_info)

            db.close()

        except Exception as e:
            logger.error(f"获取可用工具列表失败: {e}", category=LogCategory.SYSTEM)

        return tools

    @with_retry(
        RetryConfig(max_attempts=3, base_delay=1.0, exponential_base=2.0),
        circuit_breaker_name="start_tool",
        circuit_breaker_config=CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60.0)
    )
    @error_handler
    async def start_tool(self, tool_id: int, force: bool = False) -> bool:
        """启动工具"""
        try:
            from app.services.tools import ToolService
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
                # 检查实际进程是否存在
                actual_status = await self.get_tool_status(tool_id)
                if actual_status == ToolStatus.RUNNING:
                    logger.warning(f"工具已在运行: {tool.name}", category=LogCategory.SYSTEM)
                    return True
                else:
                    # 数据库状态与实际状态不一致，需要重新启动
                    logger.warning(f"工具状态不一致，数据库显示运行但进程不存在: {tool.name}，将重新启动", category=LogCategory.SYSTEM)
                    # 清理状态并继续启动流程
                    await self._cleanup_tool(tool_id)

            if not tool.enabled and not force:
                raise ProcessError(f"工具已禁用: {tool.name}")

            # 停止现有进程（如果存在）
            if tool_id in self.processes:
                await self.stop_tool(tool_id, force=True)

            # 更新状态为启动中
            tool_service.update_tool_status(tool_id, ToolStatus.STARTING)

            # 启动进程
            process = await self._start_process_with_retry(tool)
            if not process:
                tool_service.update_tool_status(
                    tool_id,
                    ToolStatus.ERROR,
                    error_message="进程启动失败"
                )
                raise ProcessStartError(f"工具进程启动失败: {tool.name}")

            # 保存进程信息
            self.processes[tool_id] = process

            # 注册到进程监控器
            process_monitor.register_process(tool_id, process, tool.startup_command or "")

            # 创建 MCP 客户端
            client = await self._create_client_with_retry(tool, process)
            if not client:
                await self._cleanup_process(tool_id)
                tool_service.update_tool_status(
                    tool_id,
                    ToolStatus.ERROR,
                    error_message="MCP 客户端创建失败"
                )
                raise MCPConnectionError(f"MCP 客户端创建失败: {tool.name}")

            self.clients[tool_id] = client

            # 更新状态为运行中
            tool_service.update_tool_status(
                tool_id,
                ToolStatus.RUNNING,
                process_id=process.pid
            )

            logger.info(f"工具启动成功: {tool.name} (PID: {process.pid})", category=LogCategory.SYSTEM)

            # 记录系统日志
            try:
                from app.services.system import LogService
                log_service = LogService(db)
                log_data = SystemLogCreate(
                    level=LogLevel.INFO,
                    category=LogCategory.TOOL,
                    message=f"工具启动成功: {tool.name}",
                    details={
                        "tool_id": tool.id,
                        "tool_name": tool.name,
                        "process_id": process.pid,
                        "tool_type": tool.type.value,
                        "force_start": force
                    }
                )
                log_service.create_system_log(log_data)
            except Exception as log_error:
                logger.warning(f"记录系统日志失败: {log_error}", category=LogCategory.SYSTEM)

            # 启动健康检查
            asyncio.create_task(self._health_check_loop(tool_id))

            return True

        except (ProcessStartError, MCPConnectionError, ToolNotFoundError) as e:
            logger.error(f"启动工具失败: {e}", category=LogCategory.SYSTEM)
            await self._cleanup_tool(tool_id)
            raise
        except Exception as e:
            logger.error(f"启动工具失败: {e}", category=LogCategory.SYSTEM)
            await self._cleanup_tool(tool_id)
            raise ProcessStartError(f"工具启动失败: {e}")
        finally:
            db.close()

    @with_retry(
        RetryConfig(max_attempts=2, base_delay=0.5, exponential_base=1.5),
        circuit_breaker_name="stop_tool",
        circuit_breaker_config=CircuitBreakerConfig(failure_threshold=3, recovery_timeout=30.0)
    )
    @error_handler
    async def stop_tool(self, tool_id: int, force: bool = False) -> bool:
        """停止工具"""
        try:
            from app.services.tools import ToolService
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
                logger.warning(f"工具已停止: {tool.name}", category=LogCategory.SYSTEM)
                return True

            # 更新状态为停止中
            tool_service.update_tool_status(tool_id, ToolStatus.STOPPING)

            # 关闭 MCP 客户端
            if tool_id in self.clients:
                try:
                    await asyncio.wait_for(self.clients[tool_id].close(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning(f"关闭 MCP 客户端超时: {tool.name}", category=LogCategory.SYSTEM)
                except Exception as e:
                    logger.warning(f"关闭 MCP 客户端失败: {e}", category=LogCategory.SYSTEM)
                finally:
                    del self.clients[tool_id]

            # 停止进程
            success = await self._stop_process_with_retry(tool_id, force)

            # 从进程监控器注销
            process_monitor.unregister_process(tool_id)

            # 更新状态
            if success:
                tool_service.update_tool_status(tool_id, ToolStatus.STOPPED)
                logger.info(f"工具停止成功: {tool.name}", category=LogCategory.SYSTEM)

                # 记录系统日志
                try:
                    from app.services.system import LogService
                    log_service = LogService(db)
                    log_data = SystemLogCreate(
                        level=LogLevel.INFO,
                        category=LogCategory.TOOL,
                        message=f"工具停止成功: {tool.name}",
                        details={
                            "tool_id": tool.id,
                            "tool_name": tool.name,
                            "force_stop": force
                        }
                    )
                    log_service.create_system_log(log_data)
                except Exception as log_error:
                    logger.warning(f"记录系统日志失败: {log_error}", category=LogCategory.SYSTEM)
            else:
                tool_service.update_tool_status(
                    tool_id,
                    ToolStatus.ERROR,
                    error_message="进程停止失败"
                )
                raise ProcessStopError(f"工具进程停止失败: {tool.name}")

            return success

        except (ProcessStopError, ToolNotFoundError) as e:
            logger.error(f"停止工具失败: {e}", category=LogCategory.SYSTEM)
            raise
        except Exception as e:
            logger.error(f"停止工具失败: {e}", category=LogCategory.SYSTEM)
            raise ProcessStopError(f"工具停止失败: {e}")
        finally:
            db.close()

    @error_handler
    async def restart_tool(self, tool_id: int, force: bool = False) -> bool:
        """重启工具"""
        try:
            from app.services.tools import ToolService
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
            logger.error(f"重启工具失败: {e}", category=LogCategory.SYSTEM)
            raise
        finally:
            db.close()

    @error_handler
    @cached(ttl=300)
    async def get_tool_status(self, tool_id: int) -> Optional[ToolStatus]:
        """获取工具实时状态"""
        try:
            logger.debug(f"检查工具状态: tool_id={tool_id}", category=LogCategory.SYSTEM)

            # 检查进程是否存在
            if tool_id not in self.processes:
                logger.debug(f"工具进程不存在: tool_id={tool_id}", category=LogCategory.SYSTEM)
                return ToolStatus.STOPPED

            process = self.processes[tool_id]
            logger.debug(f"工具进程存在: tool_id={tool_id}, pid={process.pid}", category=LogCategory.SYSTEM)

            # 检查进程是否还在运行
            poll_result = process.poll()
            if poll_result is not None:
                # 进程已结束
                logger.debug(f"工具进程已结束: tool_id={tool_id}, exit_code={poll_result}", category=LogCategory.SYSTEM)
                await self._cleanup_process(tool_id)
                return ToolStatus.STOPPED

            logger.debug(f"工具进程正在运行: tool_id={tool_id}", category=LogCategory.SYSTEM)

            # 检查 MCP 客户端连接
            if tool_id in self.clients:
                client = self.clients[tool_id]
                logger.debug(f"检查MCP客户端连接: tool_id={tool_id}", category=LogCategory.SYSTEM)
                is_connected = await client.is_connected()
                logger.debug(f"MCP客户端连接状态: tool_id={tool_id}, connected={is_connected}", category=LogCategory.SYSTEM)
                if is_connected:
                    return ToolStatus.RUNNING
                else:
                    return ToolStatus.ERROR
            else:
                logger.debug(f"MCP客户端不存在: tool_id={tool_id}", category=LogCategory.SYSTEM)

            return ToolStatus.STARTING

        except Exception as e:
            logger.error(f"获取工具状态失败: {e}", category=LogCategory.SYSTEM)
            return ToolStatus.ERROR

    @with_retry(
        RetryConfig(max_attempts=3, base_delay=0.5, exponential_base=2.0),
        circuit_breaker_name="execute_tool_method",
        circuit_breaker_config=CircuitBreakerConfig(failure_threshold=5, recovery_timeout=30.0)
    )
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

            # 检查连接状态
            if not await client.is_connected():
                raise MCPConnectionError(f"工具连接已断开: {tool_id}")

            # 执行方法调用，设置超时
            result = await asyncio.wait_for(
                client.call_method(method, params or {}),
                timeout=30.0
            )

            return result

        except asyncio.TimeoutError:
            logger.error(f"执行工具方法超时: {tool_id}.{method}", category=LogCategory.SYSTEM)
            raise MCPTimeoutError(f"工具方法执行超时: {method}")
        except MCPConnectionError:
            raise
        except Exception as e:
            logger.error(f"执行工具方法失败: {e}", category=LogCategory.SYSTEM)
            raise MCPConnectionError(f"工具方法执行失败: {e}")

    @error_handler
    async def start_tool_by_name(self, tool_name: str, force: bool = False) -> bool:
        """通过工具名称启动工具"""
        try:
            from app.services.tools import ToolService
            from app.core.database import get_db

            # 获取数据库会话
            db = next(get_db())
            tool_service = ToolService(db)

            # 通过名称获取工具
            tool = tool_service.get_tool_by_name(tool_name)
            if not tool:
                raise ToolNotFoundError(f"工具不存在: {tool_name}")

            db.close()

            # 调用现有的start_tool方法
            return await self.start_tool(tool.id, force=force)

        except Exception as e:
            logger.error(f"通过名称启动工具失败: {e}", category=LogCategory.SYSTEM)
            raise

    @error_handler
    async def stop_tool_by_name(self, tool_name: str, force: bool = False) -> bool:
        """通过工具名称停止工具"""
        try:
            from app.services.tools import ToolService
            from app.core.database import get_db

            # 获取数据库会话
            db = next(get_db())
            tool_service = ToolService(db)

            # 通过名称获取工具
            tool = tool_service.get_tool_by_name(tool_name)
            if not tool:
                raise ToolNotFoundError(f"工具不存在: {tool_name}")

            db.close()

            # 调用现有的stop_tool方法
            return await self.stop_tool(tool.id, force=force)

        except Exception as e:
            logger.error(f"通过名称停止工具失败: {e}", category=LogCategory.SYSTEM)
            raise


    @error_handler
    @cached(ttl=300)
    async def get_tool_capabilities(self, tool_id: int) -> Dict[str, Any]:
        """获取工具能力"""
        try:
            if tool_id not in self.clients:
                raise MCPConnectionError(f"工具未连接: {tool_id}")

            client = self.clients[tool_id]
            capabilities = await client.get_capabilities()

            return capabilities

        except Exception as e:
            logger.error(f"获取工具能力失败: {e}", category=LogCategory.SYSTEM)
            raise

    @error_handler
    async def list_tools(self, tool_id: int) -> List[Dict[str, Any]]:
        """列出工具提供的工具"""
        try:
            if tool_id not in self.clients:
                raise MCPConnectionError(f"工具未连接: {tool_id}")

            client = self.clients[tool_id]
            tools = await client.list_tools()

            return tools

        except Exception as e:
            logger.error(f"列出工具失败: {e}", category=LogCategory.SYSTEM)
            raise

    @with_retry(
        RetryConfig(max_attempts=3, base_delay=0.5, exponential_base=2.0),
        circuit_breaker_name="call_tool",
        circuit_breaker_config=CircuitBreakerConfig(failure_threshold=5, recovery_timeout=30.0)
    )
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

            # 检查连接状态
            if not await client.is_connected():
                raise MCPConnectionError(f"工具连接已断开: {tool_id}")

            # 调用工具，设置超时
            result = await asyncio.wait_for(
                client.call_tool(tool_name, arguments or {}),
                timeout=60.0
            )

            return result

        except asyncio.TimeoutError:
            logger.error(f"调用工具超时: {tool_id}.{tool_name}", category=LogCategory.SYSTEM)
            raise MCPTimeoutError(f"工具调用超时: {tool_name}")
        except MCPConnectionError:
            raise
        except Exception as e:
            logger.error(f"调用工具失败: {e}", category=LogCategory.SYSTEM)
            raise MCPConnectionError(f"工具调用失败: {e}")

    @error_handler
    @cached(ttl=300)
    async def get_client(self, tool_id: int) -> Optional[MCPClient]:
        """获取指定工具的MCP客户端"""
        return self.clients.get(tool_id)

    @error_handler
    @cached(ttl=300)
    async def get_client_by_name(self, tool_name: str) -> Optional[MCPClient]:
        """通过工具名称获取MCP客户端"""
        try:
            from app.services.tools import ToolService
            from app.core.database import get_db

            db = next(get_db())
            tool_service = ToolService(db)
            tool = tool_service.get_tool_by_name(tool_name)
            db.close()

            if not tool:
                logger.warning(f"工具未找到: {tool_name}", category=LogCategory.SYSTEM)
                return None

            logger.info(f"查找工具客户端: tool_id={tool.id}, clients字典内容: {list(self.clients.keys())}", category=LogCategory.SYSTEM)
            client = self.clients.get(tool.id)
            logger.info(f"获取到的客户端: {client}", category=LogCategory.SYSTEM)
            return client

        except Exception as e:
            logger.error(f"获取工具客户端失败: {tool_name}, 错误: {e}", category=LogCategory.SYSTEM)
            return None

    @error_handler
    async def shutdown(self) -> None:
        """关闭服务"""
        try:
            logger.info("正在关闭 MCP 服务...", category=LogCategory.SYSTEM)

            self._shutdown_event.set()

            # 停止进程监控器
            await process_monitor.shutdown()

            # 关闭所有客户端
            for tool_id, client in list(self.clients.items()):
                try:
                    await client.close()
                except Exception as e:
                    logger.warning(f"关闭客户端失败 {tool_id}: {e}", category=LogCategory.SYSTEM)

            self.clients.clear()

            # 停止所有进程
            for tool_id in list(self.processes.keys()):
                try:
                    await self._stop_process(tool_id, force=True)
                except Exception as e:
                    logger.warning(f"停止进程失败 {tool_id}: {e}", category=LogCategory.SYSTEM)

            self.processes.clear()

            logger.info("MCP 服务已关闭", category=LogCategory.SYSTEM)

        except Exception as e:
            logger.error(f"关闭 MCP 服务失败: {e}", category=LogCategory.SYSTEM)

    # 私有方法
    @error_handler
    def _start_process_sync(self, tool: MCPTool) -> Optional[subprocess.Popen]:
        """同步启动工具进程（在线程中运行）"""
        try:
            # 构建环境变量
            env = os.environ.copy()

            # 添加编码相关的环境变量以解决中文乱码问题
            if platform.system() == "Windows":
                env.update({
                    'PYTHONIOENCODING': 'utf-8',
                    'PYTHONLEGACYWINDOWSSTDIO': '0',
                    'FORCE_COLOR': '0',  # 禁用颜色输出避免编码问题
                    'CHCP': '65001'  # 设置Windows代码页为UTF-8
                })
            else:
                env.update({
                    'PYTHONIOENCODING': 'utf-8',
                    'LANG': 'zh_CN.UTF-8',
                    'LC_ALL': 'zh_CN.UTF-8',
                    'FORCE_COLOR': '0'  # 禁用颜色输出避免编码问题
                })

            if tool.environment_variables:
                env.update(tool.environment_variables)

            logger.info(f"启动工具进程: {tool.name}, 命令: {tool.command}", category=LogCategory.SYSTEM)

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
                kwargs["text"] = True
                kwargs["encoding"] = 'utf-8'
                kwargs["errors"] = 'strict'
                process = subprocess.Popen(tool.command, **kwargs)

            else:
                # 在非Windows平台上解析命令和参数
                cmd_parts = shlex.split(tool.command)
                kwargs["start_new_session"] = True
                kwargs["text"] = True
                kwargs["encoding"] = 'utf-8'
                kwargs["errors"] = 'strict'
                process = subprocess.Popen(cmd_parts, **kwargs)

            # 等待一小段时间确保进程启动
            import time
            time.sleep(0.1)

            # 检查进程是否还在运行
            if process.poll() is not None:
                logger.error(f"进程启动后立即退出，退出码: {process.returncode}", category=LogCategory.SYSTEM)
                return None

            logger.info(f"工具进程启动成功: {tool.name}, PID: {process.pid}", category=LogCategory.SYSTEM)
            return process

        except Exception as e:
            import traceback
            error_details = f"启动进程失败: {e}\n命令: {tool.command}\n工作目录: {tool.working_directory or '未设置'}\n异常详情: {traceback.format_exc()}"
            logger.error(error_details, category=LogCategory.SYSTEM)
            return None

    @error_handler
    async def _start_process(self, tool: MCPTool) -> Optional[subprocess.Popen]:
        """异步启动工具进程"""
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(executor, self._start_process_sync, tool)

    @with_retry(RetryConfig(max_attempts=3, base_delay=1.0, exponential_base=2.0))
    @error_handler
    async def _start_process_with_retry(self, tool: MCPTool) -> Optional[subprocess.Popen]:
        """带重试的启动工具进程"""
        try:
            process = await self._start_process(tool)
            if not process:
                raise ProcessStartError(f"进程启动失败: {tool.name}")
            return process
        except Exception as e:
            logger.error(f"启动进程失败: {tool.name}, 错误: {e}", category=LogCategory.SYSTEM)
            raise ProcessStartError(f"进程启动失败: {e}")

    @error_handler
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
                    logger.warning(f"进程优雅关闭超时，强制终止: {process.pid}", category=LogCategory.SYSTEM)

            # 强制终止
            try:
                process.kill()
                await asyncio.wait_for(process.wait(), timeout=3.0)
            except asyncio.TimeoutError:
                logger.error(f"强制终止进程超时: {process.pid}", category=LogCategory.SYSTEM)
                return False

            del self.processes[tool_id]
            return True

        except Exception as e:
            logger.error(f"停止进程失败: {e}", category=LogCategory.SYSTEM)
            return False

    @with_retry(RetryConfig(max_attempts=2, base_delay=0.5, exponential_base=1.5))
    @error_handler
    async def _stop_process_with_retry(self, tool_id: int, force: bool = False) -> bool:
        """带重试的停止进程"""
        try:
            success = await self._stop_process(tool_id, force)
            if not success:
                raise ProcessStopError(f"进程停止失败: {tool_id}")
            return success
        except Exception as e:
            logger.error(f"停止进程失败: {tool_id}, 错误: {e}", category=LogCategory.SYSTEM)
            raise ProcessStopError(f"进程停止失败: {e}")

    @error_handler
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
                logger.error(f"不支持的连接类型: {tool.connection_type}", category=LogCategory.SYSTEM)
                return None

            # 连接客户端
            success = await client.connect(timeout=tool.timeout or 30)
            if not success:
                logger.error(f"MCP 客户端连接失败: {tool.name}", category=LogCategory.SYSTEM)
                return None

            return client

        except Exception as e:
            logger.error(f"创建 MCP 客户端失败: {e}", category=LogCategory.SYSTEM)
            return None

    @with_retry(RetryConfig(max_attempts=3, base_delay=1.0, exponential_base=2.0))
    @error_handler
    async def _create_client_with_retry(self, tool: MCPTool, process: subprocess.Popen) -> Optional[MCPClient]:
        """带重试的创建 MCP 客户端"""
        try:
            client = await self._create_client(tool, process)
            if not client:
                raise MCPConnectionError(f"MCP 客户端创建失败: {tool.name}")
            return client
        except Exception as e:
            logger.error(f"创建 MCP 客户端失败: {tool.name}, 错误: {e}", category=LogCategory.SYSTEM)
            raise MCPConnectionError(f"MCP 客户端创建失败: {e}")

    @error_handler
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

    @error_handler
    async def _cleanup_tool(self, tool_id: int) -> None:
        """清理工具资源"""
        await self._cleanup_process(tool_id)

        # 更新数据库状态
        try:
            from app.services.tools import ToolService
            from app.core.database import get_db

            db = next(get_db())
            tool_service = ToolService(db)
            tool_service.update_tool_status(tool_id, ToolStatus.ERROR)
            db.close()
        except Exception as e:
            logger.error(f"更新工具状态失败: {e}", category=LogCategory.SYSTEM)

    @error_handler
    async def _health_check_loop(self, tool_id: int) -> None:
        """健康检查循环"""
        try:
            from app.services.tools import ToolService
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
                        exit_code = process.returncode
                        await self._cleanup_process(tool_id)

                        # 检查是否需要自动重启
                        if tool.restart_on_failure and tool.restart_count < tool.max_restart_attempts:
                            logger.info(f"工具异常退出（退出码: {exit_code}），自动重启: {tool.name}", category=LogCategory.SYSTEM)
                            try:
                                asyncio.create_task(self.restart_tool(tool_id))
                            except Exception as restart_error:
                                logger.error(f"自动重启失败: {restart_error}", category=LogCategory.SYSTEM)
                                tool_service.update_tool_status(
                                    tool_id,
                                    ToolStatus.ERROR,
                                    error_message=f"进程异常退出且重启失败: {restart_error}"
                                )
                        else:
                            error_msg = f"进程异常退出（退出码: {exit_code}）"
                            if tool.restart_count >= tool.max_restart_attempts:
                                error_msg += f"，重启次数已达上限 ({tool.max_restart_attempts})"
                            tool_service.update_tool_status(
                                tool_id,
                                ToolStatus.ERROR,
                                error_message=error_msg
                            )
                        break

                    # 检查 MCP 连接
                    if tool_id in self.clients:
                        client = self.clients[tool_id]
                        if not await client.is_connected():
                            logger.warning(f"MCP 连接断开: {tool.name}", category=LogCategory.SYSTEM)
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
                    logger.error(f"健康检查失败 {tool_id}: {e}", category=LogCategory.SYSTEM)
                    await asyncio.sleep(30)

        except Exception as e:
            logger.error(f"健康检查循环异常 {tool_id}: {e}", category=LogCategory.SYSTEM)

    @error_handler
    async def _auto_start_tools(self) -> None:
        """自动启动设置了auto_start=true的工具"""
        try:
            from app.services.tools import ToolService
            from app.core.database import get_db

            logger.info("开始自动启动工具...", category=LogCategory.SYSTEM)

            db = next(get_db())
            tool_service = ToolService(db)

            # 查找所有设置了auto_start=true且启用的工具
            filters = {
                'enabled': True
            }
            tools, _ = tool_service.get_tools(filters=filters)

            auto_start_tools = [tool for tool in tools if getattr(tool, 'auto_start', False)]

            if not auto_start_tools:
                logger.info("没有找到需要自动启动的工具", category=LogCategory.SYSTEM)
                db.close()
                return

            logger.info(f"找到 {len(auto_start_tools)} 个需要自动启动的工具", category=LogCategory.SYSTEM)

            # 并发启动所有auto_start工具
            start_tasks = []
            for tool in auto_start_tools:
                logger.info(f"准备自动启动工具: {tool.name} (ID: {tool.id})", category=LogCategory.SYSTEM)
                task = asyncio.create_task(self._auto_start_single_tool(tool.id, tool.name))
                start_tasks.append(task)

            # 等待所有启动任务完成
            if start_tasks:
                results = await asyncio.gather(*start_tasks, return_exceptions=True)

                success_count = 0
                for i, result in enumerate(results):
                    tool = auto_start_tools[i]
                    if isinstance(result, Exception):
                        logger.error(f"自动启动工具失败: {tool.name}, 错误: {result}", category=LogCategory.SYSTEM)
                    elif result:
                        success_count += 1
                        logger.info(f"自动启动工具成功: {tool.name}", category=LogCategory.SYSTEM)
                    else:
                        logger.warning(f"自动启动工具失败: {tool.name}", category=LogCategory.SYSTEM)

                logger.info(f"自动启动完成: 成功 {success_count}/{len(auto_start_tools)} 个工具", category=LogCategory.SYSTEM)

            db.close()

        except Exception as e:
            logger.error(f"自动启动工具失败: {e}", category=LogCategory.SYSTEM)

    @error_handler
    async def _auto_start_single_tool(self, tool_id: int, tool_name: str) -> bool:
        """自动启动单个工具"""
        try:
            logger.info(f"正在自动启动工具: {tool_name} (ID: {tool_id})", category=LogCategory.SYSTEM)
            return await self.start_tool(tool_id, force=False)
        except Exception as e:
            logger.error(f"自动启动工具失败: {tool_name} (ID: {tool_id}), 错误: {e}", category=LogCategory.SYSTEM)
            return False

# 全局 MCP 服务实例
mcp_service = MCPService()
