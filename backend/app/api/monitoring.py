"""监控和健康检查API模块

提供系统监控、健康检查和可观测性功能，包括：
- 健康检查端点
- 性能指标收集
- 系统状态监控
- Prometheus指标导出
"""

import asyncio
import time
import psutil
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Depends, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
import json
import logging

from ..services.mcp.mcp_proxy_server import MCPProxyServer
from ..services.tools.tool_registry import ToolRegistry
from ..services.integrations.request_router import RequestRouter
from ..services.system.process_manager import ProcessManager
from ..core.unified_config_manager import UnifiedConfigManager as ConfigManager
from ..core.dependencies import get_mcp_proxy_server
from ..utils.exceptions import MCPServiceError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/monitoring", tags=["monitoring"])


class HealthStatus(BaseModel):
    """健康状态模型"""
    status: str  # healthy, unhealthy, degraded
    timestamp: datetime
    uptime_seconds: float
    version: str
    components: Dict[str, Dict[str, Any]]
    checks: List[Dict[str, Any]]


class SystemMetrics(BaseModel):
    """系统指标模型"""
    timestamp: datetime
    cpu: Dict[str, float]
    memory: Dict[str, float]
    disk: Dict[str, float]
    network: Dict[str, int]
    process: Dict[str, Any]


class ProxyMetrics(BaseModel):
    """代理服务指标模型"""
    timestamp: datetime
    server_info: Dict[str, Any]
    request_metrics: Dict[str, Any]
    tool_metrics: Dict[str, Any]
    cache_metrics: Dict[str, Any]
    error_metrics: Dict[str, Any]


@router.get("/health", response_model=HealthStatus)
async def health_check(
    proxy_server: MCPProxyServer = Depends(get_mcp_proxy_server)
) -> HealthStatus:
    """系统健康检查

    返回系统整体健康状态和各组件状态。
    """
    try:
        start_time = time.time()

        # 获取系统基本信息
        uptime = time.time() - (proxy_server._start_time.timestamp() if hasattr(proxy_server, '_start_time') and proxy_server._start_time else time.time())

        # 检查各组件状态
        components = {}
        checks = []
        overall_status = "healthy"

        # 检查代理服务器
        proxy_status = await _check_proxy_server(proxy_server)
        components["proxy_server"] = proxy_status
        checks.append({
            "name": "proxy_server",
            "status": proxy_status["status"],
            "message": proxy_status.get("message", "")
        })

        if proxy_status["status"] != "healthy":
            overall_status = "degraded"

        # 检查工具注册中心
        if hasattr(proxy_server, 'tool_registry'):
            registry_status = await _check_tool_registry(proxy_server.tool_registry)
            components["tool_registry"] = registry_status
            checks.append({
                "name": "tool_registry",
                "status": registry_status["status"],
                "message": registry_status.get("message", "")
            })

            if registry_status["status"] != "healthy":
                overall_status = "degraded"

        # 检查系统资源
        system_status = await _check_system_resources()
        components["system"] = system_status
        checks.append({
            "name": "system_resources",
            "status": system_status["status"],
            "message": system_status.get("message", "")
        })

        if system_status["status"] == "unhealthy":
            overall_status = "unhealthy"
        elif system_status["status"] == "degraded" and overall_status == "healthy":
            overall_status = "degraded"

        # 添加响应时间检查
        response_time = time.time() - start_time
        checks.append({
            "name": "response_time",
            "status": "healthy" if response_time < 1.0 else "degraded",
            "message": f"Health check completed in {response_time:.3f}s",
            "response_time_ms": response_time * 1000
        })

        return HealthStatus(
            status=overall_status,
            timestamp=datetime.now(),
            uptime_seconds=uptime,
            version="1.0.0",
            components=components,
            checks=checks
        )

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/health/live")
async def liveness_probe() -> Dict[str, str]:
    """存活性探针

    简单的存活性检查，用于容器编排系统。
    """
    return {"status": "alive", "timestamp": datetime.now().isoformat()}


