#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动 MCPS.ONE MCP 代理服务器
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到 Python 路径
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# 设置数据库路径环境变量
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(backend_dir, 'data', 'mcps.db')}"

def log_message(message):
    """记录日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    log_file = os.path.join(backend_dir, 'mcp_proxy_server.log')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_msg + '\n')

async def start_mcp_proxy_server():
    """启动 MCP 代理服务器"""
    log_message("=== 启动 MCPS.ONE MCP 代理服务器 ===")

    mcp_server = None
    try:
        # 导入必要的模块
        log_message("导入服务模块...")
        from app.services.mcp import MCPProxyServer

        # 创建 MCP 代理服务器
        log_message("创建 MCP 代理服务器...")
        mcp_server = MCPProxyServer()

        # 启动服务器 (stdio 模式)
        log_message("启动 MCP 代理服务器 (stdio 模式)...")
        await mcp_server.run_stdio()
        
        log_message("MCP 代理服务器已停止")

    except KeyboardInterrupt:
        log_message("收到中断信号，MCP 代理服务器已停止")
        return True
    except Exception as e:
        log_message(f"启动服务器失败: {e}")
        import traceback
        log_message(f"错误详情: {traceback.format_exc()}")
        return False

    return True

if __name__ == "__main__":
    # 清空日志文件
    log_file = os.path.join(backend_dir, 'mcp_proxy_server.log')
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("")

    try:
        asyncio.run(start_mcp_proxy_server())
    except KeyboardInterrupt:
        print("\n服务器已停止")
