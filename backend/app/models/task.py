"""任务管理模型"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Enum as SQLEnum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from datetime import datetime
from typing import Dict, Any, Optional

from app.core.database import Base


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TaskType(str, Enum):
    """任务类型"""
    SINGLE_TOOL = "single_tool"
    MULTI_TOOL = "multi_tool"
    WORKFLOW = "workflow"
    BATCH = "batch"
    SCHEDULED = "scheduled"


class TaskPriority(str, Enum):
    """任务优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class MCPTask(Base):
    """MCP 任务模型"""
    __tablename__ = "mcp_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(255), unique=True, index=True, nullable=False, comment="任务ID")
    
    # 任务基本信息
    name = Column(String(255), nullable=False, comment="任务名称")
    description = Column(Text, comment="任务描述")
    task_type = Column(SQLEnum(TaskType), default=TaskType.SINGLE_TOOL, comment="任务类型")
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.NORMAL, comment="任务优先级")
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, comment="任务状态")
    
    # 关联信息
    session_id = Column(Integer, ForeignKey("mcp_sessions.id"), nullable=True, comment="会话ID")
    tool_id = Column(Integer, ForeignKey("mcp_tools.id"), nullable=True, comment="主要工具ID")
    user_id = Column(String(255), nullable=True, comment="用户ID")
    parent_task_id = Column(Integer, ForeignKey("mcp_tasks.id"), nullable=True, comment="父任务ID")
    
    # 任务配置和数据
    input_data = Column(Text, comment="输入数据(JSON)")
    output_data = Column(Text, comment="输出数据(JSON)")
    config = Column(Text, comment="任务配置(JSON)")
    task_metadata = Column(Text, comment="任务元数据(JSON)")
    
    # 执行信息
    progress = Column(Float, default=0.0, comment="执行进度(0-100)")
    error_message = Column(Text, comment="错误信息")
    error_code = Column(String(50), comment="错误代码")
    retry_count = Column(Integer, default=0, comment="重试次数")
    max_retries = Column(Integer, default=3, comment="最大重试次数")
    
    # 时间信息
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    started_at = Column(DateTime, nullable=True, comment="开始时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    scheduled_at = Column(DateTime, nullable=True, comment="计划执行时间")
    timeout_at = Column(DateTime, nullable=True, comment="超时时间")
    
    # 性能统计
    execution_time = Column(Float, nullable=True, comment="执行时间(秒)")
    cpu_usage = Column(Float, nullable=True, comment="CPU使用率")
    memory_usage = Column(Float, nullable=True, comment="内存使用量(MB)")
    
    # 关联关系
    session = relationship("MCPSession", back_populates="tasks")
    tool = relationship("MCPTool", back_populates="tasks")
    parent_task = relationship("MCPTask", remote_side=[id], back_populates="child_tasks")
    child_tasks = relationship("MCPTask", back_populates="parent_task")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "task_type": self.task_type,
            "priority": self.priority,
            "status": self.status,
            "session_id": self.session_id,
            "tool_id": self.tool_id,
            "user_id": self.user_id,
            "parent_task_id": self.parent_task_id,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "config": self.config,
            "metadata": self.task_metadata,
            "progress": self.progress,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "timeout_at": self.timeout_at.isoformat() if self.timeout_at else None,
            "execution_time": self.execution_time,
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
        }
    
    def is_running(self) -> bool:
        """检查任务是否正在运行"""
        return self.status == TaskStatus.RUNNING
    
    def is_completed(self) -> bool:
        """检查任务是否已完成"""
        return self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.TIMEOUT]
    
    def can_retry(self) -> bool:
        """检查任务是否可以重试"""
        return (
            self.status == TaskStatus.FAILED and 
            self.retry_count < self.max_retries
        )
    
    def start_task(self):
        """开始任务"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def complete_task(self, output_data: Optional[str] = None):
        """完成任务"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.progress = 100.0
        
        if output_data:
            self.output_data = output_data
        
        # 计算执行时间
        if self.started_at:
            self.execution_time = (self.completed_at - self.started_at).total_seconds()
    
    def fail_task(self, error_message: str, error_code: Optional[str] = None):
        """任务失败"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.error_message = error_message
        
        if error_code:
            self.error_code = error_code
        
        # 计算执行时间
        if self.started_at:
            self.execution_time = (self.completed_at - self.started_at).total_seconds()
    
    def cancel_task(self):
        """取消任务"""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # 计算执行时间
        if self.started_at:
            self.execution_time = (self.completed_at - self.started_at).total_seconds()
    
    def update_progress(self, progress: float):
        """更新任务进度"""
        self.progress = max(0.0, min(100.0, progress))
        self.updated_at = datetime.utcnow()
    
    def increment_retry(self):
        """增加重试次数"""
        self.retry_count += 1
        self.updated_at = datetime.utcnow()