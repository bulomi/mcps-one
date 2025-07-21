"""MCP 代理服务相关的数据模型"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

# 基础枚举类型
class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AgentMode(str, Enum):
    """代理模式"""
    SINGLE_TOOL = "single_tool"  # 单工具模式
    MULTI_TOOL = "multi_tool"    # 多工具模式
    PIPELINE = "pipeline"        # 流水线模式
    AUTONOMOUS = "autonomous"    # 自主模式

# 工具调用相关模型
class ToolCallRequest(BaseModel):
    """工具调用请求"""
    name: str = Field(..., description="工具名称")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="工具参数")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "search_files",
                "arguments": {
                    "query": "python",
                    "path": "/home/user"
                }
            }
        }
    )

class ToolCallResponse(BaseModel):
    """工具调用响应"""
    tool_id: int = Field(..., description="工具ID")
    tool_name: str = Field(..., description="工具名称")
    result: Any = Field(..., description="调用结果")
    execution_time: Optional[float] = Field(None, description="执行时间（秒）")
    error: Optional[str] = Field(None, description="错误信息")

class ToolInfo(BaseModel):
    """工具信息"""
    name: str = Field(..., description="工具名称")
    description: Optional[str] = Field(None, description="工具描述")
    input_schema: Optional[Dict[str, Any]] = Field(None, description="输入参数模式")

class ToolCapabilitiesResponse(BaseModel):
    """工具能力响应"""
    tool_id: int = Field(..., description="工具ID")
    capabilities: Dict[str, Any] = Field(..., description="工具能力信息")

class ToolListResponse(BaseModel):
    """工具列表响应"""
    tool_id: int = Field(..., description="工具ID")
    tools: List[ToolInfo] = Field(..., description="工具列表")

# 资源管理相关模型
class ResourceInfo(BaseModel):
    """资源信息"""
    uri: str = Field(..., description="资源URI")
    name: Optional[str] = Field(None, description="资源名称")
    description: Optional[str] = Field(None, description="资源描述")
    mime_type: Optional[str] = Field(None, description="MIME类型")

class ResourceListResponse(BaseModel):
    """资源列表响应"""
    tool_id: int = Field(..., description="工具ID")
    resources: List[ResourceInfo] = Field(..., description="资源列表")

class ResourceReadRequest(BaseModel):
    """资源读取请求"""
    uri: str = Field(..., description="资源URI")

class ResourceReadResponse(BaseModel):
    """资源读取响应"""
    tool_id: int = Field(..., description="工具ID")
    uri: str = Field(..., description="资源URI")
    data: Any = Field(..., description="资源数据")

# 提示管理相关模型
class PromptInfo(BaseModel):
    """提示信息"""
    name: str = Field(..., description="提示名称")
    description: Optional[str] = Field(None, description="提示描述")
    arguments: Optional[List[Dict[str, Any]]] = Field(None, description="参数列表")

class PromptListResponse(BaseModel):
    """提示列表响应"""
    tool_id: int = Field(..., description="工具ID")
    prompts: List[PromptInfo] = Field(..., description="提示列表")

class PromptGetRequest(BaseModel):
    """获取提示请求"""
    name: str = Field(..., description="提示名称")
    arguments: Optional[Dict[str, Any]] = Field(default_factory=dict, description="提示参数")

class PromptGetResponse(BaseModel):
    """获取提示响应"""
    tool_id: int = Field(..., description="工具ID")
    name: str = Field(..., description="提示名称")
    data: Any = Field(..., description="提示数据")

# 代理会话相关模型
class AgentConfig(BaseModel):
    """代理配置"""
    mode: AgentMode = Field(default=AgentMode.SINGLE_TOOL, description="代理模式")
    max_iterations: int = Field(default=10, description="最大迭代次数")
    timeout: int = Field(default=300, description="超时时间（秒）")
    auto_retry: bool = Field(default=True, description="是否自动重试")
    retry_count: int = Field(default=3, description="重试次数")
    parallel_execution: bool = Field(default=False, description="是否并行执行")

class AgentSessionCreate(BaseModel):
    """创建代理会话请求"""
    name: Optional[str] = Field(None, description="会话名称")
    description: Optional[str] = Field(None, description="会话描述")
    tools: List[int] = Field(..., description="使用的工具ID列表")
    config: AgentConfig = Field(default_factory=AgentConfig, description="代理配置")

class AgentSessionResponse(BaseModel):
    """代理会话响应"""
    session_id: str = Field(..., description="会话ID")
    name: Optional[str] = Field(None, description="会话名称")
    description: Optional[str] = Field(None, description="会话描述")
    tools: List[int] = Field(..., description="使用的工具ID列表")
    config: AgentConfig = Field(..., description="代理配置")
    created_at: datetime = Field(..., description="创建时间")
    status: str = Field(..., description="会话状态")

# 代理任务相关模型
class TaskStep(BaseModel):
    """任务步骤"""
    step_id: str = Field(..., description="步骤ID")
    tool_id: int = Field(..., description="工具ID")
    tool_name: str = Field(..., description="工具名称")
    arguments: Dict[str, Any] = Field(..., description="工具参数")
    depends_on: Optional[List[str]] = Field(None, description="依赖的步骤ID列表")

class AgentExecuteRequest(BaseModel):
    """代理执行请求"""
    task_name: Optional[str] = Field(None, description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    steps: List[TaskStep] = Field(..., description="任务步骤列表")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="执行上下文")

class TaskResult(BaseModel):
    """任务结果"""
    step_id: str = Field(..., description="步骤ID")
    status: TaskStatus = Field(..., description="步骤状态")
    result: Optional[Any] = Field(None, description="执行结果")
    error: Optional[str] = Field(None, description="错误信息")
    execution_time: Optional[float] = Field(None, description="执行时间（秒）")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")

class AgentExecuteResponse(BaseModel):
    """代理执行响应"""
    session_id: str = Field(..., description="会话ID")
    task_id: str = Field(..., description="任务ID")
    status: TaskStatus = Field(..., description="任务状态")
    progress: float = Field(default=0.0, description="执行进度（0-100）")
    results: List[TaskResult] = Field(default_factory=list, description="步骤结果列表")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    total_execution_time: Optional[float] = Field(None, description="总执行时间（秒）")

# 批量操作相关模型
class BatchToolCallRequest(BaseModel):
    """批量工具调用请求"""
    calls: List[ToolCallRequest] = Field(..., description="工具调用列表")
    parallel: bool = Field(default=False, description="是否并行执行")
    fail_fast: bool = Field(default=False, description="是否快速失败")

class BatchToolCallResponse(BaseModel):
    """批量工具调用响应"""
    results: List[ToolCallResponse] = Field(..., description="调用结果列表")
    summary: Dict[str, Any] = Field(..., description="执行摘要")

# 监控和统计相关模型
class ToolUsageStats(BaseModel):
    """工具使用统计"""
    tool_id: int = Field(..., description="工具ID")
    tool_name: str = Field(..., description="工具名称")
    call_count: int = Field(..., description="调用次数")
    success_count: int = Field(..., description="成功次数")
    error_count: int = Field(..., description="错误次数")
    avg_execution_time: float = Field(..., description="平均执行时间（秒）")
    last_called_at: Optional[datetime] = Field(None, description="最后调用时间")

class AgentStats(BaseModel):
    """代理统计信息"""
    total_sessions: int = Field(..., description="总会话数")
    active_sessions: int = Field(..., description="活跃会话数")
    total_tasks: int = Field(..., description="总任务数")
    completed_tasks: int = Field(..., description="已完成任务数")
    failed_tasks: int = Field(..., description="失败任务数")
    avg_task_duration: float = Field(..., description="平均任务时长（秒）")
    tool_usage: List[ToolUsageStats] = Field(..., description="工具使用统计")

# 错误处理相关模型
class MCPError(BaseModel):
    """MCP错误信息"""
    code: int = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    data: Optional[Dict[str, Any]] = Field(None, description="错误数据")

class AgentError(BaseModel):
    """代理错误信息"""
    error_type: str = Field(..., description="错误类型")
    error_message: str = Field(..., description="错误消息")
    tool_id: Optional[int] = Field(None, description="相关工具ID")
    step_id: Optional[str] = Field(None, description="相关步骤ID")
    timestamp: datetime = Field(..., description="错误时间")
    stack_trace: Optional[str] = Field(None, description="堆栈跟踪")

# 配置相关模型
class MCPServerConfig(BaseModel):
    """MCP服务器配置"""
    name: str = Field(..., description="服务器名称")
    command: List[str] = Field(..., description="启动命令")
    args: Optional[List[str]] = Field(None, description="命令参数")
    env: Optional[Dict[str, str]] = Field(None, description="环境变量")
    cwd: Optional[str] = Field(None, description="工作目录")
    connection_type: str = Field(default="stdio", description="连接类型")
    host: Optional[str] = Field(None, description="主机地址")
    port: Optional[int] = Field(None, description="端口号")
    websocket_url: Optional[str] = Field(None, description="WebSocket URL")

class AgentSystemConfig(BaseModel):
    """代理系统配置"""
    max_concurrent_sessions: int = Field(default=10, description="最大并发会话数")
    max_concurrent_tasks: int = Field(default=50, description="最大并发任务数")
    default_timeout: int = Field(default=300, description="默认超时时间（秒）")
    cleanup_interval: int = Field(default=3600, description="清理间隔（秒）")
    log_level: str = Field(default="INFO", description="日志级别")
    enable_metrics: bool = Field(default=True, description="是否启用指标收集")
    metrics_interval: int = Field(default=60, description="指标收集间隔（秒）")
