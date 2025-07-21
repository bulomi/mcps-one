"""核心基础设施初始化脚本

这个脚本演示了如何初始化和配置MCPS.ONE的核心基础设施组件。
"""

import os
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional

from .unified_config_manager import init_unified_config_manager, ConfigSource
from .unified_error import init_error_handler, ErrorCategory, ErrorSeverity
from .unified_logging import init_logging, LogCategory, LogLevel
from .unified_cache import init_cache, CacheBackend

def init_core_infrastructure(config_dir: Optional[str] = None,
                           log_dir: Optional[str] = None,
                           cache_backend: CacheBackend = CacheBackend.MEMORY,
                           **kwargs) -> Dict[str, Any]:
    """初始化核心基础设施

    Args:
        config_dir: 配置文件目录
        log_dir: 日志文件目录
        cache_backend: 缓存后端类型
        **kwargs: 其他配置参数

    Returns:
        包含所有初始化组件的字典
    """

    # 设置默认路径
    if config_dir is None:
        config_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config")

    if log_dir is None:
        log_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "logs")

    # 确保目录存在
    Path(config_dir).mkdir(parents=True, exist_ok=True)
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    # 1. 初始化配置管理器
    print("正在初始化配置管理器...")
    config_manager = init_unified_config_manager(config_dir)

    # 设置一些默认配置
    default_configs = {
        "system.debug_mode": False,
        "system.max_workers": 4,
        "system.timeout": 30,
        "logging.level": "INFO",
        "logging.console_output": True,
        "logging.file_output": True,
        "cache.default_ttl": 3600,
        "cache.max_size": 1000,
        "mcp.default_timeout": 30,
        "mcp.max_connections": 10,
        "api.rate_limit": 100,
        "api.cors_enabled": True
    }

    for key, value in default_configs.items():
        if config_manager.get(key) is None:
            config_manager.set(key, value, ConfigSource.DEFAULT, persist=False)

    # 2. 初始化错误处理器
    print("正在初始化错误处理器...")
    error_handler = init_error_handler()

    # 注册错误回调
    def log_critical_errors(error_info):
        if error_info.severity == ErrorSeverity.CRITICAL:
            print(f"严重错误: {error_info.message} (ID: {error_info.error_id})")

    error_handler.register_callback(log_critical_errors)

    # 3. 初始化日志系统
    print("正在初始化日志系统...")
    log_level = config_manager.get("logging.level", "INFO")
    console_output = config_manager.get("logging.console_output", True)
    file_output = config_manager.get("logging.file_output", True)

    logging_manager = init_logging(
        log_dir=log_dir,
        level=getattr(LogLevel, log_level.upper()).value,
        console_output=console_output,
        file_output=file_output,
        structured_format=True
    )

    # 创建分类日志器
    system_logger = logging_manager.create_category_logger(
        LogCategory.SYSTEM, "system.log"
    )
    api_logger = logging_manager.create_category_logger(
        LogCategory.API, "api.log"
    )
    mcp_logger = logging_manager.create_category_logger(
        LogCategory.MCP, "mcp.log"
    )

    # 4. 初始化缓存系统
    print("正在初始化缓存系统...")
    cache_config = {
        "default_ttl": config_manager.get("cache.default_ttl", 3600)
    }

    if cache_backend == CacheBackend.MEMORY:
        cache_config["max_size"] = config_manager.get("cache.max_size", 1000)
    elif cache_backend == CacheBackend.REDIS:
        cache_config["redis_url"] = config_manager.get("cache.redis_url", "redis://localhost:6379")
        cache_config["key_prefix"] = "mcps:"

    cache_manager = init_cache(cache_backend, **cache_config)

    # 记录初始化完成
    system_logger.info("核心基础设施初始化完成", metadata={
        "config_dir": config_dir,
        "log_dir": log_dir,
        "cache_backend": cache_backend.value
    })

    return {
        "config_manager": config_manager,
        "error_handler": error_handler,
        "logging_manager": logging_manager,
        "cache_manager": cache_manager,
        "loggers": {
            "system": system_logger,
            "api": api_logger,
            "mcp": mcp_logger
        }
    }

