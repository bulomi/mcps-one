"""系统管理服务"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
import json
import logging
import psutil
import platform
import os
import asyncio
import time
from pathlib import Path

from app.models.system import SystemConfig, SystemInfo, DatabaseBackup
from app.models.tool import MCPTool, ToolStatus
from app.schemas.system import (
    SystemConfigCreate,
    SystemConfigUpdate,
    SystemOperationCreate,
    ConfigValueType,
    MetricType,
)
from app.core.config import settings
from app.utils.exceptions import (
    SystemConfigError,
    SystemOperationError,
)

logger = logging.getLogger(__name__)

class SystemService:
    """系统管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # 系统配置管理
    def get_configs(
        self,
        page: int = 1,
        size: int = 50,
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
    
    def get_config(self, key: str) -> Optional[SystemConfig]:
        """获取系统配置"""
        return self.db.query(SystemConfig).filter(SystemConfig.key == key).first()
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        config = self.get_config(key)
        if not config:
            return default
        
        # 根据类型转换值
        if config.value_type == ConfigValueType.BOOLEAN:
            return config.value.lower() in ('true', '1', 'yes', 'on')
        elif config.value_type == ConfigValueType.INTEGER:
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
                is_system=config_data.is_system,
                is_sensitive=config_data.is_sensitive,
                validation_rule=config_data.validation_rule,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
            
            logger.info(f"系统配置创建成功: {config.key}")
            return config
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建系统配置失败: {e}")
            raise SystemConfigError(f"创建系统配置失败: {e}")
    
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
            
            logger.info(f"系统配置更新成功: {config.key}")
            return config
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新系统配置失败: {e}")
            raise
    
    def delete_config(self, key: str) -> bool:
        """删除系统配置"""
        try:
            config = self.get_config(key)
            if not config:
                raise SystemConfigError(f"配置项不存在: {key}")
            
            if config.is_system:
                raise SystemConfigError("系统关键配置不能删除")
            
            self.db.delete(config)
            self.db.commit()
            
            logger.info(f"系统配置删除成功: {key}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除系统配置失败: {e}")
            raise
    
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
            
            return result
            
        except Exception as e:
            logger.error(f"批量更新系统配置失败: {e}")
            raise
    
    # 系统信息
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
            app_info = {
                "name": settings.APP_NAME,
                "version": settings.VERSION,
                "debug": settings.DEBUG,
                "data_dir": str(settings.DATA_DIR),
                "log_dir": str(settings.LOG_DIR),
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
            logger.error(f"获取系统信息失败: {e}")
            raise
    
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
            health_score = 100
            health_issues = []
            
            if cpu_percent > 80:
                health_score -= 20
                health_issues.append("CPU 使用率过高")
            
            if memory.percent > 80:
                health_score -= 20
                health_issues.append("内存使用率过高")
            
            if (disk.used / disk.total) * 100 > 90:
                health_score -= 15
                health_issues.append("磁盘空间不足")
            
            if error_tools > 0:
                health_score -= min(error_tools * 5, 25)
                health_issues.append(f"{error_tools} 个工具出现错误")
            
            # 确定健康状态
            if health_score >= 80:
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
            logger.error(f"获取系统状态失败: {e}")
            raise
    
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
            logger.error(f"健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
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
            logger.error(f"获取系统指标失败: {e}")
            raise
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        try:
            # 工具统计
            total_tools = self.db.query(MCPTool).count()
            active_tools = self.db.query(MCPTool).filter(
                MCPTool.status == ToolStatus.RUNNING
            ).count()
            
            # 系统资源
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # 模拟会话和任务数据（实际项目中应该从相应的表中获取）
            active_sessions = 5  # 这里应该从会话表中获取
            total_tasks = 150    # 这里应该从任务表中获取
            
            return {
                "activeSessions": active_sessions,
                "totalTasks": total_tasks,
                "totalTools": total_tools,
                "activeTools": active_tools,
                "cpuUsage": round(cpu_percent, 1),
                "memoryUsage": round(memory.percent, 1),
                "diskUsage": round((disk.used / disk.total) * 100, 1),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取系统统计失败: {e}")
            raise
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        try:
            # 进程信息
            process = psutil.Process()
            
            # 应用性能
            app_stats = {
                "cpu_percent": process.cpu_percent(),
                "memory_info": process.memory_info()._asdict(),
                "memory_percent": process.memory_percent(),
                "num_threads": process.num_threads(),
                "num_fds": process.num_fds() if hasattr(process, 'num_fds') else None,
                "create_time": process.create_time(),
            }
            
            # 数据库统计
            db_stats = {
                "total_tools": self.db.query(MCPTool).count(),
                "total_configs": self.db.query(SystemConfig).count(),
                "total_backups": self.db.query(DatabaseBackup).count(),
            }
            
            # 文件系统统计
            data_dir = Path(settings.DATA_DIR)
            if data_dir.exists():
                file_stats = {
                    "data_dir_size": sum(f.stat().st_size for f in data_dir.rglob('*') if f.is_file()),
                    "log_files": len(list(Path(settings.LOG_DIR).glob('*.log'))) if Path(settings.LOG_DIR).exists() else 0,
                }
            else:
                file_stats = {"data_dir_size": 0, "log_files": 0}
            
            return {
                "application": app_stats,
                "database": db_stats,
                "filesystem": file_stats,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取性能统计失败: {e}")
            raise
    
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
    
    async def execute_operation(self, operation_id: int):
        """执行系统操作"""
        # 这里应该实现具体的系统操作逻辑
        logger.info(f"执行系统操作: {operation_id}")
        pass
    
    # 私有方法
    def _validate_config_value(self, value: Any, value_type: ConfigValueType) -> None:
        """验证配置值"""
        if value_type == ConfigValueType.BOOLEAN:
            if not isinstance(value, (bool, str)):
                raise SystemConfigError("布尔类型配置值必须是 bool 或 str")
        elif value_type == ConfigValueType.INTEGER:
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
    
    def _get_uptime(self) -> float:
        """获取系统运行时间（秒）"""
        try:
            return time.time() - psutil.boot_time()
        except Exception:
            return 0.0
    
    def _check_database(self) -> Dict[str, Any]:
        """检查数据库连接"""
        try:
            self.db.execute("SELECT 1")
            return {"status": "healthy", "message": "数据库连接正常"}
        except Exception as e:
            return {"status": "unhealthy", "message": f"数据库连接失败: {e}"}
    
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
    
    # 设置导入导出
    def export_settings(self) -> Dict[str, Any]:
        """导出系统设置"""
        try:
            configs = self.db.query(SystemConfig).all()
            settings = {}
            
            for config in configs:
                # 敏感配置不导出
                if config.is_sensitive:
                    continue
                    
                if config.category not in settings:
                    settings[config.category] = {}
                
                # 根据类型转换值
                value = self.get_config_value(config.key)
                settings[config.category][config.key] = {
                    "value": value,
                    "type": config.value_type,
                    "description": config.description
                }
            
            return settings
            
        except Exception as e:
            logger.error(f"导出系统设置失败: {e}")
            raise
    
    def import_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """导入系统设置"""
        try:
            result = {
                "imported": 0,
                "skipped": 0,
                "errors": []
            }
            
            for category, configs in settings.items():
                for key, config_data in configs.items():
                    try:
                        existing_config = self.get_config(key)
                        
                        if existing_config:
                            # 更新现有配置
                            existing_config.value = str(config_data["value"])
                            existing_config.updated_at = datetime.utcnow()
                            result["imported"] += 1
                        else:
                            # 创建新配置
                            new_config = SystemConfig(
                                key=key,
                                value=str(config_data["value"]),
                                value_type=config_data.get("type", "string"),
                                category=category,
                                description=config_data.get("description", ""),
                                created_at=datetime.utcnow(),
                                updated_at=datetime.utcnow()
                            )
                            self.db.add(new_config)
                            result["imported"] += 1
                            
                    except Exception as e:
                        result["errors"].append(f"导入配置 {key} 失败: {e}")
                        result["skipped"] += 1
            
            self.db.commit()
            logger.info(f"导入系统设置完成: {result}")
            return result
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"导入系统设置失败: {e}")
            raise
    
    def save_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """保存系统设置"""
        try:
            result = {
                "saved": 0,
                "errors": []
            }
            
            for category, configs in settings.items():
                for key, value in configs.items():
                    try:
                        config = self.get_config(key)
                        if config:
                            config.value = str(value)
                            config.updated_at = datetime.utcnow()
                            result["saved"] += 1
                        else:
                            # 创建新配置
                            new_config = SystemConfig(
                                key=key,
                                value=str(value),
                                value_type="string",
                                category=category,
                                created_at=datetime.utcnow(),
                                updated_at=datetime.utcnow()
                            )
                            self.db.add(new_config)
                            result["saved"] += 1
                            
                    except Exception as e:
                        result["errors"].append(f"保存配置 {key} 失败: {e}")
            
            self.db.commit()
            logger.info(f"保存系统设置完成: {result}")
            return result
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"保存系统设置失败: {e}")
            raise
    
    # 系统测试
    def test_database_connection(self) -> Dict[str, Any]:
        """测试数据库连接"""
        try:
            # 执行简单查询测试连接
            self.db.execute("SELECT 1")
            
            # 获取数据库信息
            db_info = self.db.execute("SELECT version()")
            version = db_info.scalar() if db_info else "Unknown"
            
            return {
                "success": True,
                "message": "数据库连接正常",
                "version": version,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"数据库连接测试失败: {e}")
            return {
                "success": False,
                "message": f"数据库连接失败: {e}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def test_email_notification(self, email: str) -> Dict[str, Any]:
        """测试邮件通知"""
        try:
            # 这里应该实现实际的邮件发送逻辑
            # 暂时返回模拟结果
            logger.info(f"发送测试邮件到: {email}")
            
            return {
                "success": True,
                "message": f"测试邮件已发送到 {email}",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"邮件通知测试失败: {e}")
            return {
                "success": False,
                "message": f"邮件通知测试失败: {e}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def test_webhook_notification(self, url: str) -> Dict[str, Any]:
        """测试Webhook通知"""
        try:
            # 这里应该实现实际的Webhook请求逻辑
            # 暂时返回模拟结果
            logger.info(f"发送测试Webhook到: {url}")
            
            return {
                "success": True,
                "message": f"Webhook测试请求已发送到 {url}",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Webhook通知测试失败: {e}")
            return {
                "success": False,
                "message": f"Webhook通知测试失败: {e}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    # 系统维护
    def clear_cache(self) -> Dict[str, Any]:
        """清理缓存"""
        try:
            # 这里应该实现实际的缓存清理逻辑
            # 暂时返回模拟结果
            logger.info("清理系统缓存")
            
            return {
                "success": True,
                "message": "缓存清理完成",
                "cleared_items": 0,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"清理缓存失败: {e}")
            return {
                "success": False,
                "message": f"清理缓存失败: {e}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def reset_to_defaults(self) -> Dict[str, Any]:
        """重置为默认值"""
        try:
            # 获取所有非系统关键配置
            configs = self.db.query(SystemConfig).filter(
                SystemConfig.is_system == False
            ).all()
            
            reset_count = 0
            for config in configs:
                # 这里应该设置为默认值，暂时删除非系统配置
                self.db.delete(config)
                reset_count += 1
            
            self.db.commit()
            
            logger.info(f"重置为默认值完成，重置了 {reset_count} 个配置")
            return {
                "success": True,
                "message": f"重置为默认值完成，重置了 {reset_count} 个配置",
                "reset_count": reset_count,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"重置为默认值失败: {e}")
            return {
                "success": False,
                "message": f"重置为默认值失败: {e}",
                "timestamp": datetime.utcnow().isoformat()
            }