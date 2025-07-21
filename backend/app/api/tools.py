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
from app.services.tools import ToolService
from app.services.mcp import MCPService
from app.utils.response import success_response, error_response
from app.utils.pagination import simple_paginate as paginate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tools", tags=["工具管理"])

# 工具 CRUD 操作
@router.options("/", summary="工具列表选项")
async def options_tools():
    """处理工具列表的 OPTIONS 请求"""
    return {"message": "OK"}

@router.get("/", response_model=dict, summary="获取工具列表")
async def get_tools(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=200, description="每页大小"),
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
                "total": total,
                "page": page,
                "size": size
            },
            message="获取工具列表成功"
        )
    except Exception as e:
        logger.error(f"获取工具列表失败: {e}")
        return error_response(message="获取工具列表失败", error_code=str(e))

# 工具统计 - 必须在 /{tool_id} 之前定义
@router.get("/stats", response_model=dict, summary="获取工具统计")
async def get_tool_stats(
    db: Session = Depends(get_db)
):
    """获取工具统计信息"""
    try:
        tool_service = ToolService(db)
        stats = tool_service.get_tool_stats()

        return success_response(
            data=stats,
            message="获取工具统计成功"
        )
    except Exception as e:
        logger.error(f"获取工具统计失败: {e}")
        return error_response(message="获取工具统计失败", error_code=str(e))

# 工具分类管理 - 必须在 /{tool_id} 之前定义
@router.get("/categories/", response_model=dict, summary="获取工具分类列表")
async def get_categories(
    db: Session = Depends(get_db)
):
    """获取工具分类列表"""
    try:
        tool_service = ToolService(db)
        categories = tool_service.get_categories()

        # 返回分类名称的字符串数组，符合前端期望
        category_names = [category.name for category in categories]

        return success_response(
            data=category_names,
            message="获取工具分类列表成功"
        )
    except Exception as e:
        logger.error(f"获取工具分类列表失败: {e}")
        return error_response(message="获取工具分类列表失败", error_code=str(e))

@router.post("/categories/", response_model=dict, summary="创建工具分类")
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

# 工具配置验证 - 必须在 /{tool_id} 之前定义
@router.post("/validate", response_model=dict, summary="验证工具配置")
async def validate_tool_config(
    tool_data: ToolCreate,
    db: Session = Depends(get_db)
):
    """验证工具配置"""
    try:
        tool_service = ToolService(db)

        # 验证工具配置
        validation_result = tool_service.validate_tool_config(tool_data)

        return success_response(
            data=validation_result,
            message="工具配置验证完成"
        )
    except Exception as e:
        logger.error(f"验证工具配置失败: {e}")
        return error_response(message="验证工具配置失败", error_code=str(e))

