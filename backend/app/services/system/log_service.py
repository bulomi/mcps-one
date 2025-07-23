"""日志管理服务"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
import json
from app.core import get_logger, LogLevel, LogCategory, create_log_context
from app.core.unified_cache import cached
import asyncio
from pathlib import Path
import csv
import io

from app.models.log import SystemLog, OperationLog, MCPLog, LogLevel, LogCategory
from app.schemas.log import (
    SystemLogCreate,
    OperationLogCreate,
    MCPLogCreate,
    LogQuery,
    LogStatistics,
    LogCleanup,
    OperationAction,
    OperationStatus,
    MessageDirection
)
from app.core import get_unified_config_manager
from app.core import MCPSError, handle_error, error_handler, error_context
from app.utils.exceptions import LogServiceError

logger = get_logger(__name__)

# 常量定义
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200
DEFAULT_STATS_DAYS = 30
DEFAULT_EXPORT_LIMIT = 10000

class LogService:
    """日志管理服务"""

    @error_handler
    def __init__(self, db: Session):
        self.db = db

    # 系统日志
    def get_system_logs(
        self,
        page: int = 1,
        size: int = DEFAULT_PAGE_SIZE,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[SystemLog], int]:
        """获取系统日志列表"""
        query = self.db.query(SystemLog)

        # 应用过滤条件
        if filters:
            query = self._apply_system_log_filters(query, filters)

        # 获取总数
        total = query.count()

        # 分页和排序
        logs = query.order_by(desc(SystemLog.timestamp)).offset(
            (page - 1) * size
        ).limit(size).all()

        return logs, total

    @error_handler
    @cached(ttl=300)
    @error_handler
    @cached(ttl=300)
    def get_system_log(self, log_id: int) -> Optional[SystemLog]:
        """获取系统日志详情"""
        return self.db.query(SystemLog).filter(SystemLog.id == log_id).first()

    @error_handler
    def create_system_log(self, log_data: SystemLogCreate) -> SystemLog:
        """创建系统日志"""
        try:
            log = SystemLog(
                level=log_data.level,
                category=log_data.category,
                message=log_data.message,
                details=log_data.details,
                source=log_data.source,
                tool_id=log_data.tool_id,
                tool_name=log_data.tool_name,
                stack_trace=log_data.stack_trace,
                request_id=log_data.request_id,
                ip_address=log_data.ip_address,
                user_agent=log_data.user_agent,
                timestamp=datetime.utcnow()
            )

            self.db.add(log)
            self.db.commit()
            self.db.refresh(log)

            return log

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建系统日志失败: {e}", category=LogCategory.SYSTEM)
            raise LogServiceError(f"创建系统日志失败: {e}")

    # 操作日志
    def get_operation_logs(
        self,
        page: int = 1,
        size: int = DEFAULT_PAGE_SIZE,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[OperationLog], int]:
        """获取操作日志列表"""
        query = self.db.query(OperationLog)

        # 应用过滤条件
        if filters:
            query = self._apply_operation_log_filters(query, filters)

        # 获取总数
        total = query.count()

        # 分页和排序
        logs = query.order_by(desc(OperationLog.timestamp)).offset(
            (page - 1) * size
        ).limit(size).all()

        return logs, total

    @error_handler
    @cached(ttl=300)
    def get_operation_log(self, log_id: int) -> Optional[OperationLog]:
        """获取操作日志详情"""
        return self.db.query(OperationLog).filter(OperationLog.id == log_id).first()

    @error_handler
    def create_operation_log(self, log_data: OperationLogCreate) -> OperationLog:
        """创建操作日志"""
        try:
            log = OperationLog(
                action=log_data.action,
                resource_type=log_data.resource_type,
                resource_id=log_data.resource_id,
                resource_name=log_data.resource_name,
                description=log_data.description,
                status=log_data.status,
                error_message=log_data.error_message,
                duration=log_data.duration,
                user_id=log_data.user_id,
                ip_address=log_data.ip_address,
                user_agent=log_data.user_agent,
                request_data=log_data.request_data,
                response_data=log_data.response_data,
                timestamp=log_data.timestamp or datetime.utcnow()
            )

            self.db.add(log)
            self.db.commit()
            self.db.refresh(log)

            return log

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建操作日志失败: {e}", category=LogCategory.SYSTEM)
            raise LogServiceError(f"创建操作日志失败: {e}")

    # MCP 协议日志
    def get_mcp_logs(
        self,
        page: int = 1,
        size: int = DEFAULT_PAGE_SIZE,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[MCPLog], int]:
        """获取 MCP 协议日志列表"""
        query = self.db.query(MCPLog)

        # 应用过滤条件
        if filters:
            query = self._apply_mcp_log_filters(query, filters)

        # 获取总数
        total = query.count()

        # 分页和排序
        logs = query.order_by(desc(MCPLog.timestamp)).offset(
            (page - 1) * size
        ).limit(size).all()

        return logs, total

    @error_handler
    @cached(ttl=300)
    def get_mcp_log(self, log_id: int) -> Optional[MCPLog]:
        """获取 MCP 协议日志详情"""
        return self.db.query(MCPLog).filter(MCPLog.id == log_id).first()

    @error_handler
    def create_mcp_log(self, log_data: MCPLogCreate) -> MCPLog:
        """创建 MCP 协议日志"""
        try:
            log = MCPLog(
                tool_id=log_data.tool_id,
                tool_name=log_data.tool_name,
                message_type=log_data.message_type,
                direction=log_data.direction,
                method=log_data.method,
                request_data=log_data.request_data,
                response_data=log_data.response_data,
                error_data=log_data.error_data,
                processing_time_ms=log_data.processing_time_ms,
                timestamp=datetime.utcnow()
            )

            self.db.add(log)
            self.db.commit()
            self.db.refresh(log)

            return log

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建 MCP 协议日志失败: {e}", category=LogCategory.SYSTEM)
            raise LogServiceError(f"创建 MCP 协议日志失败: {e}")

    # 日志统计
    @error_handler
    @cached(ttl=300)
    def get_log_statistics(self, period: str = "24h") -> Dict[str, Any]:
        """获取日志统计"""
        try:
            # 解析时间周期
            if period == "1h":
                start_time = datetime.utcnow() - timedelta(hours=1)
            elif period == "24h":
                start_time = datetime.utcnow() - timedelta(days=1)
            elif period == "7d":
                start_time = datetime.utcnow() - timedelta(days=7)
            elif period == "30d":
                start_time = datetime.utcnow() - timedelta(days=30)
            else:
                start_time = datetime.utcnow() - timedelta(days=1)

            # 系统日志统计
            system_stats = self._get_system_log_stats(start_time)

            # 操作日志统计
            operation_stats = self._get_operation_log_stats(start_time)

            # MCP 日志统计
            mcp_stats = self._get_mcp_log_stats(start_time)

            # 总体统计
            total_logs = (
                system_stats["total"] +
                operation_stats["total"] +
                mcp_stats["total"]
            )

            return {
                "period": period,
                "start_time": start_time.isoformat(),
                "end_time": datetime.utcnow().isoformat(),
                "total_logs": total_logs,
                "system_logs": system_stats,
                "operation_logs": operation_stats,
                "mcp_logs": mcp_stats
            }

        except Exception as e:
            logger.error(f"获取日志统计失败: {e}", category=LogCategory.SYSTEM)
            raise

    @error_handler
    @cached(ttl=300)
    def get_summary_statistics(self) -> Dict[str, Any]:
        """获取汇总统计"""
        try:
            # 今日统计
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

            # 系统日志汇总
            system_total = self.db.query(SystemLog).count()
            system_today = self.db.query(SystemLog).filter(
                SystemLog.timestamp >= today
            ).count()
            system_errors = self.db.query(SystemLog).filter(
                and_(
                    SystemLog.timestamp >= today,
                    SystemLog.level == LogLevel.ERROR
                )
            ).count()

            # 操作日志汇总
            operation_total = self.db.query(OperationLog).count()
            operation_today = self.db.query(OperationLog).filter(
                OperationLog.timestamp >= today
            ).count()
            operation_errors = self.db.query(OperationLog).filter(
                and_(
                    OperationLog.timestamp >= today,
                    OperationLog.status == OperationStatus.FAILED
                )
            ).count()

            # MCP 日志汇总
            mcp_total = self.db.query(MCPLog).count()
            mcp_today = self.db.query(MCPLog).filter(
                MCPLog.timestamp >= today
            ).count()
            mcp_errors = self.db.query(MCPLog).filter(
                and_(
                    MCPLog.timestamp >= today,
                    MCPLog.error_data.isnot(None)
                )
            ).count()

            # 最近活跃工具
            active_tools = self.db.query(
                MCPLog.tool_id,
                func.count(MCPLog.id).label('log_count')
            ).filter(
                MCPLog.timestamp >= today
            ).group_by(MCPLog.tool_id).order_by(
                desc('log_count')
            ).limit(5).all()

            return {
                "overview": {
                    "total_logs": system_total + operation_total + mcp_total,
                    "today_logs": system_today + operation_today + mcp_today,
                    "today_errors": system_errors + operation_errors + mcp_errors
                },
                "system_logs": {
                    "total": system_total,
                    "today": system_today,
                    "errors": system_errors
                },
                "operation_logs": {
                    "total": operation_total,
                    "today": operation_today,
                    "errors": operation_errors
                },
                "mcp_logs": {
                    "total": mcp_total,
                    "today": mcp_today,
                    "errors": mcp_errors
                },
                "active_tools": [
                    {"tool_id": tool_id, "log_count": count}
                    for tool_id, count in active_tools
                ],
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"获取汇总统计失败: {e}", category=LogCategory.SYSTEM)
            raise

    # 日志清理
    @error_handler
    def cleanup_logs(self, cleanup_data: LogCleanup) -> Dict[str, Any]:
        """清理日志"""
        try:
            result = {
                "system_logs_deleted": 0,
                "operation_logs_deleted": 0,
                "mcp_logs_deleted": 0,
                "total_deleted": 0
            }

            # 计算截止时间
            if cleanup_data.days:
                cutoff_time = datetime.utcnow() - timedelta(days=cleanup_data.days)
            else:
                cutoff_time = cleanup_data.before_date

            # 清理系统日志
            if cleanup_data.log_types is None or "system" in cleanup_data.log_types:
                query = self.db.query(SystemLog).filter(SystemLog.timestamp < cutoff_time)

                if cleanup_data.levels:
                    query = query.filter(SystemLog.level.in_(cleanup_data.levels))

                deleted = query.delete(synchronize_session=False)
                result["system_logs_deleted"] = deleted

            # 清理操作日志
            if cleanup_data.log_types is None or "operation" in cleanup_data.log_types:
                query = self.db.query(OperationLog).filter(OperationLog.timestamp < cutoff_time)

                deleted = query.delete(synchronize_session=False)
                result["operation_logs_deleted"] = deleted

            # 清理 MCP 日志
            if cleanup_data.log_types is None or "mcp" in cleanup_data.log_types:
                query = self.db.query(MCPLog).filter(MCPLog.timestamp < cutoff_time)

                deleted = query.delete(synchronize_session=False)
                result["mcp_logs_deleted"] = deleted

            # 计算总删除数
            result["total_deleted"] = (
                result["system_logs_deleted"] +
                result["operation_logs_deleted"] +
                result["mcp_logs_deleted"]
            )

            self.db.commit()

            logger.info(f"日志清理完成: {result}", category=LogCategory.SYSTEM)
            return result

        except Exception as e:
            self.db.rollback()
            logger.error(f"日志清理失败: {e}", category=LogCategory.SYSTEM)
            raise

    # 日志导出
    def export_logs(
        self,
        log_type: str,
        format: str = "csv",
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """导出日志"""
        try:
            # 获取日志数据
            if log_type == "system":
                logs, _ = self.get_system_logs(page=1, size=DEFAULT_EXPORT_LIMIT, filters=filters)
                headers = ["ID", "级别", "分类", "消息", "来源", "时间"]
                rows = [
                    [log.id, log.level.value, log.category.value, log.message, log.source, log.timestamp]
                    for log in logs
                ]
            elif log_type == "operation":
                logs, _ = self.get_operation_logs(page=1, size=DEFAULT_EXPORT_LIMIT, filters=filters)
                headers = ["ID", "操作", "资源类型", "资源名称", "状态", "时间"]
                rows = [
                    [log.id, log.action.value, log.resource_type, log.resource_name, log.status.value, log.timestamp]
                    for log in logs
                ]
            elif log_type == "mcp":
                logs, _ = self.get_mcp_logs(page=1, size=DEFAULT_EXPORT_LIMIT, filters=filters)
                headers = ["ID", "工具ID", "消息类型", "方向", "方法", "时间"]
                rows = [
                    [log.id, log.tool_id, log.message_type, log.direction.value, log.method, log.timestamp]
                    for log in logs
                ]
            else:
                raise LogServiceError(f"不支持的日志类型: {log_type}")

            # 生成导出内容
            if format == "csv":
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(headers)
                writer.writerows(rows)
                return output.getvalue()
            elif format == "json":
                data = [
                    dict(zip(headers, row))
                    for row in rows
                ]
                return json.dumps(data, ensure_ascii=False, indent=2, default=str)
            else:
                raise LogServiceError(f"不支持的导出格式: {format}")

        except Exception as e:
            logger.error(f"导出日志失败: {e}", category=LogCategory.SYSTEM)
            raise

    # 实时日志
    async def get_realtime_logs(
        self,
        log_types: List[str],
        levels: Optional[List[LogLevel]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取实时日志"""
        try:
            logs = []

            # 获取最近的日志
            if "system" in log_types:
                query = self.db.query(SystemLog)
                if levels:
                    query = query.filter(SystemLog.level.in_(levels))

                system_logs = query.order_by(desc(SystemLog.timestamp)).limit(limit).all()
                logs.extend([
                    {
                        "type": "system",
                        "id": log.id,
                        "level": log.level.value,
                        "category": log.category.value,
                        "message": log.message,
                        "source": log.source,
                        "timestamp": log.timestamp.isoformat()
                    }
                    for log in system_logs
                ])

            if "operation" in log_types:
                operation_logs = self.db.query(OperationLog).order_by(
                    desc(OperationLog.timestamp)
                ).limit(limit).all()

                logs.extend([
                    {
                        "type": "operation",
                        "id": log.id,
                        "action": log.action.value,
                        "resource_type": log.resource_type,
                        "resource_name": log.resource_name,
                        "status": log.status.value,
                        "timestamp": log.timestamp.isoformat()
                    }
                    for log in operation_logs
                ])

            if "mcp" in log_types:
                mcp_logs = self.db.query(MCPLog).order_by(
                    desc(MCPLog.timestamp)
                ).limit(limit).all()

                logs.extend([
                    {
                        "type": "mcp",
                        "id": log.id,
                        "tool_id": log.tool_id,
                        "message_type": log.message_type,
                        "direction": log.direction.value,
                        "method": log.method,
                        "timestamp": log.timestamp.isoformat()
                    }
                    for log in mcp_logs
                ])

            # 按时间排序
            logs.sort(key=lambda x: x["timestamp"], reverse=True)

            return logs[:limit]

        except Exception as e:
            logger.error(f"获取实时日志失败: {e}", category=LogCategory.SYSTEM)
            raise

    # 日志搜索
    def search_logs(
        self,
        query: LogQuery,
        page: int = 1,
        size: int = DEFAULT_PAGE_SIZE
    ) -> Tuple[List[Dict[str, Any]], int]:
        """搜索日志"""
        try:
            results = []
            total = 0

            # 搜索系统日志
            if query.log_types is None or "system" in query.log_types:
                system_query = self.db.query(SystemLog)
                system_query = self._apply_search_filters(system_query, query, "system")

                system_logs = system_query.order_by(desc(SystemLog.timestamp)).all()
                results.extend([
                    {
                        "type": "system",
                        "id": log.id,
                        "level": log.level.value,
                        "category": log.category.value,
                        "message": log.message,
                        "source": log.source,
                        "timestamp": log.timestamp.isoformat(),
                        "relevance": self._calculate_relevance(log.message, query.keyword)
                    }
                    for log in system_logs
                ])

            # 搜索操作日志
            if query.log_types is None or "operation" in query.log_types:
                operation_query = self.db.query(OperationLog)
                operation_query = self._apply_search_filters(operation_query, query, "operation")

                operation_logs = operation_query.order_by(desc(OperationLog.timestamp)).all()
                results.extend([
                    {
                        "type": "operation",
                        "id": log.id,
                        "action": log.action.value,
                        "resource_type": log.resource_type,
                        "resource_name": log.resource_name,
                        "description": log.description,
                        "status": log.status.value,
                        "timestamp": log.timestamp.isoformat(),
                        "relevance": self._calculate_relevance(log.description or "", query.keyword)
                    }
                    for log in operation_logs
                ])

            # 搜索 MCP 日志
            if query.log_types is None or "mcp" in query.log_types:
                mcp_query = self.db.query(MCPLog)
                mcp_query = self._apply_search_filters(mcp_query, query, "mcp")

                mcp_logs = mcp_query.order_by(desc(MCPLog.timestamp)).all()
                results.extend([
                    {
                        "type": "mcp",
                        "id": log.id,
                        "tool_id": log.tool_id,
                        "message_type": log.message_type,
                        "direction": log.direction.value,
                        "method": log.method,
                        "timestamp": log.timestamp.isoformat(),
                        "relevance": self._calculate_relevance(log.method or "", query.keyword)
                    }
                    for log in mcp_logs
                ])

            # 按相关性和时间排序
            results.sort(key=lambda x: (x["relevance"], x["timestamp"]), reverse=True)

            total = len(results)

            # 分页
            start = (page - 1) * size
            end = start + size
            results = results[start:end]

            return results, total

        except Exception as e:
            logger.error(f"搜索日志失败: {e}", category=LogCategory.SYSTEM)
            raise

    # 私有方法
    @error_handler
    def _apply_system_log_filters(self, query, filters: Dict[str, Any]):
        """应用系统日志过滤条件"""
        if filters.get('level'):
            # 处理日志级别过滤，支持字符串和枚举
            level_value = filters['level']
            if isinstance(level_value, str):
                # 将字符串转换为枚举
                try:
                    level_enum = LogLevel(level_value.upper())
                    query = query.filter(SystemLog.level == level_enum)
                except ValueError:
                    # 如果无效的级别值，忽略此过滤条件
                    logger.warning(f"无效的日志级别: {level_value}", category=LogCategory.SYSTEM)
            else:
                query = query.filter(SystemLog.level == level_value)

        if filters.get('category'):
            query = query.filter(SystemLog.category == filters['category'])

        if filters.get('source'):
            query = query.filter(SystemLog.source.ilike(f"%{filters['source']}%"))

        if filters.get('start_time'):
            query = query.filter(SystemLog.timestamp >= filters['start_time'])

        if filters.get('end_time'):
            query = query.filter(SystemLog.timestamp <= filters['end_time'])

        if filters.get('search'):
            search_term = f"%{filters['search']}%"
            query = query.filter(
                or_(
                    SystemLog.message.ilike(search_term),
                    SystemLog.details.ilike(search_term)
                )
            )

        return query

    @error_handler
    def _apply_operation_log_filters(self, query, filters: Dict[str, Any]):
        """应用操作日志过滤条件"""
        if filters.get('action'):
            query = query.filter(OperationLog.action == filters['action'])

        if filters.get('resource_type'):
            query = query.filter(OperationLog.resource_type == filters['resource_type'])

        if filters.get('status'):
            query = query.filter(OperationLog.status == filters['status'])

        if filters.get('user_id'):
            query = query.filter(OperationLog.user_id == filters['user_id'])

        if filters.get('start_time'):
            query = query.filter(OperationLog.timestamp >= filters['start_time'])

        if filters.get('end_time'):
            query = query.filter(OperationLog.timestamp <= filters['end_time'])

        if filters.get('search'):
            search_term = f"%{filters['search']}%"
            query = query.filter(
                or_(
                    OperationLog.description.ilike(search_term),
                    OperationLog.resource_name.ilike(search_term)
                )
            )

        return query

    @error_handler
    def _apply_mcp_log_filters(self, query, filters: Dict[str, Any]):
        """应用 MCP 日志过滤条件"""
        if filters.get('tool_id'):
            query = query.filter(MCPLog.tool_id == filters['tool_id'])

        # 会话管理功能已移除
        # if filters.get('session_id'):
        #     query = query.filter(MCPLog.session_id == filters['session_id'])

        if filters.get('message_type'):
            query = query.filter(MCPLog.message_type == filters['message_type'])

        if filters.get('direction'):
            query = query.filter(MCPLog.direction == filters['direction'])

        if filters.get('method'):
            query = query.filter(MCPLog.method.ilike(f"%{filters['method']}%"))

        if filters.get('start_time'):
            query = query.filter(MCPLog.timestamp >= filters['start_time'])

        if filters.get('end_time'):
            query = query.filter(MCPLog.timestamp <= filters['end_time'])

        if filters.get('has_error'):
            if filters['has_error']:
                query = query.filter(MCPLog.error_data.isnot(None))
            else:
                query = query.filter(MCPLog.error_data.is_(None))

        return query

    @error_handler
    def _apply_search_filters(self, query, search_query: LogQuery, log_type: str):
        """应用搜索过滤条件"""
        # 时间范围
        if search_query.start_time:
            if log_type == "system":
                query = query.filter(SystemLog.timestamp >= search_query.start_time)
            elif log_type == "operation":
                query = query.filter(OperationLog.timestamp >= search_query.start_time)
            elif log_type == "mcp":
                query = query.filter(MCPLog.timestamp >= search_query.start_time)

        if search_query.end_time:
            if log_type == "system":
                query = query.filter(SystemLog.timestamp <= search_query.end_time)
            elif log_type == "operation":
                query = query.filter(OperationLog.timestamp <= search_query.end_time)
            elif log_type == "mcp":
                query = query.filter(MCPLog.timestamp <= search_query.end_time)

        # 关键词搜索
        if search_query.keyword:
            keyword = f"%{search_query.keyword}%"
            if log_type == "system":
                query = query.filter(
                    or_(
                        SystemLog.message.ilike(keyword),
                        SystemLog.details.ilike(keyword),
                        SystemLog.source.ilike(keyword)
                    )
                )
            elif log_type == "operation":
                query = query.filter(
                    or_(
                        OperationLog.description.ilike(keyword),
                        OperationLog.resource_name.ilike(keyword),
                        OperationLog.resource_type.ilike(keyword)
                    )
                )
            elif log_type == "mcp":
                query = query.filter(
                    or_(
                        MCPLog.method.ilike(keyword),
                        MCPLog.content.ilike(keyword)
                    )
                )

        return query

    @error_handler
    def _get_system_log_stats(self, start_time: datetime) -> Dict[str, Any]:
        """获取系统日志统计"""
        total = self.db.query(SystemLog).filter(
            SystemLog.timestamp >= start_time
        ).count()

        # 按级别统计
        level_stats = self.db.query(
            SystemLog.level,
            func.count(SystemLog.id).label('count')
        ).filter(
            SystemLog.timestamp >= start_time
        ).group_by(SystemLog.level).all()

        # 按分类统计
        category_stats = self.db.query(
            SystemLog.category,
            func.count(SystemLog.id).label('count')
        ).filter(
            SystemLog.timestamp >= start_time
        ).group_by(SystemLog.category).all()

        return {
            "total": total,
            "by_level": {level.value: count for level, count in level_stats},
            "by_category": {category.value: count for category, count in category_stats}
        }

    @error_handler
    def _get_operation_log_stats(self, start_time: datetime) -> Dict[str, Any]:
        """获取操作日志统计"""
        total = self.db.query(OperationLog).filter(
            OperationLog.timestamp >= start_time
        ).count()

        # 按操作统计
        action_stats = self.db.query(
            OperationLog.action,
            func.count(OperationLog.id).label('count')
        ).filter(
            OperationLog.timestamp >= start_time
        ).group_by(OperationLog.action).all()

        # 按状态统计
        status_stats = self.db.query(
            OperationLog.status,
            func.count(OperationLog.id).label('count')
        ).filter(
            OperationLog.timestamp >= start_time
        ).group_by(OperationLog.status).all()

        return {
            "total": total,
            "by_action": {action.value: count for action, count in action_stats},
            "by_status": {status.value: count for status, count in status_stats}
        }

    @error_handler
    def _get_mcp_log_stats(self, start_time: datetime) -> Dict[str, Any]:
        """获取 MCP 日志统计"""
        total = self.db.query(MCPLog).filter(
            MCPLog.timestamp >= start_time
        ).count()

        # 按工具统计
        tool_stats = self.db.query(
            MCPLog.tool_id,
            func.count(MCPLog.id).label('count')
        ).filter(
            MCPLog.timestamp >= start_time
        ).group_by(MCPLog.tool_id).all()

        # 按方向统计
        direction_stats = self.db.query(
            MCPLog.direction,
            func.count(MCPLog.id).label('count')
        ).filter(
            MCPLog.timestamp >= start_time
        ).group_by(MCPLog.direction).all()

        # 错误统计
        error_count = self.db.query(MCPLog).filter(
            and_(
                MCPLog.timestamp >= start_time,
                MCPLog.error_data.isnot(None)
            )
        ).count()

        return {
            "total": total,
            "by_tool": {tool_id: count for tool_id, count in tool_stats},
            "by_direction": {direction.value: count for direction, count in direction_stats},
            "errors": error_count
        }

    @error_handler
    def _calculate_relevance(self, text: str, keyword: str) -> float:
        """计算相关性分数"""
        if not keyword or not text:
            return 0.0

        text_lower = text.lower()
        keyword_lower = keyword.lower()

        # 精确匹配
        if keyword_lower in text_lower:
            return 1.0

        # 部分匹配
        words = keyword_lower.split()
        matches = sum(1 for word in words if word in text_lower)

        return matches / len(words) if words else 0.0
