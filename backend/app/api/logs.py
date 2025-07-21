"""日志管理 API 路由"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.schemas.log import (
    SystemLogResponse,
    OperationLogResponse,
    MCPLogResponse,
    LogQueryParams,
    LogStatsResponse,
    LogCleanupParams,
    PaginatedResponse,
)
from app.services.system import LogService
from app.utils.response import success_response, error_response
from app.utils.pagination import simple_paginate as paginate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/logs", tags=["日志管理"])

# 系统日志
@router.get("/system", response_model=dict, summary="获取系统日志")
async def get_system_logs(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(50, ge=1, le=200, description="每页大小"),
    level: Optional[str] = Query(None, description="日志级别"),
    category: Optional[str] = Query(None, description="日志分类"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db)
):
    """获取系统日志"""
    try:
        log_service = LogService(db)

        # 构建过滤条件
        filters = {}
        if level:
            filters['level'] = level
        if category:
            filters['category'] = category
        if start_time:
            filters['start_time'] = start_time
        if end_time:
            filters['end_time'] = end_time
        if search:
            filters['search'] = search

        # 获取日志列表
        logs, total = log_service.get_system_logs(
            page=page,
            size=size,
            filters=filters
        )

        # 分页信息
        pagination = paginate(total, page, size)

        return success_response(
            data={
                "items": [log.to_dict() for log in logs],
                "pagination": pagination
            },
            message="获取系统日志成功"
        )
    except Exception as e:
        logger.error(f"获取系统日志失败: {e}")
        return error_response(message="获取系统日志失败", error_code=str(e))

@router.get("/system/{log_id}", response_model=dict, summary="获取系统日志详情")
async def get_system_log(
    log_id: int,
    db: Session = Depends(get_db)
):
    """获取系统日志详情"""
    try:
        log_service = LogService(db)
        log = log_service.get_system_log(log_id)

        if not log:
            raise HTTPException(status_code=404, detail="日志不存在")

        return success_response(
            data=log.to_dict(),
            message="获取系统日志详情成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取系统日志详情失败: {e}")
        return error_response(message="获取系统日志详情失败", error_code=str(e))

# 操作日志
@router.get("/operations", response_model=dict, summary="获取操作日志")
async def get_operation_logs(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(50, ge=1, le=200, description="每页大小"),
    action: Optional[str] = Query(None, description="操作类型"),
    status: Optional[str] = Query(None, description="操作状态"),
    resource_type: Optional[str] = Query(None, description="资源类型"),
    resource_id: Optional[str] = Query(None, description="资源ID"),
    user_id: Optional[str] = Query(None, description="用户ID"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db)
):
    """获取操作日志"""
    try:
        log_service = LogService(db)

        # 构建过滤条件
        filters = {}
        if action:
            filters['action'] = action
        if status:
            filters['status'] = status
        if resource_type:
            filters['resource_type'] = resource_type
        if resource_id:
            filters['resource_id'] = resource_id
        if user_id:
            filters['user_id'] = user_id
        if start_time:
            filters['start_time'] = start_time
        if end_time:
            filters['end_time'] = end_time
        if search:
            filters['search'] = search

        # 获取日志列表
        logs, total = log_service.get_operation_logs(
            page=page,
            size=size,
            filters=filters
        )

        # 分页信息
        pagination = paginate(total, page, size)

        return success_response(
            data={
                "items": [log.to_dict() for log in logs],
                "pagination": pagination
            },
            message="获取操作日志成功"
        )
    except Exception as e:
        logger.error(f"获取操作日志失败: {e}")
        return error_response(message="获取操作日志失败", error_code=str(e))

@router.get("/operations/{log_id}", response_model=dict, summary="获取操作日志详情")
async def get_operation_log(
    log_id: int,
    db: Session = Depends(get_db)
):
    """获取操作日志详情"""
    try:
        log_service = LogService(db)
        log = log_service.get_operation_log(log_id)

        if not log:
            raise HTTPException(status_code=404, detail="日志不存在")

        return success_response(
            data=log.to_dict(),
            message="获取操作日志详情成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取操作日志详情失败: {e}")
        return error_response(message="获取操作日志详情失败", error_code=str(e))

# MCP 协议日志
@router.get("/mcp", response_model=dict, summary="获取MCP协议日志")
async def get_mcp_logs(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(50, ge=1, le=200, description="每页大小"),
    tool_id: Optional[int] = Query(None, description="工具ID"),
    direction: Optional[str] = Query(None, description="消息方向"),
    method: Optional[str] = Query(None, description="方法名"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db)
):
    """获取MCP协议日志"""
    try:
        log_service = LogService(db)

        # 构建过滤条件
        filters = {}
        if tool_id:
            filters['tool_id'] = tool_id
        if direction:
            filters['direction'] = direction
        if method:
            filters['method'] = method
        if start_time:
            filters['start_time'] = start_time
        if end_time:
            filters['end_time'] = end_time
        if search:
            filters['search'] = search

        # 获取日志列表
        logs, total = log_service.get_mcp_logs(
            page=page,
            size=size,
            filters=filters
        )

        # 分页信息
        pagination = paginate(total, page, size)

        return success_response(
            data={
                "items": [log.to_dict() for log in logs],
                "pagination": pagination
            },
            message="获取MCP协议日志成功"
        )
    except Exception as e:
        logger.error(f"获取MCP协议日志失败: {e}")
        return error_response(message="获取MCP协议日志失败", error_code=str(e))

@router.get("/mcp/{log_id}", response_model=dict, summary="获取MCP协议日志详情")
async def get_mcp_log(
    log_id: int,
    db: Session = Depends(get_db)
):
    """获取MCP协议日志详情"""
    try:
        log_service = LogService(db)
        log = log_service.get_mcp_log(log_id)

        if not log:
            raise HTTPException(status_code=404, detail="日志不存在")

        return success_response(
            data=log.to_dict(),
            message="获取MCP协议日志详情成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取MCP协议日志详情失败: {e}")
        return error_response(message="获取MCP协议日志详情失败", error_code=str(e))

# 日志统计
@router.get("/stats", response_model=dict, summary="获取日志统计")
async def get_log_stats(
    period: str = Query("24h", description="统计周期"),
    log_type: Optional[str] = Query(None, description="日志类型"),
    db: Session = Depends(get_db)
):
    """获取日志统计"""
    try:
        log_service = LogService(db)

        # 解析时间周期
        if period == "1h":
            start_time = datetime.now() - timedelta(hours=1)
        elif period == "24h":
            start_time = datetime.now() - timedelta(days=1)
        elif period == "7d":
            start_time = datetime.now() - timedelta(days=7)
        elif period == "30d":
            start_time = datetime.now() - timedelta(days=30)
        else:
            start_time = datetime.now() - timedelta(days=1)

        # 获取统计数据
        stats = log_service.get_log_statistics(
            period=period
        )

        return success_response(
            data=stats,
            message="获取日志统计成功"
        )
    except Exception as e:
        logger.error(f"获取日志统计失败: {e}")
        return error_response(message="获取日志统计失败", error_code=str(e))

@router.get("/stats/summary", response_model=dict, summary="获取日志汇总统计")
async def get_log_summary(
    db: Session = Depends(get_db)
):
    """获取日志汇总统计"""
    try:
        log_service = LogService(db)
        summary = log_service.get_summary_statistics()

        return success_response(
            data=summary,
            message="获取日志汇总统计成功"
        )
    except Exception as e:
        logger.error(f"获取日志汇总统计失败: {e}")
        return error_response(message="获取日志汇总统计失败", error_code=str(e))

# 日志管理
@router.post("/cleanup", response_model=dict, summary="清理日志")
async def cleanup_logs(
    cleanup_params: LogCleanupParams,
    db: Session = Depends(get_db)
):
    """清理日志"""
    try:
        log_service = LogService(db)
        result = log_service.cleanup_logs(cleanup_params)

        return success_response(
            data=result,
            message="日志清理完成"
        )
    except Exception as e:
        logger.error(f"清理日志失败: {e}")
        return error_response(message="清理日志失败", error_code=str(e))

@router.post("/export", response_model=dict, summary="导出日志")
async def export_logs(
    log_type: str = Query(..., description="日志类型"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    format: str = Query("csv", description="导出格式"),
    db: Session = Depends(get_db)
):
    """导出日志"""
    try:
        log_service = LogService(db)

        # 构建过滤条件
        filters = {}
        if start_time:
            filters['start_time'] = start_time
        if end_time:
            filters['end_time'] = end_time

        # 导出日志
        export_result = log_service.export_logs(
            log_type=log_type,
            filters=filters,
            format=format
        )

        return success_response(
            data=export_result,
            message="日志导出成功"
        )
    except Exception as e:
        logger.error(f"导出日志失败: {e}")
        return error_response(message="导出日志失败", error_code=str(e))

# 实时日志
@router.get("/realtime", response_model=dict, summary="获取实时日志")
async def get_realtime_logs(
    log_type: str = Query("system", description="日志类型"),
    level: Optional[str] = Query(None, description="日志级别"),
    limit: int = Query(100, ge=1, le=500, description="限制数量"),
    db: Session = Depends(get_db)
):
    """获取实时日志"""
    try:
        log_service = LogService(db)

        # 获取最新日志
        logs = log_service.get_realtime_logs(
            log_type=log_type,
            level=level,
            limit=limit
        )

        return success_response(
            data=[log.to_dict() for log in logs],
            message="获取实时日志成功"
        )
    except Exception as e:
        logger.error(f"获取实时日志失败: {e}")
        return error_response(message="获取实时日志失败", error_code=str(e))

# 日志搜索
@router.get("/search", response_model=dict, summary="搜索日志")
async def search_logs(
    query: str = Query(..., description="搜索查询"),
    log_type: Optional[str] = Query(None, description="日志类型"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(50, ge=1, le=200, description="每页大小"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    db: Session = Depends(get_db)
):
    """搜索日志"""
    try:
        log_service = LogService(db)

        # 构建过滤条件
        filters = {
            'search': query
        }
        if start_time:
            filters['start_time'] = start_time
        if end_time:
            filters['end_time'] = end_time

        # 搜索日志
        logs, total = log_service.search_logs(
            log_type=log_type,
            filters=filters,
            page=page,
            size=size
        )

        # 分页信息
        pagination = paginate(total, page, size)

        return success_response(
            data={
                "items": [log.to_dict() for log in logs],
                "pagination": pagination
            },
            message="搜索日志成功"
        )
    except Exception as e:
        logger.error(f"搜索日志失败: {e}")
        return error_response(message="搜索日志失败", error_code=str(e))
