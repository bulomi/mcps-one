"""进程管理器模块

负责MCP工具进程的生命周期管理。
主要功能：
- 进程启动和停止
- 进程监控和重启
- 资源管理和限制
- 进程通信管理
"""

import asyncio
import logging
import subprocess
import signal
import psutil
import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

# from .tool_registry import ToolRegistry, ToolConfig, ToolInstance, ToolHealthStatus  # 模块不存在
from app.core.unified_config_manager import get_config
from app.core.unified_logging import get_logger
from app.utils.exceptions import (
    ProcessManagementError,
    MCPServiceError,
    ConfigurationError
)

logger = get_logger(__name__)

class ProcessStatus(Enum):
    """进程状态"""
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    CRASHED = "crashed"

@dataclass
class ProcessInfo:
    """进程信息"""
    instance_id: str
    tool_name: str
    pid: Optional[int] = None
    status: ProcessStatus = ProcessStatus.STOPPED
    start_time: Optional[datetime] = None
    stop_time: Optional[datetime] = None
    restart_count: int = 0
    last_restart_time: Optional[datetime] = None
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    command: str = ""
    working_dir: str = ""
    environment: Dict[str, str] = None
    stdout_file: Optional[str] = None
    stderr_file: Optional[str] = None
    exit_code: Optional[int] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.environment is None:
            self.environment = {}

@dataclass
class ProcessLimits:
    """进程资源限制"""
    max_memory_mb: int = 512  # 最大内存使用量(MB)
    max_cpu_percent: float = 50.0  # 最大CPU使用率(%)
    max_restart_count: int = 5  # 最大重启次数
    restart_window_minutes: int = 10  # 重启窗口时间(分钟)
    startup_timeout_seconds: int = 30  # 启动超时时间(秒)
    shutdown_timeout_seconds: int = 10  # 关闭超时时间(秒)

