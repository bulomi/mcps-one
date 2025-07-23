"""WebSocket管理模块

提供WebSocket连接池管理、消息批处理和性能优化功能。
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Set, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
from weakref import WeakSet

from fastapi import WebSocket, WebSocketDisconnect
# from app.utils.exceptions import SessionError # 会话管理功能已移除
from app.utils.exceptions import MCPSException

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """消息类型"""
    TOOL_STATUS = "tool_status"
    SYSTEM_STATS = "system_stats"
    CALL_RECORD = "call_record"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    NOTIFICATION = "notification"


class ConnectionState(Enum):
    """连接状态"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class WebSocketMessage:
    """WebSocket消息"""
    type: MessageType
    data: Any
    timestamp: float = field(default_factory=time.time)
    priority: int = 0  # 优先级，数字越大优先级越高
    target_clients: Optional[Set[str]] = None  # 目标客户端ID，None表示广播

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp
        }

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


@dataclass
class ConnectionInfo:
    """连接信息"""
    client_id: str
    websocket: WebSocket
    state: ConnectionState
    connected_at: float
    last_heartbeat: float
    subscriptions: Set[MessageType] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_alive(self, heartbeat_timeout: float = 60.0) -> bool:
        """检查连接是否存活"""
        return (
            self.state == ConnectionState.CONNECTED and
            time.time() - self.last_heartbeat < heartbeat_timeout
        )

    def update_heartbeat(self):
        """更新心跳时间"""
        self.last_heartbeat = time.time()


class MessageBatcher:
    """消息批处理器"""

    def __init__(self, batch_size: int = 10, batch_timeout: float = 0.1):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.pending_messages: Dict[str, List[WebSocketMessage]] = defaultdict(list)
        self.batch_timers: Dict[str, asyncio.Task] = {}
        self.send_callback: Optional[Callable] = None

    def set_send_callback(self, callback: Callable):
        """设置发送回调函数"""
        self.send_callback = callback

    async def add_message(self, client_id: str, message: WebSocketMessage):
        """添加消息到批处理队列"""
        self.pending_messages[client_id].append(message)

        # 检查是否需要立即发送
        if len(self.pending_messages[client_id]) >= self.batch_size:
            await self._flush_batch(client_id)
        else:
            # 设置定时器
            if client_id not in self.batch_timers:
                self.batch_timers[client_id] = asyncio.create_task(
                    self._batch_timer(client_id)
                )

    async def _batch_timer(self, client_id: str):
        """批处理定时器"""
        try:
            await asyncio.sleep(self.batch_timeout)
            await self._flush_batch(client_id)
        except asyncio.CancelledError:
            pass

    async def _flush_batch(self, client_id: str):
        """刷新批处理消息"""
        if client_id not in self.pending_messages:
            return

        messages = self.pending_messages[client_id]
        if not messages:
            return

        # 清理
        self.pending_messages[client_id] = []
        if client_id in self.batch_timers:
            self.batch_timers[client_id].cancel()
            del self.batch_timers[client_id]

        # 发送批处理消息
        if self.send_callback:
            try:
                await self.send_callback(client_id, messages)
            except Exception as e:
                logger.error(f"发送批处理消息失败: {e}")

    async def flush_all(self):
        """刷新所有待处理消息"""
        for client_id in list(self.pending_messages.keys()):
            await self._flush_batch(client_id)


