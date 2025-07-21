"""MCP 客户端模块"""

import asyncio
import json
import logging
import subprocess
import websockets
import aiohttp
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

from app.utils.exceptions import MCPConnectionError, MCPTimeoutError, MCPMethodError

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class MCPClient:
    """MCP 协议客户端"""

    def __init__(
        self,
        connection_type: str,
        process: Optional[subprocess.Popen] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        websocket_url: Optional[str] = None
    ):
        self.connection_type = connection_type  # "stdio", "server", "websocket"
        self.process = process
        self.host = host
        self.port = port
        self.websocket_url = websocket_url
        self.websocket = None
        self.session = None
        self.connected = False
        self.request_id = 0

    async def connect(self, timeout: int = 30) -> bool:
        """连接到MCP服务"""
        try:
            if self.connection_type == "stdio":
                return await self._connect_stdio(timeout)
            elif self.connection_type == "server":
                return await self._connect_server(timeout)
            elif self.connection_type == "websocket":
                return await self._connect_websocket(timeout)
            else:
                raise MCPConnectionError(f"不支持的连接类型: {self.connection_type}")

        except Exception as e:
            logger.error(f"MCP连接失败: {e}")
            await self.close()
            raise MCPConnectionError(f"连接失败: {e}")

    async def _connect_stdio(self, timeout: int = 30) -> bool:
        """STDIO连接"""
        if not self.process:
            raise MCPConnectionError("STDIO连接需要进程对象")

        # 发送初始化请求
        init_request = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {
                        "listChanged": True
                    },
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "MCPS.ONE",
                    "version": "1.0.0"
                }
            }
        }

        response = await self._send_request(init_request, timeout)
        if response and "result" in response:
            self.connected = True
            logger.info(f"MCP STDIO客户端连接成功 (PID: {self.process.pid})")
            return True
        else:
            logger.error(f"MCP初始化失败: {response}")
            return False

    async def _connect_server(self, timeout: int = 30) -> bool:
        """HTTP服务器连接"""
        if not self.host or not self.port:
            raise MCPConnectionError("服务器连接需要host和port")

        self.session = aiohttp.ClientSession()

        # 测试连接
        try:
            url = f"http://{self.host}:{self.port}/health"
            async with self.session.get(url, timeout=timeout) as response:
                if response.status == 200:
                    self.connected = True
                    logger.info(f"MCP服务器客户端连接成功: {self.host}:{self.port}")
                    return True
                else:
                    logger.error(f"服务器健康检查失败: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"服务器连接失败: {e}")
            return False

    async def _connect_websocket(self, timeout: int = 30) -> bool:
        """WebSocket连接"""
        if not self.websocket_url:
            raise MCPConnectionError("WebSocket连接需要URL")

        try:
            self.websocket = await asyncio.wait_for(
                websockets.connect(self.websocket_url),
                timeout=timeout
            )

            # 发送初始化请求
            init_request = {
                "jsonrpc": "2.0",
                "id": self._next_request_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "roots": {
                            "listChanged": True
                        },
                        "sampling": {}
                    },
                    "clientInfo": {
                        "name": "MCPS.ONE",
                        "version": "1.0.0"
                    }
                }
            }

            await self.websocket.send(json.dumps(init_request))
            response_str = await asyncio.wait_for(
                self.websocket.recv(),
                timeout=timeout
            )

            response = json.loads(response_str)
            if response and "result" in response:
                self.connected = True
                logger.info(f"MCP WebSocket客户端连接成功: {self.websocket_url}")
                return True
            else:
                logger.error(f"MCP初始化失败: {response}")
                return False

        except Exception as e:
            logger.error(f"WebSocket连接失败: {e}")
            return False

    async def close(self):
        """关闭连接"""
        try:
            self.connected = False

            if self.connection_type == "stdio" and self.process:
                try:
                    self.process.terminate()
                    await asyncio.sleep(1)
                    if self.process.poll() is None:
                        self.process.kill()
                except Exception as e:
                    logger.error(f"关闭STDIO进程时出错: {e}")
                finally:
                    self.process = None

            elif self.connection_type == "server" and self.session:
                try:
                    await self.session.close()
                except Exception as e:
                    logger.error(f"关闭HTTP会话时出错: {e}")
                finally:
                    self.session = None

            elif self.connection_type == "websocket" and self.websocket:
                try:
                    await self.websocket.close()
                except Exception as e:
                    logger.error(f"关闭WebSocket时出错: {e}")
                finally:
                    self.websocket = None

        except Exception as e:
            logger.error(f"关闭连接时出错: {e}")

    async def disconnect(self):
        """断开连接（兼容性方法）"""
        await self.close()

    async def is_connected(self) -> bool:
        """检查连接状态"""
        logger.debug(f"检查MCP客户端连接状态: connected={self.connected}, type={self.connection_type}")

        if not self.connected:
            logger.debug("MCP客户端未标记为已连接")
            return False

        try:
            if self.connection_type == "stdio":
                process_running = self.process and self.process.poll() is None
                logger.debug(f"STDIO连接检查: process={self.process is not None}, poll={self.process.poll() if self.process else 'N/A'}, running={process_running}")
                return process_running
            elif self.connection_type == "server":
                session_open = self.session and not self.session.closed
                logger.debug(f"Server连接检查: session={self.session is not None}, closed={self.session.closed if self.session else 'N/A'}, open={session_open}")
                return session_open
            elif self.connection_type == "websocket":
                websocket_open = self.websocket and not self.websocket.closed
                logger.debug(f"WebSocket连接检查: websocket={self.websocket is not None}, closed={self.websocket.closed if self.websocket else 'N/A'}, open={websocket_open}")
                return websocket_open
            else:
                logger.debug(f"不支持的连接类型: {self.connection_type}")
                return False
        except Exception as e:
            logger.debug(f"连接状态检查异常: {e}")
            return False

    async def list_tools(self) -> List[Dict[str, Any]]:
        """获取工具列表"""
        if not self.connected:
            raise MCPConnectionError("未连接到MCP服务")

        request = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "tools/list",
            "params": {}
        }

        response = await self._send_request(request)
        if response and "result" in response:
            return response["result"].get("tools", [])
        else:
            raise MCPMethodError(f"获取工具列表失败: {response}")

    async def call_tool(self, name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """调用工具"""
        if not self.connected:
            raise MCPConnectionError("未连接到MCP服务")

        request = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments or {}
            }
        }

        response = await self._send_request(request)
        if response and "result" in response:
            return response["result"]
        else:
            raise MCPMethodError(f"调用工具失败: {response}")

    async def list_resources(self) -> List[Dict[str, Any]]:
        """获取资源列表"""
        if not self.connected:
            raise MCPConnectionError("未连接到MCP服务")

        request = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "resources/list",
            "params": {}
        }

        response = await self._send_request(request)
        if response and "result" in response:
            return response["result"].get("resources", [])
        else:
            raise MCPMethodError(f"获取资源列表失败: {response}")

    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """读取资源"""
        if not self.connected:
            raise MCPConnectionError("未连接到MCP服务")

        request = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "resources/read",
            "params": {
                "uri": uri
            }
        }

        response = await self._send_request(request)
        if response and "result" in response:
            return response["result"]
        else:
            raise MCPMethodError(f"读取资源失败: {response}")

    async def list_prompts(self) -> List[Dict[str, Any]]:
        """获取提示列表"""
        if not self.connected:
            raise MCPConnectionError("未连接到MCP服务")

        request = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "prompts/list",
            "params": {}
        }

        response = await self._send_request(request)
        if response and "result" in response:
            return response["result"].get("prompts", [])
        else:
            raise MCPMethodError(f"获取提示列表失败: {response}")

    async def get_prompt(self, name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """获取提示"""
        if not self.connected:
            raise MCPConnectionError("未连接到MCP服务")

        request = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "prompts/get",
            "params": {
                "name": name,
                "arguments": arguments or {}
            }
        }

        response = await self._send_request(request)
        if response and "result" in response:
            return response["result"]
        else:
            raise MCPMethodError(f"获取提示失败: {response}")

    async def _send_request(self, request: Dict[str, Any], timeout: int = 30) -> Optional[Dict[str, Any]]:
        """发送请求"""
        try:
            if self.connection_type == "stdio":
                return await self._send_stdio_request(request, timeout)
            elif self.connection_type == "server":
                return await self._send_server_request(request, timeout)
            elif self.connection_type == "websocket":
                return await self._send_websocket_request(request, timeout)
            else:
                raise MCPConnectionError(f"不支持的连接类型: {self.connection_type}")

        except Exception as e:
            if isinstance(e, (MCPConnectionError, MCPTimeoutError, MCPMethodError)):
                raise
            else:
                raise MCPConnectionError(f"发送请求失败: {e}")

    async def _send_stdio_request(self, request: Dict[str, Any], timeout: int = 30) -> Optional[Dict[str, Any]]:
        """发送STDIO请求"""
        if not self.process or not self.process.stdin:
            raise MCPConnectionError("进程未启动或stdin不可用")

        try:
            # 检查进程状态
            if self.process.poll() is not None:
                raise MCPConnectionError(f"进程已退出，退出码: {self.process.poll()}")

            # 发送请求 - 增强编码处理
            request_str = json.dumps(request, ensure_ascii=False) + "\n"
            logger.debug(f"发送MCP请求: {request_str.strip()}")

            # 确保正确的编码处理
            try:
                # 如果 stdin 需要 bytes，则编码为 UTF-8
                if hasattr(self.process.stdin, 'mode') and 'b' in self.process.stdin.mode:
                    self.process.stdin.write(request_str.encode('utf-8'))
                else:
                    # 否则直接写入字符串
                    self.process.stdin.write(request_str)
                self.process.stdin.flush()
            except UnicodeEncodeError as e:
                logger.error(f"编码错误: {e}，尝试使用 ASCII 编码")
                # 如果 UTF-8 编码失败，回退到 ASCII 编码
                request_str_ascii = json.dumps(request, ensure_ascii=True) + "\n"
                self.process.stdin.write(request_str_ascii)
                self.process.stdin.flush()

            # 等待响应
            response_str = await asyncio.wait_for(
                asyncio.to_thread(self.process.stdout.readline),
                timeout=timeout
            )

            if not response_str:
                # 检查进程是否有错误输出
                stderr_output = ""
                if self.process.stderr:
                    try:
                        stderr_data = self.process.stderr.read(1024)
                        if stderr_data:
                            stderr_output = stderr_data.decode('utf-8', errors='replace')
                    except Exception as e:
                        stderr_output = f"读取错误输出失败: {e}"
                raise MCPConnectionError(f"未收到响应，进程可能已退出。stderr: {stderr_output}")

            # 增强的响应编码处理
            if isinstance(response_str, bytes):
                # 尝试多种编码方式解码
                try:
                    response_text = response_str.decode('utf-8').strip()
                except UnicodeDecodeError:
                    try:
                        response_text = response_str.decode('gbk').strip()
                    except UnicodeDecodeError:
                        response_text = response_str.decode('utf-8', errors='replace').strip()
                        logger.warning("响应解码时发生错误，使用替换模式")
            else:
                response_text = response_str.strip()

            logger.debug(f"收到MCP响应: {response_text}")

            if not response_text:
                raise MCPConnectionError("收到空响应")

            # JSON 解析时确保正确处理 Unicode
            try:
                response = json.loads(response_text)
            except json.JSONDecodeError as e:
                # 如果 JSON 解析失败，尝试处理可能的编码问题
                logger.warning(f"JSON 解析失败: {e}，尝试修复编码问题")
                try:
                    # 尝试修复可能的双重编码问题
                    fixed_text = response_text.encode('latin1').decode('utf-8')
                    response = json.loads(fixed_text)
                except Exception:
                    # 如果修复失败，重新抛出原始错误
                    raise e

            # 检查错误
            if "error" in response:
                error = response["error"]
                raise MCPMethodError(f"MCP错误: {error.get('message', '未知错误')}")

            return response

        except asyncio.TimeoutError:
            raise MCPTimeoutError(f"请求超时: {timeout}秒")
        except json.JSONDecodeError as e:
            raise MCPMethodError(f"JSON解析错误: {e}, 响应内容: {response_text if 'response_text' in locals() else 'N/A'}")

    async def _send_server_request(self, request: Dict[str, Any], timeout: int = 30) -> Optional[Dict[str, Any]]:
        """发送HTTP服务器请求"""
        if not self.session:
            raise MCPConnectionError("HTTP会话未建立")

        try:
            url = f"http://{self.host}:{self.port}/mcp"
            async with self.session.post(
                url,
                json=request,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                if response.status == 200:
                    result = await response.json()

                    # 检查错误
                    if "error" in result:
                        error = result["error"]
                        raise MCPMethodError(f"MCP错误: {error.get('message', '未知错误')}")

                    return result
                else:
                    raise MCPConnectionError(f"HTTP错误: {response.status}")

        except asyncio.TimeoutError:
            raise MCPTimeoutError(f"请求超时: {timeout}秒")
        except aiohttp.ClientError as e:
            raise MCPConnectionError(f"HTTP请求失败: {e}")

    async def _send_websocket_request(self, request: Dict[str, Any], timeout: int = 30) -> Optional[Dict[str, Any]]:
        """发送WebSocket请求"""
        if not self.websocket:
            raise MCPConnectionError("WebSocket连接未建立")

        try:
            # 发送请求
            await self.websocket.send(json.dumps(request, ensure_ascii=False))

            # 等待响应
            response_str = await asyncio.wait_for(
                self.websocket.recv(),
                timeout=timeout
            )

            response = json.loads(response_str)

            # 检查错误
            if "error" in response:
                error = response["error"]
                raise MCPMethodError(f"MCP错误: {error.get('message', '未知错误')}")

            return response

        except asyncio.TimeoutError:
            raise MCPTimeoutError(f"请求超时: {timeout}秒")
        except websockets.exceptions.ConnectionClosed:
            raise MCPConnectionError("WebSocket连接已关闭")
        except json.JSONDecodeError as e:
            raise MCPMethodError(f"JSON解析错误: {e}")

    def _next_request_id(self) -> int:
        """获取下一个请求ID"""
        self.request_id += 1
        return self.request_id

    @property
    def process_id(self) -> Optional[int]:
        """获取进程ID"""
        if self.connection_type == "stdio" and self.process:
            return self.process.pid
        return None

    async def get_capabilities(self) -> Dict[str, Any]:
        """获取服务器能力"""
        if not self.connected:
            raise MCPConnectionError("未连接到MCP服务")

        request = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "capabilities",
            "params": {}
        }

        response = await self._send_request(request)
        if response and "result" in response:
            return response["result"]
        else:
            raise MCPMethodError(f"获取能力失败: {response}")

    async def call_method(self, method: str, params: Dict[str, Any] = None) -> Any:
        """调用通用方法"""
        if not self.connected:
            raise MCPConnectionError("未连接到MCP服务")

        request = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": method,
            "params": params or {}
        }

        response = await self._send_request(request)
        if response and "result" in response:
            return response["result"]
        else:
            raise MCPMethodError(f"调用方法失败: {response}")
