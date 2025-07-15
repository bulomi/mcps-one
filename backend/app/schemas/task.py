"""任务管理相关的 Pydantic 模型"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


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


class TaskBase(BaseModel):
    """任务基础模型"""
    name: str = Field(..., min_length=1, max_length=255, description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    task_type: TaskType = Field(TaskType.SINGLE_TOOL, description="任务类型")
    priority: TaskPriority = Field(TaskPriority.NORMAL, description="任务优先级")
    session_id: Optional[int] = Field(None, description="会话ID")
    tool_id: Optional[int] = Field(None, description="主要工具ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    parent_task_id: Optional[int] = Field(None, description="父任务ID")
    input_data: Optional[Dict[str, Any]] = Field(None, description="输入数据")
    config: Optional[Dict[str, Any]] = Field(None, description="任务配置")
    metadata: Optional[Dict[str, Any]] = Field(None, description="任务元数据")
    max_retries: int = Field(3, ge=0, le=10, description="最大重试次数")
    scheduled_at: Optional[datetime] = Field(None, description="计划执行时间")
    timeout_at: Optional[datetime] = Field(None, description="超时时间")


class TaskCreate(TaskBase):
    """创建任务模型"""
    pass


class TaskUpdate(BaseModel):
    """更新任务模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    priority: Optional[TaskPriority] = Field(None, description="任务优先级")
    status: Optional[TaskStatus] = Field(None, description="任务状态")
    progress: Optional[float] = Field(None, ge=0.0, le=100.0, description="执行进度")
    config: Optional[Dict[str, Any]] = Field(None, description="任务配置")
    metadata: Optional[Dict[str, Any]] = Field(None, description="任务元数据")
    max_retries: Optional[int] = Field(None, ge=0, le=10, description="最大重试次数")
    scheduled_at: Optional[datetime] = Field(None, description="计划执行时间")
    timeout_at: Optional[datetime] = Field(None, description="超时时间")


class TaskResponse(TaskBase):
    """任务响应模型"""
    id: int
    task_id: str
    status: TaskStatus
    progress: float = 0.0
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    retry_count: int = 0
    output_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time: Optional[float] = None
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    
    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """任务列表响应模型"""
    items: List[TaskResponse]
    total: int
    page: int
    size: int
    pages: int


class TaskStatsResponse(BaseModel):
    """任务统计响应模型"""
    total_tasks: int
    pending_tasks: int
    running_tasks: int
    completed_tasks: int
    failed_tasks: int
    cancelled_tasks: int
    timeout_tasks: int
    avg_execution_time: float  # 平均执行时间（秒）
    success_rate: float  # 成功率（百分比）
    total_retries: int


class TaskExecutionRequest(BaseModel):
    """任务执行请求模型"""
    action: str = Field(..., description="执行动作: start, stop, pause, resume, retry")
    force: bool = Field(False, description="是否强制执行")
    reason: Optional[str] = Field(None, description="执行原因")


class TaskExecutionResponse(BaseModel):
    """任务执行响应模型"""
    task_id: str
    action: str
    success: bool
    message: str
    timestamp: datetime


class TaskProgressUpdate(BaseModel):
    """任务进度更新模型"""
    progress: float = Field(..., ge=0.0, le=100.0, description="进度百分比")
    message: Optional[str] = Field(None, description="进度消息")
    data: Optional[Dict[str, Any]] = Field(None, description="进度数据")


class TaskBatchOperation(BaseModel):
    """任务批量操作模型"""
    task_ids: List[str] = Field(..., min_items=1, description="任务ID列表")
    action: str = Field(..., description="批量操作类型")
    force: bool = Field(False, description="是否强制执行")
    reason: Optional[str] = Field(None, description="操作原因")


class TaskBatchOperationResponse(BaseModel):
    """任务批量操作响应模型"""
    total: int
    success: int
    failed: int
    results: List[TaskExecutionResponse]