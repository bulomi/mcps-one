"""系统监控 API 路由"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
import psutil
import time
from datetime import datetime, timedelta

from app.core.database import get_db
from app.utils.response import success_response, error_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/monitor", tags=["系统监控"])


@router.get("/system", response_model=dict, summary="获取系统信息")
async def get_system_info():
    """获取系统信息"""
    try:
        # 获取CPU信息
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # 获取内存信息
        memory = psutil.virtual_memory()
        
        # 获取磁盘信息
        disk = psutil.disk_usage('/')
        
        # 获取网络信息
        network = psutil.net_io_counters()
        
        return success_response(
            data={
                "cpu": {
                    "usage_percent": cpu_percent,
                    "core_count": cpu_count
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "usage_percent": memory.percent
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "usage_percent": (disk.used / disk.total) * 100
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                "timestamp": datetime.now().isoformat()
            },
            message="获取系统信息成功"
        )
    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")
        return error_response(message="获取系统信息失败", error_code=str(e))


@router.get("/processes", response_model=dict, summary="获取进程信息")
async def get_processes(
    limit: int = Query(10, ge=1, le=100, description="返回进程数量")
):
    """获取进程信息"""
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # 按CPU使用率排序
        processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
        
        return success_response(
            data={
                "processes": processes[:limit],
                "total_processes": len(processes)
            },
            message="获取进程信息成功"
        )
    except Exception as e:
        logger.error(f"获取进程信息失败: {e}")
        return error_response(message="获取进程信息失败", error_code=str(e))


@router.get("/stats", response_model=dict, summary="获取监控统计")
async def get_monitor_stats(
    db: Session = Depends(get_db)
):
    """获取监控统计"""
    try:
        # TODO: 从数据库获取统计信息
        return success_response(
            data={
                "tools": {
                    "total": 0,
                    "active": 0,
                    "inactive": 0,
                    "error": 0
                },
                "proxies": {
                    "total": 0,
                    "active": 0,
                    "inactive": 0
                },
                "uptime": time.time(),
                "last_updated": datetime.now().isoformat()
            },
            message="获取监控统计成功"
        )
    except Exception as e:
        logger.error(f"获取监控统计失败: {e}")
        return error_response(message="获取监控统计失败", error_code=str(e))