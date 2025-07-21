"""MCP 服务端实现"

让 MCPS.ONE 作为 MCP 服务端，供 Cursor 等客户端连接并自动发现已配置的 MCP 工具。
"""

import asyncio
import json
import logging
import sys
import time
import traceback
from typing import Dict, List, Optional, Any, Sequence
from datetime import datetime
from contextlib import asynccontextmanager

from fastmcp import FastMCP
from mcp.types import (
    Tool,
    Resource,
    Prompt,
    TextContent,
    ImageContent,
    EmbeddedResource
)
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.unified_config_manager import get_unified_config_manager, init_unified_config_manager
from app.core import get_logger
from app.models.tool import MCPTool, ToolStatus
from .mcp_service import MCPService
from ..base import BaseService
from app.utils.mcp_client import MCPClient

# 自定义序列化器，确保中文正确显示
def custom_tool_serializer(obj: Any) -> str:
    """自定义工具序列化器，确保中文字符正确处理"""
    return json.dumps(obj, ensure_ascii=False, indent=2)

logger = get_logger(__name__)

class MCPSServer(BaseService):
    """MCPS.ONE MCP 服务端"

    作为 MCP 服务端，暴露已配置的 MCP 工具给客户端使用。
    """

    def __init__(self):
        super().__init__("MCPSServer")
        
        # 确保配置管理器已初始化
        config_manager = get_unified_config_manager()
        if config_manager is None:
            config_manager = init_unified_config_manager()
        
        self.mcp_service = MCPService()
        self.server = FastMCP(
            "MCPS.ONE",
            tool_serializer=custom_tool_serializer,
            json_response=False
        )
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.last_health_check = time.time()
        self._tools_registered = False
        self._setup_server()

        # 配置日志级别
        log_level_str = config_manager.get("mcp.server.log_level", "INFO").upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        self.logger.setLevel(log_level)

    async def _initialize_impl(self) -> None:
        """具体的初始化实现"""
        # 初始化MCP服务
        await self.mcp_service.initialize()

        # 这里可以添加其他初始化逻辑，比如：
        # - 预加载工具
        # - 初始化连接
        # - 设置监控等

    async def _start_impl(self) -> None:
        """具体的启动实现"""
        # 启动MCP服务
        await self.mcp_service.start()

        # 注册实际的工具
        if not self._tools_registered:
            await self._register_actual_tools()
            self._tools_registered = True

    async def _stop_impl(self) -> None:
        """具体的停止实现"""
        # 停止MCP服务
        if hasattr(self.mcp_service, 'stop'):
            await self.mcp_service.stop()

    async def _cleanup_impl(self) -> None:
        """具体的清理实现"""
        # 清理MCP服务
        if hasattr(self.mcp_service, 'cleanup'):
            await self.mcp_service.cleanup()

    def _setup_server(self):
        """设置 MCP 服务端"""
        # 动态注册工具
        self._register_dynamic_tools()

        # 注册资源 - 临时禁用以避免日志冲突
        # self._register_resources()

        # 注册提示
        # self._register_prompts()  # FastMCP 不支持 prompt 装饰器

    def _register_dynamic_tools(self):
        """动态注册已配置的 MCP 工具"""

        # 注册管理工具
        @self.server.tool(description="列出所有可用的MCP工具")
        async def list_available_tools() -> str:
            """列出所有可用的 MCP 工具"

            返回当前系统中所有可用的 MCP 工具列表，包括工具名称、描述、状态等信息
            """
            try:
                # 获取数据库中的工具
                db = SessionLocal()
                tools = db.query(MCPTool).all()
                db.close()

                tool_list = []
                for tool in tools:
                    tool_info = {
                        "name": tool.name,
                        "description": tool.description,
                        "category": tool.category,
                        "status": tool.status.value,
                        "capabilities": []
                    }

                    # 尝试获取工具的能力信息
                    try:
                        if tool.status == ToolStatus.RUNNING:
                            client = await self.mcp_service.get_client_by_name(tool.name)
                            if client:
                                capabilities = await client.list_tools()
                                tool_info["capabilities"] = [
                                    {
                                        "name": cap.get("name", ""),
                                        "description": cap.get("description", ""),
                                        "inputSchema": cap.get("inputSchema", {})
                                    }
                                    for cap in capabilities
                                ]
                    except Exception as e:
                        logger.warning(f"获取工具 {tool.name} 能力失败: {e}")

                    tool_list.append(tool_info)

                return json.dumps(tool_list, ensure_ascii=False)
            except Exception as e:
                logger.error(f"列出工具失败: {e}")
                return json.dumps([{"error": f"获取工具列表失败: {str(e)}"}], ensure_ascii=False)

        # 动态注册实际的工具将在服务器启动后执行
        self._tools_registered = False


        @self.server.tool(description="调用指定的MCP工具功能")
        async def call_tool(tool_name: str, tool_function: str, arguments: str) -> str:
            """调用指定的 MCP 工具功能"

            Args:
                tool_name: MCP 工具名称
                tool_function: 要调用的工具函数名
                arguments: 函数参数 (JSON 格式)
            """
            try:
                # 解析参数
                try:
                    args = json.loads(arguments) if arguments else {}
                except json.JSONDecodeError:
                    return f"参数格式错误，必须是有效的 JSON: {arguments}"

                # 获取 MCP 客户端
                client = await self.mcp_service.get_client_by_name(tool_name)
                if not client:
                    return f"工具 {tool_name} 未找到或未运行"

                # 调用工具
                result = await client.call_tool(tool_function, args)

                if result.get("isError", False):
                    return f"工具调用失败: {result.get('content', [{}])[0].get('text', '未知错误') if result.get('content') else '未知错误'}"

                # 格式化返回结果
                content_parts = []
                for content in result.get('content', []):
                    if isinstance(content, dict):
                        if 'text' in content:
                            content_parts.append(content['text'])
                        elif 'data' in content:
                            content_parts.append(f"[图片数据: {content.get('mimeType', 'unknown')}]")
                    elif hasattr(content, 'text'):
                        content_parts.append(content.text)
                    elif hasattr(content, 'data'):
                        content_parts.append(f"[图片数据: {content.mimeType}]")

                return "\n".join(content_parts)

            except Exception as e:
                logger.error(f"调用工具 {tool_name}.{tool_function} 失败: {e}")
                return f"工具调用失败: {str(e)}"

        @self.server.tool(description="获取指定工具的能力列表")
        async def get_tool_capabilities(tool_name: str) -> str:
            """获取指定工具的能力列表"

            Args:
                tool_name: MCP 工具名称
            """
            try:
                client = await self.mcp_service.get_client_by_name(tool_name)
                if not client:
                    return f"工具 {tool_name} 未找到或未运行"

                capabilities = await client.list_tools()

                cap_list = []
                for cap in capabilities:
                    cap_info = {
                        "name": cap.get("name", ""),
                        "description": cap.get("description", ""),
                        "inputSchema": cap.get("inputSchema", {})
                    }
                    cap_list.append(cap_info)

                return json.dumps(cap_list, ensure_ascii=False, indent=2)

            except Exception as e:
                logger.error(f"获取工具 {tool_name} 能力失败: {e}")
                return f"获取工具能力失败: {str(e)}"

        @self.server.tool(description="启动指定的MCP工具")
        async def start_tool(tool_name: str) -> str:
            """启动指定的 MCP 工具"

            Args:
                tool_name: MCP 工具名称
            """
            try:
                success = await self.mcp_service.start_tool_by_name(tool_name)
                if success:
                    return f"工具 {tool_name} 启动成功"
                else:
                    return f"工具 {tool_name} 启动失败"
            except Exception as e:
                logger.error(f"启动工具 {tool_name} 失败: {e}")
                return f"启动工具失败: {str(e)}"

        @self.server.tool(description="停止指定的MCP工具")
        async def stop_tool(tool_name: str) -> str:
            """停止指定的 MCP 工具"

            Args:
                tool_name: MCP 工具名称
            """
            try:
                success = await self.mcp_service.stop_tool_by_name(tool_name)
                if success:
                    return f"工具 {tool_name} 停止成功"
                else:
                    return f"工具 {tool_name} 停止失败"
            except Exception as e:
                logger.error(f"停止工具 {tool_name} 失败: {e}")
                return f"停止工具失败: {str(e)}"


        @self.server.tool(description="健康检查")
        async def health_check() -> str:
            """健康检查"

            返回服务端健康状态信息
            """
            try:
                self.last_health_check = time.time()
                uptime = time.time() - self.start_time

                # 检查数据库连接
                db_status = "healthy"
                try:
                    db = SessionLocal()
                    db.execute("SELECT 1")
                    db.close()
                except Exception as e:
                    db_status = f"unhealthy: {str(e)}"

                # 检查MCP服务
                mcp_status = "healthy"
                try:
                    # 简单检查MCP服务是否可用
                    if not self.mcp_service:
                        mcp_status = "unhealthy: MCP service not available"
                except Exception as e:
                    mcp_status = f"unhealthy: {str(e)}"

                health_info = {
                    "status": "healthy" if db_status == "healthy" and mcp_status == "healthy" else "unhealthy",
                    "uptime_seconds": round(uptime, 2),
                    "request_count": self.request_count,
                    "error_count": self.error_count,
                    "database_status": db_status,
                    "mcp_service_status": mcp_status,
                    "timestamp": datetime.now().isoformat()
                }

                return json.dumps(health_info, ensure_ascii=False, indent=2)

            except Exception as e:
                self.error_count += 1
                logger.error(f"健康检查失败: {e}")
                return json.dumps({
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }, ensure_ascii=False, indent=2)

    async def _register_actual_tools(self):
        """动态注册实际的MCP工具"""
        try:
            # 等待MCP服务初始化完成
            await asyncio.sleep(2)

            db = SessionLocal()
            tools = db.query(MCPTool).filter(
                MCPTool.status == ToolStatus.RUNNING
            ).all()
            db.close()

            logger.info(f"找到 {len(tools)} 个运行中的工具")

            for tool in tools:
                try:
                    client = await self.mcp_service.get_client_by_name(tool.name)
                    if not client:
                        logger.warning(f"无法获取工具 {tool.name} 的客户端")
                        continue

                    # 获取工具的能力
                    capabilities = await client.list_tools()
                    logger.info(f"工具 {tool.name} 有 {len(capabilities)} 个能力")

                    for cap in capabilities:
                        # 为每个能力创建一个MCP工具
                        tool_name = cap['name'] if isinstance(cap, dict) else cap.name
                        tool_desc = cap['description'] if isinstance(cap, dict) else cap.description

                        # 动态创建工具函数
                        def create_tool_function(tool_client, capability_name):
                            async def tool_function(input: str) -> str:
                                try:
                                    # 解析输入参数
                                    import json
                                    try:
                                        args = json.loads(input) if input else {}
                                    except json.JSONDecodeError:
                                        args = {"input": input}

                                    result = await tool_client.call_tool(capability_name, args)

                                    if result.get("isError", False):
                                        error_msg = result.get('content', [{}])[0].get('text', '未知错误') if result.get('content') else '未知错误'
                                        return f"工具调用失败: {error_msg}"

                                    # 格式化返回结果
                                    content_parts = []
                                    for content in result.get('content', []):
                                        if isinstance(content, dict):
                                            if 'text' in content:
                                                content_parts.append(content['text'])
                                            elif 'data' in content:
                                                content_parts.append(f"[图片数据: {content.get('mimeType', 'unknown')}]")
                                        elif hasattr(content, 'text'):
                                            content_parts.append(content.text)
                                        elif hasattr(content, 'data'):
                                            content_parts.append(f"[图片数据: {content.mimeType}]")

                                    return "\n".join(content_parts)

                                except Exception as e:
                                    logger.error(f"调用工具 {capability_name} 失败: {e}")
                                    return f"工具调用失败: {str(e)}"

                            return tool_function

                        # 注册工具
                        tool_func = create_tool_function(client, tool_name)

                        # 使用装饰器方式注册工具
                        decorated_func = self.server.tool(name=tool_name, description=tool_desc)(tool_func)

                        logger.info(f"已注册工具: {tool_name}")

                except Exception as e:
                    logger.error(f"注册工具 {tool.name} 失败: {e}")
                    import traceback
                    traceback.print_exc()

        except Exception as e:
            logger.error(f"动态注册工具失败: {e}")
            import traceback
            traceback.print_exc()

        @self.server.tool()
        async def get_metrics() -> str:
            """获取服务端指标"

            返回详细的性能和使用指标
            """
            try:
                uptime = time.time() - self.start_time

                # 获取工具统计
                db = SessionLocal()
                total_tools = db.query(MCPTool).count()
                running_tools = db.query(MCPTool).filter(MCPTool.status == ToolStatus.RUNNING).count()
                stopped_tools = db.query(MCPTool).filter(MCPTool.status == ToolStatus.STOPPED).count()
                error_tools = db.query(MCPTool).filter(MCPTool.status == ToolStatus.ERROR).count()
                db.close()

                metrics = {
                    "server_info": {
                        "name": "MCPS.ONE MCP Server",
                        "version": get_unified_config().get("VERSION,"),
                        "uptime_seconds": round(uptime, 2),
                        "start_time": datetime.fromtimestamp(self.start_time).isoformat()
                    },
                    "request_metrics": {
                        "total_requests": self.request_count,
                        "total_errors": self.error_count,
                        "error_rate": round(self.error_count / max(self.request_count, 1) * 100, 2)
                    },
                    "tool_metrics": {
                        "total_tools": total_tools,
                        "running_tools": running_tools,
                        "stopped_tools": stopped_tools,
                        "error_tools": error_tools
                    },
                    "system_metrics": {
                        "last_health_check": datetime.fromtimestamp(self.last_health_check).isoformat(),
                        "health_check_enabled": get_unified_config().get("HEALTH_CHECK_ENABLED,"),
                        "metrics_enabled": get_unified_config().get("METRICS_ENABLED,"),
                    },
                    "timestamp": datetime.now().isoformat()
                }

                return json.dumps(metrics, ensure_ascii=False, indent=2)

            except Exception as e:
                self.error_count += 1
                logger.error(f"获取指标失败: {e}")
                return json.dumps({
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }, ensure_ascii=False, indent=2)

    def _register_resources(self):
        """注册资源"""

        @self.server.resource("mcps://tools")
        async def get_tools_resource() -> str:
            """获取所有工具的详细信息"""
            try:
                db = SessionLocal()
                tools = db.query(MCPTool).all()
                db.close()

                tools_data = []
                for tool in tools:
                    tool_data = {
                    "id": tool.id,
                    "tool_name": tool.name,  # 重命名避免与LogRecord的name字段冲突
                    "description": tool.description,
                    "category": tool.category,
                    "status": tool.status.value,
                    "created_at": tool.created_at.isoformat() if tool.created_at else None,
                    "updated_at": tool.updated_at.isoformat() if tool.updated_at else None,
                    "config": tool.config
                }
                    tools_data.append(tool_data)

                return json.dumps(tools_data, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"获取工具资源失败: {e}")
                return f"获取工具资源失败: {str(e)}"

        @self.server.resource("mcps://tool/{tool_name}")
        async def get_tool_resource(tool_name: str) -> str:
            """获取指定工具的详细信息"""
            try:
                db = SessionLocal()
                tool = db.query(MCPTool).filter(MCPTool.name == tool_name).first()
                db.close()

                if not tool:
                    return f"工具 {tool_name} 不存在"

                tool_data = {
                    "id": tool.id,
                    "tool_name": tool.name,  # 重命名避免与LogRecord的name字段冲突
                    "description": tool.description,
                    "category": tool.category,
                    "status": tool.status.value,
                    "created_at": tool.created_at.isoformat() if tool.created_at else None,
                    "updated_at": tool.updated_at.isoformat() if tool.updated_at else None,
                    "config": tool.config
                }

                # 获取工具能力
                try:
                    client = await self.mcp_service.get_client_by_name(tool_name)
                    if client:
                        capabilities = await client.list_tools()
                        tool_data["capabilities"] = [
                            {
                                "name": cap.name,
                                "description": cap.description,
                                "inputSchema": cap.inputSchema
                            }
                            for cap in capabilities
                        ]
                except Exception as e:
                    logger.warning(f"获取工具 {tool_name} 能力失败: {e}")
                    tool_data["capabilities"] = []

                return json.dumps(tool_data, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"获取工具 {tool_name} 资源失败: {e}")
                return f"获取工具资源失败: {str(e)}"

    def _register_prompts(self):
        """注册提示"""

        @self.server.prompt()
        async def use_tool_prompt(tool_name: str, task_description: str) -> str:
            """生成使用指定工具完成任务的提示"

            Args:
                tool_name: 要使用的工具名称
                task_description: 任务描述
            """
            try:
                # 获取工具能力
                client = await self.mcp_service.get_client_by_name(tool_name)
                if not client:
                    return f"工具 {tool_name} 未找到或未运行，无法生成提示。"

                capabilities = await client.list_tools()

                prompt = f"""请使用 {tool_name} 工具来完成以下任务："

任务描述：{task_description}

可用的工具功能：
"""

                for cap in capabilities:
                    prompt += f"\n- {cap.name}: {cap.description}"
                    if cap.inputSchema and 'properties' in cap.inputSchema:
                        prompt += "\n  参数："
                        for param, details in cap.inputSchema['properties'].items():
                            param_desc = details.get('description', '无描述')
                            param_type = details.get('type', '未知类型')
                            prompt += f"\n    - {param} ({param_type}): {param_desc}"

                prompt += "\n\n请根据任务需求选择合适的工具功能并提供正确的参数。"

                return prompt

            except Exception as e:
                logger.error(f"生成工具 {tool_name} 提示失败: {e}")
                return f"生成提示失败: {str(e)}"

        @self.server.prompt()
        async def explore_tools_prompt() -> str:
            """生成探索可用工具的提示"""
            return """欢迎使用 MCPS.ONE！"

我可以帮助您使用已配置的 MCP 工具。以下是一些常用操作：

1. 查看所有可用工具：
   使用 `list_available_tools()` 函数

2. 获取特定工具的能力：
   使用 `get_tool_capabilities(tool_name)` 函数

3. 调用工具功能：
   使用 `call_tool(tool_name, tool_function, arguments)` 函数

4. 管理工具：
   - 启动工具：`start_tool(tool_name)`
   - 停止工具：`stop_tool(tool_name)`

请告诉我您想要完成什么任务，我会帮您选择合适的工具！
"""

    async def run_stdio(self):
        """以 stdio 模式运行 MCP 服务端"""
        logger.info("启动 MCPS.ONE MCP 服务端 (stdio 模式)")
        # 在异步上下文中使用 run_stdio_async
        await self.server.run_stdio_async()

    async def run_http(self, host: str = "127.0.0.1", port: int = 8000):
        """Run the MCP server with HTTP transport"""
        try:
            logger.info(f"启动 MCPS.ONE MCP 服务端 (HTTP 模式) - {host}:{port}")
            logger.info(f"配置信息: transport={get_unified_config().get('MCP_SERVER_TRANSPORT')}, log_level={get_unified_config().get('MCP_SERVER_LOG_LEVEL')}")

            # 注意：run_streamable_http_async 不接受 host/port 参数
            # 它使用默认的 0.0.0.0:8000
            # 如果需要自定义 host/port，需要使用其他方法或配置
            logger.warning(f"注意：FastMCP run_streamable_http_async 使用默认配置 (0.0.0.0:8000)，忽略传入的 {host}:{port}")

            await self.server.run_streamable_http_async()

        except Exception as e:
            self.error_count += 1
            logger.error(f"HTTP模式启动失败: {e}")
            logger.error(f"错误详情: {traceback.format_exc()}")
            raise

    def run_sync_stdio(self):
        """同步方式运行 stdio 模式"""
        logger.info("启动 MCPS.ONE MCP 服务端 (stdio 模式)")
        self.server.run(transport="stdio")

    def run_sync_http(self, host: str = "127.0.0.1", port: int = 8001):
        """同步方式运行 HTTP 模式"""
        logger.info(f"启动 MCPS.ONE MCP 服务端 (HTTP 模式) - {host}:{port}")
        import asyncio
        asyncio.run(self.server.run_streamable_http_async())


# 全局服务端实例
_server_instance: Optional[MCPSServer] = None

def get_mcp_server() -> MCPSServer:
    """获取 MCP 服务端实例"""
    global _server_instance
    if _server_instance is None:
        _server_instance = MCPSServer()
    return _server_instance


if __name__ == "__main__":
    # 命令行运行模式
    import argparse

    parser = argparse.ArgumentParser(description="MCPS.ONE MCP 服务端")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="传输协议 (默认: stdio)"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="HTTP 模式的主机地址 (默认: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="HTTP 模式的端口号 (默认: 8001)"
    )

    args = parser.parse_args()

    server = get_mcp_server()

    if args.transport == "stdio":
        server.run_sync_stdio()
    else:
        server.run_sync_http(args.host, args.port)