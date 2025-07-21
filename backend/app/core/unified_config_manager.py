"""统一配置管理器

整合所有配置管理功能，提供统一的配置接口。
消除重复的配置管理器，简化配置架构。
"""

import os
import yaml
import json
from typing import Dict, Any, Optional, Union, List, Callable
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
from pydantic import BaseModel, Field, field_validator, ConfigDict
from sqlalchemy.orm import Session

from app.models.system import SystemConfig
from app.utils.exceptions import SystemConfigError
from app.core.log_levels import ALLOWED_LOG_LEVELS

logger = logging.getLogger(__name__)


class ConfigSource(Enum):
    """配置来源"""
    FILE = "file"  # 配置文件
    ENV = "env"  # 环境变量
    DATABASE = "database"  # 数据库
    DEFAULT = "default"  # 默认值


class ConfigType(Enum):
    """配置类型"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    LIST = "list"


class ConfigLevel(Enum):
    """配置级别"""
    SYSTEM = "system"  # 系统级配置
    USER = "user"  # 用户级配置
    RUNTIME = "runtime"  # 运行时配置


@dataclass
class ConfigItem:
    """配置项"""
    key: str
    value: Any
    type: ConfigType
    source: ConfigSource
    level: ConfigLevel = ConfigLevel.SYSTEM
    description: str = ""
    category: str = "general"
    required: bool = False
    default: Any = None
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    is_sensitive: bool = False  # 是否为敏感信息


class ConfigFileWatcher(FileSystemEventHandler):
    """配置文件监控器"""

    def __init__(self, config_manager: 'UnifiedConfigManager'):
        self.config_manager = config_manager

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(('.yaml', '.yml', '.json')):
            logger.info(f"配置文件 {event.src_path} 已修改，重新加载配置")
            self.config_manager.reload()


class UnifiedConfigManager:
    """统一配置管理器

    整合所有配置管理功能，提供统一的配置接口。
    支持配置文件、环境变量、数据库配置的统一管理。
    """

    def __init__(self, config_dir: Optional[str] = None, db_session: Optional[Session] = None):
        self.config_dir = Path(config_dir) if config_dir else Path("config")
        self.db_session = db_session
        self.config_items: Dict[str, ConfigItem] = {}
        self._watchers: List[Callable] = []
        self._load_order = [ConfigSource.DEFAULT, ConfigSource.FILE, ConfigSource.ENV, ConfigSource.DATABASE]

        # 文件监控
        self._observer: Optional[Observer] = None
        self._file_watcher: Optional[ConfigFileWatcher] = None

        # 确保配置目录存在
        self.config_dir.mkdir(exist_ok=True)

        # 加载配置
        self._load_all_configs()

        # 启动文件监控
        self._start_file_watching()

    def _load_all_configs(self) -> None:
        """加载所有配置"""
        for source in self._load_order:
            try:
                if source == ConfigSource.DEFAULT:
                    self._load_default_configs()
                elif source == ConfigSource.FILE:
                    self._load_file_configs()
                elif source == ConfigSource.ENV:
                    self._load_env_configs()
                elif source == ConfigSource.DATABASE:
                    self._load_database_configs()
            except Exception as e:
                logger.warning(f"加载配置源 {source.value} 失败: {e}")

    def _load_default_configs(self) -> None:
        """加载默认配置"""
        default_configs = {
            # 应用配置
            'app.name': ('MCPS.ONE', ConfigType.STRING, '应用名称'),
            'app.version': ('1.0.0', ConfigType.STRING, '应用版本'),
            'app.description': ('MCP 工具管理平台', ConfigType.STRING, '应用描述'),
            'app.show_title': (True, ConfigType.BOOLEAN, '是否显示标题'),
            'app.logo_url': ('', ConfigType.STRING, 'Logo URL'),

            # 服务器配置
            'server.host': ('0.0.0.0', ConfigType.STRING, '服务器主机地址'),
            'server.port': (8000, ConfigType.INTEGER, '服务器端口'),
            'server.debug': (False, ConfigType.BOOLEAN, '调试模式'),
            'server.cors_origins': (['http://localhost:5173'], ConfigType.LIST, 'CORS允许的源'),
            'server.allowed_hosts': (['localhost', '127.0.0.1'], ConfigType.LIST, '允许的主机'),

            # 数据库配置
            'database.url': ('sqlite:///./data/mcps.db', ConfigType.STRING, '数据库连接URL'),
            'database.echo': (False, ConfigType.BOOLEAN, '是否显示SQL日志'),
            'database.backup_enabled': (True, ConfigType.BOOLEAN, '是否启用备份'),
            'database.backup_interval': ('daily', ConfigType.STRING, '备份间隔'),
            'database.backup_retention_days': (30, ConfigType.INTEGER, '备份保留天数'),

            # 日志配置
            'logging.level': ('INFO', ConfigType.STRING, '日志级别'),
            'logging.format': ('%(asctime)s - %(name)s - %(levelname)s - %(message)s', ConfigType.STRING, '日志格式'),
            'logging.file': ('./data/logs/app.log', ConfigType.STRING, '日志文件路径'),
            'logging.max_file_size': ('10MB', ConfigType.STRING, '日志文件最大大小'),
            'logging.backup_count': (5, ConfigType.INTEGER, '日志文件备份数量'),
            'logging.console_output': (True, ConfigType.BOOLEAN, '是否输出到控制台'),

            # MCP配置
            'mcp.enabled': (True, ConfigType.BOOLEAN, '是否启用MCP服务'),
            'mcp.max_processes': (10, ConfigType.INTEGER, 'MCP最大进程数'),
            'mcp.process_timeout': (30, ConfigType.INTEGER, 'MCP进程超时时间'),
            'mcp.restart_delay': (5, ConfigType.INTEGER, 'MCP重启延迟'),
            'mcp.tools_dir': ('./data/tools', ConfigType.STRING, 'MCP工具目录'),
            'mcp.logs_dir': ('./data/logs', ConfigType.STRING, 'MCP日志目录'),

            # 功能开关
            'features.developer_mode': (False, ConfigType.BOOLEAN, '开发者模式'),
            'features.api_docs': (True, ConfigType.BOOLEAN, 'API文档'),
            'features.verbose_errors': (False, ConfigType.BOOLEAN, '详细错误信息'),
            'features.experimental_features': (False, ConfigType.BOOLEAN, '实验性功能'),
            'features.auto_update': (False, ConfigType.BOOLEAN, '自动更新'),
            'features.health_check': (True, ConfigType.BOOLEAN, '健康检查'),
            'features.websocket_enabled': (True, ConfigType.BOOLEAN, 'WebSocket支持'),
        }

        for key, (value, config_type, description) in default_configs.items():
            category = key.split('.')[0]
            self._add_config_item(
                key=key,
                value=value,
                config_type=config_type,
                source=ConfigSource.DEFAULT,
                description=description,
                category=category
            )

    def _load_file_configs(self) -> None:
        """从文件加载配置"""
        # 加载YAML配置文件
        yaml_files = list(self.config_dir.glob("*.yaml")) + list(self.config_dir.glob("*.yml"))
        for yaml_file in yaml_files:
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    self._process_config_data(data, ConfigSource.FILE, yaml_file.stem)
            except Exception as e:
                logger.error(f"加载YAML配置文件 {yaml_file} 失败: {e}")

        # 加载JSON配置文件
        json_files = list(self.config_dir.glob("*.json"))
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._process_config_data(data, ConfigSource.FILE, json_file.stem)
            except Exception as e:
                logger.error(f"加载JSON配置文件 {json_file} 失败: {e}")

    def _load_env_configs(self) -> None:
        """从环境变量加载配置"""
        # 加载以MCPS_开头的环境变量
        for key, value in os.environ.items():
            if key.startswith('MCPS_'):
                config_key = key[5:].lower().replace('_', '.')  # 移除MCPS_前缀并转换格式
                self._add_config_item(
                    key=config_key,
                    value=value,
                    config_type=self._infer_type(value),
                    source=ConfigSource.ENV,
                    description=f"环境变量 {key}"
                )

    def _load_database_configs(self) -> None:
        """从数据库加载配置"""
        if not self.db_session:
            return

        try:
            configs = self.db_session.query(SystemConfig).all()
            for config in configs:
                # 映射数据库中的value_type字符串到ConfigType枚举
                type_mapping = {
                    'string': ConfigType.STRING,
                    'integer': ConfigType.INTEGER,
                    'float': ConfigType.FLOAT,
                    'boolean': ConfigType.BOOLEAN,
                    'json': ConfigType.JSON,
                    'list': ConfigType.LIST
                }
                config_type = type_mapping.get(config.value_type, ConfigType.STRING)

                self._add_config_item(
                    key=config.key,
                    value=config.get_typed_value(),
                    config_type=config_type,
                    source=ConfigSource.DATABASE,
                    description=config.description or "",
                    category=config.category or "general",
                    required=False  # 数据库配置默认不是必需的
                )
        except Exception as e:
            logger.error(f"从数据库加载配置失败: {e}")

    def _process_config_data(self, data: Dict[str, Any], source: ConfigSource, category: str) -> None:
        """处理配置数据"""
        def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten_dict(v, new_key, sep=sep).items())
                else:
                    items.append((new_key, v))
            return dict(items)

        flattened = flatten_dict(data)
        for key, value in flattened.items():
            self._add_config_item(
                key=key,
                value=value,
                config_type=self._infer_type(value),
                source=source,
                category=category
            )

    def _add_config_item(self, key: str, value: Any, config_type: ConfigType,
                        source: ConfigSource, description: str = "",
                        category: str = "general", required: bool = False) -> None:
        """添加配置项"""
        # 如果配置项已存在，根据优先级决定是否覆盖
        if key in self.config_items:
            existing_item = self.config_items[key]
            if self._get_source_priority(source) <= self._get_source_priority(existing_item.source):
                return  # 不覆盖更高优先级的配置

        # 转换值类型
        converted_value = self._convert_value(value, config_type)

        config_item = ConfigItem(
            key=key,
            value=converted_value,
            type=config_type,
            source=source,
            description=description,
            category=category,
            required=required
        )

        self.config_items[key] = config_item

        # 通知监听器
        for watcher in self._watchers:
            try:
                watcher(key, converted_value)
            except Exception as e:
                logger.error(f"配置监听器执行失败: {e}")

    def _get_source_priority(self, source: ConfigSource) -> int:
        """获取配置源优先级（数字越小优先级越高）"""
        priority_map = {
            ConfigSource.DATABASE: 1,  # 最高优先级
            ConfigSource.ENV: 2,
            ConfigSource.FILE: 3,
            ConfigSource.DEFAULT: 4   # 最低优先级
        }
        return priority_map.get(source, 999)

    def _infer_type(self, value: Any) -> ConfigType:
        """推断值类型"""
        if isinstance(value, bool):
            return ConfigType.BOOLEAN
        elif isinstance(value, int):
            return ConfigType.INTEGER
        elif isinstance(value, float):
            return ConfigType.FLOAT
        elif isinstance(value, list):
            return ConfigType.LIST
        elif isinstance(value, dict):
            return ConfigType.JSON
        else:
            return ConfigType.STRING

    def _convert_value(self, value: Any, config_type: ConfigType) -> Any:
        """转换值类型"""
        try:
            if config_type == ConfigType.BOOLEAN:
                if isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'on')
                return bool(value)
            elif config_type == ConfigType.INTEGER:
                return int(value)
            elif config_type == ConfigType.FLOAT:
                return float(value)
            elif config_type == ConfigType.LIST:
                if isinstance(value, str):
                    return json.loads(value)
                return list(value) if not isinstance(value, list) else value
            elif config_type == ConfigType.JSON:
                if isinstance(value, str):
                    return json.loads(value)
                return value
            else:
                return str(value)
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            logger.warning(f"配置值类型转换失败: {e}，使用原始值")
            return value

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        item = self.config_items.get(key)
        return item.value if item else default

    def get_item(self, key: str) -> Optional[ConfigItem]:
        """获取配置项"""
        return self.config_items.get(key)

    def set(self, key: str, value: Any, persist: bool = True) -> None:
        """设置配置值"""
        # 更新内存中的配置
        if key in self.config_items:
            item = self.config_items[key]
            item.value = self._convert_value(value, item.type)
            item.last_updated = datetime.utcnow()
        else:
            # 新增配置项
            config_type = self._infer_type(value)
            self._add_config_item(
                key=key,
                value=value,
                config_type=config_type,
                source=ConfigSource.RUNTIME
            )

        # 持久化到数据库
        if persist and self.db_session:
            self._persist_to_database(key, value)

        # 通知监听器
        for watcher in self._watchers:
            try:
                watcher(key, value)
            except Exception as e:
                logger.error(f"配置监听器执行失败: {e}")

    def _persist_to_database(self, key: str, value: Any) -> None:
        """持久化配置到数据库"""
        try:
            item = self.config_items[key]

            # 查找现有配置
            config = self.db_session.query(SystemConfig).filter_by(key=key).first()

            if config:
                # 更新现有配置
                config.set_typed_value(value)
                config.updated_at = datetime.utcnow()
            else:
                # 创建新配置
                # 映射ConfigType到数据库字段
                type_mapping = {
                    ConfigType.STRING: 'string',
                    ConfigType.INTEGER: 'integer',
                    ConfigType.FLOAT: 'float',
                    ConfigType.BOOLEAN: 'boolean',
                    ConfigType.JSON: 'json',
                    ConfigType.LIST: 'list'
                }

                config = SystemConfig(
                    key=key,
                    value=str(value),
                    value_type=type_mapping.get(item.type, 'string'),
                    category=item.category,
                    description=item.description
                )
                self.db_session.add(config)

            self.db_session.commit()
        except Exception as e:
            logger.error(f"持久化配置到数据库失败: {e}")
            self.db_session.rollback()

    def add_watcher(self, callback: Callable[[str, Any], None]) -> None:
        """添加配置变更监听器"""
        self._watchers.append(callback)

    def remove_watcher(self, callback: Callable[[str, Any], None]) -> None:
        """移除配置变更监听器"""
        if callback in self._watchers:
            self._watchers.remove(callback)

    def _start_file_watching(self) -> None:
        """启动文件监控"""
        try:
            self._file_watcher = ConfigFileWatcher(self)
            self._observer = Observer()
            self._observer.schedule(self._file_watcher, str(self.config_dir), recursive=False)
            self._observer.start()
            logger.info(f"配置文件监控已启动，监控目录: {self.config_dir}")
        except Exception as e:
            logger.error(f"启动配置文件监控失败: {e}")

    def reload(self) -> None:
        """重新加载配置"""
        logger.info("重新加载配置...")
        self.config_items.clear()
        self._load_all_configs()
        logger.info("配置已重新加载")

    def get_all_configs(self) -> Dict[str, ConfigItem]:
        """获取所有配置项"""
        return self.config_items.copy()

    def get_configs_by_category(self, category: str) -> Dict[str, ConfigItem]:
        """根据分类获取配置项"""
        return {k: v for k, v in self.config_items.items() if v.category == category}

    def close(self) -> None:
        """关闭配置管理器"""
        if self._observer:
            self._observer.stop()
            self._observer.join()
        logger.info("配置管理器已关闭")


# 全局配置管理器实例
_config_manager: Optional[UnifiedConfigManager] = None


def init_unified_config_manager(config_dir: Optional[str] = None,
                               db_session: Optional[Session] = None) -> UnifiedConfigManager:
    """初始化统一配置管理器"""
    global _config_manager
    _config_manager = UnifiedConfigManager(config_dir, db_session)
    return _config_manager


def get_unified_config_manager() -> Optional[UnifiedConfigManager]:
    """获取统一配置管理器实例"""
    return _config_manager


def get_config(key: str, default: Any = None) -> Any:
    """获取配置值的便捷函数"""
    if _config_manager:
        return _config_manager.get(key, default)
    return default


def set_config(key: str, value: Any, persist: bool = True) -> None:
    """设置配置值的便捷函数"""
    if _config_manager:
        _config_manager.set(key, value, persist)
