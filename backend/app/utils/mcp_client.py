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
        if not self.connected:
            return False
        
        try:
            if self.connection_type == "stdio":
                return self.process and self.process.poll() is None
            elif self.connection_type == "server":
                return self.session and not self.session.closed
            elif self.connection_type == "websocket":
                return self.websocket and not self.websocket.closed
            else:
                return False
        except Exception:
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
            # 发送请求
            request_str = json.dumps(request) + "\n"
            self.process.stdin.write(request_str.encode())
            self.process.stdin.flush()
            
            # 等待响应
            response_str = await asyncio.wait_for(
                asyncio.to_thread(self.process.stdout.readline),
                timeout=timeout
            )
            
            if not response_str:
                raise MCPConnectionError("未收到响应")
            
            response = json.loads(response_str.decode().strip())
            
            # 检查错误
            if "error" in response:
                error = response["error"]
                raise MCPMethodError(f"MCP错误: {error.get('message', '未知错误')}")
            
            return response
            
        except asyncio.TimeoutError:
            raise MCPTimeoutError(f"请求超时: {timeout}秒")
        except json.JSONDecodeError as e:
            raise MCPMethodError(f"JSON解析错误: {e}")
    
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
            await self.websocket.send(json.dumps(request))
            
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