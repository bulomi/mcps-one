"""系统管理 API 路由"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
import asyncio

from app.core.database import get_db
from app.schemas.system import (
    SystemConfigCreate,
    SystemConfigUpdate,
    SystemConfigResponse,
    SystemInfoResponse,
    SystemStatusResponse,
    SystemOperationCreate,
    ConfigBatchUpdate,
    HealthCheckResponse,
)
from app.services.system_service import SystemService

from app.utils.response import success_response, error_response
from app.utils.pagination import simple_paginate as paginate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/system", tags=["系统管理"])

# 系统配置管理
@router.get("/config", response_model=dict, summary="获取系统配置列表")
async def get_system_configs(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(50, ge=1, le=200, description="每页大小"),
    category: Optional[str] = Query(None, description="配置分类"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db)
):
    """获取系统配置列表"""
    try:
        system_service = SystemService(db)
        
        # 构建过滤条件
        filters = {}
        if category:
            filters['category'] = category
        if search:
            filters['search'] = search
        
        # 获取配置列表
        configs, total = system_service.get_configs(
            page=page,
            size=size,
            filters=filters
        )
        
        # 分页信息
        pagination = paginate(total, page, size)
        
        return success_response(
            data={
                "items": [config.to_dict() for config in configs],
                "pagination": pagination
            },
            message="获取系统配置列表成功"
        )
    except Exception as e:
        logger.error(f"获取系统配置列表失败: {e}")
        return error_response(message="获取系统配置列表失败", error_code=str(e))

@router.get("/config/{key}", response_model=dict, summary="获取系统配置")
async def get_system_config(
    key: str,
    db: Session = Depends(get_db)
):
    """获取系统配置"""
    try:
        system_service = SystemService(db)
        config = system_service.get_config(key)
        
        if not config:
            raise HTTPException(status_code=404, detail="配置项不存在")
        
        return success_response(
            data=config.to_dict(),
            message="获取系统配置成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取系统配置失败: {e}")
        return error_response(message="获取系统配置失败", error_code=str(e))

@router.post("/config", response_model=dict, summary="创建系统配置")
async def create_system_config(
    config_data: SystemConfigCreate,
    db: Session = Depends(get_db)
):
    """创建系统配置"""
    try:
        system_service = SystemService(db)
        
        # 检查配置键是否已存在
        if system_service.get_config(config_data.key):
            raise HTTPException(status_code=400, detail="配置键已存在")
        
        # 创建配置
        config = system_service.create_config(config_data)
        
        return success_response(
            data=config.to_dict(),
            message="创建系统配置成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建系统配置失败: {e}")
        return error_response(message="创建系统配置失败", error_code=str(e))

@router.put("/config/{key}", response_model=dict, summary="更新系统配置")
async def update_system_config(
    key: str,
    config_data: SystemConfigUpdate,
    db: Session = Depends(get_db)
):
    """更新系统配置"""
    try:
        system_service = SystemService(db)
        
        # 检查配置是否存在
        config = system_service.get_config(key)
        if not config:
            raise HTTPException(status_code=404, detail="配置项不存在")
        
        # 更新配置
        updated_config = system_service.update_config(key, config_data)
        
        return success_response(
            data=updated_config.to_dict(),
            message="更新系统配置成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新系统配置失败: {e}")
        return error_response(message="更新系统配置失败", error_code=str(e))

@router.delete("/config/{key}", response_model=dict, summary="删除系统配置")
async def delete_system_config(
    key: str,
    db: Session = Depends(get_db)
):
    """删除系统配置"""
    try:
        system_service = SystemService(db)
        
        # 检查配置是否存在
        config = system_service.get_config(key)
        if not config:
            raise HTTPException(status_code=404, detail="配置项不存在")
        
        # 检查是否为系统关键配置
        if config.is_system:
            raise HTTPException(status_code=400, detail="系统关键配置不能删除")
        
        # 删除配置
        system_service.delete_config(key)
        
        return success_response(message="删除系统配置成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除系统配置失败: {e}")
        return error_response(message="删除系统配置失败", error_code=str(e))

@router.post("/config/batch", response_model=dict, summary="批量更新系统配置")
async def batch_update_configs(
    batch_data: ConfigBatchUpdate,
    db: Session = Depends(get_db)
):
    """批量更新系统配置"""
    try:
        system_service = SystemService(db)
        result = system_service.batch_update_configs(batch_data.configs)
        
        return success_response(
            data=result,
            message="批量更新系统配置成功"
        )
    except Exception as e:
        logger.error(f"批量更新系统配置失败: {e}")
        return error_response(message="批量更新系统配置失败", error_code=str(e))

# 系统信息
@router.get("/info", response_model=dict, summary="获取系统信息")
async def get_system_info(
    db: Session = Depends(get_db)
):
    """获取系统信息"""
    try:
        system_service = SystemService(db)
        info = system_service.get_system_info()
        
        return success_response(
            data=info,
            message="获取系统信息成功"
        )
    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")
        return error_response(message="获取系统信息失败", error_code=str(e))

@router.get("/status", response_model=dict, summary="获取系统状态")
async def get_system_status(
    db: Session = Depends(get_db)
):
    """获取系统状态"""
    try:
        system_service = SystemService(db)
        status = system_service.get_system_status()
        
        return success_response(
            data=status,
            message="获取系统状态成功"
        )
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        return error_response(message="获取系统状态失败", error_code=str(e))

@router.get("/health", response_model=dict, summary="健康检查")
async def health_check(
    db: Session = Depends(get_db)
):
    """健康检查"""
    try:
        system_service = SystemService(db)
        health = system_service.health_check()
        
        # 根据健康状态设置HTTP状态码
        status_code = 200 if health["status"] == "healthy" else 503
        
        return success_response(
            data=health,
            message="健康检查完成"
        )
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return error_response(message="健康检查失败", error_code=str(e))



# 设置导入导出
@router.get("/settings/export", response_model=dict, summary="导出系统设置")
async def export_settings(
    db: Session = Depends(get_db)
):
    """导出系统设置"""
    try:
        system_service = SystemService(db)
        settings = system_service.export_settings()
        
        return success_response(
            data=settings,
            message="导出系统设置成功"
        )
    except Exception as e:
        logger.error(f"导出系统设置失败: {e}")
        return error_response(message="导出系统设置失败", error_code=str(e))

@router.post("/settings/import", response_model=dict, summary="导入系统设置")
async def import_settings(
    settings: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """导入系统设置"""
    try:
        system_service = SystemService(db)
        result = system_service.import_settings(settings)
        
        return success_response(
            data=result,
            message="导入系统设置成功"
        )
    except Exception as e:
        logger.error(f"导入系统设置失败: {e}")
        return error_response(message="导入系统设置失败", error_code=str(e))

@router.post("/settings/save", response_model=dict, summary="保存系统设置")
async def save_settings(
    settings: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """保存系统设置"""
    try:
        system_service = SystemService(db)
        result = system_service.save_settings(settings)
        
        return success_response(
            data=result,
            message="保存系统设置成功"
        )
    except Exception as e:
        logger.error(f"保存系统设置失败: {e}")
        return error_response(message="保存系统设置失败", error_code=str(e))

# 系统测试

@router.post("/test/email", response_model=dict, summary="测试邮件通知")
async def test_email_notification(
    email: str = Query(..., description="测试邮箱地址"),
    db: Session = Depends(get_db)
):
    """测试邮件通知"""
    try:
        system_service = SystemService(db)
        result = system_service.test_email_notification(email)
        
        return success_response(
            data=result,
            message="邮件通知测试完成"
        )
    except Exception as e:
        logger.error(f"测试邮件通知失败: {e}")
        return error_response(message="测试邮件通知失败", error_code=str(e))

@router.post("/test/webhook", response_model=dict, summary="测试Webhook通知")
async def test_webhook_notification(
    url: str = Query(..., description="Webhook URL"),
    db: Session = Depends(get_db)
):
    """测试Webhook通知"""
    try:
        system_service = SystemService(db)
        result = system_service.test_webhook_notification(url)
        
        return success_response(
            data=result,
            message="Webhook通知测试完成"
        )
    except Exception as e:
        logger.error(f"测试Webhook通知失败: {e}")
        return error_response(message="测试Webhook通知失败", error_code=str(e))

# 系统维护
@router.post("/cache/clear", response_model=dict, summary="清理缓存")
async def clear_cache(
    db: Session = Depends(get_db)
):
    """清理缓存"""
    try:
        system_service = SystemService(db)
        result = system_service.clear_cache()
        
        return success_response(
            data=result,
            message="清理缓存成功"
        )
    except Exception as e:
        logger.error(f"清理缓存失败: {e}")
        return error_response(message="清理缓存失败", error_code=str(e))

@router.post("/settings/reset", response_model=dict, summary="重置为默认值")
async def reset_to_defaults(
    confirm: bool = Query(False, description="确认重置"),
    db: Session = Depends(get_db)
):
    """重置为默认值"""
    try:
        if not confirm:
            raise HTTPException(status_code=400, detail="请确认重置操作")
        
        system_service = SystemService(db)
        result = system_service.reset_to_defaults()
        
        return success_response(
            data=result,
            message="重置为默认值成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重置为默认值失败: {e}")
        return error_response(message="重置为默认值失败", error_code=str(e))

# 系统操作
@router.post("/operations", response_model=dict, summary="执行系统操作")
async def execute_system_operation(
    operation_data: SystemOperationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """执行系统操作"""
    try:
        system_service = SystemService(db)
        
        # 验证操作类型
        valid_operations = [
            "restart_system",
            "clear_cache",
            "cleanup_logs",
            "optimize_database",
            "update_system",
            "reset_config"
        ]
        
        if operation_data.operation not in valid_operations:
            raise HTTPException(status_code=400, detail="无效的操作类型")
        
        # 记录操作
        operation = system_service.create_operation(operation_data)
        
        # 异步执行操作
        background_tasks.add_task(
            system_service.execute_operation,
            operation.id
        )
        
        return success_response(
            data=operation.to_dict(),
            message="系统操作已启动"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行系统操作失败: {e}")
        return error_response(message="执行系统操作失败", error_code=str(e))

# 系统监控
@router.get("/stats", response_model=dict, summary="获取系统统计信息")
async def get_system_stats(
    db: Session = Depends(get_db)
):
    """获取系统统计信息"""
    try:
        system_service = SystemService(db)
        stats = system_service.get_system_stats()
        
        return success_response(
            data=stats,
            message="获取系统统计信息成功"
        )
    except Exception as e:
        logger.error(f"获取系统统计信息失败: {e}")
        return error_response(message="获取系统统计信息失败", error_code=str(e))

@router.get("/metrics", response_model=dict, summary="获取系统指标")
async def get_system_metrics(
    period: str = Query("1h", description="时间周期"),
    db: Session = Depends(get_db)
):
    """获取系统指标"""
    try:
        system_service = SystemService(db)
        metrics = system_service.get_system_metrics(period)
        
        return success_response(
            data=metrics,
            message="获取系统指标成功"
        )
    except Exception as e:
        logger.error(f"获取系统指标失败: {e}")
        return error_response(message="获取系统指标失败", error_code=str(e))