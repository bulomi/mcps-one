"""FastAPI 依赖注入模块

提供应用程序级别的依赖注入函数。
"""

import logging
from typing import Optional
from functools import lru_cache

from ..services.mcp.mcp_proxy_server import MCPProxyServer
from app.core import get_unified_config_manager

logger = logging.getLogger(__name__)

# 全局代理服务器实例
_proxy_server: Optional[MCPProxyServer] = None


@lru_cache()
def get_proxy_config() -> dict:
    """获取代理服务器配置"""
    config_manager = get_unified_config_manager()
    return {
        'host': config_manager.get('mcp.proxy.host', 'localhost'),
        'port': config_manager.get('mcp.proxy.port', 8000),
        'max_concurrent_tools': config_manager.get('mcp.proxy.max_concurrent_tools', 10),
        'tool_timeout': config_manager.get('mcp.proxy.tool_timeout', 30),
        'enable_caching': config_manager.get('mcp.proxy.enable_caching', True),
        'cache_ttl': config_manager.get('mcp.proxy.cache_ttl', 300),
        'enable_health_check': config_manager.get('mcp.proxy.enable_health_check', True),
        'health_check_interval': config_manager.get('mcp.proxy.health_check_interval', 30)
    }


async def get_mcp_proxy_server() -> MCPProxyServer:
    """获取MCP代理服务器实例

    这是一个FastAPI依赖注入函数，用于在API路由中获取代理服务器实例。

    Returns:
        MCPProxyServer: 代理服务器实例
    """
    global _proxy_server

    if _proxy_server is None:
        logger.info("创建新的MCP代理服务器实例")
        config = get_proxy_config()
        _proxy_server = MCPProxyServer(config=config)

        try:
            # 初始化代理服务器
            await _proxy_server.initialize()

            # 如果服务器未运行，则启动它
            if not _proxy_server.is_running():
                await _proxy_server.start()

        except Exception as e:
            logger.error(f"初始化MCP代理服务器失败: {e}")
            # 如果初始化失败，仍然返回实例，但记录错误
            # 这样可以避免应用程序完全崩溃

    return _proxy_server


async def shutdown_proxy_server() -> None:
    """关闭代理服务器

    在应用程序关闭时调用，用于清理资源。
    """
    global _proxy_server

    if _proxy_server is not None:
        try:
            logger.info("关闭MCP代理服务器")
            await _proxy_server.stop()
        except Exception as e:
            logger.error(f"关闭MCP代理服务器失败: {e}")
        finally:
            _proxy_server = None


def reset_proxy_server() -> None:
    """重置代理服务器实例

    主要用于测试环境，强制重新创建代理服务器实例。
    """
    global _proxy_server
    _proxy_server = None
    # 清除配置缓存
    get_proxy_config.cache_clear()
