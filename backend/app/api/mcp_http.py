"""MCP HTTP 端点

提供标准的 MCP HTTP 接口，让其他 IDE 可以通过简单的 URL 配置连接到 MCPS.ONE。
"""

import json
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, HTTPException, Response
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import asyncio
from datetime import datetime

from ..services.mcp.mcp_unified_service import unified_service
from ..core.database import SessionLocal
from ..models.tool import MCPTool, ToolStatus
from ..services.mcp.mcp_service import MCPService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["MCP HTTP"])

# 添加一个不带前缀的路由器来处理重定向问题
no_prefix_router = APIRouter(tags=["MCP HTTP"])

# MCP 协议模型
class MCPRequest(BaseModel):
    """MCP 请求模型"""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    method: str
    params: Optional[Dict[str, Any]] = None

class MCPResponse(BaseModel):
    """MCP 响应模型"""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None

class MCPError(BaseModel):
    """MCP 错误模型"""
    code: int
    message: str
    data: Optional[Any] = None

# MCP 服务实例
mcp_service = MCPService()

@router.get("/")
async def mcp_info():
    """MCP 服务信息端点"""
    return {
        "name": "MCPS.ONE MCP Server",
        "version": "1.0.0",
        "description": "MCPS.ONE MCP 服务端 - 统一的 MCP 工具聚合器",
        "protocol_version": "2024-11-05",
        "capabilities": {
            "tools": True,
            "resources": False,
            "prompts": False,
            "logging": True
        },
        "endpoints": {
            "http": "/api/v1/mcp",
            "websocket": "/api/v1/mcp/ws"
        },
        "authentication": "none",
        "status": "ready" if unified_service.is_running else "starting"
    }

@router.post("/")
async def handle_mcp_request(request: Request):
    """处理 MCP 请求"""
    try:
        # 获取原始请求体
        body = await request.body()
        logger.info(f"收到 MCP 请求，Content-Type: {request.headers.get('content-type')}, Body: {body[:200]}...")

        # 尝试解析 JSON
        try:
            if body:
                data = json.loads(body)
            else:
                data = {}
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32700,
                        "message": "解析错误",
                        "data": str(e)
                    }
                }
            )

        # 验证 MCP 请求格式
        if not isinstance(data, dict):
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32600,
                        "message": "无效请求",
                        "data": "请求必须是 JSON 对象"
                    }
                }
            )

        # 提取请求信息
        method = data.get("method")
        params = data.get("params", {})
        request_id = data.get("id")

        if not method:
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32600,
                        "message": "无效请求",
                        "data": "缺少 method 字段"
                    }
                }
            )

        logger.info(f"处理 MCP 方法: {method}")

        # 确保服务已启动
        if not unified_service.is_running:
            await unified_service.start_service()

        # 路由到相应的处理方法
        if method == "initialize":
            result = await handle_initialize(params)
        elif method == "tools/list":
            result = await handle_list_tools()
        elif method == "tools/call":
            result = await handle_call_tool(params)
        elif method == "ping":
            result = {"status": "pong"}
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": "方法未找到",
                        "data": f"不支持的方法: {method}"
                    }
                }
            )

        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
        )

    except Exception as e:
        logger.error(f"处理 MCP 请求失败: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0",
                "id": data.get("id") if 'data' in locals() else None,
                "error": {
                    "code": -32603,
                    "message": "内部错误",
                    "data": str(e)
                }
            }
        )

async def handle_initialize(params: Dict[str, Any]) -> Dict[str, Any]:
    """处理初始化请求"""
    logger.info("处理 MCP 初始化请求")

    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {
                "listChanged": False
            },
            "logging": {}
        },
        "serverInfo": {
            "name": "MCPS.ONE",
            "version": "1.0.0"
        }
    }

