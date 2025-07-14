"""工具管理服务"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
import json
import logging

from app.models.tool import MCPTool, ToolCategory, ToolStatus, ToolType
from app.schemas.tool import (
    ToolCreate,
    ToolUpdate,
    CategoryCreate,
    CategoryUpdate,
    ToolExport,
    ToolImport,
)
from app.core.config import settings
from app.utils.exceptions import (
    ToolNotFoundError,
    ToolValidationError,
    CategoryNotFoundError,
)

logger = logging.getLogger(__name__)

class ToolService:
    """工具管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # 工具 CRUD 操作
    def get_tools(
        self,
        page: int = 1,
        size: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[MCPTool], int]:
        """获取工具列表"""
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
    
    def get_tool(self, tool_id: int) -> Optional[MCPTool]:
        """获取工具详情"""
        return self.db.query(MCPTool).filter(MCPTool.id == tool_id).first()
    
    def get_tool_by_name(self, name: str) -> Optional[MCPTool]:
        """根据名称获取工具"""
        return self.db.query(MCPTool).filter(MCPTool.name == name).first()
    
    def create_tool(self, tool_data: ToolCreate) -> MCPTool:
        """创建工具"""
        try:
            # 验证工具配置
            self._validate_tool_config(tool_data)
            
            # 创建工具实例
            tool = MCPTool(
                name=tool_data.name,
                description=tool_data.description,
                type=tool_data.type,
                category=tool_data.category,
                command=tool_data.command,
                args=tool_data.args or [],
                env=tool_data.env or {},
                working_dir=tool_data.working_dir,
                connection_config=tool_data.connection_config.dict() if tool_data.connection_config else {},
                runtime_config=tool_data.runtime_config.dict() if tool_data.runtime_config else {},
                enabled=tool_data.enabled,
                auto_start=tool_data.auto_start,
                auto_restart=tool_data.auto_restart,
                max_restarts=tool_data.max_restarts,
                restart_delay=tool_data.restart_delay,
                health_check_interval=tool_data.health_check_interval,
                timeout=tool_data.timeout,
                metadata=tool_data.metadata or {},
                status=ToolStatus.STOPPED,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(tool)
            self.db.commit()
            self.db.refresh(tool)
            
            logger.info(f"工具创建成功: {tool.name} (ID: {tool.id})")
            return tool
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建工具失败: {e}")
            raise ToolValidationError(f"创建工具失败: {e}")
    
    def update_tool(self, tool_id: int, tool_data: ToolUpdate) -> MCPTool:
        """更新工具"""
        try:
            tool = self.get_tool(tool_id)
            if not tool:
                raise ToolNotFoundError(f"工具不存在: {tool_id}")
            
            # 验证更新数据
            if tool_data.name and tool_data.name != tool.name:
                existing = self.get_tool_by_name(tool_data.name)
                if existing:
                    raise ToolValidationError("工具名称已存在")
            
            # 更新字段
            update_data = tool_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                if field in ['connection_config', 'runtime_config', 'metadata'] and value:
                    value = value.dict() if hasattr(value, 'dict') else value
                setattr(tool, field, value)
            
            tool.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(tool)
            
            logger.info(f"工具更新成功: {tool.name} (ID: {tool.id})")
            return tool
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新工具失败: {e}")
            raise
    
    def delete_tool(self, tool_id: int) -> bool:
        """删除工具"""
        try:
            tool = self.get_tool(tool_id)
            if not tool:
                raise ToolNotFoundError(f"工具不存在: {tool_id}")
            
            self.db.delete(tool)
            self.db.commit()
            
            logger.info(f"工具删除成功: {tool.name} (ID: {tool.id})")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除工具失败: {e}")
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
            
            logger.info(f"工具状态更新: {tool.name} {old_status.value} -> {status.value}")
            return tool
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新工具状态失败: {e}")
            raise
    
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
            logger.error(f"更新重启计数失败: {e}")
            raise
    
    # 工具分类管理
    def get_categories(self) -> List[ToolCategory]:
        """获取工具分类列表"""
        return self.db.query(ToolCategory).order_by(ToolCategory.sort_order, ToolCategory.name).all()
    
    def get_category(self, category_id: int) -> Optional[ToolCategory]:
        """获取分类详情"""
        return self.db.query(ToolCategory).filter(ToolCategory.id == category_id).first()
    
    def get_category_by_name(self, name: str) -> Optional[ToolCategory]:
        """根据名称获取分类"""
        return self.db.query(ToolCategory).filter(ToolCategory.name == name).first()
    
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
            
            logger.info(f"工具分类创建成功: {category.name} (ID: {category.id})")
            return category
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建工具分类失败: {e}")
            raise
    
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
            
            logger.info(f"工具分类更新成功: {category.name} (ID: {category.id})")
            return category
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新工具分类失败: {e}")
            raise
    
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
            
            logger.info(f"工具分类删除成功: {category.name} (ID: {category.id})")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除工具分类失败: {e}")
            raise
    
    # 工具统计
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
                "running": running_tools,
                "stopped": stopped_tools,
                "error": error_tools,
                "enabled": enabled_tools,
                "disabled": total_tools - enabled_tools,
                "by_type": {stat.type.value: stat.count for stat in type_stats},
                "by_category": {stat.category or "未分类": stat.count for stat in category_stats}
            }
            
        except Exception as e:
            logger.error(f"获取工具统计失败: {e}")
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
            logger.error(f"导出工具配置失败: {e}")
            raise
    
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
            logger.error(f"导入工具配置失败: {e}")
            raise
    
    # 私有方法
    def _validate_tool_config(self, tool_data: ToolCreate) -> None:
        """验证工具配置"""
        # 验证命令
        if not tool_data.command or not tool_data.command.strip():
            raise ToolValidationError("工具命令不能为空")
        
        # 验证连接配置
        if tool_data.type == ToolType.STDIO and not tool_data.command:
            raise ToolValidationError("STDIO 类型工具必须指定命令")
        
        if tool_data.type == ToolType.SERVER and tool_data.connection_config:
            config = tool_data.connection_config
            if not config.host or not config.port:
                raise ToolValidationError("服务器类型工具必须指定主机和端口")
    
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
    
    def _category_to_export_dict(self, category: ToolCategory) -> Dict[str, Any]:
        """将分类转换为导出字典"""
        return {
            "name": category.name,
            "description": category.description,
            "icon": category.icon,
            "color": category.color,
            "sort_order": category.sort_order
        }