"""MCP 代理服务 API 路由"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
import json

from app.core.database import get_db
from app.schemas.mcp_agent import (
    ToolCallRequest,
    ToolCallResponse,
    ToolInfo,
    ResourceInfo,
    PromptInfo,
    AgentConfig,
    AgentSessionCreate,
    AgentExecuteRequest,
    TaskResult,
    AgentExecuteResponse
)
from pydantic import BaseModel
from app.services.mcp_service import MCPService
from app.services.tool_service import ToolService
from app.services.mcp_agent_service import get_agent_service
from app.utils.response import success_response, error_response
from app.utils.mcp_client import MCPClient

# 临时Schema定义
class ResourceReadRequest(BaseModel):
    uri: str

class PromptGetRequest(BaseModel):
    name: str
    arguments: dict = {}

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/mcp-agent", tags=["MCP代理服务"])

# 工具调用相关接口
@router.post("/tools/{tool_name}/call", response_model=dict, summary="调用MCP工具")
async def call_tool(
    tool_name: str,
    request: ToolCallRequest,
    db: Session = Depends(get_db)
):
    """调用指定的MCP工具"""
    try:
        # 获取工具信息
        tool_service = ToolService(db)
        tool = await tool_service.get_tool_by_name(tool_name)
        
        if not tool:
            return error_response(message="工具不存在", status_code=404)
        
        if not tool.is_enabled:
            return error_response(message="工具未启用", status_code=400)
        
        # 获取MCP客户端
        mcp_service = MCPService()
        client = mcp_service.get_client(tool_name)
        
        if not client:
            return error_response(message="MCP客户端未连接", status_code=503)
        
        # 调用工具
        result = await client.call_tool(request.tool_name, request.arguments)
        
        return success_response(
            data={
                "tool_name": request.tool_name,
                "arguments": request.arguments,
                "result": result,
                "success": True
            },
            message="工具调用成功"
        )
    except Exception as e:
        logger.error(f"调用工具失败: {e}")
        return error_response(message="调用工具失败", error_code=str(e))

@router.get("/tools/{tool_name}/capabilities", response_model=dict, summary="获取工具能力")
async def get_tool_capabilities(
    tool_name: str,
    db: Session = Depends(get_db)
):
    """获取指定工具的能力信息"""
    try:
        # 获取工具信息
        tool_service = ToolService(db)
        tool = await tool_service.get_tool_by_name(tool_name)
        
        if not tool:
            return error_response(message="工具不存在", status_code=404)
        
        # 获取MCP客户端
        mcp_service = MCPService()
        client = mcp_service.get_client(tool_name)
        
        if not client:
            return error_response(message="MCP客户端未连接", status_code=503)
        
        # 获取工具能力
        capabilities = await client.get_capabilities()
        
        return success_response(
            data=capabilities,
            message="获取工具能力成功"
        )
    except Exception as e:
        logger.error(f"获取工具能力失败: {e}")
        return error_response(message="获取工具能力失败", error_code=str(e))

@router.get("/tools", response_model=dict, summary="获取工具列表")
async def list_tools(
    db: Session = Depends(get_db)
):
    """获取所有可用的MCP工具列表"""
    try:
        tool_service = ToolService(db)
        mcp_service = MCPService()
        
        # 获取所有工具
        tools = await tool_service.get_all_tools()
        
        # 获取工具状态和能力信息
        tool_list = []
        for tool in tools:
            client = mcp_service.get_client(tool.name)
            
            tool_info = {
                "id": tool.id,
                "name": tool.name,
                "description": tool.description,
                "is_enabled": tool.is_enabled,
                "is_connected": client is not None,
                "capabilities": None
            }
            
            # 如果客户端连接，获取能力信息
            if client:
                try:
                    capabilities = await client.get_capabilities()
                    tool_info["capabilities"] = capabilities
                except Exception as e:
                    logger.warning(f"获取工具 {tool.name} 能力失败: {e}")
            
            tool_list.append(tool_info)
        
        return success_response(
            data={
                "tools": tool_list,
                "total": len(tool_list)
            },
            message="获取工具列表成功"
        )
    except Exception as e:
        logger.error(f"获取工具列表失败: {e}")
        return error_response(message="获取工具列表失败", error_code=str(e))



# 资源管理相关接口
@router.get("/tools/{tool_name}/resources", response_model=dict, summary="获取资源列表")
async def list_resources(
    tool_name: str,
    db: Session = Depends(get_db)
):
    """获取指定工具的资源列表"""
    try:
        # 获取工具信息
        tool_service = ToolService(db)
        tool = await tool_service.get_tool_by_name(tool_name)
        
        if not tool:
            return error_response(message="工具不存在", status_code=404)
        
        if not tool.is_enabled:
            return error_response(message="工具未启用", status_code=400)
        
        # 获取MCP客户端
        mcp_service = MCPService()
        client = mcp_service.get_client(tool_name)
        
        if not client:
            return error_response(message="MCP客户端未连接", status_code=503)
        
        # 获取资源列表
        resources = await client.list_resources()
        
        return success_response(
            data={
                "tool_name": tool_name,
                "resources": resources
            },
            message="获取资源列表成功"
        )
    except Exception as e:
        logger.error(f"获取资源列表失败: {e}")
        return error_response(message="获取资源列表失败", error_code=str(e))

@router.post("/tools/{tool_name}/resources/read", response_model=dict, summary="读取资源")
async def read_resource(
    tool_name: str,
    request: ResourceReadRequest,
    db: Session = Depends(get_db)
):
    """读取指定工具的资源"""
    try:
        # 获取工具信息
        tool_service = ToolService(db)
        tool = await tool_service.get_tool_by_name(tool_name)
        
        if not tool:
            return error_response(message="工具不存在", status_code=404)
        
        if not tool.is_enabled:
            return error_response(message="工具未启用", status_code=400)
        
        # 获取MCP客户端
        mcp_service = MCPService()
        client = mcp_service.get_client(tool_name)
        
        if not client:
            return error_response(message="MCP客户端未连接", status_code=503)
        
        # 读取资源
        resource_data = await client.read_resource(request.uri)
        
        return success_response(
            data={
                "tool_name": tool_name,
                "uri": request.uri,
                "data": resource_data
            },
            message="读取资源成功"
        )
    except Exception as e:
        logger.error(f"读取资源失败: {e}")
        return error_response(message="读取资源失败", error_code=str(e))

# 提示管理相关接口
@router.get("/tools/{tool_name}/prompts", response_model=dict, summary="获取提示列表")
async def list_prompts(
    tool_name: str,
    db: Session = Depends(get_db)
):
    """获取指定工具的提示列表"""
    try:
        # 获取工具信息
        tool_service = ToolService(db)
        tool = await tool_service.get_tool_by_name(tool_name)
        
        if not tool:
            return error_response(message="工具不存在", status_code=404)
        
        if not tool.is_enabled:
            return error_response(message="工具未启用", status_code=400)
        
        # 获取MCP客户端
        mcp_service = MCPService()
        client = mcp_service.get_client(tool_name)
        
        if not client:
            return error_response(message="MCP客户端未连接", status_code=503)
        
        # 获取提示列表
        prompts = await client.list_prompts()
        
        return success_response(
            data={
                "tool_name": tool_name,
                "prompts": prompts
            },
            message="获取提示列表成功"
        )
    except Exception as e:
        logger.error(f"获取提示列表失败: {e}")
        return error_response(message="获取提示列表失败", error_code=str(e))

@router.post("/tools/{tool_name}/prompts/get", response_model=dict, summary="获取提示")
async def get_prompt(
    tool_name: str,
    request: PromptGetRequest,
    db: Session = Depends(get_db)
):
    """获取指定工具的提示"""
    try:
        # 获取工具信息
        tool_service = ToolService(db)
        tool = await tool_service.get_tool_by_name(tool_name)
        
        if not tool:
            return error_response(message="工具不存在", status_code=404)
        
        if not tool.is_enabled:
            return error_response(message="工具未启用", status_code=400)
        
        # 获取MCP客户端
        mcp_service = MCPService()
        client = mcp_service.get_client(tool_name)
        
        if not client:
            return error_response(message="MCP客户端未连接", status_code=503)
        
        # 获取提示
        prompt_data = await client.get_prompt(request.name, request.arguments)
        
        return success_response(
            data={
                "tool_name": tool_name,
                "name": request.name,
                "data": prompt_data
            },
            message="获取提示成功"
        )
    except Exception as e:
        logger.error(f"获取提示失败: {e}")
        return error_response(message="获取提示失败", error_code=str(e))

# 代理会话管理
@router.post("/sessions", response_model=dict, summary="创建代理会话")
async def create_session(
    request: AgentSessionCreate,
    db: Session = Depends(get_db)
):
    """创建新的代理会话"""
    try:
        agent_service = get_agent_service()
        session = await agent_service.create_session(request)
        
        return success_response(
            data=session.to_dict(),
            message="创建代理会话成功"
        )
    except Exception as e:
        logger.error(f"创建代理会话失败: {e}")
        return error_response(message="创建代理会话失败", error_code=str(e))

@router.post("/sessions/{session_id}/execute", response_model=dict, summary="执行代理任务")
async def execute_agent_task(
    session_id: str,
    request: AgentExecuteRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """在指定会话中执行代理任务"""
    try:
        agent_service = get_agent_service()
        task_id = await agent_service.submit_task(session_id, request)
        
        return success_response(
            data={
                "task_id": task_id,
                "session_id": session_id,
                "status": "submitted",
                "message": request.message
            },
            message="任务已提交执行"
        )
    except Exception as e:
        logger.error(f"执行代理任务失败: {e}")
        return error_response(message="执行代理任务失败", error_code=str(e))

@router.get("/tasks/{task_id}/status", response_model=dict, summary="获取任务状态")
async def get_task_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    """获取代理任务执行状态"""
    try:
        agent_service = get_agent_service()
        task_result = await agent_service.get_task_status(task_id)
        
        if task_result is None:
            return error_response(message="任务不存在", status_code=404)
        
        return success_response(
            data=task_result.to_dict(),
            message="获取任务状态成功"
        )
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        return error_response(message="获取任务状态失败", error_code=str(e))

# 辅助函数
async def _execute_agent_task(
    session_id: str,
    task_id: str,
    request: AgentExecuteRequest,
    db: Session
):
    """异步执行代理任务"""
    try:
        # TODO: 实现具体的代理任务执行逻辑
        logger.info(f"开始执行代理任务: session_id={session_id}, task_id={task_id}")
        
        # 模拟任务执行
        import asyncio
        await asyncio.sleep(5)
        
        logger.info(f"代理任务执行完成: session_id={session_id}, task_id={task_id}")
    except Exception as e:
        logger.error(f"代理任务执行失败: session_id={session_id}, task_id={task_id}, error={e}")

# 健康检查
@router.get("/health", response_model=dict, summary="健康检查")
async def health_check():
    """MCP代理服务健康检查"""
    try:
        return success_response(
            data={
                "status": "healthy",
                "timestamp": __import__('datetime').datetime.now().isoformat()
            },
            message="MCP代理服务运行正常"
        )
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return error_response(message="健康检查失败", error_code=str(e))