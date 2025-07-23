"""工具管理服务"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
import json
from app.core import get_logger, LogLevel, LogCategory, create_log_context

from app.models.tool import MCPTool, ToolCategory, ToolStatus, ToolType
from app.schemas.tool import (
    ToolCreate,
    ToolUpdate,
    CategoryCreate,
    CategoryUpdate,
    ToolExport,
    ToolImport,
)
from app.schemas.log import SystemLogCreate, LogLevel, LogCategory
from app.core import get_unified_config_manager
from app.core import MCPSError, handle_error, error_handler, error_context
from app.utils.exceptions import (
    ToolNotFoundError,
    ToolValidationError,
    CategoryNotFoundError
)
from app.core.unified_cache import cached

logger = get_logger(__name__)

# 常量定义
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

class ToolService:
    """工具管理服务"""

    @error_handler
    def __init__(self, db: Session):
        self.db = db

    # 工具 CRUD 操作
    def get_tools(
        self,
        page: int = 1,
        size: int = DEFAULT_PAGE_SIZE,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[MCPTool], int]:
        """获取工具列表"""
        # 限制页面大小
        size = min(size, MAX_PAGE_SIZE)
        query = self.db.query(MCPTool)

        # 应用过滤条件
        if filters:
            if filters.get('category'):
                query = query.filter(MCPTool.category == filters['category'])

            if filters.get('type'):
                query = query.filter(MCPTool.type == ToolType(filters['type']))

            if filters.get('status'):
                query = query.filter(MCPTool.status == ToolStatus(filters['status']))

            if filters.get('enabled') is not None:
                query = query.filter(MCPTool.enabled == filters['enabled'])

            if filters.get('search'):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        MCPTool.name.ilike(search_term),
                        MCPTool.description.ilike(search_term),
                        MCPTool.command.ilike(search_term)
                    )
                )

        # 获取总数
        total = query.count()

        # 分页和排序
        tools = query.order_by(MCPTool.created_at.desc()).offset(
            (page - 1) * size
        ).limit(size).all()

        return tools, total

    @error_handler
    @cached(ttl=300)
    def get_tool(self, tool_id: int) -> Optional[MCPTool]:
        """获取工具详情"""
        return self.db.query(MCPTool).filter(MCPTool.id == tool_id).first()

    @error_handler
    @cached(ttl=300)
    def get_tool_by_name(self, name: str) -> Optional[MCPTool]:
        """根据名称获取工具"""
        return self.db.query(MCPTool).filter(MCPTool.name == name).first()

    @error_handler
    @cached(ttl=300)
    def get_available_tool_ids(self) -> List[int]:
        """获取可用工具ID列表"""
        try:
            # 获取启用且状态为运行中的工具ID
            tool_ids = self.db.query(MCPTool.id).filter(
                and_(
                    MCPTool.enabled == True,
                    MCPTool.status == ToolStatus.RUNNING
                )
            ).all()

            # 提取ID列表
            return [tool_id[0] for tool_id in tool_ids]

        except Exception as e:
            logger.error(f"获取可用工具ID列表失败: {e}", category=LogCategory.SYSTEM)
            return []

    @error_handler
    def create_tool(self, tool_data: ToolCreate) -> MCPTool:
        """创建工具"""
        try:
            # 验证工具配置
            self._validate_tool_config(tool_data)

            # 创建工具实例
            tool = MCPTool(
                name=tool_data.name,
                display_name=tool_data.display_name,
                description=tool_data.description,
                type=tool_data.type,
                category=tool_data.category,
                tags=tool_data.tags,
                command=tool_data.command,
                working_directory=tool_data.working_directory,
                environment_variables=tool_data.environment_variables or {},
                connection_type=tool_data.connection_type,
                host=tool_data.host,
                port=tool_data.port,
                path=tool_data.path,
                auto_start=tool_data.auto_start,
                restart_on_failure=tool_data.restart_on_failure,
                max_restart_attempts=tool_data.max_restart_attempts,
                timeout=tool_data.timeout,
                version=tool_data.version,
                author=tool_data.author,
                homepage=tool_data.homepage,
                enabled=tool_data.enabled,
                status=ToolStatus.STOPPED
            )

            self.db.add(tool)
            self.db.commit()
            self.db.refresh(tool)

            logger.info(f"工具创建成功: {tool.name} (ID: {tool.id})", category=LogCategory.SYSTEM)

            # 记录系统日志
            try:
                from ..system import LogService
                log_service = LogService(self.db)
                log_data = SystemLogCreate(
                    level=LogLevel.INFO,
                    category=LogCategory.TOOL,
                    message=f"工具创建成功: {tool.name}",
                    details={
                        "tool_id": tool.id,
                        "tool_name": tool.name,
                        "tool_type": tool.type.value,
                        "category": tool.category
                    }
                )
                log_service.create_system_log(log_data)
            except Exception as log_error:
                logger.warning(f"记录系统日志失败: {log_error}", category=LogCategory.SYSTEM)

            return tool

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建工具失败: {e}", category=LogCategory.SYSTEM)
            raise ToolValidationError(f"创建工具失败: {e}")

    @error_handler
    def update_tool(self, tool_id: int, tool_data: ToolUpdate) -> MCPTool:
        """更新工具"""
        try:
            tool = self.get_tool(tool_id)
            if not tool:
                raise ToolNotFoundError(f"工具不存在: {tool_id}")

            # 更新字段
            update_data = tool_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if field in ['connection_config', 'runtime_config', 'metadata'] and value:
                    value = value.model_dump() if hasattr(value, 'model_dump') else value
                setattr(tool, field, value)

            tool.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(tool)

            logger.info(f"工具更新成功: {tool.name} (ID: {tool.id})", category=LogCategory.SYSTEM)
            return tool

        except Exception as e:
            self.db.rollback()
            logger.error(f"更新工具失败: {e}", category=LogCategory.SYSTEM)
            raise

    @error_handler
    def delete_tool(self, tool_id: int) -> bool:
        """删除工具"""
        try:
            tool = self.get_tool(tool_id)
            if not tool:
                raise ToolNotFoundError(f"工具不存在: {tool_id}")

            self.db.delete(tool)
            self.db.commit()

            logger.info(f"工具删除成功: {tool.name} (ID: {tool.id})", category=LogCategory.SYSTEM)
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"删除工具失败: {e}", category=LogCategory.SYSTEM)
            raise

    def update_tool_status(
        self,
        tool_id: int,
        status: ToolStatus,
        process_id: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> MCPTool:
        """更新工具状态"""
        try:
            tool = self.get_tool(tool_id)
            if not tool:
                raise ToolNotFoundError(f"工具不存在: {tool_id}")

            old_status = tool.status
            tool.status = status
            tool.updated_at = datetime.utcnow()

            if process_id is not None:
                tool.process_id = process_id

            if error_message:
                tool.last_error = error_message

            # 更新时间戳
            if status == ToolStatus.RUNNING and old_status != ToolStatus.RUNNING:
                tool.last_started_at = datetime.utcnow()
            elif status == ToolStatus.STOPPED and old_status == ToolStatus.RUNNING:
                tool.last_stopped_at = datetime.utcnow()
                tool.process_id = None
            elif status == ToolStatus.ERROR:
                tool.last_error_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(tool)

            logger.info(f"工具状态更新: {tool.name} {old_status.value} -> {status.value}", category=LogCategory.SYSTEM)

            # 记录系统日志
            try:
                from ..system import LogService
                log_service = LogService(self.db)

                # 根据状态变化确定日志级别
                log_level = LogLevel.INFO
                if status == ToolStatus.ERROR:
                    log_level = LogLevel.WARNING
                elif status == ToolStatus.STOPPED and old_status == ToolStatus.RUNNING:
                    log_level = LogLevel.INFO

                log_data = SystemLogCreate(
                    level=log_level,
                    category=LogCategory.TOOL,
                    message=f"工具状态变更: {tool.name} {old_status.value} -> {status.value}",
                    details={
                        "tool_id": tool.id,
                        "tool_name": tool.name,
                        "old_status": old_status.value,
                        "new_status": status.value,
                        "process_id": process_id,
                        "error_message": error_message
                    }
                )
                log_service.create_system_log(log_data)
            except Exception as log_error:
                logger.warning(f"记录系统日志失败: {log_error}", category=LogCategory.SYSTEM)

            # 发送 WebSocket 通知
            try:
                import asyncio
                from ...websocket import notify_tool_status_change

                # 在后台发送通知，不阻塞当前操作
                asyncio.create_task(
                    notify_tool_status_change(
                        tool_id=str(tool.id),
                        status=status.value,
                        details={"old_status": old_status.value}
                    )
                )
            except Exception as e:
                logger.warning(f"发送工具状态变更通知失败: {e}", category=LogCategory.SYSTEM)

            return tool

        except Exception as e:
            self.db.rollback()
            logger.error(f"更新工具状态失败: {e}", category=LogCategory.SYSTEM)
            raise

    @error_handler
    def increment_restart_count(self, tool_id: int) -> MCPTool:
        """增加重启计数"""
        try:
            tool = self.get_tool(tool_id)
            if not tool:
                raise ToolNotFoundError(f"工具不存在: {tool_id}")

            tool.restart_count += 1
            tool.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(tool)

            return tool

        except Exception as e:
            self.db.rollback()
            logger.error(f"更新重启计数失败: {e}", category=LogCategory.SYSTEM)
            raise

    # 工具操作方法
    @error_handler
    async def start_tool(self, tool_id: int, force: bool = False) -> bool:
        """启动工具"""
        try:
            from ..mcp import MCPService

            # 检查工具是否存在
            tool = self.get_tool(tool_id)
            if not tool:
                raise ToolNotFoundError(f"工具不存在: {tool_id}")

            # 检查工具是否可以启动（允许 running 状态继续处理以便状态同步）
            if not tool.can_start and not force and tool.status.value != "running":
                raise ToolValidationError(f"工具无法启动: {tool.name} (状态: {tool.status.value})")

            # 使用 MCP 服务启动工具
            mcp_service = MCPService()
            result = await mcp_service.start_tool(tool_id, force)

            logger.info(f"工具启动{'成功' if result else '失败'}: {tool.name} (ID: {tool_id})", category=LogCategory.SYSTEM)
            return result

        except Exception as e:
            logger.error(f"启动工具失败: {e}", category=LogCategory.SYSTEM)
            raise

    @error_handler
    async def stop_tool(self, tool_id: int, force: bool = False) -> bool:
        """停止工具"""
        try:
            from ..mcp import MCPService

            # 检查工具是否存在
            tool = self.get_tool(tool_id)
            if not tool:
                raise ToolNotFoundError(f"工具不存在: {tool_id}")

            # 检查工具是否可以停止
            if not tool.can_stop and not force:
                raise ToolValidationError(f"工具无法停止: {tool.name} (状态: {tool.status.value})")

            # 使用 MCP 服务停止工具
            mcp_service = MCPService()
            result = await mcp_service.stop_tool(tool_id, force)

            logger.info(f"工具停止{'成功' if result else '失败'}: {tool.name} (ID: {tool_id})", category=LogCategory.SYSTEM)
            return result

        except Exception as e:
            logger.error(f"停止工具失败: {e}", category=LogCategory.SYSTEM)
            raise

    @error_handler
    async def restart_tool(self, tool_id: int, force: bool = False) -> bool:

        """重启工具"""
        try:
            from ..mcp import MCPService

            # 检查工具是否存在
            tool = self.get_tool(tool_id)
            if not tool:
                raise ToolNotFoundError(f"工具不存在: {tool_id}")

            # 使用 MCP 服务重启工具
            mcp_service = MCPService()
            result = await mcp_service.restart_tool(tool_id, force)

            logger.info(f"工具重启{'成功' if result else '失败'}: {tool.name} (ID: {tool_id})", category=LogCategory.SYSTEM)
            return result

        except Exception as e:
            logger.error(f"重启工具失败: {e}", category=LogCategory.SYSTEM)
            raise
    
    @error_handler
    async def get_tool_status(self, tool_id: int) -> Dict[str, Any]:
        """获取工具状态信息（包含实时状态检查）"""
        try:
            tool = self.get_tool(tool_id)
            if not tool:
                raise ToolNotFoundError(f"工具不存在: {tool_id}")

            # 获取实时状态
            real_status = tool.status
            try:
                # 导入MCP统一服务来获取实时状态
                from ..mcp import unified_service
                if unified_service and unified_service.is_running:
                    # 通过统一服务获取代理服务实例
                    proxy_service = unified_service._proxy_service
                    if proxy_service and proxy_service.is_initialized:
                        real_status = await proxy_service.get_tool_status(tool_id)
                        if real_status and real_status != tool.status:
                            # 更新数据库中的状态
                            self.update_tool_status(tool_id, real_status)
                            tool.status = real_status
                            logger.info(f"工具状态已同步: {tool.name} -> {real_status.value}", category=LogCategory.SYSTEM)
            except Exception as status_error:
                logger.warning(f"获取实时状态失败，使用数据库状态: {status_error}", category=LogCategory.SYSTEM)

            return {
                "id": tool.id,
                "name": tool.name,
                "status": tool.status.value,
                "enabled": tool.enabled,
                "process_id": tool.process_id,
                "last_started_at": tool.last_started_at.isoformat() if tool.last_started_at else None,
                "last_stopped_at": tool.last_stopped_at.isoformat() if tool.last_stopped_at else None,
                "last_error_at": tool.last_error_at.isoformat() if tool.last_error_at else None,
                "last_error": tool.last_error,
                "restart_count": tool.restart_count,
                "can_start": tool.can_start,
                "can_stop": tool.can_stop,
                "is_running": tool.is_running
            }

        except Exception as e:
            logger.error(f"获取工具状态失败: {e}", category=LogCategory.SYSTEM)
            raise

    @error_handler
    async def batch_tool_action(self, tool_ids: List[int], action: str, force: bool = False) -> Dict[str, Any]:

        """批量工具操作"""
        try:
            results = {
                "success": [],
                "failed": [],
                "total": len(tool_ids)
            }

            for tool_id in tool_ids:
                try:
                    if action == "start":
                        success = await self.start_tool(tool_id, force)
                    elif action == "stop":
                        success = await self.stop_tool(tool_id, force)
                    elif action == "restart":
                        success = await self.restart_tool(tool_id, force)
                    else:
                        raise ToolValidationError(f"不支持的操作: {action}")

                    if success:
                        results["success"].append(tool_id)
                    else:
                        results["failed"].append({"id": tool_id, "error": "操作失败"})

                except Exception as e:
                    results["failed"].append({"id": tool_id, "error": str(e)})

            logger.info(f"批量工具操作完成: {action}, 成功: {len(results['success'])}, 失败: {len(results['failed'])}", category=LogCategory.SYSTEM)
            return results

        except Exception as e:
            logger.error(f"批量工具操作失败: {e}", category=LogCategory.SYSTEM)
            raise

    # 工具分类管理
    @error_handler
    @cached(ttl=300)
    def get_categories(self) -> List[ToolCategory]:
        """获取工具分类列表"""
        return self.db.query(ToolCategory).order_by(ToolCategory.sort_order, ToolCategory.name).all()

    @error_handler
    @cached(ttl=300)
    def get_category(self, category_id: int) -> Optional[ToolCategory]:
        """获取分类详情"""
        return self.db.query(ToolCategory).filter(ToolCategory.id == category_id).first()

    @error_handler
    @cached(ttl=300)
    def get_category_by_name(self, name: str) -> Optional[ToolCategory]:
        """根据名称获取分类"""
        return self.db.query(ToolCategory).filter(ToolCategory.name == name).first()

    @error_handler
    def create_category(self, category_data: CategoryCreate) -> ToolCategory:
        """创建工具分类"""
        try:
            category = ToolCategory(
                name=category_data.name,
                description=category_data.description,
                icon=category_data.icon,
                color=category_data.color,
                sort_order=category_data.sort_order or 0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.db.add(category)
            self.db.commit()
            self.db.refresh(category)

            logger.info(f"工具分类创建成功: {category.name} (ID: {category.id})", category=LogCategory.SYSTEM)
            return category

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建工具分类失败: {e}", category=LogCategory.SYSTEM)
            raise

    @error_handler
    def update_category(self, category_id: int, category_data: CategoryUpdate) -> ToolCategory:
        """更新工具分类"""
        try:
            category = self.get_category(category_id)
            if not category:
                raise CategoryNotFoundError(f"分类不存在: {category_id}")

            # 更新字段
            update_data = category_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(category, field, value)

            category.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(category)

            logger.info(f"工具分类更新成功: {category.name} (ID: {category.id})", category=LogCategory.SYSTEM)
            return category

        except Exception as e:
            self.db.rollback()
            logger.error(f"更新工具分类失败: {e}", category=LogCategory.SYSTEM)
            raise

    @error_handler
    def delete_category(self, category_id: int) -> bool:
        """删除工具分类"""
        try:
            category = self.get_category(category_id)
            if not category:
                raise CategoryNotFoundError(f"分类不存在: {category_id}")

            # 检查是否有工具使用此分类
            tools_count = self.db.query(MCPTool).filter(MCPTool.category == category.name).count()
            if tools_count > 0:
                raise ToolValidationError(f"分类下还有 {tools_count} 个工具，无法删除")

            self.db.delete(category)
            self.db.commit()

            logger.info(f"工具分类删除成功: {category.name} (ID: {category.id})", category=LogCategory.SYSTEM)
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"删除工具分类失败: {e}", category=LogCategory.SYSTEM)
            raise

    # 工具统计
    @error_handler
    @cached(ttl=300)
    def get_tool_stats(self) -> Dict[str, Any]:
        """获取工具统计信息"""
        try:
            total_tools = self.db.query(MCPTool).count()
            running_tools = self.db.query(MCPTool).filter(MCPTool.status == ToolStatus.RUNNING).count()
            stopped_tools = self.db.query(MCPTool).filter(MCPTool.status == ToolStatus.STOPPED).count()
            error_tools = self.db.query(MCPTool).filter(MCPTool.status == ToolStatus.ERROR).count()
            enabled_tools = self.db.query(MCPTool).filter(MCPTool.enabled == True).count()

            # 按类型统计
            type_stats = self.db.query(
                MCPTool.type,
                func.count(MCPTool.id).label('count')
            ).group_by(MCPTool.type).all()

            # 按分类统计
            category_stats = self.db.query(
                MCPTool.category,
                func.count(MCPTool.id).label('count')
            ).group_by(MCPTool.category).all()

            return {
                "total": total_tools,
                "active": running_tools,
                "inactive": stopped_tools,
                "error": error_tools,
                "enabled": enabled_tools,
                "disabled": total_tools - enabled_tools,
                "by_type": {(stat.type.value if stat.type else "未知"): stat.count for stat in type_stats},
                "by_category": {stat.category or "未分类": stat.count for stat in category_stats}
            }

        except Exception as e:
            logger.error(f"获取工具统计失败: {e}", category=LogCategory.SYSTEM)
            raise

    # 导入导出
    def export_tools(
        self,
        tool_ids: Optional[List[int]] = None,
        include_categories: bool = True
    ) -> Dict[str, Any]:
        """导出工具配置"""
        try:
            # 获取工具列表
            query = self.db.query(MCPTool)
            if tool_ids:
                query = query.filter(MCPTool.id.in_(tool_ids))

            tools = query.all()

            # 导出数据
            export_data = {
                "version": "1.0",
                "exported_at": datetime.utcnow().isoformat(),
                "tools": [self._tool_to_export_dict(tool) for tool in tools]
            }

            # 包含分类信息
            if include_categories:
                categories = self.get_categories()
                export_data["categories"] = [
                    self._category_to_export_dict(category) for category in categories
                ]

            return export_data

        except Exception as e:
            logger.error(f"导出工具配置失败: {e}", category=LogCategory.SYSTEM)
            raise

    @error_handler
    def import_tools(self, import_data: ToolImport) -> Dict[str, Any]:
        """导入工具配置"""
        try:
            result = {
                "imported_tools": 0,
                "imported_categories": 0,
                "skipped_tools": 0,
                "skipped_categories": 0,
                "errors": []
            }

            # 导入分类
            if import_data.categories:
                for category_data in import_data.categories:
                    try:
                        if not self.get_category_by_name(category_data["name"]):
                            category = CategoryCreate(**category_data)
                            self.create_category(category)
                            result["imported_categories"] += 1
                        else:
                            result["skipped_categories"] += 1
                    except Exception as e:
                        result["errors"].append(f"导入分类失败 {category_data.get('name', '')}: {e}")

            # 导入工具
            for tool_data in import_data.tools:
                try:
                    if not self.get_tool_by_name(tool_data["name"]):
                        # 移除运行时状态字段
                        clean_data = {k: v for k, v in tool_data.items()
                                    if k not in ['id', 'status', 'process_id', 'last_started_at',
                                                'last_stopped_at', 'last_error_at', 'restart_count']}

                        tool = ToolCreate(**clean_data)
                        self.create_tool(tool)
                        result["imported_tools"] += 1
                    else:
                        result["skipped_tools"] += 1
                except Exception as e:
                    result["errors"].append(f"导入工具失败 {tool_data.get('name', '')}: {e}")

            return result

        except Exception as e:
            logger.error(f"导入工具配置失败: {e}", category=LogCategory.SYSTEM)
            raise

    @error_handler
    def validate_tool_config(self, tool_data: ToolCreate) -> Dict[str, Any]:
        """验证工具配置"""
        try:
            errors = []
            warnings = []

            # 验证命令
            if not tool_data.command or not tool_data.command.strip():
                errors.append("工具命令不能为空")

            # 验证连接配置
            if tool_data.type == ToolType.STDIO and not tool_data.command:
                errors.append("STDIO 类型工具必须指定命令")

            if tool_data.connection_type in ["http", "websocket"]:
                if not tool_data.host or not tool_data.port:
                    errors.append(f"{tool_data.connection_type.upper()} 连接类型必须指定主机和端口")

            # 注意：这里不检查工具名称是否已存在，因为这是验证配置而不是创建工具
            # 实际的重名检查应该在创建工具时进行

            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings
            }

        except Exception as e:
            logger.error(f"验证工具配置失败: {e}", category=LogCategory.SYSTEM)
            return {
                "valid": False,
                "errors": [f"验证过程出错: {str(e)}"],
                "warnings": []
            }

    # 私有方法
    @error_handler
    def _validate_tool_config(self, tool_data: ToolCreate) -> None:
        """验证工具配置"""
        # 验证命令
        if not tool_data.command or not tool_data.command.strip():
            raise ToolValidationError("工具命令不能为空")

        # 验证连接配置
        if tool_data.connection_type in ["http", "websocket"]:
            if not tool_data.host or not tool_data.port:
                raise ToolValidationError(f"{tool_data.connection_type.upper()} 连接类型必须指定主机和端口")

    @error_handler
    def _tool_to_export_dict(self, tool: MCPTool) -> Dict[str, Any]:
        """将工具转换为导出字典"""
        return {
            "name": tool.name,
            "description": tool.description,
            "type": tool.type.value,
            "category": tool.category,
            "command": tool.command,
            "args": tool.args,
            "env": tool.env,
            "working_dir": tool.working_dir,
            "connection_config": tool.connection_config,
            "runtime_config": tool.runtime_config,
            "enabled": tool.enabled,
            "auto_start": tool.auto_start,
            "auto_restart": tool.auto_restart,
            "max_restarts": tool.max_restarts,
            "restart_delay": tool.restart_delay,
            "health_check_interval": tool.health_check_interval,
            "timeout": tool.timeout,
            "metadata": tool.metadata
        }

    @error_handler
    def _category_to_export_dict(self, category: ToolCategory) -> Dict[str, Any]:
        """将分类转换为导出字典"""
        return {
            "name": category.name,
            "description": category.description,
            "icon": category.icon,
            "color": category.color,
            "sort_order": category.sort_order
        }