@router.get("/health/ready")
async def readiness_probe(
    proxy_server: MCPProxyServer = Depends(get_mcp_proxy_server)
) -> Dict[str, str]:
    """就绪性探针

    检查服务是否准备好接收流量，用于容器编排系统。
    """
    try:
        if hasattr(proxy_server, 'is_running') and not proxy_server.is_running():
            raise HTTPException(status_code=503, detail="Proxy server not running")

        # 检查关键组件是否就绪
        active_tools_count = 0
        if hasattr(proxy_server, 'tool_registry'):
            active_tools = await proxy_server.tool_registry.get_active_tools()
            active_tools_count = len(active_tools)

        return {
            "status": "ready",
            "timestamp": datetime.now().isoformat(),
            "active_tools": active_tools_count
        }

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service not ready: {str(e)}"
        )


@router.get("/metrics/system", response_model=SystemMetrics)
async def get_system_metrics() -> SystemMetrics:
    """获取系统指标

    返回CPU、内存、磁盘、网络等系统资源使用情况。
    """
    try:
        # CPU指标
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()

        # 内存指标
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()

        # 磁盘指标
        disk = psutil.disk_usage('/')

        # 网络指标
        network = psutil.net_io_counters()

        # 进程指标
        process = psutil.Process()
        process_memory = process.memory_info()

        return SystemMetrics(
            timestamp=datetime.now(),
            cpu={
                "percent": cpu_percent,
                "count": cpu_count,
                "frequency_mhz": cpu_freq.current if cpu_freq else 0
            },
            memory={
                "total_mb": memory.total / 1024 / 1024,
                "available_mb": memory.available / 1024 / 1024,
                "used_mb": memory.used / 1024 / 1024,
                "percent": memory.percent,
                "swap_total_mb": swap.total / 1024 / 1024,
                "swap_used_mb": swap.used / 1024 / 1024,
                "swap_percent": swap.percent
            },
            disk={
                "total_gb": disk.total / 1024 / 1024 / 1024,
                "used_gb": disk.used / 1024 / 1024 / 1024,
                "free_gb": disk.free / 1024 / 1024 / 1024,
                "percent": (disk.used / disk.total) * 100
            },
            network={
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            },
            process={
                "pid": process.pid,
                "memory_rss_mb": process_memory.rss / 1024 / 1024,
                "memory_vms_mb": process_memory.vms / 1024 / 1024,
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads(),
                "create_time": datetime.fromtimestamp(process.create_time()).isoformat()
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system metrics: {str(e)}"
        )


@router.get("/metrics/prometheus", response_class=PlainTextResponse)
async def get_prometheus_metrics() -> str:
    """获取Prometheus格式的指标

    返回符合Prometheus格式的指标数据。
    """
    try:
        system_metrics = await get_system_metrics()

        prometheus_metrics = []

        # 系统指标
        prometheus_metrics.extend([
            f"# HELP system_cpu_percent CPU usage percentage",
            f"# TYPE system_cpu_percent gauge",
            f"system_cpu_percent {system_metrics.cpu['percent']}",
            "",
            f"# HELP system_memory_percent Memory usage percentage",
            f"# TYPE system_memory_percent gauge",
            f"system_memory_percent {system_metrics.memory['percent']}",
            "",
            f"# HELP system_disk_percent Disk usage percentage",
            f"# TYPE system_disk_percent gauge",
            f"system_disk_percent {system_metrics.disk['percent']}",
            "",
            f"# HELP process_memory_rss_bytes Process RSS memory in bytes",
            f"# TYPE process_memory_rss_bytes gauge",
            f"process_memory_rss_bytes {system_metrics.process['memory_rss_mb'] * 1024 * 1024}",
            ""
        ])

        return "\n".join(prometheus_metrics)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate Prometheus metrics: {str(e)}"
        )


@router.get("/status")
async def get_status(
    proxy_server: MCPProxyServer = Depends(get_mcp_proxy_server)
) -> Dict[str, Any]:
    """获取服务状态概览

    返回服务的整体状态概览信息。
    """
    try:
        status = {}
        if hasattr(proxy_server, 'get_status'):
            status = proxy_server.get_status()

        # 添加额外的状态信息
        active_tools_count = 0
        active_tools = []
        if hasattr(proxy_server, 'tool_registry'):
            active_tools = await proxy_server.tool_registry.get_active_tools()
            active_tools_count = len(active_tools)

        status.update({
            "active_tools_count": active_tools_count,
            "active_tools": active_tools,
            "timestamp": datetime.now().isoformat()
        })

        return status

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get status: {str(e)}"
        )


