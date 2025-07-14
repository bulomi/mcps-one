"""工具管理 API 路由"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.database import get_db
from app.schemas.tool import (
    ToolCreate,
    ToolUpdate,
    ToolResponse,
    ToolAction,
    ToolStatusResponse,
    ToolBatchAction,
    ToolExport,
    ToolImport,
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
)
from app.services.tool_service import ToolService
from app.services.mcp_service import MCPService
from app.utils.response import success_response, error_response
from app.utils.pagination import simple_paginate as paginate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tools", tags=["工具管理"])

# 工具 CRUD 操作
@router.get("/", response_model=dict, summary="获取工具列表")
async def get_tools(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    category: Optional[str] = Query(None, description="工具分类"),
    type: Optional[str] = Query(None, description="工具类型"),
    status: Optional[str] = Query(None, description="工具状态"),
    enabled: Optional[bool] = Query(None, description="是否启用"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db)
):
    """获取工具列表"""
    try:
        tool_service = ToolService(db)
        
        # 构建过滤条件
        filters = {}
        if category:
            filters['category'] = category
        if type:
            filters['type'] = type
        if status:
            filters['status'] = status
        if enabled is not None:
            filters['enabled'] = enabled
        if search:
            filters['search'] = search
        
        # 获取工具列表
        tools, total = tool_service.get_tools(
            page=page,
            size=size,
            filters=filters
        )
        
        # 分页信息
        pagination = paginate(total, page, size)
        
        return success_response(
            data={
                "items": [tool.to_dict() for tool in tools],
                "pagination": pagination
            },
            message="获取工具列表成功"
        )
    except Exception as e:
        logger.error(f"获取工具列表失败: {e}")
        return error_response(message="获取工具列表失败", error_code=str(e))

@router.get("/{tool_id}", response_model=dict, summary="获取工具详情")
async def get_tool(
    tool_id: int,
    db: Session = Depends(get_db)
):
    """获取工具详情"""
    try:
        tool_service = ToolService(db)
        tool = tool_service.get_tool(tool_id)
        
        if not tool:
            raise HTTPException(status_code=404, detail="工具不存在")
        
        return success_response(
            data=tool.to_dict(),
            message="获取工具详情成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工具详情失败: {e}")
        return error_response(message="获取工具详情失败", error_code=str(e))

@router.post("/", response_model=dict, summary="创建工具")
async def create_tool(
    tool_data: ToolCreate,
    db: Session = Depends(get_db)
):
    """创建工具"""
    try:
        tool_service = ToolService(db)
        
        # 检查工具名称是否已存在
        if tool_service.get_tool_by_name(tool_data.name):
            raise HTTPException(status_code=400, detail="工具名称已存在")
        
        # 创建工具
        tool = tool_service.create_tool(tool_data)
        
        return success_response(
            data=tool.to_dict(),
            message="创建工具成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建工具失败: {e}")
        return error_response(message="创建工具失败", error_code=str(e))

@router.put("/{tool_id}", response_model=dict, summary="更新工具")
async def update_tool(
    tool_id: int,
    tool_data: ToolUpdate,
    db: Session = Depends(get_db)
):
    """更新工具"""
    try:
        tool_service = ToolService(db)
        
        # 检查工具是否存在
        tool = tool_service.get_tool(tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail="工具不存在")
        
        # 更新工具
        updated_tool = tool_service.update_tool(tool_id, tool_data)
        
        return success_response(
            data=updated_tool.to_dict(),
            message="更新工具成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新工具失败: {e}")
        return error_response(message="更新工具失败", error_code=str(e))

@router.delete("/{tool_id}", response_model=dict, summary="删除工具")
async def delete_tool(
    tool_id: int,
    force: bool = Query(False, description="是否强制删除"),
    db: Session = Depends(get_db)
):
    """删除工具"""
    try:
        tool_service = ToolService(db)
        mcp_service = MCPService()
        
        # 检查工具是否存在
        tool = tool_service.get_tool(tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail="工具不存在")
        
        # 检查工具是否正在运行
        if tool.is_running and not force:
            raise HTTPException(status_code=400, detail="工具正在运行，请先停止工具或使用强制删除")
        
        # 停止工具（如果正在运行）
        if tool.is_running:
            await mcp_service.stop_tool(tool_id)
        
        # 删除工具
        tool_service.delete_tool(tool_id)
        
        return success_response(message="删除工具成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除工具失败: {e}")
        return error_response(message="删除工具失败", error_code=str(e))

# 工具操作
@router.post("/{tool_id}/action", response_model=dict, summary="执行工具操作")
async def tool_action(
    tool_id: int,
    action_data: ToolAction,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """执行工具操作（启动、停止、重启）"""
    try:
        tool_service = ToolService(db)
        mcp_service = MCPService()
        
        # 检查工具是否存在
        tool = tool_service.get_tool(tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail="工具不存在")
        
        # 检查工具是否启用
        if not tool.enabled and action_data.action != "stop":
            raise HTTPException(status_code=400, detail="工具已禁用")
        
        # 执行操作
        if action_data.action == "start":
            if not tool.can_start and not action_data.force:
                raise HTTPException(status_code=400, detail="工具无法启动")
            
            background_tasks.add_task(mcp_service.start_tool, tool_id)
            message = "工具启动请求已提交"
            
        elif action_data.action == "stop":
            if not tool.can_stop and not action_data.force:
                raise HTTPException(status_code=400, detail="工具无法停止")
            
            background_tasks.add_task(mcp_service.stop_tool, tool_id, action_data.force)
            message = "工具停止请求已提交"
            
        elif action_data.action == "restart":
            background_tasks.add_task(mcp_service.restart_tool, tool_id, action_data.force)
            message = "工具重启请求已提交"
            
        else:
            raise HTTPException(status_code=400, detail="无效的操作类型")
        
        return success_response(message=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行工具操作失败: {e}")
        return error_response(message="执行工具操作失败", error_code=str(e))

@router.get("/{tool_id}/status", response_model=dict, summary="获取工具状态")
async def get_tool_status(
    tool_id: int,
    db: Session = Depends(get_db)
):
    """获取工具状态"""
    try:
        tool_service = ToolService(db)
        mcp_service = MCPService()
        
        # 检查工具是否存在
        tool = tool_service.get_tool(tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail="工具不存在")
        
        # 获取实时状态
        real_status = await mcp_service.get_tool_status(tool_id)
        
        # 更新数据库状态（如果不一致）
        if real_status and real_status != tool.status:
            tool_service.update_tool_status(tool_id, real_status)
            tool = tool_service.get_tool(tool_id)  # 重新获取
        
        status_data = {
            "id": tool.id,
            "name": tool.name,
            "status": tool.status.value,
            "process_id": tool.process_id,
            "last_started_at": tool.last_started_at.isoformat() if tool.last_started_at else None,
            "last_stopped_at": tool.last_stopped_at.isoformat() if tool.last_stopped_at else None,
            "restart_count": tool.restart_count,
            "is_running": tool.is_running,
            "can_start": tool.can_start,
            "can_stop": tool.can_stop,
        }
        
        return success_response(
            data=status_data,
            message="获取工具状态成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工具状态失败: {e}")
        return error_response(message="获取工具状态失败", error_code=str(e))

# 批量操作
@router.post("/batch", response_model=dict, summary="批量操作工具")
async def batch_tool_action(
    batch_data: ToolBatchAction,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """批量操作工具"""
    try:
        tool_service = ToolService(db)
        mcp_service = MCPService()
        
        results = []
        
        for tool_id in batch_data.tool_ids:
            try:
                # 检查工具是否存在
                tool = tool_service.get_tool(tool_id)
                if not tool:
                    results.append({
                        "tool_id": tool_id,
                        "success": False,
                        "error": "工具不存在"
                    })
                    continue
                
                # 执行操作
                if batch_data.action == "start":
                    if tool.can_start or batch_data.force:
                        background_tasks.add_task(mcp_service.start_tool, tool_id)
                        results.append({"tool_id": tool_id, "success": True})
                    else:
                        results.append({
                            "tool_id": tool_id,
                            "success": False,
                            "error": "工具无法启动"
                        })
                        
                elif batch_data.action == "stop":
                    if tool.can_stop or batch_data.force:
                        background_tasks.add_task(mcp_service.stop_tool, tool_id, batch_data.force)
                        results.append({"tool_id": tool_id, "success": True})
                    else:
                        results.append({
                            "tool_id": tool_id,
                            "success": False,
                            "error": "工具无法停止"
                        })
                        
                elif batch_data.action == "restart":
                    background_tasks.add_task(mcp_service.restart_tool, tool_id, batch_data.force)
                    results.append({"tool_id": tool_id, "success": True})
                    
                elif batch_data.action == "delete":
                    if not tool.is_running or batch_data.force:
                        if tool.is_running:
                            await mcp_service.stop_tool(tool_id)
                        tool_service.delete_tool(tool_id)
                        results.append({"tool_id": tool_id, "success": True})
                    else:
                        results.append({
                            "tool_id": tool_id,
                            "success": False,
                            "error": "工具正在运行"
                        })
                        
            except Exception as e:
                results.append({
                    "tool_id": tool_id,
                    "success": False,
                    "error": str(e)
                })
        
        success_count = sum(1 for r in results if r["success"])
        failed_count = len(results) - success_count
        
        return success_response(
            data={
                "results": results,
                "summary": {
                    "total": len(batch_data.tool_ids),
                    "success": success_count,
                    "failed": failed_count
                }
            },
            message=f"批量操作完成，成功 {success_count} 个，失败 {failed_count} 个"
        )
    except Exception as e:
        logger.error(f"批量操作工具失败: {e}")
        return error_response(message="批量操作工具失败", error_code=str(e))

# 工具分类管理
@router.get("/categories", response_model=dict, summary="获取工具分类列表")
async def get_categories(
    db: Session = Depends(get_db)
):
    """获取工具分类列表"""
    try:
        tool_service = ToolService(db)
        categories = tool_service.get_categories()
        
        return success_response(
            data=[category.to_dict() for category in categories],
            message="获取工具分类列表成功"
        )
    except Exception as e:
        logger.error(f"获取工具分类列表失败: {e}")
        return error_response(message="获取工具分类列表失败", error_code=str(e))

@router.post("/categories", response_model=dict, summary="创建工具分类")
async def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db)
):
    """创建工具分类"""
    try:
        tool_service = ToolService(db)
        
        # 检查分类名称是否已存在
        if tool_service.get_category_by_name(category_data.name):
            raise HTTPException(status_code=400, detail="分类名称已存在")
        
        # 创建分类
        category = tool_service.create_category(category_data)
        
        return success_response(
            data=category.to_dict(),
            message="创建工具分类成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建工具分类失败: {e}")
        return error_response(message="创建工具分类失败", error_code=str(e))

# 导入导出
@router.get("/export", response_model=dict, summary="导出工具配置")
async def export_tools(
    tool_ids: Optional[List[int]] = Query(None, description="要导出的工具ID列表"),
    include_categories: bool = Query(True, description="是否包含分类"),
    db: Session = Depends(get_db)
):
    """导出工具配置"""
    try:
        tool_service = ToolService(db)
        export_data = tool_service.export_tools(tool_ids, include_categories)
        
        return success_response(
            data=export_data,
            message="导出工具配置成功"
        )
    except Exception as e:
        logger.error(f"导出工具配置失败: {e}")
        return error_response(message="导出工具配置失败", error_code=str(e))

@router.post("/import", response_model=dict, summary="导入工具配置")
async def import_tools(
    import_data: ToolImport,
    db: Session = Depends(get_db)
):
    """导入工具配置"""
    try:
        tool_service = ToolService(db)
        result = tool_service.import_tools(import_data)
        
        return success_response(
            data=result,
            message="导入工具配置成功"
        )
    except Exception as e:
        logger.error(f"导入工具配置失败: {e}")
        return error_response(message="导入工具配置失败", error_code=str(e))