# 导入导出 - 必须在 /{tool_id} 之前定义
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

            background_tasks.add_task(tool_service.start_tool, tool_id)
            message = "工具启动请求已提交"

        elif action_data.action == "stop":
            if not tool.can_stop and not action_data.force:
                raise HTTPException(status_code=400, detail="工具无法停止")

            background_tasks.add_task(tool_service.stop_tool, tool_id, action_data.force)
            message = "工具停止请求已提交"

        elif action_data.action == "restart":
            background_tasks.add_task(tool_service.restart_tool, tool_id, action_data.force)
            message = "工具重启请求已提交"

        else:
            raise HTTPException(status_code=400, detail="无效的操作类型")

        return success_response(message=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行工具操作失败: {e}")
        return error_response(message="执行工具操作失败", error_code=str(e))

@router.get("/{tool_id}/status/", response_model=dict, summary="获取工具状态")
async def get_tool_status(
    tool_id: int,
    db: Session = Depends(get_db)
):
    """获取工具状态"""
    try:
        tool_service = ToolService(db)

        # 获取工具状态信息（异步调用）
        status_data = await tool_service.get_tool_status(tool_id)

        return success_response(
            data=status_data,
            message="获取工具状态成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工具状态失败: {e}")
        return error_response(message="获取工具状态失败", error_code=str(e))

# 单独的工具操作端点
@router.post("/{tool_id}/start/", response_model=dict, summary="启动工具")
async def start_tool(
    tool_id: int,
    background_tasks: BackgroundTasks,
    force: bool = Query(False, description="是否强制启动"),
    db: Session = Depends(get_db)
):
    """启动工具"""
    try:
        tool_service = ToolService(db)

        # 检查工具是否存在
        tool = tool_service.get_tool(tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail="工具不存在")

        # 检查工具是否可以启动
        if not tool.can_start and not force:
            raise HTTPException(status_code=400, detail=f"工具无法启动: {tool.status.value}")

        # 启动工具
        background_tasks.add_task(tool_service.start_tool, tool_id, force)

        return success_response(
            data={"tool_id": tool_id, "action": "start"},
            message="工具启动任务已提交"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动工具失败: {e}")
        return error_response(message="启动工具失败", error_code=str(e))

@router.post("/{tool_id}/stop/", response_model=dict, summary="停止工具")
async def stop_tool(
    tool_id: int,
    background_tasks: BackgroundTasks,
    force: bool = Query(False, description="是否强制停止"),
    db: Session = Depends(get_db)
):
    """停止工具"""
    try:
        tool_service = ToolService(db)

        # 检查工具是否存在
        tool = tool_service.get_tool(tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail="工具不存在")

        # 检查工具是否可以停止
        if not tool.can_stop and not force:
            raise HTTPException(status_code=400, detail=f"工具无法停止: {tool.status.value}")

        # 停止工具
        background_tasks.add_task(tool_service.stop_tool, tool_id, force)

        return success_response(
            data={"tool_id": tool_id, "action": "stop"},
            message="工具停止任务已提交"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止工具失败: {e}")
        return error_response(message="停止工具失败", error_code=str(e))

@router.post("/{tool_id}/restart/", response_model=dict, summary="重启工具")
async def restart_tool(
    tool_id: int,
    background_tasks: BackgroundTasks,
    force: bool = Query(False, description="是否强制重启"),
    db: Session = Depends(get_db)
):
    """重启工具"""
    try:
        tool_service = ToolService(db)

        # 检查工具是否存在
        tool = tool_service.get_tool(tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail="工具不存在")

        # 重启工具
        background_tasks.add_task(tool_service.restart_tool, tool_id, force)

        return success_response(
            data={"tool_id": tool_id, "action": "restart"},
            message="工具重启任务已提交"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重启工具失败: {e}")
        return error_response(message="重启工具失败", error_code=str(e))

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

        # 处理删除操作
        if batch_data.action == "delete":
            results = []
            for tool_id in batch_data.tool_ids:
                try:
                    tool = tool_service.get_tool(tool_id)
                    if not tool:
                        results.append({
                            "tool_id": tool_id,
                            "success": False,
                            "error": "工具不存在"
                        })
                        continue

                    if not tool.is_running or batch_data.force:
                        if tool.is_running:
                            await tool_service.stop_tool(tool_id, True)
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
        else:
            # 使用工具服务的批量操作方法
            batch_result = await tool_service.batch_tool_action(
                batch_data.tool_ids,
                batch_data.action,
                batch_data.force
            )

            # 转换结果格式
            results = []
            for tool_id in batch_data.tool_ids:
                if tool_id in batch_result["success"]:
                    results.append({"tool_id": tool_id, "success": True})
                else:
                    # 查找失败原因
                    error_info = next(
                        (item for item in batch_result["failed"] if item["id"] == tool_id),
                        {"error": "未知错误"}
                    )
                    results.append({
                        "tool_id": tool_id,
                        "success": False,
                        "error": error_info["error"]
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

# 工具日志
@router.get("/{tool_id}/logs/", response_model=dict, summary="获取工具日志")
async def get_tool_logs(
    tool_id: int,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(50, ge=1, le=500, description="每页大小"),
    level: Optional[str] = Query(None, description="日志级别"),
    start_time: Optional[str] = Query(None, description="开始时间"),
    end_time: Optional[str] = Query(None, description="结束时间"),
    db: Session = Depends(get_db)
):
    """获取工具日志"""
    try:
        from app.services.system import LogService
        from datetime import datetime

        tool_service = ToolService(db)
        log_service = LogService(db)

        # 检查工具是否存在
        tool = tool_service.get_tool(tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail="工具不存在")

        # 构建过滤条件
        filters = {
            'tool_id': tool_id
        }
        if level:
            filters['level'] = level
        if start_time:
            try:
                filters['start_time'] = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                pass
        if end_time:
            try:
                filters['end_time'] = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError:
                pass

        # 获取系统日志（工具相关）
        system_logs, system_total = log_service.get_system_logs(
            page=page,
            size=size,
            filters=filters
        )

        # 获取MCP日志（工具相关）
        mcp_filters = {'tool_id': tool_id}
        if start_time:
            try:
                mcp_filters['start_time'] = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                pass
        if end_time:
            try:
                mcp_filters['end_time'] = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError:
                pass

        mcp_logs, mcp_total = log_service.get_mcp_logs(
            page=1,
            size=size,
            filters=mcp_filters
        )

        # 合并日志并按时间排序
        all_logs = []

        # 添加系统日志
        for log in system_logs:
            all_logs.append({
                "id": f"system_{log.id}",
                "type": "system",
                "level": log.level.value if log.level else "INFO",
                "message": log.message,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "source": log.source,
                "details": log.details
            })

        # 添加MCP日志
        for log in mcp_logs:
            all_logs.append({
                "id": f"mcp_{log.id}",
                "type": "mcp",
                "level": "INFO",
                "message": f"{log.direction.value.upper()}: {log.method or 'Unknown'}",
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "source": "MCP",
                "details": {
                    "method": log.method,
                    "direction": log.direction.value,
                    "request_data": log.request_data,
                    "response_data": log.response_data,
                    "error_data": log.error_data
                }
            })

        # 按时间排序（最新的在前）
        all_logs.sort(key=lambda x: x['timestamp'] or '', reverse=True)

        # 分页处理
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        paginated_logs = all_logs[start_idx:end_idx]

        total = system_total + mcp_total

        return success_response(
            data={
                "items": paginated_logs,
                "total": total,
                "page": page,
                "size": size
            },
            message="获取工具日志成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工具日志失败: {e}")
        return error_response(message="获取工具日志失败", error_code=str(e))
