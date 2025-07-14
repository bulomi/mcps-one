"""日志相关数据模型"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Enum, Index
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from datetime import datetime
from typing import Dict, Any, Optional

from app.core.database import Base

class LogLevel(PyEnum):
    """日志级别枚举"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class LogCategory(PyEnum):
    """日志分类枚举"""
    SYSTEM = "system"        # 系统日志
    TOOL = "tool"            # 工具日志
    API = "api"              # API 日志
    MCP = "mcp"              # MCP 协议日志
    AUTH = "auth"            # 认证日志
    OPERATION = "operation"  # 操作日志

class SystemLog(Base):
    """系统日志模型"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(Enum(LogLevel), index=True, nullable=False, comment="日志级别")
    category = Column(Enum(LogCategory), index=True, nullable=False, comment="日志分类")
    message = Column(Text, nullable=False, comment="日志消息")
    
    # 上下文信息
    source = Column(String(100), index=True, comment="日志来源")
    tool_id = Column(Integer, index=True, comment="关联工具ID")
    tool_name = Column(String(100), index=True, comment="工具名称")
    
    # 详细信息
    details = Column(JSON, comment="详细信息")
    stack_trace = Column(Text, comment="堆栈跟踪")
    
    # 请求信息（API 日志）
    request_id = Column(String(50), index=True, comment="请求ID")
    user_agent = Column(String(500), comment="用户代理")
    ip_address = Column(String(50), comment="IP地址")
    
    # 时间字段
    timestamp = Column(DateTime, default=func.now(), index=True, comment="时间戳")
    
    # 创建复合索引
    __table_args__ = (
        Index('idx_logs_category_level_time', 'category', 'level', 'timestamp'),
        Index('idx_logs_tool_time', 'tool_id', 'timestamp'),
        Index('idx_logs_source_time', 'source', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<SystemLog(id={self.id}, level='{self.level}', category='{self.category}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "level": self.level.value if self.level else None,
            "category": self.category.value if self.category else None,
            "message": self.message,
            "source": self.source,
            "tool_id": self.tool_id,
            "tool_name": self.tool_name,
            "details": self.details,
            "stack_trace": self.stack_trace,
            "request_id": self.request_id,
            "user_agent": self.user_agent,
            "ip_address": self.ip_address,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

class OperationLog(Base):
    """操作日志模型"""
    __tablename__ = "operation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    operation = Column(String(100), index=True, nullable=False, comment="操作类型")
    resource_type = Column(String(50), index=True, comment="资源类型")
    resource_id = Column(String(100), index=True, comment="资源ID")
    resource_name = Column(String(200), comment="资源名称")
    
    # 操作详情
    action = Column(String(50), index=True, comment="具体动作: create, update, delete, start, stop")
    status = Column(String(20), default="success", comment="操作状态: success, failed, pending")
    description = Column(Text, comment="操作描述")
    
    # 变更信息
    old_values = Column(JSON, comment="变更前的值")
    new_values = Column(JSON, comment="变更后的值")
    
    # 结果信息
    result = Column(JSON, comment="操作结果")
    error_message = Column(Text, comment="错误信息")
    
    # 请求信息
    request_id = Column(String(50), index=True, comment="请求ID")
    ip_address = Column(String(50), comment="IP地址")
    user_agent = Column(String(500), comment="用户代理")
    
    # 时间字段
    timestamp = Column(DateTime, default=func.now(), index=True, comment="时间戳")
    duration_ms = Column(Integer, comment="操作耗时（毫秒）")
    
    # 创建复合索引
    __table_args__ = (
        Index('idx_ops_operation_time', 'operation', 'timestamp'),
        Index('idx_ops_resource_time', 'resource_type', 'resource_id', 'timestamp'),
        Index('idx_ops_action_status_time', 'action', 'status', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<OperationLog(id={self.id}, operation='{self.operation}', action='{self.action}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "operation": self.operation,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "resource_name": self.resource_name,
            "action": self.action,
            "status": self.status,
            "description": self.description,
            "old_values": self.old_values,
            "new_values": self.new_values,
            "result": self.result,
            "error_message": self.error_message,
            "request_id": self.request_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "duration_ms": self.duration_ms,
        }

class MCPLog(Base):
    """MCP 协议日志模型"""
    __tablename__ = "mcp_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    tool_id = Column(Integer, index=True, nullable=False, comment="工具ID")
    tool_name = Column(String(100), index=True, comment="工具名称")
    
    # 消息信息
    direction = Column(String(10), index=True, comment="消息方向: in, out")
    message_type = Column(String(50), index=True, comment="消息类型")
    method = Column(String(100), comment="方法名")
    
    # 消息内容
    request_data = Column(JSON, comment="请求数据")
    response_data = Column(JSON, comment="响应数据")
    error_data = Column(JSON, comment="错误数据")
    
    # 性能信息
    processing_time_ms = Column(Integer, comment="处理时间（毫秒）")
    
    # 时间字段
    timestamp = Column(DateTime, default=func.now(), index=True, comment="时间戳")
    
    # 创建复合索引
    __table_args__ = (
        Index('idx_mcp_tool_time', 'tool_id', 'timestamp'),
        Index('idx_mcp_direction_type_time', 'direction', 'message_type', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<MCPLog(id={self.id}, tool='{self.tool_name}', type='{self.message_type}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "tool_id": self.tool_id,
            "tool_name": self.tool_name,
            "direction": self.direction,
            "message_type": self.message_type,
            "method": self.method,
            "request_data": self.request_data,
            "response_data": self.response_data,
            "error_data": self.error_data,
            "processing_time_ms": self.processing_time_ms,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }