"""MCP代理服务器 API 路由

提供MCP代理服务器的RESTful API接口，包括：
- 工具管理和状态查询
- 代理服务器控制
- 实时监控数据
- 配置管理
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.utils.response import success_response, error_response
from app.services.mcp import MCPProxyServer
from app.services.tools import ToolRegistry
from app.services.integrations import RequestRouter
from app.services.system import ProcessManager
from app.utils.exceptions import (
    MCPConnectionError,
    MCPTimeoutError,
    ToolNotFoundError,
    MCPServiceError
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/mcp-proxy", tags=["MCP代理服务器"])

# 全局代理服务器实例
_proxy_server: Optional[MCPProxyServer] = None

async def get_proxy_server() -> MCPProxyServer:
    """获取代理服务器实例"""
    global _proxy_server
    if _proxy_server is None:
        _proxy_server = MCPProxyServer()
        await _proxy_server.initialize()
    return _proxy_server


@router.get("/status", response_model=dict, summary="获取代理服务器状态")
async def get_proxy_status():
    """获取代理服务器运行状态"""
    try:
        proxy_server = await get_proxy_server()
        status = proxy_server.get_status()

        return success_response(
            data=status,
            message="获取代理服务器状态成功"
        )
    except Exception as e:
        logger.error(f"获取代理服务器状态失败: {e}")
        return error_response(message="获取代理服务器状态失败", error_code=str(e))


@router.post("/start", response_model=dict, summary="启动代理服务器")
async def start_proxy_server(background_tasks: BackgroundTasks):
    """启动代理服务器"""
    try:
        proxy_server = await get_proxy_server()

        if proxy_server.is_running():
            return success_response(
                data={"status": "already_running"},
                message="代理服务器已在运行"
            )

        # 在后台启动服务器
        background_tasks.add_task(proxy_server.start)

        return success_response(
            data={"status": "starting"},
            message="代理服务器启动中"
        )
    except Exception as e:
        logger.error(f"启动代理服务器失败: {e}")
        return error_response(message="启动代理服务器失败", error_code=str(e))


@router.post("/stop", response_model=dict, summary="停止代理服务器")
async def stop_proxy_server():
    """停止代理服务器"""
    try:
        proxy_server = await get_proxy_server()

        if not proxy_server.is_running():
            return success_response(
                data={"status": "already_stopped"},
                message="代理服务器已停止"
            )

        await proxy_server.stop()

        return success_response(
            data={"status": "stopped"},
            message="代理服务器已停止"
        )
    except Exception as e:
        logger.error(f"停止代理服务器失败: {e}")
        return error_response(message="停止代理服务器失败", error_code=str(e))


@router.post("/restart", response_model=dict, summary="重启代理服务器")
async def restart_proxy_server(background_tasks: BackgroundTasks):
    """重启代理服务器"""
    try:
        proxy_server = await get_proxy_server()

        # 停止服务器
        if proxy_server.is_running():
            await proxy_server.stop()

        # 在后台重新启动
        background_tasks.add_task(proxy_server.start)

        return success_response(
            data={"status": "restarting"},
            message="代理服务器重启中"
        )
    except Exception as e:
        logger.error(f"重启代理服务器失败: {e}")
        return error_response(message="重启代理服务器失败", error_code=str(e))


@router.get("/tools", response_model=dict, summary="获取工具列表")
async def get_tools(
    enabled_only: bool = Query(False, description="仅显示启用的工具")
):
    """获取所有注册的工具列表"""
    try:
        proxy_server = await get_proxy_server()
        tools = await proxy_server.tool_registry.get_all_tools()

        if enabled_only:
            tools = [tool for tool in tools if tool.get('enabled', False)]

        return success_response(
            data={
                "tools": tools,
                "total": len(tools)
            },
            message="获取工具列表成功"
        )
    except Exception as e:
        logger.error(f"获取工具列表失败: {e}")
        return error_response(message="获取工具列表失败", error_code=str(e))


@router.get("/tools/{tool_name}", response_model=dict, summary="获取工具详情")
async def get_tool_info(tool_name: str):
    """获取指定工具的详细信息"""
    try:
        proxy_server = await get_proxy_server()
        tool_config = await proxy_server.tool_registry.get_tool_config(tool_name)

        if not tool_config:
            raise ToolNotFoundError(f"工具不存在: {tool_name}")

        # 获取工具状态
        process_info = await proxy_server.process_manager.get_process_info(tool_name)

        return success_response(
            data={
                "config": tool_config.to_dict() if hasattr(tool_config, 'to_dict') else tool_config,
                "process_info": process_info.to_dict() if process_info and hasattr(process_info, 'to_dict') else process_info
            },
            message="获取工具详情成功"
        )
    except ToolNotFoundError as e:
        return error_response(message=str(e), status_code=404)
    except Exception as e:
        logger.error(f"获取工具详情失败: {e}")
        return error_response(message="获取工具详情失败", error_code=str(e))


@router.post("/tools/{tool_name}/start", response_model=dict, summary="启动工具")
async def start_tool(tool_name: str):
    """启动指定工具"""
    try:
        proxy_server = await get_proxy_server()

        # 检查工具是否存在
        tool_config = await proxy_server.tool_registry.get_tool_config(tool_name)
        if not tool_config:
            raise ToolNotFoundError(f"工具不存在: {tool_name}")

        # 启动工具
        process_id = await proxy_server.process_manager.start_tool_instance(tool_name)

        return success_response(
            data={
                "tool_name": tool_name,
                "process_id": process_id,
                "status": "starting"
            },
            message="工具启动成功"
        )
    except ToolNotFoundError as e:
        return error_response(message=str(e), status_code=404)
    except Exception as e:
        logger.error(f"启动工具失败: {e}")
        return error_response(message="启动工具失败", error_code=str(e))


@router.post("/tools/{tool_name}/stop", response_model=dict, summary="停止工具")
async def stop_tool(tool_name: str):
    """停止指定工具"""
    try:
        proxy_server = await get_proxy_server()

        # 停止工具
        success = await proxy_server.process_manager.stop_tool_instance(tool_name)

        return success_response(
            data={
                "tool_name": tool_name,
                "success": success,
                "status": "stopped" if success else "failed"
            },
            message="工具停止成功" if success else "工具停止失败"
        )
    except Exception as e:
        logger.error(f"停止工具失败: {e}")
        return error_response(message="停止工具失败", error_code=str(e))


@router.post("/tools/{tool_name}/restart", response_model=dict, summary="重启工具")
async def restart_tool(tool_name: str):
    """重启指定工具"""
    try:
        proxy_server = await get_proxy_server()

        # 重启工具
        process_id = await proxy_server.process_manager.restart_tool_instance(tool_name)

        return success_response(
            data={
                "tool_name": tool_name,
                "process_id": process_id,
                "status": "restarting"
            },
            message="工具重启成功"
        )
    except Exception as e:
        logger.error(f"重启工具失败: {e}")
        return error_response(message="重启工具失败", error_code=str(e))


@router.get("/tools/{tool_name}/status", response_model=dict, summary="获取工具状态")
async def get_tool_status(tool_name: str):
    """获取指定工具的运行状态"""
    try:
        proxy_server = await get_proxy_server()

        # 获取进程信息
        process_info = await proxy_server.process_manager.get_process_info(tool_name)

        if not process_info:
            return success_response(
                data={
                    "tool_name": tool_name,
                    "status": "not_running",
                    "process_info": None
                },
                message="工具未运行"
            )

        return success_response(
            data={
                "tool_name": tool_name,
                "status": "running",
                "process_info": process_info.to_dict() if hasattr(process_info, 'to_dict') else process_info
            },
            message="获取工具状态成功"
        )
    except Exception as e:
        logger.error(f"获取工具状态失败: {e}")
        return error_response(message="获取工具状态失败", error_code=str(e))


@router.get("/metrics", response_model=dict, summary="获取代理服务器指标")
async def get_proxy_metrics():
    """获取代理服务器性能指标"""
    try:
        proxy_server = await get_proxy_server()
        metrics = proxy_server.get_metrics()

        return success_response(
            data=metrics,
            message="获取代理服务器指标成功"
        )
    except Exception as e:
        logger.error(f"获取代理服务器指标失败: {e}")
        return error_response(message="获取代理服务器指标失败", error_code=str(e))


@router.get("/config", response_model=dict, summary="获取代理服务器配置")
async def get_proxy_config():
    """获取代理服务器配置"""
    try:
        proxy_server = await get_proxy_server()
        config = await proxy_server.config_manager.get_all_configs()

        return success_response(
            data=config,
            message="获取代理服务器配置成功"
        )
    except Exception as e:
        logger.error(f"获取代理服务器配置失败: {e}")
        return error_response(message="获取代理服务器配置失败", error_code=str(e))


@router.put("/config", response_model=dict, summary="更新代理服务器配置")
async def update_proxy_config(config_data: Dict[str, Any]):
    """更新代理服务器配置"""
    try:
        proxy_server = await get_proxy_server()

        # 更新配置
        for key, value in config_data.items():
            await proxy_server.config_manager.set_config(key, value)

        return success_response(
            data={"updated_keys": list(config_data.keys())},
            message="更新代理服务器配置成功"
        )
    except Exception as e:
        logger.error(f"更新代理服务器配置失败: {e}")
        return error_response(message="更新代理服务器配置失败", error_code=str(e))


@router.get("/logs", response_model=dict, summary="获取代理服务器日志")
async def get_proxy_logs(
    level: Optional[str] = Query(None, description="日志级别过滤"),
    limit: int = Query(100, ge=1, le=1000, description="返回日志条数")
):
    """获取代理服务器日志"""
    try:
        proxy_server = await get_proxy_server()
        logs = proxy_server.get_logs(level=level, limit=limit)

        return success_response(
            data={
                "logs": logs,
                "total": len(logs)
            },
            message="获取代理服务器日志成功"
        )
    except Exception as e:
        logger.error(f"获取代理服务器日志失败: {e}")
        return error_response(message="获取代理服务器日志失败", error_code=str(e))


@router.post("/tools/discover", response_model=dict, summary="发现新工具")
async def discover_tools():
    """发现和注册新的MCP工具"""
    try:
        proxy_server = await get_proxy_server()
        discovered_tools = await proxy_server.tool_registry.discover_tools()

        return success_response(
            data={
                "discovered_tools": discovered_tools,
                "count": len(discovered_tools)
            },
            message="工具发现完成"
        )
    except Exception as e:
        logger.error(f"工具发现失败: {e}")
        return error_response(message="工具发现失败", error_code=str(e))


@router.post("/tools/reload", response_model=dict, summary="重新加载工具配置")
async def reload_tools():
    """重新加载工具配置"""
    try:
        proxy_server = await get_proxy_server()
        await proxy_server.tool_registry.reload_tools()

        return success_response(
            data={"status": "reloaded"},
            message="工具配置重新加载成功"
        )
    except Exception as e:
        logger.error(f"重新加载工具配置失败: {e}")
        return error_response(message="重新加载工具配置失败", error_code=str(e))
