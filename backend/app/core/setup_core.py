#!/usr/bin/env python3
"""统一核心基础设施设置脚本

这个脚本负责初始化和配置MCPS.ONE的所有核心基础设施组件：
- 统一配置管理
- 统一错误处理
- 统一日志系统
- 统一缓存系统
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.unified_config import UnifiedConfigManager
from app.core.unified_error import ErrorHandler
from app.core.unified_logging import LoggingManager
from app.core.unified_cache import CacheFactory, CacheBackend

class CoreInfrastructureSetup:
    """核心基础设施设置类"""

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir) if data_dir else Path("data")
        self.config_manager: Optional[UnifiedConfigManager] = None
        self.error_handler: Optional[ErrorHandler] = None
        self.logging_manager: Optional[LoggingManager] = None
        self.cache_manager = None

        # 确保数据目录存在
        self.data_dir.mkdir(exist_ok=True)
        (self.data_dir / "logs").mkdir(exist_ok=True)
        (self.data_dir / "config").mkdir(exist_ok=True)
        (self.data_dir / "cache").mkdir(exist_ok=True)

    async def setup_config_manager(self) -> UnifiedConfigManager:
        """设置统一配置管理器"""
        print("初始化统一配置管理器...")

        config_dir = self.data_dir / "config"
        self.config_manager = UnifiedConfigManager(str(config_dir))

        # 设置默认配置
        default_configs = {
            # 应用配置
            "app.name": "MCPS.ONE",
            "app.version": "1.0.0",
            "app.description": "MCP工具管理平台",
            "app.debug": False,

            # 服务器配置
            "server.host": "0.0.0.0",
            "server.port": 8000,
            "server.workers": 1,

            # 数据库配置
            "database.url": f"sqlite:///{self.data_dir}/mcps.db",
            "database.echo": False,
            "database.pool_size": 5,

            # 日志配置
            "logging.level": "INFO",
            "logging.format": "structured",
            "logging.file_enabled": True,
            "logging.console_enabled": True,
            "logging.max_file_size": "10MB",
            "logging.backup_count": 5,

            # 缓存配置
            "cache.backend": "memory",
            "cache.default_ttl": 300,
            "cache.max_size": 1000,

            # MCP配置
            "mcp.server.transport": "stdio",
            "mcp.server.host": "127.0.0.1",
            "mcp.server.port": 8001,
            "mcp.server.log_level": "INFO",
            "mcp.proxy.enabled": True,
            "mcp.proxy.max_instances": 3,
            "mcp.proxy.timeout": 30,

            # 工具配置
            "tools.auto_start": False,
            "tools.restart_on_failure": True,
            "tools.max_restart_attempts": 3,
            "tools.health_check_interval": 30,

            # 安全配置
            "security.secret_key": "your-secret-key-here",
            "security.algorithm": "HS256",
            "security.access_token_expire_minutes": 30,
        }

        # 设置默认配置
        for key, value in default_configs.items():
            if self.config_manager.get(key) is None:
                self.config_manager.set(key, value)

        print("✓ 统一配置管理器初始化完成")
        return self.config_manager

    async def setup_error_handler(self) -> ErrorHandler:
        """设置统一错误处理器"""
        print("初始化统一错误处理器...")

        self.error_handler = ErrorHandler()

        # 配置错误处理器
        error_config = {
            "max_error_history": 1000,
            "error_report_enabled": True,
            "critical_error_notification": True,
            "error_aggregation_window": 300,  # 5分钟
        }

        # 注册默认错误处理器
        self.error_handler.register_callback(
            lambda error_info: print(f"系统错误: {error_info.message}")
        )

        self.error_handler.register_callback(
            lambda error_info: print(f"MCP错误: {error_info.message}")
        )

        print("✓ 统一错误处理器初始化完成")
        return self.error_handler

    async def setup_logging_manager(self) -> LoggingManager:
        """设置统一日志管理器"""
        print("初始化统一日志管理器...")

        log_dir = self.data_dir / "logs"

        # 日志配置
        logging_config = {
            "level": "INFO",
            "format": "structured",
            "console_enabled": True,
            "file_enabled": True,
            "file_path": str(log_dir / "app.log"),
            "max_file_size": "10MB",
            "backup_count": 5,
            "colored_console": True,
        }

        self.logging_manager = LoggingManager(str(log_dir))
        self.logging_manager.configure(
            level=logging_config["level"],
            console_output=logging_config["console_enabled"],
            file_output=logging_config["file_enabled"],
            structured_format=logging_config["format"] == "structured",
            max_file_size=10 * 1024 * 1024,  # 10MB
            backup_count=logging_config["backup_count"]
        )

        print("✓ 统一日志管理器初始化完成")
        return self.logging_manager

    async def setup_cache_manager(self):
        """设置统一缓存管理器"""
        print("初始化统一缓存管理器...")

        # 缓存配置
        cache_config = {
            "backend": CacheBackend.MEMORY,
            "default_ttl": 300,
            "max_size": 1000,
            "cleanup_interval": 60,
        }

        self.cache_manager = CacheFactory.create_memory_cache(
            max_size=cache_config["max_size"],
            cleanup_interval=cache_config["cleanup_interval"],
            default_ttl=cache_config["default_ttl"]
        )

        print("✓ 统一缓存管理器初始化完成")
        return self.cache_manager

    async def setup_all(self) -> Dict[str, Any]:
        """设置所有核心基础设施组件"""
        print("开始初始化MCPS.ONE核心基础设施...")
        print(f"数据目录: {self.data_dir.absolute()}")

        try:
            # 按顺序初始化各个组件
            config_manager = await self.setup_config_manager()
            error_handler = await self.setup_error_handler()
            logging_manager = await self.setup_logging_manager()
            cache_manager = await self.setup_cache_manager()

            # 设置全局实例
            from app.core import (
                init_unified_config, init_error_handler,
                init_logging, init_cache
            )
            from app.core.unified_cache import CacheBackend

            init_unified_config(str(self.data_dir / "config"))
            init_error_handler()  # 不需要参数
            init_logging(str(self.data_dir / "logs"))  # 传递日志目录
            init_cache(CacheBackend.MEMORY)  # 传递缓存后端类型

            print("\n🎉 核心基础设施初始化完成！")
            print("\n组件状态:")
            print(f"  ✓ 配置管理器: {len(config_manager.config_items)} 个配置项")
            print(f"  ✓ 错误处理器: {len(error_handler._global_callbacks)} 个全局回调")
            print(f"  ✓ 日志管理器: 已启动")
            print(f"  ✓ 缓存管理器: {type(cache_manager.backend).__name__} 后端")

            return {
                "config_manager": config_manager,
                "error_handler": error_handler,
                "logging_manager": logging_manager,
                "cache_manager": cache_manager,
            }

        except Exception as e:
            print(f"❌ 核心基础设施初始化失败: {e}")
            raise

    async def verify_setup(self) -> bool:
        """验证设置是否正确"""
        print("\n验证核心基础设施设置...")

        try:
            from app.core import (
                get_unified_config, get_error_handler,
                get_logging_manager, get_cache_manager
            )

            # 测试配置管理
            config = get_unified_config()
            app_name = config.get("app.name")
            print(f"  ✓ 配置管理: 应用名称 = {app_name}")

            # 测试错误处理
            error_handler = get_error_handler()
            print(f"  ✓ 错误处理: {len(error_handler._global_callbacks)} 个全局回调")

            # 测试日志系统
            logging_manager = get_logging_manager()
            logger = logging_manager.get_logger("test")
            logger.info("测试日志消息")
            print("  ✓ 日志系统: 测试消息已记录")

            # 测试缓存系统
            cache_manager = get_cache_manager()
            await cache_manager.set("test_key", "test_value", ttl=60)
            value = await cache_manager.get("test_key")
            assert value == "test_value"
            print("  ✓ 缓存系统: 读写测试通过")

            print("\n✅ 所有核心组件验证通过！")
            return True

        except Exception as e:
            print(f"\n❌ 验证失败: {e}")
            return False

    def create_startup_script(self) -> Path:
        """创建启动脚本"""
        startup_script = self.data_dir.parent / "startup_core.py"

        script_content = f'''
#!/usr/bin/env python3
"""MCPS.ONE 核心基础设施启动脚本"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.setup_core import CoreInfrastructureSetup

