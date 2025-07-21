"""WebSocket 实时数据推送服务"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Set, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.system import SystemService
from app.services.tools import ToolService
from app.models.tool import ToolStatus
from app.utils.websocket_manager import (
    websocket_manager, WebSocketMessage, MessageType, ConnectionState
)

logger = logging.getLogger(__name__)

# 兼容性映射：将旧的事件类型映射到新的MessageType
EVENT_TYPE_MAPPING = {
    "system_stats": MessageType.SYSTEM_STATS,
    "tool_status": MessageType.TOOL_STATUS,
    "tool_status_change": MessageType.TOOL_STATUS,
    "task_status_change": MessageType.NOTIFICATION,
    "call_record": MessageType.CALL_RECORD,
    "error": MessageType.ERROR,
    "ping": MessageType.HEARTBEAT,
    "pong": MessageType.HEARTBEAT
}

# 数据缓存
data_cache: Dict[str, Any] = {}

class WebSocketService:
    """WebSocket数据推送服务"""

    def __init__(self):
        self.is_running = False
        self.update_interval = 5  # 5秒更新间隔

    async def start_background_tasks(self):
        """启动后台数据更新任务"""
        if self.is_running:
            return

        self.is_running = True
        logger.info("WebSocket后台数据更新任务已启动")

        # 启动WebSocket管理器
        await websocket_manager.start()

        # 启动各种数据更新任务
        asyncio.create_task(self._update_system_stats())
        asyncio.create_task(self._update_tool_status())


    async def stop_background_tasks(self):
        """停止后台数据更新任务"""
        self.is_running = False

        # 停止WebSocket管理器
        await websocket_manager.stop()

        logger.info("WebSocket后台数据更新任务已停止")

    async def _update_system_stats(self):
        """更新系统统计数据"""
        while self.is_running:
            try:
                # 获取数据库会话
                db = next(get_db())
                try:
                    system_service = SystemService(db)
                    stats = system_service.get_system_stats()

                    # 检查数据是否有变化
                    cache_key = "system_stats"
                    if data_cache.get(cache_key) != stats:
                        data_cache[cache_key] = stats

                        message = WebSocketMessage(
                            type=MessageType.SYSTEM_STATS,
                            data=stats
                        )

                        await websocket_manager.broadcast(message, MessageType.SYSTEM_STATS)

                finally:
                    db.close()

            except Exception as e:
                logger.error(f"更新系统统计数据失败: {e}")

            await asyncio.sleep(self.update_interval)

    async def _update_tool_status(self):
        """更新工具状态数据"""
        while self.is_running:
            try:
                db = next(get_db())
                try:
                    tool_service = ToolService(db)
                    tools, _ = tool_service.get_tools()

                    # 构建工具状态数据
                    tool_status_data = []
                    for tool in tools:
                        tool_status_data.append({
                            "id": tool.id,
                            "name": tool.name,
                            "status": tool.status.value if tool.status else "unknown",
                            "last_started": tool.last_started_at.isoformat() if tool.last_started_at else None,
                            "process_id": tool.process_id,
                            "mcp_port": tool.port
                        })

                    # 检查数据是否有变化
                    cache_key = "tool_status"
                    if data_cache.get(cache_key) != tool_status_data:
                        data_cache[cache_key] = tool_status_data

                        message = WebSocketMessage(
                            type=MessageType.TOOL_STATUS,
                            data=tool_status_data
                        )

                        await websocket_manager.broadcast(message, MessageType.TOOL_STATUS)

                finally:
                    db.close()

            except Exception as e:
                logger.error(f"更新工具状态数据失败: {e}")

            await asyncio.sleep(self.update_interval)



# 全局WebSocket服务实例
websocket_service = WebSocketService()

async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点处理函数"""
    # 生成连接ID
    connection_id = str(uuid.uuid4())

    # 使用新的WebSocket管理器连接
    await websocket_manager.connect(websocket, connection_id)

    # 启动后台任务
    await websocket_service.start_background_tasks()

    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            message = json.loads(data)

            # 处理不同类型的消息
            await handle_websocket_message(websocket, message, connection_id)

    except WebSocketDisconnect:
        await websocket_manager.disconnect(connection_id)
    except Exception as e:
        logger.error(f"WebSocket处理错误: {e}")
        await websocket_manager.disconnect(connection_id)

async def handle_websocket_message(websocket: WebSocket, message: dict, connection_id: str):
    """处理WebSocket消息"""
    try:
        msg_type = message.get("type")
        data = message.get("data", {})

        if msg_type == "subscribe":
            # 订阅事件
            event_types = data.get("events", [])
            # 转换为新的MessageType
            message_types = [EVENT_TYPE_MAPPING.get(event, MessageType.NOTIFICATION) for event in event_types]

            websocket_manager.subscribe(connection_id, message_types)

            # 发送确认消息
            response = WebSocketMessage(
                type=MessageType.NOTIFICATION,
                data={"events": event_types, "status": "subscribed"}
            )
            await websocket_manager.send_to_client(connection_id, response)

        elif msg_type == "unsubscribe":
            # 取消订阅事件
            event_types = data.get("events", [])
            # 转换为新的MessageType
            message_types = [EVENT_TYPE_MAPPING.get(event, MessageType.NOTIFICATION) for event in event_types]

            websocket_manager.unsubscribe(connection_id, message_types)

            # 发送确认消息
            response = WebSocketMessage(
                type=MessageType.NOTIFICATION,
                data={"events": event_types, "status": "unsubscribed"}
            )
            await websocket_manager.send_to_client(connection_id, response)

        elif msg_type == "ping":
            # 心跳检测
            response = WebSocketMessage(
                type=MessageType.HEARTBEAT,
                data={"type": "pong"}
            )
            await websocket_manager.send_to_client(connection_id, response)

        else:
            logger.warning(f"未知的消息类型: {msg_type}")

    except Exception as e:
        logger.error(f"处理WebSocket消息失败: {e}")

# 工具状态变更通知
async def notify_tool_status_change(tool_id: str, status: str, details: dict = None):
    """通知工具状态变更"""
    message = WebSocketMessage(
        type=MessageType.TOOL_STATUS,
        data={
            "tool_id": tool_id,
            "status": status,
            "details": details or {}
        }
    )

    await websocket_manager.broadcast(message, MessageType.TOOL_STATUS)
    logger.info(f"已广播工具状态变更: {tool_id} -> {status}")

async def notify_task_status_change(task_id: str, status: str, result: dict = None):
    """通知任务状态变更"""
    message = WebSocketMessage(
        type=MessageType.NOTIFICATION,
        data={
            "task_id": task_id,
            "status": status,
            "result": result or {}
        }
    )

    await websocket_manager.broadcast(message, MessageType.NOTIFICATION)
    logger.info(f"已广播任务状态变更: {task_id} -> {status}")
