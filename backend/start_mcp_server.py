#!/usr/bin/env python3
"""MCPS.ONE MCP 服务端启动脚本

用于启动 MCPS.ONE 作为 MCP 服务端，供 Cursor、Claude Desktop 等客户端连接。
"""

import asyncio
import logging
import sys
import os
import traceback
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.mcp_server import get_mcp_server
from app.core.config import settings
from app.core.database import init_db

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)  # 输出到 stderr，避免与 stdio 协议冲突
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """主函数"""
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="MCPS.ONE MCP 服务端",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  stdio 模式: python start_mcp_server.py --transport stdio
  HTTP 模式:  python start_mcp_server.py --transport http --host 127.0.0.1 --port 8001

注意: HTTP 模式当前使用 FastMCP 默认配置 (0.0.0.0:8000)
        """
    )
    parser.add_argument(
        "--transport", 
        choices=["stdio", "http"], 
        default=settings.MCP_SERVER_TRANSPORT,
        help=f"传输协议 (默认: {settings.MCP_SERVER_TRANSPORT})"
    )
    parser.add_argument(
        "--host", 
        default=settings.MCP_SERVER_HOST,
        help=f"HTTP 模式的主机地址 (默认: {settings.MCP_SERVER_HOST})"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=settings.MCP_SERVER_PORT,
        help=f"HTTP 模式的端口号 (默认: {settings.MCP_SERVER_PORT})"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=settings.MCP_SERVER_LOG_LEVEL,
        help=f"日志级别 (默认: {settings.MCP_SERVER_LOG_LEVEL})"
    )
    parser.add_argument(
        "--validate-config",
        action="store_true",
        help="验证配置并退出"
    )
    
    args = parser.parse_args()
    
    try:
        # 更新配置
        if hasattr(args, 'log_level'):
            settings.MCP_SERVER_LOG_LEVEL = args.log_level
        
        # 重新配置日志级别
        log_level = getattr(logging, args.log_level.upper(), logging.INFO)
        logging.getLogger().setLevel(log_level)
        
        # 验证配置
        logger.info("验证 MCP 服务端配置...")
        try:
            config = settings.get_mcp_server_config()
            logger.info("配置验证通过")
            
            if args.validate_config:
                logger.info("配置验证完成，退出")
                print("\n=== MCP 服务端配置 ===")
                for key, value in config.items():
                    print(f"{key}: {value}")
                return
                
        except ValueError as e:
            logger.error(f"配置验证失败: {e}")
            sys.exit(1)
        
        # 初始化数据库
        logger.info("初始化数据库...")
        try:
            init_db()
            logger.info("数据库初始化完成")
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            sys.exit(1)
        
        # 获取 MCP 服务端实例
        logger.info("创建 MCP 服务端实例...")
        try:
            server = get_mcp_server()
            logger.info("MCP 服务端实例创建完成")
        except Exception as e:
            logger.error(f"创建 MCP 服务端实例失败: {e}")
            sys.exit(1)
        
        # 根据传输协议启动服务端
        if args.transport == "stdio":
            logger.info("启动 MCPS.ONE MCP 服务端 (stdio 模式)...")
            await server.run_stdio()
        else:
            logger.info(f"启动 MCPS.ONE MCP 服务端 (HTTP 模式) - {args.host}:{args.port}...")
            await server.run_http(args.host, args.port)
        
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务端...")
    except Exception as e:
        logger.error(f"服务端启动失败: {e}")
        logger.error(f"错误详情: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    # 检查是否在正确的目录
    if not os.path.exists("app"):
        print("错误: 请在 backend 目录下运行此脚本", file=sys.stderr)
        sys.exit(1)
    
    # 运行服务端
    asyncio.run(main())