"""MCP 工具相关数据模型"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from datetime import datetime
from typing import Optional, Dict, Any

from app.core.database import Base

class ToolStatus(PyEnum):
    """工具状态枚举"""
    STOPPED = "stopped"      # 已停止
    STARTING = "starting"    # 启动中
    RUNNING = "running"      # 运行中
    STOPPING = "stopping"   # 停止中
    ERROR = "error"          # 错误状态
    UNKNOWN = "unknown"      # 未知状态

class ToolType(PyEnum):
    """工具类型枚举"""
    BUILTIN = "builtin"      # 内置工具
    CUSTOM = "custom"        # 自定义工具
    EXTERNAL = "external"    # 外部工具

class MCPTool(Base):
    """MCP 工具配置模型"""
    __tablename__ = "mcp_tools"

    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False, comment="工具名称")
    display_name = Column(String(200), nullable=False, comment="显示名称")
    description = Column(Text, comment="工具描述")

    # 工具分类
    type = Column(Enum(ToolType, values_callable=lambda x: [e.value for e in x]), default=ToolType.CUSTOM, comment="工具类型")
    category = Column(String(50), index=True, comment="工具分类")
    tags = Column(JSON, default=list, comment="工具标签")

    # 执行配置
    command = Column(Text, nullable=False, comment="启动命令")
    startup_command = Column(Text, comment="启动命令（用于进程监控）")
    working_directory = Column(String(500), comment="工作目录")
    environment_variables = Column(JSON, default=dict, comment="环境变量")

    # 连接配置
    connection_type = Column(String(20), default="stdio", comment="连接类型: stdio, http, websocket")
    host = Column(String(100), comment="主机地址（HTTP/WebSocket）")
    port = Column(Integer, comment="端口号（HTTP/WebSocket）")
    path = Column(String(200), comment="路径（HTTP/WebSocket）")

    # 运行时配置
    auto_start = Column(Boolean, default=False, comment="自动启动")
    restart_on_failure = Column(Boolean, default=True, comment="失败时重启")
    max_restart_attempts = Column(Integer, default=3, comment="最大重启次数")
    timeout = Column(Integer, default=30, comment="超时时间（秒）")
    max_memory_mb = Column(Integer, default=512, comment="最大内存使用（MB）")
    max_cpu_percent = Column(Integer, default=80, comment="最大CPU使用率（%）")

    # 状态信息
    status = Column(Enum(ToolStatus, values_callable=lambda x: [e.value for e in x]), default=ToolStatus.STOPPED, comment="当前状态")
    process_id = Column(Integer, comment="进程ID")
    last_started_at = Column(DateTime, comment="最后启动时间")
    last_stopped_at = Column(DateTime, comment="最后停止时间")
    last_error_at = Column(DateTime, comment="最后错误时间")
    last_error = Column(Text, comment="最后错误信息")
    restart_count = Column(Integer, default=0, comment="重启次数")

    # 元数据
    version = Column(String(20), comment="工具版本")
    author = Column(String(100), comment="作者")
    homepage = Column(String(500), comment="主页")

    # 系统字段
    enabled = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关联关系
    # sessions = relationship("MCPSession", back_populates="tool") # 会话管理功能已移除
    # tasks = relationship("MCPTask", back_populates="tool") # 任务管理功能已移除

    def __repr__(self):
        return f"<MCPTool(id={self.id}, name='{self.name}', status='{self.status}')>"

    @property
    def is_running(self) -> bool:
        """检查工具是否正在运行"""
        return self.status == ToolStatus.RUNNING

    @property
    def can_start(self) -> bool:
        """检查工具是否可以启动"""
        return self.enabled and self.status in [ToolStatus.STOPPED, ToolStatus.ERROR]

    @property
    def can_stop(self) -> bool:
        """检查工具是否可以停止"""
        return self.status in [ToolStatus.RUNNING, ToolStatus.STARTING]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "type": self.type.value if self.type else None,
            "category": self.category,
            "tags": self.tags or [],
            "command": self.command,
            "startup_command": self.startup_command,
            "working_directory": self.working_directory,
            "environment_variables": self.environment_variables or {},
            "connection_type": self.connection_type,
            "host": self.host,
            "port": self.port,
            "path": self.path,
            "auto_start": self.auto_start,
            "restart_on_failure": self.restart_on_failure,
            "max_restart_attempts": self.max_restart_attempts,
            "timeout": self.timeout,
            "max_memory_mb": self.max_memory_mb,
            "max_cpu_percent": self.max_cpu_percent,
            "status": self.status.value if self.status else None,
            "process_id": self.process_id,
            "last_started_at": self.last_started_at.isoformat() if self.last_started_at else None,
            "last_stopped_at": self.last_stopped_at.isoformat() if self.last_stopped_at else None,
            "last_error_at": self.last_error_at.isoformat() if self.last_error_at else None,
            "last_error": self.last_error,
            "restart_count": self.restart_count,
            "version": self.version,
            "author": self.author,
            "homepage": self.homepage,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class ToolCategory(Base):
    """工具分类模型"""
    __tablename__ = "tool_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False, comment="分类名称")
    display_name = Column(String(100), nullable=False, comment="显示名称")
    description = Column(Text, comment="分类描述")
    icon = Column(String(50), comment="图标")
    color = Column(String(20), comment="颜色")
    sort_order = Column(Integer, default=0, comment="排序")

    # 系统字段
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<ToolCategory(id={self.id}, name='{self.name}')>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "icon": self.icon,
            "color": self.color,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
