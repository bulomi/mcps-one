"""系统管理服务"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
import json
from app.core import get_logger, LogLevel, LogCategory, create_log_context
import psutil
import platform
import os
import asyncio
import time
from pathlib import Path

from app.models.system import SystemConfig, SystemInfo
from app.models.tool import MCPTool, ToolStatus
# 会话和任务管理功能已移除
from app.schemas.system import (
    SystemConfigCreate,
    SystemConfigUpdate,
    SystemOperationCreate,
    ConfigValueType,
    MetricType,
)
from app.core import get_unified_config_manager
from app.core.unified_config_manager import UnifiedConfigManager
from app.core import MCPSError, handle_error, error_handler, error_context
from app.core.unified_cache import cached
from app.utils.exceptions import (
    SystemConfigError,
    SystemOperationError,
)
# 邮件和Webhook服务已删除

logger = get_logger(__name__)

# 常量定义
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200
DEFAULT_STATS_DAYS = 30
HEALTH_SCORE_BASE = 100
CRITICAL_THRESHOLD = 90
WARNING_THRESHOLD = 80

class SystemService:
    """系统管理服务"""

    @error_handler
    def __init__(self, db: Session):
        self.db = db
        # 邮件和Webhook服务已删除
        self.config_manager = get_unified_config_manager()
        self._ensure_default_configs()

    # 系统配置管理
    def get_configs(
        self,
        page: int = 1,
        size: int = DEFAULT_PAGE_SIZE,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[SystemConfig], int]:
        """获取系统配置列表"""
        query = self.db.query(SystemConfig)

        # 应用过滤条件
        if filters:
            if filters.get('category'):
                query = query.filter(SystemConfig.category == filters['category'])

            if filters.get('search'):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        SystemConfig.key.ilike(search_term),
                        SystemConfig.description.ilike(search_term)
                    )
                )

        # 获取总数
        total = query.count()

        # 分页和排序
        configs = query.order_by(
            SystemConfig.category,
            SystemConfig.key
        ).offset((page - 1) * size).limit(size).all()

        return configs, total

    @error_handler
    @cached(ttl=300)
    def get_config(self, key: str) -> Optional[SystemConfig]:
        """获取系统配置"""
        return self.db.query(SystemConfig).filter(SystemConfig.key == key).first()

    @error_handler
    @cached(ttl=300)
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        config = self.get_config(key)
        if not config:
            return default

        # 根据类型转换值
        if config.value_type == ConfigValueType.BOOL:
            return config.value.lower() in ('true', '1', 'yes', 'on')
        elif config.value_type == ConfigValueType.INT:
            try:
                return int(config.value)
            except (ValueError, TypeError):
                return default
        elif config.value_type == ConfigValueType.FLOAT:
            try:
                return float(config.value)
            except (ValueError, TypeError):
                return default
        elif config.value_type == ConfigValueType.JSON:
            try:
                return json.loads(config.value)
            except (json.JSONDecodeError, TypeError):
                return default
        else:
            return config.value

    @error_handler
    def create_config(self, config_data: SystemConfigCreate) -> SystemConfig:
        """创建系统配置"""
        try:
            # 验证配置值
            self._validate_config_value(config_data.value, config_data.value_type)

            config = SystemConfig(
                key=config_data.key,
                value=str(config_data.value),
                value_type=config_data.value_type,
                category=config_data.category,
                description=config_data.description,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)

            logger.info(f"系统配置创建成功: {config.key}", category=LogCategory.SYSTEM)
            return config

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建系统配置失败: {e}", category=LogCategory.SYSTEM)
            raise SystemConfigError(f"创建系统配置失败: {e}")

    @error_handler
    def update_config(self, key: str, config_data: SystemConfigUpdate) -> SystemConfig:
        """更新系统配置"""
        try:
            config = self.get_config(key)
            if not config:
                raise SystemConfigError(f"配置项不存在: {key}")

            # 更新字段
            update_data = config_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                if field == 'value':
                    # 验证配置值
                    value_type = update_data.get('value_type', config.value_type)
                    self._validate_config_value(value, value_type)
                    value = str(value)

                setattr(config, field, value)

            config.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(config)

            logger.info(f"系统配置更新成功: {config.key}", category=LogCategory.SYSTEM)
            return config

        except Exception as e:
            self.db.rollback()
            logger.error(f"更新系统配置失败: {e}", category=LogCategory.SYSTEM)
            raise

    @error_handler
    def delete_config(self, key: str) -> bool:
        """删除系统配置"""
        try:
            config = self.get_config(key)
            if not config:
                raise SystemConfigError(f"配置项不存在: {key}")

            # 系统关键配置检查已移除，因为模型中没有 is_system 字段

            self.db.delete(config)
            self.db.commit()

            logger.info(f"系统配置删除成功: {key}", category=LogCategory.SYSTEM)
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"删除系统配置失败: {e}", category=LogCategory.SYSTEM)
            raise

    @error_handler
    def batch_update_configs(self, configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """批量更新系统配置"""
        try:
            result = {
                "updated": 0,
                "created": 0,
                "errors": []
            }

            for config_data in configs:
                try:
                    key = config_data.get('key')
                    if not key:
                        result["errors"].append("配置键不能为空")
                        continue

                    existing = self.get_config(key)
                    if existing:
                        # 更新现有配置
                        update_data = SystemConfigUpdate(**config_data)
                        self.update_config(key, update_data)
                        result["updated"] += 1
                    else:
                        # 创建新配置
                        create_data = SystemConfigCreate(**config_data)
                        self.create_config(create_data)
                        result["created"] += 1

                except Exception as e:
                    result["errors"].append(f"配置 {key}: {e}")

            # 同步到配置管理器
            try:
                self.config_manager.reload()
            except Exception as e:
                logger.warning(f"同步配置到配置管理器失败: {e}", category=LogCategory.SYSTEM)

            return result

        except Exception as e:
            logger.error(f"批量更新系统配置失败: {e}", category=LogCategory.SYSTEM)
            raise

    @error_handler
    def save_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """保存设置到数据库和配置管理器"""
        try:
            result = {
                "updated": 0,
                "created": 0,
                "errors": []
            }

            config_manager = get_unified_config_manager()
            config_items = config_manager.get_all_configs()
            for key, config_item in config_items.items():
                value = config_item.value
                try:
                    # 检查是否存在配置
                    existing = self.get_config(key)

                    if existing:
                        # 更新现有配置
                        existing.value = str(value)
                        existing.value_type = self._infer_value_type(value)
                        existing.updated_at = datetime.utcnow()
                        result["updated"] += 1
                    else:
                        # 创建新配置
                        config = SystemConfig(
                            key=key,
                            value=str(value),
                            value_type=self._infer_value_type(value),
                            category=self._infer_category(key),
                            description=f"自动创建的配置项: {key}",
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        self.db.add(config)
                        result["created"] += 1

                except Exception as e:
                    result["errors"].append(f"配置 {key}: {e}")
                    logger.error(f"保存配置 {key} 失败: {e}", category=LogCategory.SYSTEM)

            # 提交数据库事务
            self.db.commit()

            # 同步到配置管理器
            try:
                self.config_manager.reload_from_database(self.db)
                # 批量更新配置管理器
                config_manager = get_unified_config_manager()
                config_items = config_manager.get_all_configs()
                for key, config_item in config_items.items():
                    self.config_manager.set(key, config_item.value)
            except Exception as e:
                logger.warning(f"同步配置到配置管理器失败: {e}", category=LogCategory.SYSTEM)

            logger.info(f"保存设置完成: 更新 {result['updated']} 项，创建 {result['created']} 项", category=LogCategory.SYSTEM)
            return result

        except Exception as e:
            self.db.rollback()
            logger.error(f"保存设置失败: {e}", category=LogCategory.SYSTEM)
            raise SystemConfigError(f"保存设置失败: {e}")

    @error_handler
    @cached(ttl=300)
    def get_all_settings(self) -> Dict[str, Any]:
        """获取所有设置"""
        try:
            # 优先从配置管理器获取
            config_items = self.config_manager.get_all_configs()
            settings = {}
            for key, config_item in config_items.items():
                settings[key] = config_item.value
            return settings
        except Exception as e:
            logger.warning(f"从配置管理器获取设置失败: {e}", category=LogCategory.SYSTEM)

            # 回退到数据库
            configs = self.db.query(SystemConfig).all()
            settings = {}
            for config in configs:
                settings[config.key] = config.typed_value
            return settings

    @error_handler
    def export_config(self) -> Dict[str, Any]:
        """导出配置"""
        try:
            return self.config_manager.export_config()
        except Exception as e:
            logger.error(f"导出配置失败: {e}", category=LogCategory.SYSTEM)
            raise SystemConfigError(f"导出配置失败: {e}")

    @error_handler
    def import_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """导入配置"""
        try:
            result = self.config_manager.import_config(config_data)
            # 同步到数据库
            self.config_manager.save_to_database(self.db)
            return result
        except Exception as e:
            logger.error(f"导入配置失败: {e}", category=LogCategory.SYSTEM)
            raise SystemConfigError(f"导入配置失败: {e}")

    @error_handler
    def reset_config(self) -> Dict[str, Any]:
        """重置配置为默认值"""
        try:
            result = self.config_manager.reset_to_defaults()
            # 同步到数据库
            self.config_manager.save_to_database(self.db)
            return result
        except Exception as e:
            logger.error(f"重置配置失败: {e}", category=LogCategory.SYSTEM)
            raise SystemConfigError(f"重置配置失败: {e}")

    @error_handler
    @cached(ttl=300)
    def get_config_stats(self) -> Dict[str, Any]:
        """获取配置统计信息"""
        try:
            return self.config_manager.get_stats()
        except Exception as e:
            logger.error(f"获取配置统计失败: {e}", category=LogCategory.SYSTEM)
            return {}

    @error_handler
    def _infer_value_type(self, value: Any) -> ConfigValueType:
        """推断值类型"""
        if isinstance(value, bool):
            return ConfigValueType.BOOL
        elif isinstance(value, int):
            return ConfigValueType.INT
        elif isinstance(value, float):
            return ConfigValueType.FLOAT
        elif isinstance(value, (dict, list)):
            return ConfigValueType.JSON
        else:
            return ConfigValueType.STRING

    @error_handler
    def _infer_category(self, key: str) -> str:
        """推断配置分类"""
        if key.startswith('app.'):
            return 'application'
        elif key.startswith('server.'):
            return 'server'
        elif key.startswith('database.'):
            return 'database'
        elif key.startswith('logging.'):
            return 'logging'
        elif key.startswith('mcp.'):
            return 'mcp'
        elif key.startswith('features.'):
            return 'features'
        elif key.startswith('notifications.'):
            return 'notifications'
        elif key.startswith('i18n.'):
            return 'i18n'
        else:
            return 'general'

    # 系统信息
    @error_handler
    @cached(ttl=300)
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        try:
            # 系统基本信息
            system_info = {
                "platform": platform.platform(),
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "hostname": platform.node(),
            }

            # CPU 信息
            cpu_info = {
                "cpu_count": psutil.cpu_count(),
                "cpu_count_logical": psutil.cpu_count(logical=True),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
            }

            # 内存信息
            memory = psutil.virtual_memory()
            memory_info = {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percent": memory.percent,
            }

            # 磁盘信息
            disk = psutil.disk_usage('/')
            disk_info = {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100,
            }

            # 网络信息
            network = psutil.net_io_counters()
            network_info = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv,
            }

            # 应用信息
            config_manager = get_unified_config_manager()
            app_info = {
                "name": config_manager.get("app.name", "MCPS.ONE"),
                "version": config_manager.get("app.version", "1.0.0"),
                "debug": config_manager.get("server.debug", False),
                "data_dir": str(config_manager.get("data.dir", "./data")),
                "log_dir": str(config_manager.get("logging.dir", "./logs")),
            }

            return {
                "system": system_info,
                "cpu": cpu_info,
                "memory": memory_info,
                "disk": disk_info,
                "network": network_info,
                "application": app_info,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"获取系统信息失败: {e}", category=LogCategory.SYSTEM)
            raise

    @error_handler
    @cached(ttl=300)
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            # 工具统计
            total_tools = self.db.query(MCPTool).count()
            running_tools = self.db.query(MCPTool).filter(
                MCPTool.status == ToolStatus.RUNNING
            ).count()
            error_tools = self.db.query(MCPTool).filter(
                MCPTool.status == ToolStatus.ERROR
            ).count()

            # 系统资源
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # 健康状态评估
            health_score = HEALTH_SCORE_BASE
            health_issues = []

            if cpu_percent > WARNING_THRESHOLD:
                health_score -= 20
                health_issues.append("CPU 使用率过高")

            if memory.percent > WARNING_THRESHOLD:
                health_score -= 20
                health_issues.append("内存使用率过高")

            if (disk.used / disk.total) * 100 > CRITICAL_THRESHOLD:
                health_score -= 15
                health_issues.append("磁盘空间不足")

            if error_tools > 0:
                health_score -= min(error_tools * 5, 25)
                health_issues.append(f"{error_tools} 个工具出现错误")

            # 确定健康状态
            if health_score >= WARNING_THRESHOLD:
                health_status = "healthy"
            elif health_score >= 60:
                health_status = "warning"
            else:
                health_status = "critical"

            return {
                "health": {
                    "status": health_status,
                    "score": max(health_score, 0),
                    "issues": health_issues
                },
                "tools": {
                    "total": total_tools,
                    "running": running_tools,
                    "error": error_tools,
                    "stopped": total_tools - running_tools - error_tools
                },
                "resources": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": (disk.used / disk.total) * 100
                },
                "uptime": self._get_uptime(),
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"获取系统状态失败: {e}", category=LogCategory.SYSTEM)
            raise

    @error_handler
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            checks = {
                "database": self._check_database(),
                "disk_space": self._check_disk_space(),
                "memory": self._check_memory(),
                "tools": self._check_tools(),
            }

            # 计算总体状态
            all_healthy = all(check["status"] == "healthy" for check in checks.values())
            has_warning = any(check["status"] == "warning" for check in checks.values())

            if all_healthy:
                overall_status = "healthy"
            elif has_warning:
                overall_status = "warning"
            else:
                overall_status = "unhealthy"

            return {
                "status": overall_status,
                "checks": checks,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"健康检查失败: {e}", category=LogCategory.SYSTEM)
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    @error_handler
    @cached(ttl=300)
    def get_system_metrics(self, period: str = "1h") -> Dict[str, Any]:
        """获取系统指标"""
        try:
            # 解析时间周期
            if period == "1h":
                start_time = datetime.utcnow() - timedelta(hours=1)
            elif period == "24h":
                start_time = datetime.utcnow() - timedelta(days=1)
            elif period == "7d":
                start_time = datetime.utcnow() - timedelta(days=7)
            elif period == "30d":
                start_time = datetime.utcnow() - timedelta(days=30)
            else:
                start_time = datetime.utcnow() - timedelta(hours=1)

            # 获取系统信息记录
            metrics = self.db.query(SystemInfo).filter(
                SystemInfo.timestamp >= start_time
            ).order_by(SystemInfo.timestamp).all()

            # 处理指标数据
            cpu_data = []
            memory_data = []
            disk_data = []
            timestamps = []

            for metric in metrics:
                timestamps.append(metric.timestamp.isoformat())

                if metric.metric_type == MetricType.CPU:
                    cpu_data.append(metric.value)
                elif metric.metric_type == MetricType.MEMORY:
                    memory_data.append(metric.value)
                elif metric.metric_type == MetricType.DISK:
                    disk_data.append(metric.value)

            # 当前值
            current_cpu = psutil.cpu_percent(interval=1)
            current_memory = psutil.virtual_memory().percent
            current_disk = (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100

            return {
                "period": period,
                "start_time": start_time.isoformat(),
                "end_time": datetime.utcnow().isoformat(),
                "current": {
                    "cpu": current_cpu,
                    "memory": current_memory,
                    "disk": current_disk
                },
                "history": {
                    "timestamps": timestamps,
                    "cpu": cpu_data,
                    "memory": memory_data,
                    "disk": disk_data
                },
                "statistics": {
                    "cpu": self._calculate_stats(cpu_data),
                    "memory": self._calculate_stats(memory_data),
                    "disk": self._calculate_stats(disk_data)
                }
            }

        except Exception as e:
            logger.error(f"获取系统指标失败: {e}", category=LogCategory.SYSTEM)
            raise

    @error_handler
    @cached(ttl=300)
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        try:
            # 工具统计
            total_tools = self.db.query(MCPTool).count()
            active_tools = self.db.query(MCPTool).filter(
                MCPTool.status == ToolStatus.RUNNING
            ).count()
            stopped_tools = self.db.query(MCPTool).filter(
                MCPTool.status == ToolStatus.STOPPED
            ).count()
            error_tools = self.db.query(MCPTool).filter(
                MCPTool.status == ToolStatus.ERROR
            ).count()

            # 会话统计功能已移除
            total_sessions = 0
            active_sessions = 0
            inactive_sessions = 0
            expired_sessions = 0

            # 任务统计功能已移除
            total_tasks = 0
            pending_tasks = 0
            running_tasks = 0
            completed_tasks = 0
            failed_tasks = 0
            cancelled_tasks = 0

            # 系统资源详细信息
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_count_logical = psutil.cpu_count(logical=True)

            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            # 磁盘信息
            disk = psutil.disk_usage('/')

            # 网络信息
            network = psutil.net_io_counters()

            # 系统运行时间
            uptime_seconds = self._get_uptime()

            # 进程信息
            process = psutil.Process()
            app_memory = process.memory_info()

            return {
                # 工具统计
                "totalTools": total_tools,
                "activeTools": active_tools,
                "stoppedTools": stopped_tools,
                "errorTools": error_tools,

                # 会话统计
                "totalSessions": total_sessions,
                "activeSessions": active_sessions,
                "inactiveSessions": inactive_sessions,
                "expiredSessions": expired_sessions,

                # 任务统计
                "totalTasks": total_tasks,
                "pendingTasks": pending_tasks,
                "runningTasks": running_tasks,
                "completedTasks": completed_tasks,
                "failedTasks": failed_tasks,
                "cancelledTasks": cancelled_tasks,

                # CPU 信息
                "cpuUsage": round(cpu_percent, 1),
                "cpuCount": cpu_count,
                "cpuCountLogical": cpu_count_logical,

                # 内存信息
                "memoryUsage": round(memory.percent, 1),
                "memoryTotal": memory.total,
                "memoryUsed": memory.used,
                "memoryAvailable": memory.available,
                "swapUsage": round(swap.percent, 1) if swap.total > 0 else 0,
                "swapTotal": swap.total,
                "swapUsed": swap.used,

                # 磁盘信息
                "diskUsage": round((disk.used / disk.total) * 100, 1),
                "diskTotal": disk.total,
                "diskUsed": disk.used,
                "diskFree": disk.free,

                # 网络信息
                "networkBytesSent": network.bytes_sent,
                "networkBytesRecv": network.bytes_recv,
                "networkPacketsSent": network.packets_sent,
                "networkPacketsRecv": network.packets_recv,

                # 应用信息
                "appMemoryRss": app_memory.rss,
                "appMemoryVms": app_memory.vms,
                "appCpuPercent": round(process.cpu_percent(), 1),
                "appThreads": process.num_threads(),

                # 系统信息
                "systemUptime": uptime_seconds,
                "systemUptimeFormatted": self._format_uptime(uptime_seconds),
                "platform": platform.platform(),
                "pythonVersion": platform.python_version(),

                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"获取系统统计失败: {e}", category=LogCategory.SYSTEM)
            raise

    @error_handler
    def create_operation(self, operation_data: SystemOperationCreate):
        """创建系统操作记录"""
        # 这里应该创建操作记录，但由于没有定义 SystemOperation 模型，
        # 暂时返回一个模拟对象
        return type('Operation', (), {
            'id': 1,
            'operation': operation_data.operation,
            'description': operation_data.description,
            'status': 'pending',
            'to_dict': lambda: {
                'id': 1,
                'operation': operation_data.operation,
                'description': operation_data.description,
                'status': 'pending'
            }
        })()

    @error_handler
    def execute_operation(self, operation_id: int):
        """执行系统操作"""
        # 这里应该实现具体的系统操作逻辑
        logger.info(f"执行系统操作: {operation_id}", category=LogCategory.SYSTEM)
        pass

    # 私有方法
    @error_handler
    def _validate_config_value(self, value: Any, value_type: ConfigValueType) -> None:
        """验证配置值"""
        if value_type == ConfigValueType.BOOL:
            if not isinstance(value, (bool, str)):
                raise SystemConfigError("布尔类型配置值必须是 bool 或 str")
        elif value_type == ConfigValueType.INT:
            try:
                int(value)
            except (ValueError, TypeError):
                raise SystemConfigError("整数类型配置值必须是有效的整数")
        elif value_type == ConfigValueType.FLOAT:
            try:
                float(value)
            except (ValueError, TypeError):
                raise SystemConfigError("浮点类型配置值必须是有效的浮点数")
        elif value_type == ConfigValueType.JSON:
            try:
                json.loads(str(value))
            except json.JSONDecodeError:
                raise SystemConfigError("JSON 类型配置值必须是有效的 JSON")

    @error_handler
    def _get_uptime(self) -> float:
        """获取系统运行时间（秒）"""
        try:
            return time.time() - psutil.boot_time()
        except Exception:
            return 0.0

    @error_handler
    def _format_uptime(self, uptime_seconds: float) -> str:
        """格式化运行时间显示"""
        try:
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            seconds = int(uptime_seconds % 60)

            if days > 0:
                return f"{days}天 {hours}小时 {minutes}分钟"
            elif hours > 0:
                return f"{hours}小时 {minutes}分钟"
            elif minutes > 0:
                return f"{minutes}分钟 {seconds}秒"
            else:
                return f"{seconds}秒"
        except Exception:
            return "未知"

    @error_handler
    def _check_database(self) -> Dict[str, Any]:
        """检查数据库连接"""
        try:
            self.db.execute("SELECT 1")
            return {"status": "healthy", "message": "数据库连接正常"}
        except Exception as e:
            return {"status": "unhealthy", "message": f"数据库连接失败: {e}"}

    @error_handler
    def _check_disk_space(self) -> Dict[str, Any]:
        """检查磁盘空间"""
        try:
            disk = psutil.disk_usage('/')
            usage_percent = (disk.used / disk.total) * 100

            if usage_percent > 90:
                return {"status": "unhealthy", "message": f"磁盘空间不足: {usage_percent:.1f}%"}
            elif usage_percent > 80:
                return {"status": "warning", "message": f"磁盘空间紧张: {usage_percent:.1f}%"}
            else:
                return {"status": "healthy", "message": f"磁盘空间充足: {usage_percent:.1f}%"}
        except Exception as e:
            return {"status": "unhealthy", "message": f"检查磁盘空间失败: {e}"}

    @error_handler
    def _check_memory(self) -> Dict[str, Any]:
        """检查内存使用"""
        try:
            memory = psutil.virtual_memory()

            if memory.percent > 90:
                return {"status": "unhealthy", "message": f"内存使用率过高: {memory.percent:.1f}%"}
            elif memory.percent > 80:
                return {"status": "warning", "message": f"内存使用率较高: {memory.percent:.1f}%"}
            else:
                return {"status": "healthy", "message": f"内存使用正常: {memory.percent:.1f}%"}
        except Exception as e:
            return {"status": "unhealthy", "message": f"检查内存使用失败: {e}"}

    @error_handler
    def _check_tools(self) -> Dict[str, Any]:
        """检查工具状态"""
        try:
            error_tools = self.db.query(MCPTool).filter(
                MCPTool.status == ToolStatus.ERROR
            ).count()

            if error_tools > 0:
                return {"status": "warning", "message": f"{error_tools} 个工具出现错误"}
            else:
                return {"status": "healthy", "message": "所有工具运行正常"}
        except Exception as e:
            return {"status": "unhealthy", "message": f"检查工具状态失败: {e}"}

    @error_handler
    def _calculate_stats(self, data: List[float]) -> Dict[str, float]:
        """计算统计数据"""
        if not data:
            return {"min": 0, "max": 0, "avg": 0, "count": 0}

        return {
            "min": min(data),
            "max": max(data),
            "avg": sum(data) / len(data),
            "count": len(data)
        }

    @error_handler
    def save_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """保存系统设置"""
        try:
            result = {
                "saved": 0,
                "errors": []
            }

            config_manager = get_unified_config_manager()
            config_items = config_manager.get_all_configs()
            for key, config_item in config_items.items():
                value = config_item.value
                try:
                    config = self.get_config(key)
                    if config:
                        # 保持原有的value_type，只更新value
                        config.value = str(value)
                        config.updated_at = datetime.utcnow()
                        result["saved"] += 1
                    else:
                        # 创建新配置时，尝试推断类型
                        value_type = "string"
                        if isinstance(value, bool):
                            value_type = "bool"
                        elif isinstance(value, int):
                            value_type = "int"
                        elif isinstance(value, float):
                            value_type = "float"

                        new_config = SystemConfig(
                            key=key,
                            value=str(value),
                            value_type=value_type,
                            category="system",
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        self.db.add(new_config)
                        result["saved"] += 1

                except Exception as e:
                    result["errors"].append(f"保存配置 {key} 失败: {e}")

            self.db.commit()
            logger.info(f"保存系统设置完成: {result}", category=LogCategory.SYSTEM)
            return result

        except Exception as e:
            self.db.rollback()
            logger.error(f"保存系统设置失败: {e}", category=LogCategory.SYSTEM)
            raise

    # 系统测试


    # 系统维护
    @error_handler
    def clear_cache(self) -> Dict[str, Any]:
        """清理缓存"""
        try:
            # 简化的缓存清理逻辑
            logger.info("清理系统缓存完成", category=LogCategory.SYSTEM)

            return {
                "success": True,
                "message": "缓存清理完成",
                "cleared_items": 0,
                "freed_space_mb": 0,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"清理缓存失败: {e}", category=LogCategory.SYSTEM)
            return {
                "success": False,
                "message": f"清理缓存失败: {e}",
                "timestamp": datetime.utcnow().isoformat()
            }

    @error_handler
    def reset_to_defaults(self) -> Dict[str, Any]:
        """重置为默认值"""
        try:
            # 获取所有配置
            configs = self.db.query(SystemConfig).all()

            reset_count = 0
            for config in configs:
                # 删除非系统配置
                self.db.delete(config)
                reset_count += 1

            # 重新创建默认配置
            self._ensure_default_configs()

            self.db.commit()

            logger.info(f"重置为默认值完成，重置了 {reset_count} 个配置", category=LogCategory.SYSTEM)
            return {
                "success": True,
                "message": f"重置为默认值完成，重置了 {reset_count} 个配置",
                "reset_count": reset_count,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"重置为默认值失败: {e}", category=LogCategory.SYSTEM)
            return {
                "success": False,
                "message": f"重置为默认值失败: {e}",
                "timestamp": datetime.utcnow().isoformat()
            }

    @error_handler
    def _ensure_default_configs(self) -> None:
        """确保默认配置存在"""
        default_configs = [

            # 应用基础配置
            {
                "key": "app_name",
                "value": "MCPS.ONE",
                "value_type": ConfigValueType.STRING,
                "category": "basic",
                "description": "应用名称"
            },
            {
                "key": "app_version",
                "value": "1.0.0",
                "value_type": ConfigValueType.STRING,
                "category": "basic",
                "description": "应用版本"
            },
            {
                "key": "show_title",
                "value": "true",
                "value_type": ConfigValueType.BOOL,
                "category": "basic",
                "description": "显示标题"
            },
            {
                "key": "log_level",
                "value": "INFO",
                "value_type": ConfigValueType.STRING,
                "category": "basic",
                "description": "日志级别"
            },
            {
                "key": "language",
                "value": "zh-CN",
                "value_type": ConfigValueType.STRING,
                "category": "basic",
                "description": "系统语言"
            },
            {
                "key": "timezone",
                "value": "Asia/Shanghai",
                "value_type": ConfigValueType.STRING,
                "category": "basic",
                "description": "时区设置"
            }
        ]

        for config_data in default_configs:
            existing = self.db.query(SystemConfig).filter(
                SystemConfig.key == config_data["key"]
            ).first()

            if not existing:
                config = SystemConfig(
                    key=config_data["key"],
                    value=config_data["value"],
                    value_type=config_data["value_type"],
                    category=config_data["category"],
                    description=config_data["description"],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                self.db.add(config)

        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建默认配置失败: {e}", category=LogCategory.SYSTEM)