class WebSocketManager:
    """WebSocket管理器"""

    def __init__(self,
                 max_connections: int = 100,
                 heartbeat_interval: float = 30.0,
                 heartbeat_timeout: float = 60.0,
                 enable_batching: bool = True,
                 batch_size: int = 10,
                 batch_timeout: float = 0.1):

        self.max_connections = max_connections
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_timeout = heartbeat_timeout

        # 连接管理
        self.connections: Dict[str, ConnectionInfo] = {}
        self.connection_count = 0

        # 订阅管理
        self.subscriptions: Dict[MessageType, Set[str]] = defaultdict(set)

        # 消息队列
        self.message_queue: deque = deque(maxlen=1000)

        # 批处理
        self.enable_batching = enable_batching
        if enable_batching:
            self.batcher = MessageBatcher(batch_size, batch_timeout)
            self.batcher.set_send_callback(self._send_batch_messages)

        # 统计信息
        self.stats = {
            "total_connections": 0,
            "current_connections": 0,
            "messages_sent": 0,
            "messages_failed": 0,
            "bytes_sent": 0
        }

        # 后台任务
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """启动WebSocket管理器"""
        if self._running:
            return

        self._running = True

        # 启动后台任务
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        logger.info("WebSocket管理器已启动")

    async def stop(self):
        """停止WebSocket管理器"""
        if not self._running:
            return

        self._running = False

        # 停止后台任务
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()

        # 关闭所有连接
        await self.disconnect_all()

        # 刷新批处理消息
        if self.enable_batching:
            await self.batcher.flush_all()

        logger.info("WebSocket管理器已停止")

    async def connect(self, websocket: WebSocket, client_id: str,
                     metadata: Optional[Dict[str, Any]] = None) -> bool:
        """建立WebSocket连接"""
        try:
            # 检查连接数限制
            if self.connection_count >= self.max_connections:
                logger.warning(f"连接数已达上限: {self.max_connections}")
                await websocket.close(code=1013, reason="Too many connections")
                return False

            # 接受连接
            await websocket.accept()

            # 创建连接信息
            connection = ConnectionInfo(
                client_id=client_id,
                websocket=websocket,
                state=ConnectionState.CONNECTED,
                connected_at=time.time(),
                last_heartbeat=time.time(),
                metadata=metadata or {}
            )

            # 如果客户端已存在，先断开旧连接
            if client_id in self.connections:
                await self._disconnect_client(client_id)

            # 注册连接
            self.connections[client_id] = connection
            self.connection_count += 1
            self.stats["total_connections"] += 1
            self.stats["current_connections"] = self.connection_count

            logger.info(f"WebSocket连接已建立: {client_id}")

            # 发送欢迎消息
            await self.send_to_client(client_id, WebSocketMessage(
                type=MessageType.NOTIFICATION,
                data={"message": "连接成功", "client_id": client_id}
            ))

            return True

        except Exception as e:
            logger.error(f"建立WebSocket连接失败: {e}")
            return False

    async def disconnect(self, client_id: str, code: int = 1000, reason: str = "Normal closure"):
        """断开WebSocket连接"""
        await self._disconnect_client(client_id, code, reason)

    async def _disconnect_client(self, client_id: str, code: int = 1000, reason: str = "Normal closure"):
        """内部断开连接方法"""
        if client_id not in self.connections:
            return

        connection = self.connections[client_id]

        try:
            connection.state = ConnectionState.DISCONNECTING

            # 关闭WebSocket
            if connection.websocket:
                await connection.websocket.close(code=code, reason=reason)

            connection.state = ConnectionState.DISCONNECTED

        except Exception as e:
            logger.warning(f"关闭WebSocket连接时出错: {e}")
            connection.state = ConnectionState.ERROR

        finally:
            # 清理连接
            self._cleanup_connection(client_id)
            logger.info(f"WebSocket连接已断开: {client_id}")

    def _cleanup_connection(self, client_id: str):
        """清理连接资源"""
        if client_id in self.connections:
            connection = self.connections[client_id]

            # 清理订阅
            for message_type in connection.subscriptions:
                self.subscriptions[message_type].discard(client_id)

            # 移除连接
            del self.connections[client_id]
            self.connection_count -= 1
            self.stats["current_connections"] = self.connection_count

    async def disconnect_all(self):
        """断开所有连接"""
        client_ids = list(self.connections.keys())
        for client_id in client_ids:
            await self._disconnect_client(client_id)

    def subscribe(self, client_id: str, message_types: List[MessageType]):
        """订阅消息类型"""
        if client_id not in self.connections:
            raise MCPSException(f"客户端不存在: {client_id}")

        connection = self.connections[client_id]

        for message_type in message_types:
            connection.subscriptions.add(message_type)
            self.subscriptions[message_type].add(client_id)

        logger.debug(f"客户端 {client_id} 订阅了消息类型: {[mt.value for mt in message_types]}")

    def unsubscribe(self, client_id: str, message_types: List[MessageType]):
        """取消订阅消息类型"""
        if client_id not in self.connections:
            return

        connection = self.connections[client_id]

        for message_type in message_types:
            connection.subscriptions.discard(message_type)
            self.subscriptions[message_type].discard(client_id)

        logger.debug(f"客户端 {client_id} 取消订阅消息类型: {[mt.value for mt in message_types]}")

    async def send_to_client(self, client_id: str, message: WebSocketMessage):
        """发送消息给指定客户端"""
        if client_id not in self.connections:
            logger.warning(f"客户端不存在: {client_id}")
            return

        if self.enable_batching and message.priority < 5:  # 低优先级消息使用批处理
            await self.batcher.add_message(client_id, message)
        else:
            await self._send_message_direct(client_id, message)

    async def _send_message_direct(self, client_id: str, message: WebSocketMessage):
        """直接发送消息"""
        connection = self.connections.get(client_id)
        if not connection or connection.state != ConnectionState.CONNECTED:
            return

        try:
            message_json = message.to_json()
            await connection.websocket.send_text(message_json)

            # 更新统计
            self.stats["messages_sent"] += 1
            self.stats["bytes_sent"] += len(message_json.encode('utf-8'))

        except WebSocketDisconnect:
            logger.info(f"客户端已断开连接: {client_id}")
            await self._disconnect_client(client_id)
        except Exception as e:
            logger.error(f"发送消息失败: {client_id}, error: {e}")
            self.stats["messages_failed"] += 1
            await self._disconnect_client(client_id)

    async def _send_batch_messages(self, client_id: str, messages: List[WebSocketMessage]):
        """发送批处理消息"""
        connection = self.connections.get(client_id)
        if not connection or connection.state != ConnectionState.CONNECTED:
            return

        try:
            # 构建批处理消息
            batch_data = {
                "type": "batch",
                "messages": [msg.to_dict() for msg in messages],
                "count": len(messages),
                "timestamp": time.time()
            }

            message_json = json.dumps(batch_data, ensure_ascii=False)
            await connection.websocket.send_text(message_json)

            # 更新统计
            self.stats["messages_sent"] += len(messages)
            self.stats["bytes_sent"] += len(message_json.encode('utf-8'))

        except WebSocketDisconnect:
            logger.info(f"客户端已断开连接: {client_id}")
            await self._disconnect_client(client_id)
        except Exception as e:
            logger.error(f"发送批处理消息失败: {client_id}, error: {e}")
            self.stats["messages_failed"] += len(messages)
            await self._disconnect_client(client_id)

    async def broadcast(self, message: WebSocketMessage,
                      message_type: Optional[MessageType] = None):
        """广播消息"""
        target_clients = set()

        if message_type:
            # 发送给订阅了特定消息类型的客户端
            target_clients = self.subscriptions.get(message_type, set())
        else:
            # 发送给所有客户端
            target_clients = set(self.connections.keys())

        # 并发发送
        tasks = []
        for client_id in target_clients:
            if client_id in self.connections:
                tasks.append(self.send_to_client(client_id, message))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _heartbeat_loop(self):
        """心跳循环"""
        while self._running:
            try:
                # 发送心跳消息
                heartbeat_msg = WebSocketMessage(
                    type=MessageType.HEARTBEAT,
                    data={"timestamp": time.time()},
                    priority=10  # 高优先级，不使用批处理
                )

                await self.broadcast(heartbeat_msg)

                await asyncio.sleep(self.heartbeat_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"心跳循环错误: {e}")
                await asyncio.sleep(1)

    async def _cleanup_loop(self):
        """清理循环"""
        while self._running:
            try:
                # 检查死连接
                dead_clients = []
                for client_id, connection in self.connections.items():
                    if not connection.is_alive(self.heartbeat_timeout):
                        dead_clients.append(client_id)

                # 清理死连接
                for client_id in dead_clients:
                    logger.info(f"清理死连接: {client_id}")
                    await self._disconnect_client(client_id)

                await asyncio.sleep(30)  # 每30秒清理一次

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理循环错误: {e}")
                await asyncio.sleep(1)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "active_connections": len(self.connections),
            "subscriptions": {
                msg_type.value: len(clients)
                for msg_type, clients in self.subscriptions.items()
            }
        }

    def get_connection_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """获取连接信息"""
        connection = self.connections.get(client_id)
        if not connection:
            return None

        return {
            "client_id": connection.client_id,
            "state": connection.state.value,
            "connected_at": connection.connected_at,
            "last_heartbeat": connection.last_heartbeat,
            "subscriptions": [sub.value for sub in connection.subscriptions],
            "metadata": connection.metadata
        }


# 全局WebSocket管理器实例
websocket_manager = WebSocketManager()
