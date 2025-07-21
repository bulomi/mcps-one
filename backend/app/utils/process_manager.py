"""进程管理器模块"""

import asyncio
import logging
import psutil
import signal
import subprocess
from typing import Dict, Optional, List, Any
from datetime import datetime
from pathlib import Path

from app.utils.exceptions import ProcessError

logger = logging.getLogger(__name__)

class ProcessInfo:
    """进程信息类"""

    def __init__(self, pid: int, command: str, started_at: datetime):
        self.pid = pid
        self.command = command
        self.started_at = started_at
        self.process: Optional[psutil.Process] = None

        try:
            self.process = psutil.Process(pid)
        except psutil.NoSuchProcess:
            pass

    @property
    def is_running(self) -> bool:
        """检查进程是否正在运行"""
        if not self.process:
            return False

        try:
            return self.process.is_running() and self.process.status() != psutil.STATUS_ZOMBIE
        except psutil.NoSuchProcess:
            return False

    @property
    def memory_info(self) -> Optional[Dict[str, Any]]:
        """获取内存信息"""
        if not self.process or not self.is_running:
            return None

        try:
            memory = self.process.memory_info()
            return {
                "rss": memory.rss,
                "vms": memory.vms,
                "percent": self.process.memory_percent()
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None

    @property
    def cpu_info(self) -> Optional[Dict[str, Any]]:
        """获取CPU信息"""
        if not self.process or not self.is_running:
            return None

        try:
            return {
                "percent": self.process.cpu_percent(),
                "times": self.process.cpu_times()._asdict()
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None

    def terminate(self, timeout: int = 10) -> bool:
        """终止进程"""
        if not self.process or not self.is_running:
            return True

        try:
            self.process.terminate()
            try:
                self.process.wait(timeout=timeout)
                return True
            except psutil.TimeoutExpired:
                logger.warning(f"进程 {self.pid} 未在 {timeout} 秒内终止，强制杀死")
                self.process.kill()
                self.process.wait(timeout=5)
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.error(f"终止进程 {self.pid} 失败: {e}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "pid": self.pid,
            "command": self.command,
            "started_at": self.started_at.isoformat(),
            "is_running": self.is_running,
            "memory_info": self.memory_info,
            "cpu_info": self.cpu_info
        }

class ProcessManager:
    """进程管理器"""

    def __init__(self):
        self.processes: Dict[str, ProcessInfo] = {}
        self._lock = asyncio.Lock()

    async def start_process(
        self,
        name: str,
        command: str,
        working_dir: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: int = 30
    ) -> ProcessInfo:
        """启动进程"""
        async with self._lock:
            # 检查是否已存在同名进程
            if name in self.processes and self.processes[name].is_running:
                raise ProcessError(f"进程 {name} 已在运行")

            try:
                # 启动进程
                process = subprocess.Popen(
                    command.split(),
                    cwd=working_dir,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE
                )

                # 等待进程启动
                await asyncio.sleep(0.1)

                if process.poll() is not None:
                    stdout, stderr = process.communicate()
                    raise ProcessError(f"进程启动失败: {stderr.decode()}")

                # 创建进程信息
                process_info = ProcessInfo(
                    pid=process.pid,
                    command=command,
                    started_at=datetime.utcnow()
                )

                self.processes[name] = process_info
                logger.info(f"进程启动成功: {name} (PID: {process.pid})")

                return process_info

            except Exception as e:
                logger.error(f"启动进程 {name} 失败: {e}")
                raise ProcessError(f"启动进程失败: {e}")

    async def stop_process(self, name: str, timeout: int = 10) -> bool:
        """停止进程"""
        async with self._lock:
            if name not in self.processes:
                logger.warning(f"进程 {name} 不存在")
                return True

            process_info = self.processes[name]

            if not process_info.is_running:
                logger.info(f"进程 {name} 已停止")
                del self.processes[name]
                return True

            try:
                success = process_info.terminate(timeout)
                if success:
                    logger.info(f"进程停止成功: {name} (PID: {process_info.pid})")
                    del self.processes[name]
                else:
                    logger.error(f"进程停止失败: {name} (PID: {process_info.pid})")

                return success

            except Exception as e:
                logger.error(f"停止进程 {name} 时出错: {e}")
                return False

    async def restart_process(
        self,
        name: str,
        command: str,
        working_dir: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: int = 30
    ) -> ProcessInfo:
        """重启进程"""
        await self.stop_process(name)
        await asyncio.sleep(1)  # 等待进程完全停止
        return await self.start_process(name, command, working_dir, env, timeout)

    def get_process(self, name: str) -> Optional[ProcessInfo]:
        """获取进程信息"""
        return self.processes.get(name)

    def list_processes(self) -> List[ProcessInfo]:
        """列出所有进程"""
        return list(self.processes.values())

    def is_process_running(self, name: str) -> bool:
        """检查进程是否正在运行"""
        process_info = self.get_process(name)
        return process_info.is_running if process_info else False

    async def cleanup_dead_processes(self):
        """清理已死亡的进程"""
        async with self._lock:
            dead_processes = []

            for name, process_info in self.processes.items():
                if not process_info.is_running:
                    dead_processes.append(name)

            for name in dead_processes:
                logger.info(f"清理已死亡进程: {name}")
                del self.processes[name]

    async def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            return {
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count()
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                },
                "processes": {
                    "total": len(self.processes),
                    "running": sum(1 for p in self.processes.values() if p.is_running)
                }
            }
        except Exception as e:
            logger.error(f"获取系统信息失败: {e}")
            return {}

    async def kill_process_by_pid(self, pid: int, timeout: int = 10) -> bool:
        """根据PID杀死进程"""
        try:
            process = psutil.Process(pid)
            process.terminate()

            try:
                process.wait(timeout=timeout)
                return True
            except psutil.TimeoutExpired:
                logger.warning(f"进程 {pid} 未在 {timeout} 秒内终止，强制杀死")
                process.kill()
                process.wait(timeout=5)
                return True

        except psutil.NoSuchProcess:
            logger.info(f"进程 {pid} 不存在")
            return True
        except Exception as e:
            logger.error(f"杀死进程 {pid} 失败: {e}")
            return False

    def get_process_tree(self, pid: int) -> List[Dict[str, Any]]:
        """获取进程树"""
        try:
            parent = psutil.Process(pid)
            tree = []

            def _collect_children(process, level=0):
                try:
                    tree.append({
                        "pid": process.pid,
                        "name": process.name(),
                        "cmdline": " ".join(process.cmdline()),
                        "level": level,
                        "status": process.status(),
                        "memory_percent": process.memory_percent(),
                        "cpu_percent": process.cpu_percent()
                    })

                    for child in process.children():
                        _collect_children(child, level + 1)

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            _collect_children(parent)
            return tree

        except psutil.NoSuchProcess:
            return []
        except Exception as e:
            logger.error(f"获取进程树失败: {e}")
            return []

# 全局进程管理器实例
process_manager = ProcessManager()
