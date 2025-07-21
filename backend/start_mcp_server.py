#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCPS.ONE MCP 代理服务器

这个脚本启动 MCPS.ONE 的 MCP 代理服务，允许通过统一接口
访问所有在 Web 管理后台配置的 MCP 工具，包括：
- Playwright MCP 服务
- 12306-mcp 服务
- 其他已配置的 MCP 工具
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# 添加项目根目录到 Python 路径
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# 设置数据库路径环境变量
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(backend_dir, 'data', 'mcps.db')}"

def log_message(message):
    """记录日志到文件"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] {message}"

    # 写入日志文件
    log_file = os.path.join(backend_dir, 'cursor_mcp.log')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_msg + '\n')

    # 同时输出到stderr供调试
    print(log_msg, file=sys.stderr)

async def main():
    """主函数 - 启动 MCP 代理服务器"""
    log_message("=== 启动 MCPS.ONE MCP 代理服务器 ===")

    try:
        # 导入必要的模块
        log_message("导入服务模块...")
        from app.core.unified_config_manager import init_unified_config_manager
        from app.services.mcp import MCPSServer

        # 初始化配置管理器
        log_message("初始化配置管理器...")
        config_manager = init_unified_config_manager()
        log_message("配置管理器初始化完成")

        # 创建 MCP 服务器
        log_message("创建 MCP 服务器...")
        mcp_server = MCPSServer()

        # 初始化服务器
        log_message("初始化 MCP 服务器...")
        await mcp_server.initialize()

        # 启动服务器
        log_message("启动 MCP 服务器...")
        await mcp_server.start()

        log_message("✅ MCPS.ONE MCP 代理服务器启动成功")
        log_message("服务器正在运行，等待工具调用...")

        # 启动 stdio 模式 (这会阻塞直到服务器停止)
        log_message("启动 stdio 模式...")
        await mcp_server.run_stdio()

    except Exception as e:
        log_message(f"❌ 启动服务器失败: {e}")
        import traceback
        log_message(f"错误详情: {traceback.format_exc()}")
        sys.exit(1)

    finally:
        try:
            log_message("正在关闭 MCP 服务...")
            if 'mcp_server' in locals():
                await mcp_server.stop()
            log_message("MCP 服务已关闭")
        except Exception as e:
            log_message(f"关闭服务时发生错误: {e}")

if __name__ == "__main__":
    # 清空日志文件
    log_file = os.path.join(backend_dir, 'cursor_mcp.log')
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n服务器已停止", file=sys.stderr)
    except Exception as e:
        print(f"启动失败: {e}", file=sys.stderr)
        sys.exit(1)
