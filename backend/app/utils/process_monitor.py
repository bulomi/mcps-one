"""进程监控和管理模块"""
import asyncio
import psutil
import logging
import time
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from .exceptions import ProcessError, ProcessCrashError, ProcessResourceError

logger = logging.getLogger(__name__)

class ProcessState(Enum):
    """进程状态"""
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    CRASHED = "crashed"

@dataclass
class ProcessMetrics:
    """进程性能指标"""
    pid: int
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    num_threads: int
    num_fds: int  # 文件描述符数量
    create_time: float
    status: str
    timestamp: datetime

@dataclass
class ProcessConfig:
    """进程配置"""
    max_memory_mb: float = 1024.0  # 最大内存使用（MB）
    max_cpu_percent: float = 80.0  # 最大CPU使用率
    max_restart_attempts: int = 3  # 最大重启次数
    restart_delay: float = 5.0  # 重启延迟（秒）
    health_check_interval: float = 30.0  # 健康检查间隔（秒）
    startup_timeout: float = 60.0  # 启动超时（秒）
    shutdown_timeout: float = 30.0  # 关闭超时（秒）
    enable_auto_restart: bool = True  # 启用自动重启
    enable_resource_monitoring: bool = True  # 启用资源监控

class ProcessMonitor:
    """进程监控器"""

    def __init__(self, config: ProcessConfig = None):
        self.config = config or ProcessConfig()
        self.monitored_processes: Dict[int, Dict[str, Any]] = {}  # tool_id -> process_info
        self.metrics_history: Dict[int, List[ProcessMetrics]] = {}  # tool_id -> metrics list
        self.restart_counts: Dict[int, int] = {}  # tool_id -> restart_count
        self.last_restart_time: Dict[int, datetime] = {}  # tool_id -> last_restart_time
        self.monitoring_tasks: Dict[int, asyncio.Task] = {}  # tool_id -> monitoring_task
        self._shutdown_event = asyncio.Event()

        # 回调函数
        self.on_process_crash: Optional[Callable[[int, ProcessMetrics], None]] = None
        self.on_resource_limit_exceeded: Optional[Callable[[int, ProcessMetrics], None]] = None
        self.on_process_restart: Optional[Callable[[int], None]] = None

    def register_process(self, tool_id: int, process: Any, command: str = "") -> None:
        """注册进程进行监控"""
        try:
            pid = process.pid if hasattr(process, 'pid') else process

            # 验证进程是否存在
            if not psutil.pid_exists(pid):
                raise ProcessError(f"进程不存在: {pid}")

            self.monitored_processes[tool_id] = {
                'process': process,
                'pid': pid,
                'command': command,
                'state': ProcessState.STARTING,
                'start_time': datetime.utcnow(),
                'last_check_time': datetime.utcnow()
            }

            self.metrics_history[tool_id] = []
            self.restart_counts[tool_id] = 0

            # 启动监控任务
            if self.config.enable_resource_monitoring:
                task = asyncio.create_task(self._monitor_process(tool_id))
                self.monitoring_tasks[tool_id] = task

            logger.info(f"进程监控已注册: tool_id={tool_id}, pid={pid}")

        except Exception as e:
            logger.error(f"注册进程监控失败: {e}")
            raise ProcessError(f"注册进程监控失败: {e}")

    def unregister_process(self, tool_id: int) -> None:
        """取消注册进程监控"""
        try:
            # 停止监控任务
            if tool_id in self.monitoring_tasks:
                task = self.monitoring_tasks[tool_id]
                if not task.done():
                    task.cancel()
                del self.monitoring_tasks[tool_id]

            # 清理数据
            self.monitored_processes.pop(tool_id, None)
            self.metrics_history.pop(tool_id, None)
            self.restart_counts.pop(tool_id, None)
            self.last_restart_time.pop(tool_id, None)

            logger.info(f"进程监控已取消注册: tool_id={tool_id}")

        except Exception as e:
            logger.error(f"取消注册进程监控失败: {e}")

    def get_process_metrics(self, tool_id: int) -> Optional[ProcessMetrics]:
        """获取进程当前性能指标"""
        try:
            if tool_id not in self.monitored_processes:
                return None

            process_info = self.monitored_processes[tool_id]
            pid = process_info['pid']

            if not psutil.pid_exists(pid):
                return None

            proc = psutil.Process(pid)

            # 获取性能指标
            with proc.oneshot():
                cpu_percent = proc.cpu_percent()
                memory_info = proc.memory_info()
                memory_percent = proc.memory_percent()
                num_threads = proc.num_threads()
                create_time = proc.create_time()
                status = proc.status()

                # 获取文件描述符数量（Windows上可能不支持）
                try:
                    num_fds = proc.num_fds() if hasattr(proc, 'num_fds') else 0
                except (AttributeError, psutil.AccessDenied):
                    num_fds = 0

            metrics = ProcessMetrics(
                pid=pid,
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_mb=memory_info.rss / 1024 / 1024,  # 转换为MB
                num_threads=num_threads,
                num_fds=num_fds,
                create_time=create_time,
                status=status,
                timestamp=datetime.utcnow()
            )

            return metrics

        except psutil.NoSuchProcess:
            return None
        except Exception as e:
            logger.error(f"获取进程性能指标失败: {e}")
            return None

    def get_metrics_history(self, tool_id: int, limit: int = 100) -> List[ProcessMetrics]:
        """获取进程性能指标历史"""
        history = self.metrics_history.get(tool_id, [])
        return history[-limit:] if limit > 0 else history

    def is_process_healthy(self, tool_id: int) -> bool:
        """检查进程是否健康"""
        try:
            if tool_id not in self.monitored_processes:
                return False

            process_info = self.monitored_processes[tool_id]
            pid = process_info['pid']

            # 检查进程是否存在
            if not psutil.pid_exists(pid):
                return False

            # 获取当前指标
            metrics = self.get_process_metrics(tool_id)
            if not metrics:
                return False

            # 检查资源使用是否超限
            if metrics.memory_mb > self.config.max_memory_mb:
                logger.warning(f"进程内存使用超限: {metrics.memory_mb:.2f}MB > {self.config.max_memory_mb}MB")
                return False

            if metrics.cpu_percent > self.config.max_cpu_percent:
                logger.warning(f"进程CPU使用超限: {metrics.cpu_percent:.2f}% > {self.config.max_cpu_percent}%")
                return False

            return True

        except Exception as e:
            logger.error(f"检查进程健康状态失败: {e}")
            return False

    async def _monitor_process(self, tool_id: int) -> None:
        """监控单个进程"""
        try:
            while not self._shutdown_event.is_set():
                try:
                    if tool_id not in self.monitored_processes:
                        break

                    process_info = self.monitored_processes[tool_id]

                    # 获取性能指标
                    metrics = self.get_process_metrics(tool_id)
                    if not metrics:
                        # 进程不存在，标记为崩溃
                        process_info['state'] = ProcessState.CRASHED
                        logger.warning(f"进程已崩溃: tool_id={tool_id}")

                        if self.on_process_crash:
                            self.on_process_crash(tool_id, metrics)

                        # 尝试自动重启
                        if self.config.enable_auto_restart:
                            await self._attempt_restart(tool_id)

                        break

                    # 保存指标历史
                    history = self.metrics_history[tool_id]
                    history.append(metrics)

                    # 限制历史记录数量
                    if len(history) > 1000:
                        history[:] = history[-500:]  # 保留最近500条记录

                    # 检查资源使用
                    if (metrics.memory_mb > self.config.max_memory_mb or
                        metrics.cpu_percent > self.config.max_cpu_percent):

                        logger.warning(
                            f"进程资源使用超限: tool_id={tool_id}, "
                            f"内存={metrics.memory_mb:.2f}MB, CPU={metrics.cpu_percent:.2f}%"
                        )

                        if self.on_resource_limit_exceeded:
                            self.on_resource_limit_exceeded(tool_id, metrics)

                    # 更新进程状态
                    if process_info['state'] == ProcessState.STARTING:
                        # 检查启动是否超时
                        start_time = process_info['start_time']
                        if (datetime.utcnow() - start_time).total_seconds() > self.config.startup_timeout:
                            process_info['state'] = ProcessState.ERROR
                            logger.error(f"进程启动超时: tool_id={tool_id}")
                        else:
                            process_info['state'] = ProcessState.RUNNING

                    process_info['last_check_time'] = datetime.utcnow()

                    # 等待下次检查
                    await asyncio.sleep(self.config.health_check_interval)

                except Exception as e:
                    logger.error(f"监控进程失败: tool_id={tool_id}, 错误: {e}")
                    await asyncio.sleep(self.config.health_check_interval)

        except asyncio.CancelledError:
            logger.info(f"进程监控任务已取消: tool_id={tool_id}")
            raise  # 重新抛出CancelledError，让asyncio正确处理
        except Exception as e:
            logger.error(f"进程监控任务异常: tool_id={tool_id}, 错误: {e}")

    async def _attempt_restart(self, tool_id: int) -> bool:
        """尝试重启进程"""
        try:
            restart_count = self.restart_counts.get(tool_id, 0)

            # 检查重启次数限制
            if restart_count >= self.config.max_restart_attempts:
                logger.error(f"进程重启次数已达上限: tool_id={tool_id}, 次数={restart_count}")
                return False

            # 检查重启间隔
            last_restart = self.last_restart_time.get(tool_id)
            if last_restart:
                time_since_restart = (datetime.utcnow() - last_restart).total_seconds()
                if time_since_restart < self.config.restart_delay:
                    logger.warning(f"重启间隔太短，跳过重启: tool_id={tool_id}")
                    return False

            # 更新重启计数和时间
            self.restart_counts[tool_id] = restart_count + 1
            self.last_restart_time[tool_id] = datetime.utcnow()

            logger.info(f"尝试自动重启进程: tool_id={tool_id}, 第{restart_count + 1}次")

            if self.on_process_restart:
                self.on_process_restart(tool_id)

            return True

        except Exception as e:
            logger.error(f"自动重启进程失败: tool_id={tool_id}, 错误: {e}")
            return False

    def get_process_summary(self) -> Dict[str, Any]:
        """获取所有进程的摘要信息"""
        summary = {
            'total_processes': len(self.monitored_processes),
            'running_processes': 0,
            'crashed_processes': 0,
            'error_processes': 0,
            'total_memory_mb': 0.0,
            'total_cpu_percent': 0.0,
            'processes': []
        }

        for tool_id, process_info in self.monitored_processes.items():
            state = process_info['state']

            if state == ProcessState.RUNNING:
                summary['running_processes'] += 1
            elif state == ProcessState.CRASHED:
                summary['crashed_processes'] += 1
            elif state == ProcessState.ERROR:
                summary['error_processes'] += 1

            # 获取当前指标
            metrics = self.get_process_metrics(tool_id)
            if metrics:
                summary['total_memory_mb'] += metrics.memory_mb
                summary['total_cpu_percent'] += metrics.cpu_percent

                process_summary = {
                    'tool_id': tool_id,
                    'pid': metrics.pid,
                    'state': state.value,
                    'memory_mb': metrics.memory_mb,
                    'cpu_percent': metrics.cpu_percent,
                    'restart_count': self.restart_counts.get(tool_id, 0),
                    'uptime_seconds': (datetime.utcnow() - process_info['start_time']).total_seconds()
                }
                summary['processes'].append(process_summary)

        return summary

    async def shutdown(self) -> None:
        """关闭监控器"""
        try:
            logger.info("正在关闭进程监控器...")

            self._shutdown_event.set()

            # 取消所有监控任务
            for task in self.monitoring_tasks.values():
                if not task.done():
                    task.cancel()

            # 等待任务完成
            if self.monitoring_tasks:
                await asyncio.gather(*self.monitoring_tasks.values(), return_exceptions=True)

            # 清理数据
            self.monitored_processes.clear()
            self.metrics_history.clear()
            self.restart_counts.clear()
            self.last_restart_time.clear()
            self.monitoring_tasks.clear()

            logger.info("进程监控器已关闭")

        except Exception as e:
            logger.error(f"关闭进程监控器失败: {e}")

# 全局进程监控器实例
process_monitor = ProcessMonitor()