async def main():
    """主函数"""
    setup = CoreInfrastructureSetup("{self.data_dir}")

    # 初始化核心基础设施
    components = await setup.setup_all()

    # 验证设置
    if await setup.verify_setup():
        print("\n🚀 MCPS.ONE 核心基础设施已就绪！")
        return True
    else:
        print("\n💥 核心基础设施设置验证失败！")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
'''

        startup_script.write_text(script_content, encoding='utf-8')
        print(f"\n📝 启动脚本已创建: {startup_script}")
        return startup_script

async def main():
    """主函数"""
    # 获取数据目录
    data_dir = os.environ.get('MCPS_DATA_DIR', 'data')

    # 创建设置实例
    setup = CoreInfrastructureSetup(data_dir)

    try:
        # 初始化所有组件
        components = await setup.setup_all()

        # 验证设置
        if await setup.verify_setup():
            # 创建启动脚本
            startup_script = setup.create_startup_script()

            print("\n📋 下一步:")
            print(f"1. 运行启动脚本: python {startup_script.name}")
            print("2. 或在应用启动时调用 setup.setup_all()")
            print("3. 检查配置文件: data/config/")
            print("4. 查看日志文件: data/logs/")

            return True
        else:
            return False

    except Exception as e:
        print(f"\n❌ 设置失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