class ProcessManager:
    """进程管理器

    负责管理所有MCP工具进程的生命周期。
    """

    def __init__(self, tool_registry=None):  # ToolRegistry 暂时不可用
        self.tool_registry = tool_registry

        # 进程信息
        self._processes: Dict[str, ProcessInfo] = {}  # instance_id -> ProcessInfo
        self._subprocess_handles: Dict[str, subprocess.Popen] = {}  # instance_id -> Popen

        # 进程限制
        self._process_limits = ProcessLimits()

        # 监控任务
        self._monitor_task: Optional[asyncio.Task] = None
        self._running = False

        # 日志目录
        self._log_dir = Path(get_config("DATA_DIR", "./data")) / "logs" / "processes"
        self._log_dir.mkdir(parents=True, exist_ok=True)

        # 事件回调
        self.on_process_started = None
        self.on_process_stopped = None
        self.on_process_crashed = None
        self.on_process_restarted = None

    async def initialize(self) -> None:
        """初始化进程管理器"""
        try:
            logger.info("初始化进程管理器...")

            # 清理可能存在的僵尸进程
            await self._cleanup_zombie_processes()

            # 加载进程限制配置
            await self._load_process_limits()

            logger.info("进程管理器初始化完成")

        except Exception as e:
            logger.error(f"进程管理器初始化失败: {e}")
            raise MCPServiceError(f"进程管理器初始化失败: {e}")

    async def start(self) -> None:
        """启动进程管理器"""
        if self._running:
            logger.warning("进程管理器已在运行中")
            return

        try:
            logger.info("启动进程管理器...")

            # 启动监控任务
            self._monitor_task = asyncio.create_task(self._monitor_loop())

            self._running = True

            # 自动启动配置为自动启动的工具
            await self._auto_start_tools()

            logger.info("进程管理器启动完成")

        except Exception as e:
            logger.error(f"进程管理器启动失败: {e}")
            await self._cleanup()
            raise MCPServiceError(f"进程管理器启动失败: {e}")

    async def stop(self) -> None:
        """停止进程管理器"""
        if not self._running:
            logger.warning("进程管理器未在运行")
            return

        try:
            logger.info("停止进程管理器...")

            self._running = False

            # 停止监控任务
            if self._monitor_task and not self._monitor_task.done():
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass

            # 停止所有进程
            await self._stop_all_processes()

            await self._cleanup()

            logger.info("进程管理器停止完成")

        except Exception as e:
            logger.error(f"进程管理器停止失败: {e}")
            raise MCPServiceError(f"进程管理器停止失败: {e}")

    async def start_tool_instance(self, tool_name: str, instance_id: Optional[str] = None) -> str:
        """启动工具实例

        Args:
            tool_name: 工具名称
            instance_id: 实例ID, 如果不提供则自动生成

        Returns:
            实例ID

        Raises:
            ProcessManagementError: 启动失败
        """
        try:
            # 获取工具配置 (暂时跳过，因为 ToolRegistry 不可用)
            # tool_config = await self.tool_registry.get_tool_config(tool_name)
            # if not tool_config:
            #     raise ProcessManagementError(f"工具配置不存在: {tool_name}")
            # 
            # if not tool_config.enabled:
            #     raise ProcessManagementError(f"工具未启用: {tool_name}")
            
            # 临时跳过工具配置检查
            logger.warning(f"跳过工具配置检查: {tool_name} (ToolRegistry 不可用)")

            # 生成实例ID
            if not instance_id:
                instance_id = f"{tool_name}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

            # 检查实例是否已存在
            if instance_id in self._processes:
                existing_process = self._processes[instance_id]
                if existing_process.status in [ProcessStatus.RUNNING, ProcessStatus.STARTING]:
                    logger.warning(f"实例已在运行: {instance_id}")
                    return instance_id

            logger.info(f"启动工具实例: {tool_name}/{instance_id}")

            # 创建进程信息 (使用默认值，因为 tool_config 不可用)
            process_info = ProcessInfo(
                instance_id=instance_id,
                tool_name=tool_name,
                status=ProcessStatus.STARTING,
                command=f"echo 'Tool {tool_name} placeholder'",  # 临时命令
                working_dir=str(Path.cwd()),
                environment={},  # 空环境变量
                stdout_file=str(self._log_dir / f"{instance_id}.stdout.log"),
                stderr_file=str(self._log_dir / f"{instance_id}.stderr.log")
            )

            self._processes[instance_id] = process_info

            # 启动进程
            await self._start_process(process_info)

            # 在工具注册中心注册实例 (暂时跳过)
            # await self.tool_registry.add_instance(tool_name, instance_id, process_info.pid)

            # 触发回调
            if self.on_process_started:
                await self.on_process_started(process_info)

            logger.info(f"工具实例启动成功: {tool_name}/{instance_id} (PID: {process_info.pid})")

            return instance_id

        except Exception as e:
            logger.error(f"启动工具实例失败: {tool_name}/{instance_id}, error: {e}")

            # 清理失败的进程信息
            if instance_id and instance_id in self._processes:
                self._processes[instance_id].status = ProcessStatus.FAILED
                self._processes[instance_id].error_message = str(e)

            raise ProcessManagementError(f"启动工具实例失败: {e}")

    async def stop_tool_instance(self, instance_id: str, force: bool = False) -> None:
        """停止工具实例

        Args:
            instance_id: 实例ID
            force: 是否强制停止

        Raises:
            ProcessManagementError: 停止失败
        """
        try:
            if instance_id not in self._processes:
                logger.warning(f"实例不存在: {instance_id}")
                return

            process_info = self._processes[instance_id]

            if process_info.status in [ProcessStatus.STOPPED, ProcessStatus.STOPPING]:
                logger.warning(f"实例已停止或正在停止: {instance_id}")
                return

            logger.info(f"停止工具实例: {instance_id} (force: {force})")

            process_info.status = ProcessStatus.STOPPING

            # 停止进程
            await self._stop_process(process_info, force)

            # 从工具注册中心移除实例 (暂时跳过)
            # await self.tool_registry.remove_instance(instance_id)

            # 触发回调
            if self.on_process_stopped:
                await self.on_process_stopped(process_info)

            logger.info(f"工具实例停止成功: {instance_id}")

        except Exception as e:
            logger.error(f"停止工具实例失败: {instance_id}, error: {e}")
            raise ProcessManagementError(f"停止工具实例失败: {e}")

    async def restart_tool_instance(self, instance_id: str) -> None:
        """重启工具实例

        Args:
            instance_id: 实例ID

        Raises:
            ProcessManagementError: 重启失败
        """
        try:
            if instance_id not in self._processes:
                raise ProcessManagementError(f"实例不存在: {instance_id}")

            process_info = self._processes[instance_id]
            tool_name = process_info.tool_name

            logger.info(f"重启工具实例: {instance_id}")

            # 检查重启限制
            if not self._can_restart(process_info):
                raise ProcessManagementError(f"实例重启次数超过限制: {instance_id}")

            # 停止进程
            await self.stop_tool_instance(instance_id)

            # 等待一段时间
            await asyncio.sleep(1)

            # 重新启动
            process_info.restart_count += 1
            process_info.last_restart_time = datetime.now()
            process_info.status = ProcessStatus.STARTING
            process_info.error_message = None

            await self._start_process(process_info)

            # 更新工具注册中心 (暂时跳过)
            # await self.tool_registry.add_instance(tool_name, instance_id, process_info.pid)

            # 触发回调
            if self.on_process_restarted:
                await self.on_process_restarted(process_info)

            logger.info(f"工具实例重启成功: {instance_id} (重启次数: {process_info.restart_count})")

        except Exception as e:
            logger.error(f"重启工具实例失败: {instance_id}, error: {e}")
            raise ProcessManagementError(f"重启工具实例失败: {e}")

    async def get_process_info(self, instance_id: str) -> Optional[ProcessInfo]:
        """获取进程信息
        
        Args:
            instance_id: 实例ID

        Returns:
            进程信息, 如果不存在返回None
        """
        return self._processes.get(instance_id)

    async def get_all_processes(self) -> List[ProcessInfo]:
        """获取所有进程信息
        
        Returns:
            进程信息列表
        """
        return list(self._processes.values())

    async def get_tool_processes(self, tool_name: str) -> List[ProcessInfo]:
        """获取指定工具的所有进程
        
        Args:
            tool_name: 工具名称

        Returns:
            进程信息列表
        """
        return [p for p in self._processes.values() if p.tool_name == tool_name]

    async def _start_process(self, process_info: ProcessInfo) -> None:
        """启动进程
        
        Args:
            process_info: 进程信息
        """
        try:
            # 准备命令
            if isinstance(process_info.command, list):
                command = process_info.command
            else:
                command = process_info.command.split()

            # 准备环境变量
            env = process_info.environment.copy()

            # 打开日志文件
            stdout_file = open(process_info.stdout_file, 'w', encoding='utf-8')
            stderr_file = open(process_info.stderr_file, 'w', encoding='utf-8')

            # 启动进程
            process = subprocess.Popen(
                command,
                cwd=process_info.working_dir,
                env=env,
                stdout=stdout_file,
                stderr=stderr_file,
                stdin=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='strict',
                bufsize=1
            )

            # 更新进程信息
            process_info.pid = process.pid
            process_info.start_time = datetime.now()
            process_info.status = ProcessStatus.RUNNING

            # 保存进程句柄
            self._subprocess_handles[process_info.instance_id] = process

            # 等待进程启动
            await self._wait_for_startup(process_info)

        except Exception as e:
            process_info.status = ProcessStatus.FAILED
            process_info.error_message = str(e)
            raise ProcessManagementError(f"启动进程失败: {e}")

    async def _stop_process(self, process_info: ProcessInfo, force: bool = False) -> None:
        """停止进程

        Args:
            process_info: 进程信息
            force: 是否强制停止
        """
        try:
            if not process_info.pid:
                process_info.status = ProcessStatus.STOPPED
                return

            # 获取进程句柄
            process_handle = self._subprocess_handles.get(process_info.instance_id)

            if force:
                # 强制终止
                if process_handle:
                    process_handle.kill()
                else:
                    try:
                        psutil.Process(process_info.pid).kill()
                    except psutil.NoSuchProcess:
                        pass
            else:
                # 优雅关闭
                if process_handle:
                    process_handle.terminate()
                else:
                    try:
                        psutil.Process(process_info.pid).terminate()
                    except psutil.NoSuchProcess:
                        pass

                # 等待进程结束
                await self._wait_for_shutdown(process_info)

            # 清理进程句柄
            if process_info.instance_id in self._subprocess_handles:
                del self._subprocess_handles[process_info.instance_id]

            # 更新进程信息
            process_info.status = ProcessStatus.STOPPED
            process_info.stop_time = datetime.now()

            if process_handle:
                process_info.exit_code = process_handle.returncode

        except Exception as e:
            logger.error(f"停止进程失败: {process_info.instance_id}, error: {e}")
            raise ProcessManagementError(f"停止进程失败: {e}")

    async def _wait_for_startup(self, process_info: ProcessInfo) -> None:
        """等待进程启动

        Args:
            process_info: 进程信息
        """
        timeout = self._process_limits.startup_timeout_seconds
        start_time = datetime.now()

        while (datetime.now() - start_time).total_seconds() < timeout:
            try:
                if not process_info.pid:
                    break

                process = psutil.Process(process_info.pid)
                if process.is_running() and process.status() != psutil.STATUS_ZOMBIE:
                    # 进程正在运行，等待一段时间确保稳定
                    await asyncio.sleep(2)
                    if process.is_running():
                        return

            except psutil.NoSuchProcess:
                break

            await asyncio.sleep(0.5)

        # 启动超时
        process_info.status = ProcessStatus.FAILED
        process_info.error_message = "进程启动超时"
        raise ProcessManagementError(f"进程启动超时: {process_info.instance_id}")

    async def _wait_for_shutdown(self, process_info: ProcessInfo) -> None:
        """等待进程关闭

        Args:
            process_info: 进程信息
        """
        timeout = self._process_limits.shutdown_timeout_seconds
        start_time = datetime.now()

        while (datetime.now() - start_time).total_seconds() < timeout:
            try:
                if not process_info.pid:
                    return

                process = psutil.Process(process_info.pid)
                if not process.is_running():
                    return

            except psutil.NoSuchProcess:
                return

            await asyncio.sleep(0.5)

        # 关闭超时，强制终止
        logger.warning(f"进程关闭超时，强制终止: {process_info.instance_id}")
        try:
            psutil.Process(process_info.pid).kill()
        except psutil.NoSuchProcess:
            pass

    async def _monitor_loop(self) -> None:
        """监控循环"""
        while self._running:
            try:
                await self._monitor_processes()
                await asyncio.sleep(10)  # 每10秒监控一次

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"进程监控失败: {e}")
                await asyncio.sleep(5)  # 出错时短暂等待

    async def _monitor_processes(self) -> None:
        """监控所有进程"""
        for instance_id, process_info in self._processes.items():
            try:
                await self._monitor_single_process(process_info)

            except Exception as e:
                logger.error(f"监控进程失败: {instance_id}, error: {e}")

    async def _monitor_single_process(self, process_info: ProcessInfo) -> None:
        """监控单个进程

        Args:
            process_info: 进程信息
        """
        if not process_info.pid or process_info.status != ProcessStatus.RUNNING:
            return

        try:
            process = psutil.Process(process_info.pid)

            # 检查进程是否还在运行
            if not process.is_running():
                await self._handle_process_crash(process_info)
                return

            # 更新资源使用情况
            process_info.cpu_usage = process.cpu_percent()
            process_info.memory_usage = process.memory_info().rss / 1024 / 1024  # MB

            # 检查资源限制
            await self._check_resource_limits(process_info)

            # 更新工具注册中心的健康状态
            await self.tool_registry.update_instance_status(
                process_info.instance_id,
                ToolHealthStatus.HEALTHY
            )

        except psutil.NoSuchProcess:
            await self._handle_process_crash(process_info)
        except Exception as e:
            logger.error(f"监控进程失败: {process_info.instance_id}, error: {e}")
            await self.tool_registry.update_instance_status(
                process_info.instance_id,
                ToolHealthStatus.UNHEALTHY,
                str(e)
            )

    async def _handle_process_crash(self, process_info: ProcessInfo) -> None:
        """处理进程崩溃

        Args:
            process_info: 进程信息
        """
        logger.warning(f"检测到进程崩溃: {process_info.instance_id}")

        process_info.status = ProcessStatus.CRASHED
        process_info.stop_time = datetime.now()

        # TODO: 更新工具注册中心状态，当 tool_registry 可用时
        # await self.tool_registry.update_instance_status(
        #     process_info.instance_id,
        #     ToolHealthStatus.UNHEALTHY,
        #     "进程崩溃"
        # )

        # 触发回调
        if self.on_process_crashed:
            await self.on_process_crashed(process_info)

        # 尝试自动重启
        if self._can_restart(process_info):
            logger.info(f"尝试自动重启崩溃的进程: {process_info.instance_id}")
            try:
                await self.restart_tool_instance(process_info.instance_id)
            except Exception as e:
                logger.error(f"自动重启失败: {process_info.instance_id}, error: {e}")

    async def _check_resource_limits(self, process_info: ProcessInfo) -> None:
        """检查资源限制

        Args:
            process_info: 进程信息
        """
        # 检查内存使用
        if process_info.memory_usage > self._process_limits.max_memory_mb:
            logger.warning(
                f"进程内存使用超限: {process_info.instance_id}, "
                f"使用: {process_info.memory_usage:.1f}MB, "
                f"限制: {self._process_limits.max_memory_mb}MB"
            )

            # 可以选择重启进程或发出警告
            # await self.restart_tool_instance(process_info.instance_id)

        # 检查CPU使用
        if process_info.cpu_usage > self._process_limits.max_cpu_percent:
            logger.warning(
                f"进程CPU使用超限: {process_info.instance_id}, "
                f"使用: {process_info.cpu_usage:.1f}%, "
                f"限制: {self._process_limits.max_cpu_percent}%"
            )

    def _can_restart(self, process_info: ProcessInfo) -> bool:
        """检查是否可以重启

        Args:
            process_info: 进程信息

        Returns:
            是否可以重启
        """
        # 检查重启次数限制
        if process_info.restart_count >= self._process_limits.max_restart_count:
            return False

        # 检查重启窗口时间
        if process_info.last_restart_time:
            window_start = datetime.now() - timedelta(minutes=self._process_limits.restart_window_minutes)
            if process_info.last_restart_time < window_start:
                # 重置重启计数
                process_info.restart_count = 0

        return True

    def _prepare_environment(self, tool_name: str) -> Dict[str, str]:
        """准备环境变量

        Args:
            tool_name: 工具名称

        Returns:
            环境变量字典
        """
        import os

        env = os.environ.copy()

        # 添加MCP相关环境变量
        env.update({
            'MCP_TOOL_NAME': tool_name,
            'MCP_DATA_DIR': str(get_config("DATA_DIR", "./data")),
            'MCP_LOG_LEVEL': 'INFO'
        })

        return env

    async def _auto_start_tools(self) -> None:
        """自动启动配置为自动启动的工具"""
        try:
            # TODO: 重新实现自动启动逻辑，当 tool_registry 可用时
            # active_tools = await self.tool_registry.get_active_tools()
            # 
            # for tool_name in active_tools:
            #     tool_config = await self.tool_registry.get_tool_config(tool_name)
            #     if tool_config and tool_config.auto_start:
            #         logger.info(f"自动启动工具: {tool_name}")
            # 
            #         # 启动配置的实例数
            #         for i in range(tool_config.instances):
            #             try:
            #                 await self.start_tool_instance(tool_name)
            #             except Exception as e:
            #                 logger.error(f"自动启动工具实例失败: {tool_name}[{i}], error: {e}")
            logger.info("自动启动工具功能暂时禁用")

        except Exception as e:
            logger.error(f"自动启动工具失败: {e}")

    async def _stop_all_processes(self) -> None:
        """停止所有进程"""
        logger.info("停止所有进程...")

        # 首先尝试优雅关闭
        stop_tasks = []
        for instance_id in list(self._processes.keys()):
            task = asyncio.create_task(self.stop_tool_instance(instance_id))
            stop_tasks.append(task)

        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)

        # 强制终止剩余进程
        for instance_id, process_info in self._processes.items():
            if process_info.status == ProcessStatus.RUNNING and process_info.pid:
                try:
                    logger.warning(f"强制终止进程: {instance_id}")
                    psutil.Process(process_info.pid).kill()
                except psutil.NoSuchProcess:
                    pass
                except Exception as e:
                    logger.error(f"强制终止进程失败: {instance_id}, error: {e}")

    async def _cleanup_zombie_processes(self) -> None:
        """清理僵尸进程"""
        try:
            # 这里可以添加清理僵尸进程的逻辑
            pass

        except Exception as e:
            logger.error(f"清理僵尸进程失败: {e}")

    async def _load_process_limits(self) -> None:
        """加载进程限制配置"""
        try:
            # 从配置文件或设置中加载进程限制
            # 这里使用默认值
            pass

        except Exception as e:
            logger.error(f"加载进程限制配置失败: {e}")

    async def _cleanup(self) -> None:
        """清理资源"""
        try:
            # 清理进程句柄
            for handle in self._subprocess_handles.values():
                try:
                    if handle.poll() is None:
                        handle.terminate()
                except Exception:
                    pass

            self._subprocess_handles.clear()

        except Exception as e:
            logger.error(f"清理资源失败: {e}")

    def get_status(self) -> Dict[str, Any]:
        """获取进程管理器状态"""
        total_processes = len(self._processes)
        running_processes = sum(1 for p in self._processes.values() if p.status == ProcessStatus.RUNNING)
        crashed_processes = sum(1 for p in self._processes.values() if p.status == ProcessStatus.CRASHED)

        return {
            "running": self._running,
            "total_processes": total_processes,
            "running_processes": running_processes,
            "crashed_processes": crashed_processes,
            "process_limits": asdict(self._process_limits)
        }

    async def start_process(self, tool_name: str, instance_id: Optional[str] = None) -> str:
        """启动进程(start_tool_instance的别名)

        Args:
            tool_name: 工具名称
            instance_id: 实例ID

        Returns:
            实例ID
        """
        return await self.start_tool_instance(tool_name, instance_id)
