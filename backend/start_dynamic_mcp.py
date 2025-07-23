#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCPS.ONE 动态MCP启动器

根据Web管理平台的配置自动选择启动模式：
- MCP服务端模式 (start_mcp_server.py)
- FastMCP代理模式 (start_mcp_proxy_server.py) 
- API服务模式 (start_unified_mcp.py)

这个脚本会：
1. 读取数据库中的配置
2. 根据配置选择合适的启动模式
3. 动态加载对应的服务
4. 监听配置变化并支持热切换
"""

import asyncio
import sys
import os
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

# 添加项目根目录到 Python 路径
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# 设置数据库路径环境变量
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(backend_dir, 'data', 'mcps.db')}"

def log_message(message: str, level: str = "INFO"):
    """记录日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] [{level}] {message}"
    print(log_msg, file=sys.stderr)
    
    # 写入日志文件
    log_file = os.path.join(backend_dir, 'dynamic_mcp.log')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_msg + '\n')

class DynamicMCPLauncher:
    """动态MCP启动器"""
    
    def __init__(self):
        self.current_mode: Optional[str] = None
        self.current_service = None
        self.config_cache: Dict[str, Any] = {}
        self.last_config_check = 0
        self.config_check_interval = 5  # 秒
        self.running = False
        
    async def initialize(self):
        """初始化启动器"""
        log_message("=== 初始化动态MCP启动器 ===")
        
        try:
            # 导入必要的模块
            from app.core.unified_config_manager import init_unified_config_manager
            
            # 初始化配置管理器
            log_message("初始化配置管理器...")
            self.config_manager = init_unified_config_manager()
            log_message("配置管理器初始化完成")
            
            # 加载动态配置
            await self.load_dynamic_config()
            
            log_message("动态MCP启动器初始化完成")
            
        except Exception as e:
            log_message(f"初始化失败: {e}", "ERROR")
            raise
    
    async def load_dynamic_config(self):
        """从统一配置管理器加载动态配置"""
        try:
            # 动态配置现在从统一配置管理器中获取
            self.dynamic_config = {
                "mcp_server_configs": {
                    "mcp_server_mode": {
                        "startup_script": self.config_manager.get("mcp.server.startup_script", "start_mcp_server.py"),
                        "capabilities": self.config_manager.get("mcp.server.capabilities", [])
                    },
                    "fastmcp_proxy_mode": {
                        "startup_script": self.config_manager.get("mcp.proxy.startup_script", "start_mcp_proxy_server.py"),
                        "capabilities": self.config_manager.get("mcp.proxy.capabilities", [])
                    },

                },
                "runtime_config": {
                    "config_check_interval": self.config_manager.get("mcp.service.config_check_interval", 5),
                    "graceful_shutdown_timeout": self.config_manager.get("mcp.service.graceful_shutdown_timeout", 30)
                }
            }
            log_message("从统一配置管理器加载动态配置成功")
        except Exception as e:
            log_message(f"加载动态配置失败: {e}", "ERROR")
            self.dynamic_config = {}
    
    def get_current_mode_from_config(self) -> str:
        """从配置中获取当前模式"""
        try:
            # 优先检查环境变量 MCP_SERVER_MODE
            env_mode = os.environ.get("MCP_SERVER_MODE")
            if env_mode:
                log_message(f"从环境变量获取服务模式: {env_mode}")
                if env_mode == "server":
                    return "mcp_server"
                elif env_mode == "proxy":
                    return "fastmcp_proxy"
                else:
                    log_message(f"不支持的环境变量模式: {env_mode}，使用默认server模式", "WARNING")
                    return "mcp_server"
            
            # 从统一配置管理器获取配置
            mcp_enabled = self.config_manager.get("mcp.enabled", True)
            server_enabled = self.config_manager.get("mcp.server.enabled", True)
            proxy_enabled = self.config_manager.get("mcp.proxy.enabled", True)
            service_mode = self.config_manager.get("mcp.service.mode", "server")
            
            log_message(f"配置状态: mcp_enabled={mcp_enabled}, server_enabled={server_enabled}, proxy_enabled={proxy_enabled}, service_mode={service_mode}")
            
            # MCP服务始终启用，不再支持disabled模式
            
            # 根据配置映射确定模式，只支持server和proxy
            if service_mode == "server" and server_enabled:
                return "mcp_server"
            elif service_mode == "proxy" and proxy_enabled:
                return "fastmcp_proxy"
            elif server_enabled:
                return "mcp_server"
            elif proxy_enabled:
                return "fastmcp_proxy"
            else:
                return "mcp_server"  # 默认模式
                
        except Exception as e:
            log_message(f"获取配置模式失败: {e}", "ERROR")
            return "mcp_server"  # 默认模式
    
    async def start_service_by_mode(self, mode: str):
        """根据模式启动对应的服务"""
        log_message(f"启动服务模式: {mode}")
        
        try:
            if mode == "mcp_server":
                await self.start_mcp_server()
            elif mode == "fastmcp_proxy":
                await self.start_fastmcp_proxy()
            else:
                log_message(f"未知的服务模式: {mode}，使用默认server模式", "WARNING")
                await self.start_mcp_server()  # 默认启动服务端模式
                
        except Exception as e:
            log_message(f"启动服务失败: {e}", "ERROR")
            raise
    
    async def start_mcp_server(self):
        """启动MCP服务端模式"""
        log_message("启动MCP服务端模式...")
        
        try:
            from app.services.mcp import MCPSServer
            
            # 创建并初始化MCP服务器
            self.current_service = MCPSServer()
            await self.current_service.initialize()
            await self.current_service.start()
            
            log_message("✅ MCP服务端启动成功")
            
            # 启动stdio模式
            await self.current_service.run_stdio()
            
        except Exception as e:
            log_message(f"MCP服务端启动失败: {e}", "ERROR")
            raise
    
    async def start_fastmcp_proxy(self):
        """启动FastMCP代理模式"""
        log_message("启动FastMCP代理模式...")
        
        try:
            from app.services.mcp import MCPProxyServer
            
            # 创建并初始化代理服务器
            self.current_service = MCPProxyServer()
            await self.current_service.initialize()
            await self.current_service.start()
            
            log_message("✅ FastMCP代理启动成功")
            
            # 启动stdio模式
            await self.current_service.run_stdio()
            
        except Exception as e:
            log_message(f"FastMCP代理启动失败: {e}", "ERROR")
            raise
    

    
    async def stop_current_service(self):
        """停止当前服务"""
        if self.current_service:
            try:
                log_message("停止当前服务...")
                if hasattr(self.current_service, 'stop'):
                    await self.current_service.stop()
                self.current_service = None
                log_message("当前服务已停止")
            except Exception as e:
                log_message(f"停止服务失败: {e}", "ERROR")
    
    async def check_config_changes(self) -> bool:
        """检查配置是否发生变化"""
        current_time = time.time()
        if current_time - self.last_config_check < self.config_check_interval:
            return False
        
        self.last_config_check = current_time
        
        try:
            new_mode = self.get_current_mode_from_config()
            if new_mode != self.current_mode:
                log_message(f"检测到配置变化: {self.current_mode} -> {new_mode}")
                return True
        except Exception as e:
            log_message(f"检查配置变化失败: {e}", "ERROR")
        
        return False
    
    async def run(self):
        """运行动态启动器"""
        self.running = True
        
        try:
            # 初始化
            await self.initialize()
            
            # 获取初始模式
            self.current_mode = self.get_current_mode_from_config()
            log_message(f"初始服务模式: {self.current_mode}")
            
            # 启动对应的服务
            await self.start_service_by_mode(self.current_mode)
            
        except KeyboardInterrupt:
            log_message("收到中断信号，正在停止服务...")
        except Exception as e:
            log_message(f"运行时错误: {e}", "ERROR")
        finally:
            self.running = False
            await self.stop_current_service()
            log_message("动态MCP启动器已停止")

async def main():
    """主函数"""
    # 清空日志文件
    log_file = os.path.join(backend_dir, 'dynamic_mcp.log')
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("")
    
    launcher = DynamicMCPLauncher()
    await launcher.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)