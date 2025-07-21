"""MCP统一服务管理API

提供MCP服务的统一管理接口，包括：
- 服务模式切换
- 服务状态查询
- 配置管理
- 实时监控
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from ..services.mcp.mcp_unified_service import unified_service, ServiceMode
from ..utils.exceptions import MCPServiceError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp-unified", tags=["MCP统一服务"])

# 请求模型
class ServiceModeRequest(BaseModel):
    """服务模式切换请求"""
    enable_server: bool = Field(description="是否启用MCP服务端")
    enable_proxy: bool = Field(description="是否启用HTTP代理")

class ServiceStartRequest(BaseModel):
    """服务启动请求"""
    mode: Optional[str] = Field(default=None, description="服务模式 (proxy, server, both)")

class ServiceStopRequest(BaseModel):
    """服务停止请求"""
    mode: Optional[str] = Field(default=None, description="要停止的服务模式 (proxy, server, both)")

class ToolCallRequest(BaseModel):
    """工具调用请求"""
    tool_name: str = Field(description="工具名称")
    arguments: Dict[str, Any] = Field(description="工具参数")
    source: str = Field(default="auto", description="调用源 (proxy, server, auto)")

# 响应模型
class ServiceStatusResponse(BaseModel):
    """服务状态响应"""
    mode: str = Field(description="当前服务模式")
    proxy_running: bool = Field(description="代理服务是否运行")
    server_running: bool = Field(description="服务端是否运行")
    proxy_tools_count: int = Field(description="代理工具数量")
    server_connections: int = Field(description="服务端连接数")
    uptime: float = Field(description="运行时间(秒)")
    last_error: Optional[str] = Field(description="最后错误信息")
    timestamp: datetime = Field(description="状态时间戳")

class ServiceMetricsResponse(BaseModel):
    """服务指标响应"""
    total_tool_calls: int = Field(description="总工具调用次数")
    successful_calls: int = Field(description="成功调用次数")
    failed_calls: int = Field(description="失败调用次数")
    average_response_time: float = Field(description="平均响应时间(毫秒)")
    active_connections: int = Field(description="活跃连接数")
    memory_usage: float = Field(description="内存使用量(MB)")
    cpu_usage: float = Field(description="CPU使用率(%)")

class ToolInfo(BaseModel):
    """工具信息"""
    name: str = Field(description="工具名称")
    description: str = Field(description="工具描述")
    source: str = Field(description="工具来源")
    available_via: List[str] = Field(description="可用方式")
    status: str = Field(description="工具状态")

# API端点
@router.get("/service/status", response_model=ServiceStatusResponse)
async def get_service_status():
    """获取服务状态"""
    try:
        status = await unified_service.get_service_status()
        return ServiceStatusResponse(
            mode=status.mode.value,
            proxy_running=status.proxy_running,
            server_running=status.server_running,
            proxy_tools_count=status.proxy_tools_count,
            server_connections=status.server_connections,
            uptime=status.uptime,
            last_error=status.last_error,
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"获取服务状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取服务状态失败: {str(e)}")

@router.post("/service/start")
async def start_service(request: ServiceStartRequest, background_tasks: BackgroundTasks):
    """启动服务"""
    try:
        if unified_service.is_running:
            return {"message": "服务已在运行中", "status": "already_running"}

        # 在后台启动服务以避免阻塞
        background_tasks.add_task(unified_service.start_service, request.mode)

        return {
            "message": "服务启动请求已提交",
            "status": "starting",
            "mode": request.mode or unified_service.mode.value
        }
    except MCPServiceError as e:
        logger.error(f"启动服务失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"启动服务时发生未知错误: {e}")
        raise HTTPException(status_code=500, detail=f"启动服务失败: {str(e)}")

@router.post("/service/stop")
async def stop_service(request: ServiceStopRequest, background_tasks: BackgroundTasks):
    """停止服务"""
    try:
        if not unified_service.is_running:
            return {"message": "服务未在运行", "status": "not_running"}

        # 在后台停止服务以避免阻塞
        background_tasks.add_task(unified_service.stop_service, request.mode)

        return {
            "message": "服务停止请求已提交",
            "status": "stopping",
            "mode": request.mode or "both"
        }
    except MCPServiceError as e:
        logger.error(f"停止服务失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"停止服务时发生未知错误: {e}")
        raise HTTPException(status_code=500, detail=f"停止服务失败: {str(e)}")

@router.post("/service/switch-mode")
async def switch_service_mode(request: ServiceModeRequest, background_tasks: BackgroundTasks):
    """切换服务模式"""
    try:
        # 在后台切换模式以避免阻塞
        background_tasks.add_task(
            unified_service.switch_mode,
            request.enable_server,
            request.enable_proxy
        )

        # 确定新模式
        if request.enable_server and request.enable_proxy:
            new_mode = "both"
        elif request.enable_server:
            new_mode = "server"
        elif request.enable_proxy:
            new_mode = "proxy"
        else:
            new_mode = "disabled"

        return {
            "message": "服务模式切换请求已提交",
            "status": "switching",
            "old_mode": unified_service.mode.value,
            "new_mode": new_mode
        }
    except MCPServiceError as e:
        logger.error(f"切换服务模式失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"切换服务模式时发生未知错误: {e}")
        raise HTTPException(status_code=500, detail=f"切换服务模式失败: {str(e)}")

@router.post("/service/reload-config")
async def reload_configuration(background_tasks: BackgroundTasks):
    """重新加载配置"""
    try:
        # 在后台重新加载配置以避免阻塞
        background_tasks.add_task(unified_service.reload_configuration)

        return {
            "message": "配置重新加载请求已提交",
            "status": "reloading"
        }
    except MCPServiceError as e:
        logger.error(f"重新加载配置失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"重新加载配置时发生未知错误: {e}")
        raise HTTPException(status_code=500, detail=f"重新加载配置失败: {str(e)}")

@router.get("/service/metrics", response_model=ServiceMetricsResponse)
async def get_service_metrics():
    """获取服务指标"""
    try:
        # TODO: 实现真实的指标收集
        # 这里返回模拟数据，实际实现需要从服务中收集真实指标
        import psutil
        import os

        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        cpu_percent = process.cpu_percent()

        return ServiceMetricsResponse(
            total_tool_calls=0,  # TODO: 从统计中获取
            successful_calls=0,  # TODO: 从统计中获取
            failed_calls=0,      # TODO: 从统计中获取
            average_response_time=0.0,  # TODO: 从统计中获取
            active_connections=0,  # TODO: 从服务中获取
            memory_usage=memory_info.rss / 1024 / 1024,  # 转换为MB
            cpu_usage=cpu_percent
        )
    except Exception as e:
        logger.error(f"获取服务指标失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取服务指标失败: {str(e)}")

@router.get("/tools", response_model=List[ToolInfo])
async def get_available_tools():
    """获取可用工具列表"""
    try:
        tools = await unified_service.get_available_tools()
        return [
            ToolInfo(
                name=tool.get("name", ""),
                description=tool.get("description", ""),
                source=tool.get("source", "unknown"),
                available_via=tool.get("available_via", []),
                status=tool.get("status", "unknown")
            )
            for tool in tools
        ]
    except Exception as e:
        logger.error(f"获取工具列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取工具列表失败: {str(e)}")

@router.post("/tools/call")
async def call_tool(request: ToolCallRequest):
    """调用工具"""
    try:
        result = await unified_service.call_tool(
            tool_name=request.tool_name,
            arguments=request.arguments,
            source=request.source
        )

        return {
            "success": True,
            "result": result,
            "tool_name": request.tool_name,
            "source": request.source,
            "timestamp": datetime.now().isoformat()
        }
    except MCPServiceError as e:
        logger.error(f"调用工具失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"调用工具时发生未知错误: {e}")
        raise HTTPException(status_code=500, detail=f"调用工具失败: {str(e)}")

@router.get("/health")
async def health_check():
    """MCP服务健康检查"""
    try:
        status = await unified_service.get_service_status()

        # 判断服务健康状态
        is_healthy = True
        health_issues = []

        if unified_service.mode != ServiceMode.DISABLED:
            if unified_service.mode in [ServiceMode.PROXY_ONLY, ServiceMode.BOTH]:
                if not status.proxy_running:
                    is_healthy = False
                    health_issues.append("代理服务未运行")

            if unified_service.mode in [ServiceMode.SERVER_ONLY, ServiceMode.BOTH]:
                if not status.server_running:
                    is_healthy = False
                    health_issues.append("服务端未运行")

        if status.last_error:
            is_healthy = False
            health_issues.append(f"最近错误: {status.last_error}")

        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "mode": status.mode.value,
            "uptime": status.uptime,
            "issues": health_issues,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"MCP服务健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