async def handle_list_tools() -> Dict[str, Any]:
    """处理工具列表请求"""
    try:
        logger.info("处理工具列表请求")

        # 从数据库获取运行中的工具
        db = SessionLocal()
        try:
            tools = db.query(MCPTool).filter(
                MCPTool.status == ToolStatus.RUNNING
            ).all()

            tool_list = []
            for tool in tools:
                # 获取工具的具体能力
                try:
                    client = await mcp_service.get_client_by_name(tool.name)
                    if client:
                        capabilities = await client.list_tools()
                        for cap in capabilities:
                            tool_list.append({
                                "name": f"{tool.name}_{cap.name}",
                                "description": cap.description or f"{tool.description} - {cap.name}",
                                "inputSchema": cap.inputSchema or {
                                    "type": "object",
                                    "properties": {},
                                    "required": []
                                }
                            })
                    else:
                        # 如果无法获取具体能力，添加通用工具
                        tool_list.append({
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "tool_function": {
                                        "type": "string",
                                        "description": "要调用的工具函数名"
                                    },
                                    "arguments": {
                                        "type": "object",
                                        "description": "函数参数"
                                    }
                                },
                                "required": ["tool_function"]
                            }
                        })
                except Exception as e:
                    logger.warning(f"获取工具 {tool.name} 能力失败: {e}")
                    # 添加基本工具信息
                    tool_list.append({
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    })

            return {"tools": tool_list}

        finally:
            db.close()

    except Exception as e:
        logger.error(f"获取工具列表失败: {e}")
        return {"tools": []}

async def handle_call_tool(params: Dict[str, Any]) -> Dict[str, Any]:
    """处理工具调用请求"""
    try:
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if not tool_name:
            raise ValueError("缺少工具名称")

        logger.info(f"调用工具: {tool_name}")

        # 解析工具名称（可能包含前缀）
        if "_" in tool_name:
            # 格式: tool_name_function_name
            parts = tool_name.split("_", 1)
            actual_tool_name = parts[0]
            tool_function = parts[1] if len(parts) > 1 else "default"
        else:
            actual_tool_name = tool_name
            tool_function = arguments.get("tool_function", "default")
            arguments = arguments.get("arguments", arguments)

        # 获取 MCP 客户端
        client = await mcp_service.get_client_by_name(actual_tool_name)
        if not client:
            raise ValueError(f"工具 {actual_tool_name} 未找到或未运行")

        # 调用工具
        result = await client.call_tool(tool_function, arguments)

        if result.get("isError", False):
            content_list = result.get("content", [])
            error_msg = content_list[0].get("text", "未知错误") if content_list else "未知错误"
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"工具调用失败: {error_msg}"
                    }
                ],
                "isError": True
            }


        # 格式化返回结果
        content_parts = []
        content_list = result.get("content", [])
        for content in content_list:
            if isinstance(content, dict):
                if content.get("type") == "text" and "text" in content:
                    content_parts.append({
                        "type": "text",
                        "text": content["text"]
                    })
                elif content.get("type") == "image" and "data" in content:
                    content_parts.append({
                        "type": "image",
                        "data": content["data"],
                        "mimeType": content.get("mimeType", "image/png")
                    })
                else:
                    # 处理其他类型的内容
                    content_parts.append(content)
            else:
                # 如果content不是字典，尝试按对象方式处理（向后兼容）
                if hasattr(content, 'text'):
                    content_parts.append({
                        "type": "text",
                        "text": content.text
                    })
                elif hasattr(content, 'data'):
                    content_parts.append({
                        "type": "image",
                        "data": content.data,
                        "mimeType": getattr(content, 'mimeType', 'image/png')
                    })

        return {
            "content": content_parts,
            "isError": False
        }

    except Exception as e:
        logger.error(f"工具调用失败: {e}")
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"工具调用失败: {str(e)}"
                }
            ],
            "isError": True
        }

@router.get("/health")
async def health_check():
    """健康检查端点"""
    status = await unified_service.get_service_status()
    return {
        "status": "healthy" if unified_service.is_running else "starting",
        "timestamp": datetime.now().isoformat(),
        "service_mode": status.mode.value,
        "proxy_running": status.proxy_running,
        "server_running": status.server_running,
        "uptime": status.uptime
    }

@router.get("/tools")
async def list_available_tools():
    """列出可用工具（REST 风格）"""
    result = await handle_list_tools()
    return result

@router.post("/tools/{tool_name}/call")
async def call_tool_rest(tool_name: str, arguments: Dict[str, Any]):
    """调用工具（REST 风格）"""
    result = await handle_call_tool({
        "name": tool_name,
        "arguments": arguments
    })
    return result
