"""代理管理 API 路由"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
import asyncio

from app.core.database import get_db
from app.utils.response import success_response, error_response
from app.services.integrations import ProxyService
from app.utils.exceptions import ProxyNotFoundError, ProxyValidationError
from app.models.proxy import ProxyStatus, ProxyType, ProxyProtocol

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/proxy", tags=["代理管理"])


@router.get("/stats", response_model=dict, summary="获取代理统计信息")
async def get_proxy_stats(
    db: Session = Depends(get_db)
):
    """获取代理统计信息"""
    try:
        proxy_service = ProxyService(db)
        stats = proxy_service.get_proxy_stats()

        return success_response(
            data=stats,
            message="获取代理统计信息成功"
        )
    except Exception as e:
        logger.error(f"获取代理统计信息失败: {e}")
        return error_response(message="获取代理统计信息失败", error_code=str(e))


@router.get("/", response_model=dict, summary="获取代理列表")
async def get_proxies(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    category: Optional[str] = Query(None, description="代理分类"),
    proxy_type: Optional[str] = Query(None, description="代理类型"),
    status: Optional[str] = Query(None, description="代理状态"),
    enabled: Optional[bool] = Query(None, description="是否启用"),
    country: Optional[str] = Query(None, description="国家"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db)
):
    """获取代理列表"""
    try:
        proxy_service = ProxyService(db)

        # 构建过滤条件
        filters = {}
        if category:
            filters['category'] = category
        if proxy_type:
            filters['proxy_type'] = proxy_type
        if status:
            filters['status'] = status
        if enabled is not None:
            filters['enabled'] = enabled
        if country:
            filters['country'] = country
        if search:
            filters['search'] = search

        proxies, total = proxy_service.get_proxies(page, size, filters)

        # 计算总页数
        pages = (total + size - 1) // size

        return success_response(
            data={
                "items": [proxy.to_dict() for proxy in proxies],
                "pagination": {
                    "page": page,
                    "size": size,
                    "total": total,
                    "pages": pages
                }
            },
            message="获取代理列表成功"
        )
    except Exception as e:
        logger.error(f"获取代理列表失败: {e}")
        return error_response(message="获取代理列表失败", error_code=str(e))


@router.get("/{proxy_id}", response_model=dict, summary="获取代理详情")
async def get_proxy(
    proxy_id: int,
    db: Session = Depends(get_db)
):
    """获取代理详情"""
    try:
        proxy_service = ProxyService(db)
        proxy = proxy_service.get_proxy(proxy_id)

        if not proxy:
            return error_response(message="代理不存在", error_code="PROXY_NOT_FOUND")

        return success_response(
            data=proxy.to_dict(),
            message="获取代理详情成功"
        )
    except Exception as e:
        logger.error(f"获取代理详情失败: {e}")
        return error_response(message="获取代理详情失败", error_code=str(e))


@router.post("/", response_model=dict, summary="创建代理")
async def create_proxy(
    proxy_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """创建代理"""
    try:
        proxy_service = ProxyService(db)
        proxy = proxy_service.create_proxy(proxy_data)

        return success_response(
            data=proxy.to_dict(),
            message="代理创建成功"
        )
    except ProxyValidationError as e:
        return error_response(message=str(e), error_code="VALIDATION_ERROR")
    except Exception as e:
        logger.error(f"创建代理失败: {e}")
        return error_response(message="创建代理失败", error_code=str(e))


@router.put("/{proxy_id}", response_model=dict, summary="更新代理")
async def update_proxy(
    proxy_id: int,
    proxy_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """更新代理"""
    try:
        proxy_service = ProxyService(db)
        proxy = proxy_service.update_proxy(proxy_id, proxy_data)

        return success_response(
            data=proxy.to_dict(),
            message="代理更新成功"
        )
    except ProxyNotFoundError as e:
        return error_response(message=str(e), error_code="PROXY_NOT_FOUND")
    except ProxyValidationError as e:
        return error_response(message=str(e), error_code="VALIDATION_ERROR")
    except Exception as e:
        logger.error(f"更新代理失败: {e}")
        return error_response(message="更新代理失败", error_code=str(e))


@router.delete("/{proxy_id}", response_model=dict, summary="删除代理")
async def delete_proxy(
    proxy_id: int,
    db: Session = Depends(get_db)
):
    """删除代理"""
    try:
        proxy_service = ProxyService(db)
        success = proxy_service.delete_proxy(proxy_id)

        if success:
            return success_response(message="代理删除成功")
        else:
            return error_response(message="代理删除失败", error_code="DELETE_FAILED")
    except ProxyNotFoundError as e:
        return error_response(message=str(e), error_code="PROXY_NOT_FOUND")
    except Exception as e:
        logger.error(f"删除代理失败: {e}")
        return error_response(message="删除代理失败", error_code=str(e))


@router.post("/{proxy_id}/test", response_model=dict, summary="测试代理")
async def test_proxy(
    proxy_id: int,
    test_url: Optional[str] = Body(None),
    db: Session = Depends(get_db)
):
    """测试代理"""
    try:
        proxy_service = ProxyService(db)
        result = await proxy_service.test_proxy(proxy_id, test_url)

        return success_response(
            data=result.to_dict(),
            message="代理测试完成"
        )
    except ProxyNotFoundError as e:
        return error_response(message=str(e), error_code="PROXY_NOT_FOUND")
    except ProxyValidationError as e:
        return error_response(message=str(e), error_code="VALIDATION_ERROR")
    except Exception as e:
        logger.error(f"测试代理失败: {e}")
        return error_response(message="测试代理失败", error_code=str(e))


@router.post("/test-all", response_model=dict, summary="测试所有代理")
async def test_all_proxies(
    db: Session = Depends(get_db)
):
    """测试所有代理"""
    try:
        proxy_service = ProxyService(db)
        results = await proxy_service.test_all_proxies()

        return success_response(
            data={
                "total_tested": len(results),
                "results": [result.to_dict() for result in results]
            },
            message="批量测试完成"
        )
    except Exception as e:
        logger.error(f"批量测试代理失败: {e}")
        return error_response(message="批量测试代理失败", error_code=str(e))


@router.get("/active/list", response_model=dict, summary="获取活跃代理列表")
async def get_active_proxies(
    db: Session = Depends(get_db)
):
    """获取活跃代理列表"""
    try:
        proxy_service = ProxyService(db)
        proxies = proxy_service.get_active_proxies()

        return success_response(
            data=[proxy.to_dict() for proxy in proxies],
            message="获取活跃代理列表成功"
        )
    except Exception as e:
        logger.error(f"获取活跃代理列表失败: {e}")
        return error_response(message="获取活跃代理列表失败", error_code=str(e))


@router.get("/categories/", response_model=dict, summary="获取代理分类列表")
async def get_proxy_categories(
    db: Session = Depends(get_db)
):
    """获取代理分类列表"""
    try:
        proxy_service = ProxyService(db)
        categories = proxy_service.get_categories()

        return success_response(
            data=[category.to_dict() for category in categories],
            message="获取代理分类列表成功"
        )
    except Exception as e:
        logger.error(f"获取代理分类列表失败: {e}")
        return error_response(message="获取代理分类列表失败", error_code=str(e))


@router.post("/categories/", response_model=dict, summary="创建代理分类")
async def create_proxy_category(
    category_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """创建代理分类"""
    try:
        proxy_service = ProxyService(db)
        category = proxy_service.create_category(category_data)

        return success_response(
            data=category.to_dict(),
            message="代理分类创建成功"
        )
    except Exception as e:
        logger.error(f"创建代理分类失败: {e}")
        return error_response(message="创建代理分类失败", error_code=str(e))


@router.get("/enums/", response_model=dict, summary="获取代理枚举值")
async def get_proxy_enums():
    """获取代理枚举值"""
    try:
        return success_response(
            data={
                "proxy_types": [t.value for t in ProxyType],
                "protocols": [p.value for p in ProxyProtocol],
                "statuses": [s.value for s in ProxyStatus]
            },
            message="获取代理枚举值成功"
        )
    except Exception as e:
        logger.error(f"获取代理枚举值失败: {e}")
        return error_response(message="获取代理枚举值失败", error_code=str(e))
