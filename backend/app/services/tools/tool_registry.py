"""工具注册中心模块

负责MCP工具的动态发现, 注册和管理.
主要功能:
- 从配置文件和数据库加载工具
- 动态工具发现和注册
- 工具健康状态检查
- 工具元数据管理
"""

import asyncio
import json
import logging
import os
import subprocess
import shlex
import time
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from app.core import get_unified_config_manager
from app.core.unified_logging import get_logger
from app.models.tool import MCPTool, ToolStatus, ToolType
from app.utils.exceptions import (
    ToolNotFoundError,
    ConfigurationError,
    MCPServiceError
)
from app.schemas.mcp_proxy import ToolDiscoveryResult

logger = get_logger(__name__)

class ToolHealthStatus(Enum):
    """工具健康状态"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    STARTING = "starting"
    STOPPING = "stopping"

@dataclass
class ToolConfig:
    """工具配置信息"""
    name: str
    command: str
    description: str
    enabled: bool = True
    auto_start: bool = False
    instances: int = 1
    health_check: Dict[str, Any] = None
    tags: List[str] = None

    def __post_init__(self):
        if self.health_check is None:
            self.health_check = {
                "enabled": True,
                "interval": 30,
                "timeout": 5
            }
        if self.tags is None:
            self.tags = []

@dataclass
class ToolInstance:
    """工具实例信息"""
    tool_name: str
    instance_id: str
    process_id: Optional[int] = None
    status: ToolHealthStatus = ToolHealthStatus.UNKNOWN
    last_health_check: Optional[datetime] = None
    start_time: Optional[datetime] = None
    error_count: int = 0
    last_error: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class ToolRegistry:
    """工具注册中心

    负责管理所有MCP工具的配置, 状态和生命周期.
    """

    def __init__(self, auto_discovery_enabled: bool = True, discovery_interval: int = 300):
        """初始化工具注册中心

        Args:
            auto_discovery_enabled: 是否启用自动工具发现
            discovery_interval: 自动发现间隔(秒)
        """
        self._tools: Dict[str, ToolConfig] = {}  # tool_name -> ToolConfig
        self._instances: Dict[str, ToolInstance] = {}  # instance_id -> ToolInstance
        self._tool_instances: Dict[str, List[str]] = {}  # tool_name -> [instance_ids]

        config_manager = get_unified_config_manager()
        self._config_file_path = Path(config_manager.get("data.dir", "./data")) / "mcp_tools_config.json"
        self._last_config_check: Optional[datetime] = None
        self._config_check_interval = 30  # 秒

        self._health_check_task: Optional[asyncio.Task] = None
        self._config_watch_task: Optional[asyncio.Task] = None
        self._discovery_task: Optional[asyncio.Task] = None
        self._running = False

        # 自动发现配置
        self.auto_discovery_enabled = auto_discovery_enabled
        self.discovery_interval = discovery_interval
        self._last_discovery_time: Optional[datetime] = None

        # 事件回调
        self.on_tool_registered = None
        self.on_tool_unregistered = None
        self.on_tool_health_changed = None

    async def initialize(self) -> None:
        """初始化工具注册中心"""
        try:
            logger.info("初始化工具注册中心...")

            # 加载工具配置
            await self._load_tools_config()

            # 从数据库同步工具状态
            await self._sync_from_database()

            logger.info(f"工具注册中心初始化完成，已注册 {len(self._tools)} 个工具")

        except Exception as e:
            logger.error(f"工具注册中心初始化失败: {e}")
            raise MCPServiceError(f"初始化失败: {e}")

    async def start(self) -> None:
        """启动工具注册中心"""
        if self._running:
            logger.warning("工具注册中心已在运行中")
            return

        try:
            logger.info("启动工具注册中心...")

            # 启动健康检查任务
            self._health_check_task = asyncio.create_task(self._health_check_loop())

            # 启动配置文件监控任务
            self._config_watch_task = asyncio.create_task(self._config_watch_loop())

            # 启动自动发现任务
            if self.auto_discovery_enabled:
                self._discovery_task = asyncio.create_task(self._auto_discovery_loop())
                logger.info(f"自动工具发现已启用，间隔: {self.discovery_interval}秒")

            self._running = True

            logger.info("工具注册中心启动完成")

        except Exception as e:
            logger.error(f"工具注册中心启动失败: {e}")
            await self._cleanup()
            raise MCPServiceError(f"启动失败: {e}")

    async def stop(self) -> None:
        """停止工具注册中心"""
        if not self._running:
            logger.warning("工具注册中心未在运行")
            return

        try:
            logger.info("停止工具注册中心...")

            self._running = False

            # 停止后台任务
            if self._health_check_task and not self._health_check_task.done():
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass

            if self._config_watch_task and not self._config_watch_task.done():
                self._config_watch_task.cancel()
                try:
                    await self._config_watch_task
                except asyncio.CancelledError:
                    pass

            if self._discovery_task and not self._discovery_task.done():
                self._discovery_task.cancel()
                try:
                    await self._discovery_task
                except asyncio.CancelledError:
                    pass

            await self._cleanup()

            logger.info("工具注册中心停止完成")

        except Exception as e:
            logger.error(f"工具注册中心停止失败: {e}")
            raise MCPServiceError(f"停止失败: {e}")

    async def register_tool(self, tool_config: ToolConfig) -> None:
        """注册工具

        Args:
            tool_config: 工具配置
        """
        try:
            logger.info(f"注册工具: {tool_config.name}")

            # 验证工具配置
            self._validate_tool_config(tool_config)

            # 注册工具
            self._tools[tool_config.name] = tool_config

            # 初始化工具实例列表
            if tool_config.name not in self._tool_instances:
                self._tool_instances[tool_config.name] = []

            # 触发回调
            if self.on_tool_registered:
                await self.on_tool_registered(tool_config)

            logger.info(f"工具注册完成: {tool_config.name}")

        except Exception as e:
            logger.error(f"工具注册失败: {tool_config.name}, error: {e}")
            raise

    async def unregister_tool(self, tool_name: str) -> None:
        """注销工具

        Args:
            tool_name: 工具名称
        """
        try:
            logger.info(f"注销工具: {tool_name}")

            if tool_name not in self._tools:
                raise ToolNotFoundError(f"工具不存在: {tool_name}")

            tool_config = self._tools[tool_name]

            # 清理工具实例
            instance_ids = self._tool_instances.get(tool_name, [])
            for instance_id in instance_ids.copy():
                await self.remove_instance(instance_id)

            # 移除工具
            del self._tools[tool_name]
            self._tool_instances.pop(tool_name, None)

            # 触发回调
            if self.on_tool_unregistered:
                await self.on_tool_unregistered(tool_config)

            logger.info(f"工具注销完成: {tool_name}")

        except Exception as e:
            logger.error(f"工具注销失败: {tool_name}, error: {e}")
            raise

    async def add_instance(self, tool_name: str, instance_id: str, process_id: Optional[int] = None) -> None:
        """添加工具实例

        Args:
            tool_name: 工具名称
            instance_id: 实例ID
            process_id: 进程ID
        """
        try:
            if tool_name not in self._tools:
                raise ToolNotFoundError(f"工具不存在: {tool_name}")

            if instance_id in self._instances:
                logger.warning(f"实例已存在: {instance_id}")
                return

            # 创建实例
            instance = ToolInstance(
                tool_name=tool_name,
                instance_id=instance_id,
                process_id=process_id,
                status=ToolHealthStatus.STARTING,
                start_time=datetime.now()
            )

            self._instances[instance_id] = instance

            # 添加到工具实例列表
            if tool_name not in self._tool_instances:
                self._tool_instances[tool_name] = []
            self._tool_instances[tool_name].append(instance_id)

            logger.info(f"工具实例添加完成: {tool_name}/{instance_id}")

        except Exception as e:
            logger.error(f"添加工具实例失败: {tool_name}/{instance_id}, error: {e}")
            raise

    async def remove_instance(self, instance_id: str) -> None:
        """移除工具实例

        Args:
            instance_id: 实例ID
        """
        try:
            if instance_id not in self._instances:
                logger.warning(f"实例不存在: {instance_id}")
                return

            instance = self._instances[instance_id]
            tool_name = instance.tool_name

            # 从工具实例列表中移除
            if tool_name in self._tool_instances:
                try:
                    self._tool_instances[tool_name].remove(instance_id)
                except ValueError:
                    pass

            # 移除实例
            del self._instances[instance_id]

            logger.info(f"工具实例移除完成: {tool_name}/{instance_id}")

        except Exception as e:
            logger.error(f"移除工具实例失败: {instance_id}, error: {e}")
            raise

    async def get_active_tools(self) -> List[str]:
        """获取活跃工具列表

        Returns:
            活跃工具名称列表
        """
        active_tools = []

        for tool_name, tool_config in self._tools.items():
            if not tool_config.enabled:
                continue

            # 检查是否有健康的实例
            instance_ids = self._tool_instances.get(tool_name, [])
            has_healthy_instance = False

            for instance_id in instance_ids:
                instance = self._instances.get(instance_id)
                if instance and instance.status == ToolHealthStatus.HEALTHY:
                    has_healthy_instance = True
                    break

            if has_healthy_instance:
                active_tools.append(tool_name)

        return active_tools

    async def get_tool_config(self, tool_name: str) -> Optional[ToolConfig]:
        """获取工具配置

        Args:
            tool_name: 工具名称

        Returns:
            工具配置, 如果不存在返回None
        """
        return self._tools.get(tool_name)

    async def get_tool_instances(self, tool_name: str) -> List[ToolInstance]:
        """获取工具实例列表
        
        Args:
            tool_name: 工具名称

        Returns:
            工具实例列表
        """
        instance_ids = self._tool_instances.get(tool_name, [])
        instances = []

        for instance_id in instance_ids:
            instance = self._instances.get(instance_id)
            if instance:
                instances.append(instance)

        return instances

    async def get_healthy_instance(self, tool_name: str) -> Optional[ToolInstance]:
        """获取健康的工具实例
        
        Args:
            tool_name: 工具名称

        Returns:
            健康的工具实例，如果没有返回None
        """
        instances = await self.get_tool_instances(tool_name)

        for instance in instances:
            if instance.status == ToolHealthStatus.HEALTHY:
                return instance

        return None

    async def update_instance_status(self, instance_id: str, status: ToolHealthStatus, error: Optional[str] = None) -> None:
        """更新实例状态
        
        Args:
            instance_id: 实例ID
            status: 新状态
            error: 错误信息
        """
        if instance_id not in self._instances:
            logger.warning(f"实例不存在: {instance_id}")
            return

        instance = self._instances[instance_id]
        old_status = instance.status

        instance.status = status
        instance.last_health_check = datetime.now()

        if error:
            instance.error_count += 1
            instance.last_error = error

        # 触发状态变化回调
        if old_status != status and self.on_tool_health_changed:
            await self.on_tool_health_changed(instance, old_status, status)

        logger.debug(f"实例状态更新: {instance_id}, {old_status} -> {status}")

    async def reload_config(self) -> None:
        """重新加载配置"""
        try:
            logger.info("重新加载工具配置...")

            await self._load_tools_config()

            logger.info("工具配置重新加载完成")

        except Exception as e:
            logger.error(f"重新加载工具配置失败: {e}")
            raise

    async def _load_tools_config(self) -> None:
        """从配置文件加载工具配置"""
        try:
            if not self._config_file_path.exists():
                logger.warning(f"配置文件不存在: {self._config_file_path}")
                return

            with open(self._config_file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            tools_config = config_data.get('tools', {})

            # 清空现有配置
            self._tools.clear()

            # 加载工具配置
            for tool_name, tool_data in tools_config.items():
                try:
                    tool_config = ToolConfig(
                        name=tool_name,
                        command=tool_data.get('command', ''),
                        description=tool_data.get('description', ''),
                        enabled=tool_data.get('enabled', True),
                        auto_start=tool_data.get('auto_start', False),
                        instances=tool_data.get('instances', 1),
                        health_check=tool_data.get('health_check', {}),
                        tags=tool_data.get('tags', [])
                    )

                    self._tools[tool_name] = tool_config

                except Exception as e:
                    logger.error(f"加载工具配置失败: {tool_name}, error: {e}")

            self._last_config_check = datetime.now()

            logger.info(f"配置文件加载完成，共 {len(self._tools)} 个工具")

        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            raise ConfigurationError(f"配置文件加载失败: {e}")

    async def _sync_from_database(self) -> None:
        """从数据库同步工具状态

        从数据库加载工具配置并同步到内存中
        """
        try:
            from ..core.database import get_db
            from ..services.tool_service import ToolService

            db = next(get_db())
            try:
                tool_service = ToolService(db)

                # 获取数据库中的所有工具
                db_tools = tool_service.get_all_tools()

                logger.info(f"从数据库加载 {len(db_tools)} 个工具配置")

                for db_tool in db_tools:
                    # 创建工具配置对象
                    tool_config = ToolConfig(
                        name=db_tool.name,
                        command=db_tool.command,
                        description=db_tool.description or f"数据库工具: {db_tool.name}",
                        enabled=db_tool.enabled,
                        auto_start=db_tool.auto_start,
                        tags=db_tool.tags or []
                    )

                    # 添加到内存中
                    self._tools[db_tool.name] = tool_config

                    # 如果工具启用且需要自动启动，则启动工具实例
                    if db_tool.enabled and db_tool.auto_start:
                        try:
                            await self._start_tool_instance(db_tool.name)
                            logger.info(f"自动启动工具: {db_tool.name}")
                        except Exception as e:
                            logger.error(f"自动启动工具失败 {db_tool.name}: {e}")

                logger.info(f"数据库同步完成，共加载 {len(self._tools)} 个工具")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"从数据库同步工具状态失败: {e}")

    async def _start_tool_instance(self, tool_name: str) -> None:
        """启动工具实例
        
        Args:
            tool_name: 工具名称
        """
        tool_config = self._tools.get(tool_name)
        if not tool_config:
            raise ValueError(f"工具不存在: {tool_name}")

        # 检查是否已有实例
        instance_ids = self._tool_instances.get(tool_name, [])
        if instance_ids:
            logger.warning(f"工具实例已存在: {tool_name}")
            return

        try:
            # 生成实例ID
            instance_id = f"{tool_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # 启动工具进程
            process = await self._start_tool_process(tool_config.command)

            # 添加实例
            await self.add_instance(tool_name, instance_id, process.pid)

            # 更新实例状态
            await self.update_instance_status(instance_id, ToolHealthStatus.HEALTHY)

            logger.info(f"工具实例启动成功: {tool_name} (PID: {process.pid})")

        except Exception as e:
            logger.error(f"启动工具实例失败 {tool_name}: {e}")
            raise

    async def _start_tool_process(self, command: str) -> asyncio.subprocess.Process:
        """启动工具进程"

        Args:
            command: 工具命令

        Returns:
            进程对象
        """
        # 解析命令
        cmd_parts = shlex.split(command)

        # 启动进程
        process = await asyncio.create_subprocess_exec(
            *cmd_parts,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        return process

    async def sync_tool_to_database(self, tool_name: str) -> None:
        """将单个工具同步到数据库"

        Args:
            tool_name: 工具名称
        """
        tool_config = self._tools.get(tool_name)
        if not tool_config:
            raise ValueError(f"工具不存在: {tool_name}")

        try:
            from ..core.database import get_db
            from ..services.tool_service import ToolService
            from ..schemas.tool import ToolCreate, ToolUpdate

            db = next(get_db())
            try:
                tool_service = ToolService(db)

                # 检查工具是否已存在
                existing_tool = tool_service.get_tool_by_name(tool_name)

                if existing_tool:
                    # 更新现有工具
                    tool_update = ToolUpdate(
                        description=tool_config.description,
                        command=tool_config.command,
                        enabled=tool_config.enabled,
                        auto_start=tool_config.auto_start,
                        tags=tool_config.tags
                    )

                    tool_service.update_tool(existing_tool.id, tool_update)
                    logger.info(f"工具已更新到数据库: {tool_name}")
                else:
                    # 创建新工具
                    tool_create = ToolCreate(
                        name=tool_config.name,
                        display_name=tool_config.name.replace('_', ' ').title(),
                        description=tool_config.description,
                        command=tool_config.command,
                        type=ToolType.CUSTOM,
                        category='manual',
                        enabled=tool_config.enabled,
                        auto_start=tool_config.auto_start,
                        tags=tool_config.tags
                    )

                    tool_service.create_tool(tool_create)
                    logger.info(f"工具已创建到数据库: {tool_name}")

                db.commit()

            finally:
                db.close()

        except Exception as e:
            logger.error(f"同步工具到数据库失败 {tool_name}: {e}")
            raise

    async def remove_tool_from_database(self, tool_name: str) -> None:
        """从数据库中删除工具"

        Args:
            tool_name: 工具名称
        """
        try:
            from ..core.database import get_db
            from ..services.tool_service import ToolService

            db = next(get_db())
            try:
                tool_service = ToolService(db)

                # 查找工具
                db_tool = tool_service.get_tool_by_name(tool_name)
                if db_tool:
                    tool_service.delete_tool(db_tool.id)
                    db.commit()
                    logger.info(f"工具已从数据库删除: {tool_name}")
                else:
                    logger.warning(f"数据库中未找到工具: {tool_name}")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"从数据库删除工具失败 {tool_name}: {e}")
            raise

    async def _health_check_loop(self) -> None:
        """健康检查循环"""
        while self._running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(30)  # 每30秒检查一次

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"健康检查失败: {e}")
                await asyncio.sleep(10)  # 出错时短暂等待

    async def _config_watch_loop(self) -> None:
        """配置文件监控循环"""
        last_modified = {}
        config_manager = get_unified_config_manager()
        data_dir = config_manager.get("data.dir", "./data")
        config_files = [
            Path(data_dir) / "mcp_tools_config.json",
            Path(data_dir) / "tools" / "config.json",
            Path.cwd() / "tools" / "config.json"
        ]

        # 初始化文件修改时间
        for config_file in config_files:
            if config_file.exists():
                last_modified[str(config_file)] = config_file.stat().st_mtime

        logger.info(f"开始监控 {len(config_files)} 个配置文件")

        while self._running:
            try:
                config_changed = False
                changed_files = []

                for config_file in config_files:
                    if not config_file.exists():
                        continue

                    file_path = str(config_file)
                    current_modified = config_file.stat().st_mtime

                    if file_path not in last_modified:
                        # 新文件
                        last_modified[file_path] = current_modified
                        config_changed = True
                        changed_files.append(file_path)
                        logger.info(f"发现新配置文件: {file_path}")
                    elif current_modified > last_modified[file_path]:
                        # 文件已修改
                        last_modified[file_path] = current_modified
                        config_changed = True
                        changed_files.append(file_path)
                        logger.info(f"配置文件已修改: {file_path}")

                if config_changed:
                    logger.info(f"检测到配置文件变化: {changed_files}")
                    try:
                        await self.reload_config()
                        logger.info("配置重新加载成功")

                        # 触发工具发现
                        if hasattr(self, 'auto_discovery_enabled') and getattr(self, 'auto_discovery_enabled', False):
                            logger.info("触发自动工具发现")
                            try:
                                discovery_result = await self.discover_tools()
                                if discovery_result.new_tools or discovery_result.updated_tools:
                                    logger.info(f"自动发现: 新增 {len(discovery_result.new_tools)} 个工具，更新 {len(discovery_result.updated_tools)} 个工具")
                            except Exception as e:
                                logger.error(f"自动工具发现失败: {e}")

                    except Exception as e:
                        logger.error(f"重新加载配置失败: {e}")

                await asyncio.sleep(3)  # 每3秒检查一次

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"配置文件监控失败: {e}")
                await asyncio.sleep(10)  # 出错时等待更长时间

    async def _perform_health_checks(self) -> None:
        """执行健康检查"""
        if not self._instances:
            logger.debug("无工具实例需要健康检查")
            return

        logger.debug(f"开始健康检查，共 {len(self._instances)} 个实例")

        for instance_id, instance in list(self._instances.items()):
            try:
                tool_name = instance.tool_name
                tool_config = self._tools.get(tool_name)

                if not tool_config:
                    logger.warning(f"工具配置不存在，移除实例: {instance_id}")
                    await self.remove_instance(instance_id)
                    continue

                # 检查是否启用健康检查
                if not tool_config.health_check.get('enabled', True):
                    continue

                # 检查实例是否需要健康检查
                check_interval = tool_config.health_check.get('interval', 30)
                if instance.last_health_check:
                    time_since_check = (datetime.now() - instance.last_health_check).total_seconds()
                    if time_since_check < check_interval:
                        continue

                # 检查进程是否还在运行
                if instance.process_id:
                    is_running = await self._check_process_running(instance.process_id)

                    if is_running:
                        # 进程存在，执行更详细的健康检查
                        health_status = await self._check_tool_health(instance)
                        await self.update_instance_status(instance_id, health_status)

                        if health_status == ToolHealthStatus.HEALTHY:
                            logger.debug(f"工具实例健康: {instance_id}")
                        else:
                            logger.warning(f"工具实例不健康: {instance_id}, 状态: {health_status}")
                    else:
                        # 进程不存在
                        await self.update_instance_status(instance_id, ToolHealthStatus.UNHEALTHY, "进程不存在")
                        logger.warning(f"工具实例进程已停止: {instance_id} (PID: {instance.process_id})")

                        # 如果配置了自动重启，尝试重启
                        if tool_config.auto_start:
                            await self._attempt_restart_instance(instance_id, tool_name)
                else:
                    # 没有PID，标记为不健康
                    await self.update_instance_status(instance_id, ToolHealthStatus.UNHEALTHY, "无进程ID")
                    logger.warning(f"工具实例无PID: {instance_id}")

            except Exception as e:
                logger.error(f"健康检查异常 {instance_id}: {e}")
                await self.update_instance_status(instance_id, ToolHealthStatus.UNKNOWN, str(e))

    async def _check_process_running(self, pid: int) -> bool:
        """检查进程是否在运行

        Args:
            pid: 进程ID

        Returns:
            进程是否在运行
        """
        try:
            # 优先使用psutil检查进程
            try:
                import psutil
                process = psutil.Process(pid)
                return process.is_running()
            except ImportError:
                # 如果没有psutil，使用系统命令
                pass
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return False

            # 在Windows上使用tasklist检查进程
            result = await asyncio.create_subprocess_exec(
                'tasklist', '/FI', f'PID eq {pid}',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=5)

            if result.returncode == 0 and stdout:
                output = stdout.decode('utf-8', errors='ignore')
                return str(pid) in output

            return False

        except asyncio.TimeoutError:
            logger.warning(f"检查进程超时: PID {pid}")
            return False
        except Exception as e:
            logger.error(f"检查进程失败 PID {pid}: {e}")
            return False

    async def _check_tool_health(self, instance: ToolInstance) -> ToolHealthStatus:
        """检查工具健康状态

        Args:
            instance: 工具实例

        Returns:
            健康状态
        """
        try:
            # 基本的健康检查：进程存在且响应
            if not instance.process_id:
                return ToolHealthStatus.UNHEALTHY

            # 检查进程运行时间
            if instance.start_time:
                uptime = (datetime.now() - instance.start_time).total_seconds()
                if uptime < 5:  # 进程刚启动，给一些时间
                    return ToolHealthStatus.STARTING

            # 检查错误计数
            if instance.error_count > 5:  # 错误次数过多
                return ToolHealthStatus.UNHEALTHY

            # TODO: 可以添加更复杂的健康检查逻辑
            # 例如：发送ping请求、检查端口连接等

            return ToolHealthStatus.HEALTHY

        except Exception as e:
            logger.error(f"工具健康检查失败 {instance.tool_name}: {e}")
            return ToolHealthStatus.UNKNOWN

    async def _attempt_restart_instance(self, instance_id: str, tool_name: str) -> None:
        """尝试重启工具实例

        Args:
            instance_id: 实例ID
            tool_name: 工具名称
        """
        try:
            instance = self._instances.get(instance_id)
            if not instance:
                return

            # 检查重启次数限制
            max_restarts = 3
            current_restarts = getattr(instance, 'restart_count', 0)

            if current_restarts >= max_restarts:
                logger.error(f"工具实例重启次数超限: {instance_id} ({current_restarts}/{max_restarts})")
                await self.update_instance_status(instance_id, ToolHealthStatus.UNHEALTHY, "重启次数超限")
                return

            logger.info(f"尝试重启工具实例: {instance_id} (第 {current_restarts + 1} 次)")

            # 移除旧实例
            await self.remove_instance(instance_id)

            # 启动新实例
            await self._start_tool_instance(tool_name)

            # 更新重启计数
            new_instances = self._tool_instances.get(tool_name, [])
            if new_instances:
                new_instance_id = new_instances[-1]
                new_instance = self._instances.get(new_instance_id)
                if new_instance:
                    new_instance.metadata['restart_count'] = current_restarts + 1

            logger.info(f"工具实例重启成功: {tool_name}")

        except Exception as e:
            logger.error(f"重启工具实例失败 {instance_id}: {e}")

    def _validate_tool_config(self, tool_config: ToolConfig) -> None:
        """验证工具配置"""
        if not tool_config.name:
            raise ConfigurationError("工具名称不能为空")

        if not tool_config.command:
            raise ConfigurationError(f"工具命令不能为空: {tool_config.name}")

        if tool_config.instances < 1:
            raise ConfigurationError(f"工具实例数必须大于0: {tool_config.name}")

    async def _cleanup(self) -> None:
        """清理资源"""
        try:
            # 清理实例
            self._instances.clear()
            self._tool_instances.clear()

        except Exception as e:
            logger.error(f"清理资源失败: {e}")

    def get_status(self) -> Dict[str, Any]:
        """获取注册中心状态"""
        total_tools = len(self._tools)
        enabled_tools = sum(1 for config in self._tools.values() if config.enabled)
        total_instances = len(self._instances)
        healthy_instances = sum(1 for instance in self._instances.values() if instance.status == ToolHealthStatus.HEALTHY)

        return {
            "running": self._running,
            "total_tools": total_tools,
            "enabled_tools": enabled_tools,
            "total_instances": total_instances,
            "healthy_instances": healthy_instances,
            "last_config_check": self._last_config_check.isoformat() if self._last_config_check else None
        }

    async def get_active_tools(self) -> List[str]:
        """获取所有活跃工具名称列表

        Returns:
            活跃工具名称列表
        """
        active_tools = []
        for tool_name, tool_config in self._tools.items():
            if tool_config.enabled:
                active_tools.append(tool_name)

        return active_tools

    async def get_tool_config(self, tool_name: str) -> Optional[ToolConfig]:
        """获取工具配置"

        Args:
            tool_name: 工具名称

        Returns:
            工具配置对象，如果工具不存在则返回None
        """
        return self._tools.get(tool_name)

    def get_all_tools(self) -> Dict[str, ToolConfig]:
        """获取所有工具配置

        Returns:
            所有工具配置字典
        """
        return self._tools.copy()

    async def discover_tools(self, scan_paths: Optional[List[str]] = None, recursive: bool = True) -> ToolDiscoveryResult:
        """发现新的MCP工具

        Args:
            scan_paths: 扫描路径列表，如果为None则使用默认路径
            recursive: 是否递归扫描子目录

        Returns:
            工具发现结果
        """
        logger.info("开始工具发现...")

        discovered_tools = []
        new_tools = []
        updated_tools = []
        errors = []

        # 默认扫描路径
        if scan_paths is None:
            config_manager = get_unified_config_manager()
            data_dir = config_manager.get("data.dir", "./data")
            scan_paths = [
                str(Path(data_dir) / "tools"),
                str(Path.cwd() / "tools"),
                str(Path.home() / ".mcp" / "tools"),
                "/usr/local/bin",
                "/opt/mcp/tools"
            ]

        try:
            for scan_path in scan_paths:
                if not os.path.exists(scan_path):
                    logger.debug(f"扫描路径不存在: {scan_path}")
                    continue

                logger.info(f"扫描路径: {scan_path}")

                try:
                    # 扫描目录中的工具
                    found_tools = await self._scan_directory_for_tools(scan_path, recursive)

                    for tool_info in found_tools:
                        tool_name = tool_info['name']
                        discovered_tools.append(tool_name)

                        # 检查是否为新工具
                        if tool_name not in self._tools:
                            new_tools.append(tool_name)

                            # 自动注册新工具
                            try:
                                await self._auto_register_tool(tool_info)
                                logger.info(f"自动注册新工具: {tool_name}")
                            except Exception as e:
                                error_msg = f"注册工具失败 {tool_name}: {e}"
                                logger.error(error_msg)
                                errors.append(error_msg)
                        else:
                            # 检查是否需要更新
                            if await self._should_update_tool(tool_name, tool_info):
                                updated_tools.append(tool_name)
                                try:
                                    await self._update_tool_config(tool_name, tool_info)
                                    logger.info(f"更新工具配置: {tool_name}")
                                except Exception as e:
                                    error_msg = f"更新工具失败 {tool_name}: {e}"
                                    logger.error(error_msg)
                                    errors.append(error_msg)

                except Exception as e:
                    error_msg = f"扫描路径失败 {scan_path}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            # 同步到数据库
            if new_tools or updated_tools:
                await self._sync_discovered_tools_to_database(new_tools, updated_tools)

            result = ToolDiscoveryResult(
                discovered_tools=discovered_tools,
                new_tools=new_tools,
                updated_tools=updated_tools,
                errors=errors
            )

            logger.info(f"工具发现完成: 发现 {len(discovered_tools)} 个工具，新增 {len(new_tools)} 个，更新 {len(updated_tools)} 个")

            return result

        except Exception as e:
            logger.error(f"工具发现失败: {e}")
            raise MCPServiceError(f"工具发现失败: {e}")

    async def _scan_directory_for_tools(self, directory: str, recursive: bool = True) -> List[Dict[str, Any]]:
        """扫描目录查找MCP工具"

        Args:
            directory: 扫描目录
            recursive: 是否递归扫描

        Returns:
            发现的工具信息列表
        """
        tools = []
        directory_path = Path(directory)

        if not directory_path.exists() or not directory_path.is_dir():
            return tools

        # 扫描模式
        pattern = "**/*" if recursive else "*"

        # 查找可执行文件和脚本
        for file_path in directory_path.glob(pattern):
            if not file_path.is_file():
                continue

            # 检查文件是否可能是MCP工具
            if await self._is_potential_mcp_tool(file_path):
                tool_info = await self._extract_tool_info(file_path)
                if tool_info:
                    tools.append(tool_info)

        return tools

    async def _is_potential_mcp_tool(self, file_path: Path) -> bool:
        """检查文件是否可能是MCP工具"

        Args:
            file_path: 文件路径

        Returns:
            是否可能是MCP工具
        """
        # 检查文件扩展名
        mcp_extensions = {'.py', '.js', '.ts', '.sh', '.exe', '.jar'}
        if file_path.suffix.lower() not in mcp_extensions and not file_path.suffix == '':
            return False

        # 检查文件名模式
        mcp_patterns = ['mcp', 'server', 'tool', 'agent']
        file_name_lower = file_path.name.lower()

        for pattern in mcp_patterns:
            if pattern in file_name_lower:
                return True

        # 检查是否可执行
        if os.access(file_path, os.X_OK):
            return True

        # 检查文件内容（简单检查）
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1024)  # 只读前1024字符
                mcp_keywords = ['mcp', 'Model Context Protocol', 'stdio', 'tools/list']
                for keyword in mcp_keywords:
                    if keyword.lower() in content.lower():
                        return True
        except Exception:
            pass

        return False

    async def _extract_tool_info(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """从文件中提取工具信息"

        Args:
            file_path: 文件路径

        Returns:
            工具信息字典
        """
        try:
            tool_name = file_path.stem
            command = str(file_path)

            # 尝试获取工具描述
            description = await self._get_tool_description(file_path)

            # 检测工具类型
            tool_type = self._detect_tool_type(file_path)

            # 生成显示名称
            display_name = tool_name.replace('_', ' ').replace('-', ' ').title()

            return {
                'name': tool_name,
                'display_name': display_name,
                'command': command,
                'description': description or f"自动发现的MCP工具: {tool_name}",
                'type': tool_type,
                'category': 'discovered',
                'enabled': False,  # 新发现的工具默认禁用
                'auto_start': False,
                'file_path': str(file_path),
                'discovered_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"提取工具信息失败 {file_path}: {e}")
            return None

    async def _get_tool_description(self, file_path: Path) -> Optional[str]:
        """获取工具描述"

        Args:
            file_path: 文件路径

        Returns:
            工具描述
        """
        try:
            # 尝试执行工具获取描述
            if file_path.suffix == '.py':
                # Python脚本
                cmd = ['python', str(file_path), '--help']
            elif file_path.suffix in ['.js', '.ts']:
                # Node.js脚本
                cmd = ['node', str(file_path), '--help']
            elif file_path.suffix == '.sh':
                # Shell脚本
                cmd = ['bash', str(file_path), '--help']
            else:
                # 可执行文件
                cmd = [str(file_path), '--help']

            # 执行命令获取帮助信息
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                timeout=5
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0 and stdout:
                help_text = stdout.decode('utf-8', errors='ignore')
                # 提取第一行作为描述
                lines = help_text.strip().split('\n')
                if lines:
                    return lines[0][:200]  # 限制长度

        except Exception:
            pass

        # 尝试从文件内容中提取描述
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(500)  # 只读前500字符

                # 查找注释中的描述
                lines = content.split('\n')
                for line in lines[:10]:  # 只检查前10行
                    line = line.strip()
                    if line.startswith('#') or line.startswith('//'):
                        desc = line.lstrip('#/').strip()
                        if len(desc) > 10:  # 过滤太短的注释
                            return desc[:200]
                    elif line.startswith('"""') or line.startswith("'''"):
                        # Python docstring
                        desc = line.strip('"\'\'').strip()
                        if len(desc) > 10:
                            return desc[:200]
        except Exception:
            pass

        return None

    def _detect_tool_type(self, file_path: Path) -> str:
        """检测工具类型"

        Args:
            file_path: 文件路径

        Returns:
            工具类型
        """
        # 根据文件路径和名称判断类型
        path_str = str(file_path).lower()

        if 'builtin' in path_str or 'system' in path_str:
            return ToolType.BUILTIN.value
        elif 'external' in path_str or 'third-party' in path_str:
            return ToolType.EXTERNAL.value
        else:
            return ToolType.CUSTOM.value

    async def _should_update_tool(self, tool_name: str, new_info: Dict[str, Any]) -> bool:
        """检查是否需要更新工具配置"

        Args:
            tool_name: 工具名称
            new_info: 新的工具信息

        Returns:
            是否需要更新
        """
        current_config = self._tools.get(tool_name)
        if not current_config:
            return False

        # 检查命令是否变化
        if current_config.command != new_info.get('command'):
            return True

        # 检查描述是否变化
        if current_config.description != new_info.get('description'):
            return True

        return False

    async def _auto_register_tool(self, tool_info: Dict[str, Any]) -> None:
        """自动注册工具"

        Args:
            tool_info: 工具信息
        """
        tool_config = ToolConfig(
            name=tool_info['name'],
            command=tool_info['command'],
            description=tool_info['description'],
            enabled=tool_info.get('enabled', False),
            auto_start=tool_info.get('auto_start', False),
            tags=tool_info.get('tags', ['discovered'])
        )

        await self.register_tool(tool_config)

    async def _update_tool_config(self, tool_name: str, tool_info: Dict[str, Any]) -> None:
        """更新工具配置"

        Args:
            tool_name: 工具名称
            tool_info: 新的工具信息
        """
        current_config = self._tools.get(tool_name)
        if not current_config:
            return

        # 更新配置
        current_config.command = tool_info.get('command', current_config.command)
        current_config.description = tool_info.get('description', current_config.description)

        # 添加发现标签
        if 'discovered' not in current_config.tags:
            current_config.tags.append('discovered')

    async def _sync_discovered_tools_to_database(self, new_tools: List[str], updated_tools: List[str]) -> None:
        """将发现的工具同步到数据库"

        Args:
            new_tools: 新工具列表
            updated_tools: 更新的工具列表
        """
        try:
            from ..core.database import get_db
            from ..services.tool_service import ToolService

            db = next(get_db())
            try:
                tool_service = ToolService(db)

                # 同步新工具
                for tool_name in new_tools:
                    tool_config = self._tools.get(tool_name)
                    if tool_config:
                        # 创建数据库记录
                        from ..schemas.tool import ToolCreate

                        tool_create = ToolCreate(
                            name=tool_config.name,
                            display_name=tool_config.name.replace('_', ' ').title(),
                            description=tool_config.description,
                            command=tool_config.command,
                            type=ToolType.CUSTOM,
                            category='discovered',
                            enabled=tool_config.enabled,
                            auto_start=tool_config.auto_start,
                            tags=tool_config.tags
                        )

                        tool_service.create_tool(tool_create)
                        logger.info(f"工具已同步到数据库: {tool_name}")

                # 同步更新的工具
                for tool_name in updated_tools:
                    tool_config = self._tools.get(tool_name)
                    if tool_config:
                        # 查找并更新数据库记录
                        db_tool = tool_service.get_tool_by_name(tool_name)
                        if db_tool:
                            from ..schemas.tool import ToolUpdate

                            tool_update = ToolUpdate(
                                description=tool_config.description,
                                command=tool_config.command,
                                tags=tool_config.tags
                            )

                            tool_service.update_tool(db_tool.id, tool_update)
                            logger.info(f"工具配置已更新到数据库: {tool_name}")

                db.commit()

            finally:
                db.close()

        except Exception as e:
            logger.error(f"同步工具到数据库失败: {e}")

    async def _auto_discovery_loop(self) -> None:
        """自动工具发现循环"""
        while self._running:
            try:
                # 检查是否到了发现时间
                if self._last_discovery_time:
                    time_since_last = (datetime.now() - self._last_discovery_time).total_seconds()
                    if time_since_last < self.discovery_interval:
                        await asyncio.sleep(min(30, self.discovery_interval - time_since_last))
                        continue

                logger.info("开始自动工具发现...")

                # 执行工具发现
                discovery_result = await self.discover_tools()

                if discovery_result.new_tools or discovery_result.updated_tools:
                    logger.info(f"自动发现完成: 新增 {len(discovery_result.new_tools)} 个工具，更新 {len(discovery_result.updated_tools)} 个工具")
                else:
                    logger.debug("自动发现完成: 无新工具")

                self._last_discovery_time = datetime.now()

                # 等待下次发现
                await asyncio.sleep(self.discovery_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"自动工具发现失败: {e}")
                await asyncio.sleep(60)  # 出错时等待1分钟