async def init_core_infrastructure_async(config_dir: Optional[str] = None,
                                       log_dir: Optional[str] = None,
                                       cache_backend: CacheBackend = CacheBackend.MEMORY,
                                       **kwargs) -> Dict[str, Any]:
    """异步初始化核心基础设施"""

    # 同步初始化大部分组件
    components = init_core_infrastructure(config_dir, log_dir, cache_backend, **kwargs)

    # 测试缓存系统
    cache_manager = components["cache_manager"]
    await cache_manager.set("init_test", "success", ttl=60)
    test_value = await cache_manager.get("init_test")

    if test_value == "success":
        components["loggers"]["system"].info("缓存系统测试通过")
    else:
        components["loggers"]["system"].warning("缓存系统测试失败")

    return components

def create_default_config_files(config_dir: str) -> None:
    """创建默认配置文件"""
    config_path = Path(config_dir)
    config_path.mkdir(parents=True, exist_ok=True)

    # 系统配置
    system_config = {
        "system": {
            "debug_mode": False,
            "max_workers": 4,
            "timeout": 30,
            "environment": "development"
        },
        "logging": {
            "level": "INFO",
            "console_output": True,
            "file_output": True,
            "structured_format": True,
            "max_file_size": "10MB",
            "backup_count": 5
        },
        "cache": {
            "backend": "memory",
            "default_ttl": 3600,
            "max_size": 1000,
            "redis_url": "redis://localhost:6379"
        }
    }

    # MCP配置
    mcp_config = {
        "mcp": {
            "default_timeout": 30,
            "max_connections": 10,
            "retry_attempts": 3,
            "retry_delay": 1,
            "enable_heartbeat": True,
            "heartbeat_interval": 30
        },
        "tools": {
            "auto_discovery": True,
            "max_execution_time": 300,
            "enable_caching": True,
            "cache_ttl": 1800
        }
    }

    # API配置
    api_config = {
        "api": {
            "host": "0.0.0.0",
            "port": 8000,
            "rate_limit": 100,
            "cors_enabled": True,
            "cors_origins": ["*"],
            "enable_docs": True
        },
        "security": {
            "secret_key": "your-secret-key-here",
            "algorithm": "HS256",
            "access_token_expire_minutes": 30,
            "enable_rate_limiting": True
        }
    }

    # 写入配置文件
    import yaml

    with open(config_path / "system.yaml", "w", encoding="utf-8") as f:
        yaml.dump(system_config, f, default_flow_style=False, allow_unicode=True)

    with open(config_path / "mcp.yaml", "w", encoding="utf-8") as f:
        yaml.dump(mcp_config, f, default_flow_style=False, allow_unicode=True)

    with open(config_path / "api.yaml", "w", encoding="utf-8") as f:
        yaml.dump(api_config, f, default_flow_style=False, allow_unicode=True)

    print(f"默认配置文件已创建在: {config_path}")

def demo_core_usage():
    """演示核心组件的使用"""
    print("=== MCPS.ONE 核心基础设施演示 ===")

    # 创建默认配置文件
    config_dir = "demo_config"
    create_default_config_files(config_dir)

    # 初始化核心组件
    components = init_core_infrastructure(
        config_dir=config_dir,
        log_dir="demo_logs",
        cache_backend=CacheBackend.MEMORY
    )

    config_manager = components["config_manager"]
    error_handler = components["error_handler"]
    cache_manager = components["cache_manager"]
    system_logger = components["loggers"]["system"]

    # 演示配置管理
    print("\n1. 配置管理演示:")
    print(f"调试模式: {config_manager.get('system.debug_mode')}")
    print(f"最大工作线程: {config_manager.get('system.max_workers')}")

    # 演示日志记录
    print("\n2. 日志记录演示:")
    system_logger.info("这是一条信息日志")
    system_logger.warning("这是一条警告日志")

    # 演示错误处理
    print("\n3. 错误处理演示:")
    try:
        raise ValueError("这是一个演示错误")
    except Exception as e:
        from .unified_error import create_error_context
        context = create_error_context(service_name="demo", method_name="demo_function")
        error_handler.handle_error(e, context)

    # 演示缓存使用
    print("\n4. 缓存使用演示:")
    async def cache_demo():
        await cache_manager.set("demo_key", "demo_value", ttl=60)
        value = await cache_manager.get("demo_key")
        print(f"缓存值: {value}")

        stats = await cache_manager.get_stats()
        print(f"缓存统计: 命中率={stats.hit_rate:.2%}, 条目数={stats.entry_count}")

    asyncio.run(cache_demo())

    print("\n演示完成!")

if __name__ == "__main__":
    demo_core_usage()
