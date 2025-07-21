
#!/usr/bin/env python3
"""MCPS.ONE 核心基础设施启动脚本"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.app.core.setup_core import CoreInfrastructureSetup
from backend.app.core.unified_config_manager import init_unified_config_manager
from backend.app.core.unified_logging import init_logging
from backend.app.core.unified_cache import init_cache, CacheBackend
from backend.app.core.unified_error import init_error_handler

async def main():
    """主函数"""
    setup = CoreInfrastructureSetup("data")
    
    # 1. 初始化配置管理器
    print("正在初始化配置管理器...")
    config_manager = init_unified_config_manager(str(Path("data") / "config"))
    
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
