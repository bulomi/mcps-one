"""WebSocket 实时数据推送服务"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Set, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.system_service import SystemService
from app.services.tool_service import ToolService

from app.models.tool import ToolStatus

logger = logging.getLogger(__name__)

class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 存储活跃连接
        self.active_connections: Set[WebSocket] = set()
        # 订阅管理
        self.subscriptions: Dict[WebSocket, Set[str]] = {}
        # 数据缓存
        self.data_cache: Dict[str, Any] = {}
        
    async def connect(self, websocket: WebSocket):
        """接受WebSocket连接"""
        await websocket.accept()
        self.active_connections.add(websocket)
        self.subscriptions[websocket] = set()
        logger.info(f"WebSocket连接已建立，当前连接数: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        self.active_connections.discard(websocket)
        self.subscriptions.pop(websocket, None)
        logger.info(f"WebSocket连接已断开，当前连接数: {len(self.active_connections)}")
        
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """发送个人消息"""
        try:
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
        except Exception as e:
            logger.error(f"发送个人消息失败: {e}")
            self.disconnect(websocket)
            
    async def broadcast(self, message: dict, event_type: str = None):
        """广播消息给所有连接"""
        if not self.active_connections:
            return
            
        disconnected = set()
        for connection in self.active_connections:
            try:
                # 检查订阅
                if event_type and event_type not in self.subscriptions.get(connection, set()):
                    continue
                    
                await connection.send_text(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                logger.error(f"广播消息失败: {e}")
                disconnected.add(connection)
                
        # 清理断开的连接
        for connection in disconnected:
            self.disconnect(connection)
            
    def subscribe(self, websocket: WebSocket, event_types: List[str]):
        """订阅事件类型"""
        if websocket in self.subscriptions:
            self.subscriptions[websocket].update(event_types)
            
    def unsubscribe(self, websocket: WebSocket, event_types: List[str]):
        """取消订阅事件类型"""
        if websocket in self.subscriptions:
            self.subscriptions[websocket] -= set(event_types)

# 全局连接管理器
manager = ConnectionManager()

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
        
        # 启动各种数据更新任务
        asyncio.create_task(self._update_system_stats())
        asyncio.create_task(self._update_tool_status())

        
    async def stop_background_tasks(self):
        """停止后台数据更新任务"""
        self.is_running = False
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
                    if manager.data_cache.get(cache_key) != stats:
                        manager.data_cache[cache_key] = stats
                        
                        message = {
                            "type": "system_stats",
                            "data": stats,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        await manager.broadcast(message, "system_stats")
                        
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
                    tools = await tool_service.get_all_tools()
                    
                    # 构建工具状态数据
                    tool_status_data = []
                    for tool in tools:
                        tool_status_data.append({
                            "id": tool.id,
                            "name": tool.name,
                            "status": tool.status.value if tool.status else "unknown",
                            "last_started": tool.last_started.isoformat() if tool.last_started else None,
                            "process_id": tool.process_id,
                            "mcp_port": tool.mcp_port
                        })
                    
                    # 检查数据是否有变化
                    cache_key = "tool_status"
                    if manager.data_cache.get(cache_key) != tool_status_data:
                        manager.data_cache[cache_key] = tool_status_data
                        
                        message = {
                            "type": "tool_status",
                            "data": tool_status_data,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        await manager.broadcast(message, "tool_status")
                        
                finally:
                    db.close()
                    
            except Exception as e:
                logger.error(f"更新工具状态数据失败: {e}")
                
            await asyncio.sleep(self.update_interval)
            


# 全局WebSocket服务实例
websocket_service = WebSocketService()

async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点处理函数"""
    await manager.connect(websocket)
    
    # 启动后台任务
    await websocket_service.start_background_tasks()
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 处理不同类型的消息
            await handle_websocket_message(websocket, message)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket处理错误: {e}")
        manager.disconnect(websocket)

async def handle_websocket_message(websocket: WebSocket, message: dict):
    """处理WebSocket消息"""
    try:
        msg_type = message.get("type")
        
        if msg_type == "subscribe":
            # 订阅事件
            event_types = message.get("events", [])
            manager.subscribe(websocket, event_types)
            
            # 发送确认消息
            response = {
                "type": "subscribe_success",
                "events": event_types,
                "timestamp": datetime.now().isoformat()
            }
            await manager.send_personal_message(response, websocket)
            
            # 发送当前缓存的数据
            for event_type in event_types:
                if event_type in manager.data_cache:
                    cached_message = {
                        "type": event_type,
                        "data": manager.data_cache[event_type],
                        "timestamp": datetime.now().isoformat()
                    }
                    await manager.send_personal_message(cached_message, websocket)
                    
        elif msg_type == "unsubscribe":
            # 取消订阅事件
            event_types = message.get("events", [])
            manager.unsubscribe(websocket, event_types)
            
            response = {
                "type": "unsubscribe_success",
                "events": event_types,
                "timestamp": datetime.now().isoformat()
            }
            await manager.send_personal_message(response, websocket)
            
        elif msg_type == "ping":
            # 心跳检测
            response = {
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            }
            await manager.send_personal_message(response, websocket)
            
        else:
            # 未知消息类型
            response = {
                "type": "error",
                "message": f"未知消息类型: {msg_type}",
                "timestamp": datetime.now().isoformat()
            }
            await manager.send_personal_message(response, websocket)
            
    except Exception as e:
        logger.error(f"处理WebSocket消息失败: {e}")
        response = {
            "type": "error",
            "message": "消息处理失败",
            "timestamp": datetime.now().isoformat()
        }
        await manager.send_personal_message(response, websocket)

# 工具状态变更通知
async def notify_tool_status_change(tool_id: int, old_status: str, new_status: str):
    """通知工具状态变更"""
    message = {
        "type": "tool_status_change",
        "data": {
            "tool_id": tool_id,
            "old_status": old_status,
            "new_status": new_status,
            "timestamp": datetime.now().isoformat()
        }
    }
    await manager.broadcast(message, "tool_status_change")



# 任务状态变更通知
async def notify_task_status_change(task_data: dict):
    """通知任务状态变更"""
    message = {
        "type": "task_status_change",
        "data": task_data,
        "timestamp": datetime.now().isoformat()
    }
    await manager.broadcast(message, "task_status_change")