# 保留原有的前端监控数据接收功能
@router.post("/performance")
async def receive_performance_data(request: Request):
    """接收前端性能监控数据"""
    try:
        # 从请求体获取数据
        body = await request.body()
        if not body:
            return {"status": "error", "message": "No data received"}

        data = json.loads(body.decode('utf-8'))

        # 记录性能数据到日志
        logger.info(f"Performance data received: {data}")

        # 这里可以添加将数据存储到数据库的逻辑
        # 目前只是简单记录日志

        return {"status": "success", "message": "Performance data received"}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in performance data: {e}")
        return {"status": "error", "message": "Invalid JSON format"}
    except Exception as e:
        logger.error(f"Error processing performance data: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/slow-requests")
async def receive_slow_request_data(request: Request):
    """接收前端慢请求监控数据"""
    try:
        # 从请求体获取数据
        body = await request.body()
        if not body:
            return {"status": "error", "message": "No data received"}

        data = json.loads(body.decode('utf-8'))

        # 记录慢请求数据到日志
        logger.info(f"Slow request data received: {data}")

        # 这里可以添加将数据存储到数据库的逻辑
        # 目前只是简单记录日志

        return {"status": "success", "message": "Slow request data received"}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in slow request data: {e}")
        return {"status": "error", "message": "Invalid JSON format"}
    except Exception as e:
        logger.error(f"Error processing slow request data: {e}")
        return {"status": "error", "message": str(e)}


# 辅助函数

async def _check_proxy_server(proxy_server: MCPProxyServer) -> Dict[str, Any]:
    """检查代理服务器状态"""
    try:
        if hasattr(proxy_server, 'is_running') and not proxy_server.is_running():
            return {
                "status": "unhealthy",
                "message": "Proxy server is not running"
            }

        status = {}
        if hasattr(proxy_server, 'get_status'):
            status = proxy_server.get_status()

        return {
            "status": "healthy",
            "message": "Proxy server is running normally",
            "details": status
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Proxy server check failed: {str(e)}"
        }


async def _check_tool_registry(tool_registry: ToolRegistry) -> Dict[str, Any]:
    """检查工具注册中心状态"""
    try:
        active_tools = await tool_registry.get_active_tools()

        return {
            "status": "healthy",
            "message": f"Tool registry is healthy with {len(active_tools)} active tools",
            "active_tools_count": len(active_tools)
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Tool registry check failed: {str(e)}"
        }


async def _check_system_resources() -> Dict[str, Any]:
    """检查系统资源状态"""
    try:
        # CPU检查
        cpu_percent = psutil.cpu_percent(interval=1)

        # 内存检查
        memory = psutil.virtual_memory()

        # 磁盘检查
        disk = psutil.disk_usage('/')

        status = "healthy"
        messages = []

        # CPU阈值检查
        if cpu_percent > 90:
            status = "unhealthy"
            messages.append(f"High CPU usage: {cpu_percent:.1f}%")
        elif cpu_percent > 70:
            status = "degraded"
            messages.append(f"Elevated CPU usage: {cpu_percent:.1f}%")

        # 内存阈值检查
        if memory.percent > 90:
            status = "unhealthy"
            messages.append(f"High memory usage: {memory.percent:.1f}%")
        elif memory.percent > 80:
            if status == "healthy":
                status = "degraded"
            messages.append(f"Elevated memory usage: {memory.percent:.1f}%")

        # 磁盘阈值检查
        disk_percent = (disk.used / disk.total) * 100
        if disk_percent > 95:
            status = "unhealthy"
            messages.append(f"High disk usage: {disk_percent:.1f}%")
        elif disk_percent > 85:
            if status == "healthy":
                status = "degraded"
            messages.append(f"Elevated disk usage: {disk_percent:.1f}%")

        message = "; ".join(messages) if messages else "System resources are normal"

        return {
            "status": status,
            "message": message,
            "details": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk_percent
            }
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"System resource check failed: {str(e)}"
        }
