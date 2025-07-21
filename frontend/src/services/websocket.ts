/**
 * WebSocket 实时数据服务
 */

import { ref, reactive } from 'vue'
import { handleApiError } from '@/utils/errorHandler'

// WebSocket 连接状态
export enum WebSocketStatus {
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  ERROR = 'error'
}

// 事件类型
export enum EventType {
  SYSTEM_STATS = 'system_stats',
  TOOL_STATUS = 'tool_status',
  TOOL_STATUS_CHANGE = 'tool_status_change',

  TASK_STATUS_CHANGE = 'task_status_change'
}

// WebSocket 消息接口
interface WebSocketMessage {
  type: string
  data?: any
  events?: string[]
  timestamp?: string
  message?: string
}

// 事件回调函数类型
type EventCallback = (data: any) => void

class WebSocketService {
  private ws: WebSocket | null = null
  private url: string
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectInterval = 3000
  private heartbeatInterval: number | null = null
  private eventListeners: Map<string, Set<EventCallback>> = new Map()
  
  // 响应式状态
  public status = ref<WebSocketStatus>(WebSocketStatus.DISCONNECTED)
  public lastError = ref<string | null>(null)
  public isReconnecting = ref(false)
  
  // 数据缓存
  public systemStats = ref<any>(null)
  public toolStatus = ref<any[]>([])
  
  constructor(baseUrl: string = 'ws://localhost:8000') {
    this.url = `${baseUrl}/ws`
  }
  
  /**
   * 连接 WebSocket
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        resolve()
        return
      }
      
      this.status.value = WebSocketStatus.CONNECTING
      this.lastError.value = null
      
      try {
        this.ws = new WebSocket(this.url)
        
        this.ws.onopen = () => {
          console.log('WebSocket 连接已建立')
          this.status.value = WebSocketStatus.CONNECTED
          this.reconnectAttempts = 0
          this.isReconnecting.value = false
          this.startHeartbeat()
          resolve()
        }
        
        this.ws.onmessage = (event) => {
          this.handleMessage(event.data)
        }
        
        this.ws.onclose = (event) => {
          console.log('WebSocket 连接已关闭', event.code, event.reason)
          this.status.value = WebSocketStatus.DISCONNECTED
          this.stopHeartbeat()
          
          if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.attemptReconnect()
          }
        }
        
        this.ws.onerror = (error) => {
          handleApiError(error, 'WebSocket 连接错误')
          this.status.value = WebSocketStatus.ERROR
          this.lastError.value = 'WebSocket 连接错误'
          reject(error)
        }
        
      } catch (error) {
        this.status.value = WebSocketStatus.ERROR
        this.lastError.value = '无法创建 WebSocket 连接'
        reject(error)
      }
    })
  }
  
  /**
   * 断开连接
   */
  disconnect() {
    if (this.ws) {
      this.ws.close(1000, '主动断开连接')
      this.ws = null
    }
    this.stopHeartbeat()
    this.status.value = WebSocketStatus.DISCONNECTED
  }
  
  /**
   * 重连
   */
  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('WebSocket 重连次数已达上限')
      return
    }
    
    this.reconnectAttempts++
    this.isReconnecting.value = true
    
    console.log(`WebSocket 重连尝试 ${this.reconnectAttempts}/${this.maxReconnectAttempts}`)
    
    setTimeout(() => {
      this.connect().catch(error => {
        console.error('WebSocket 重连失败:', error)
      })
    }, this.reconnectInterval)
  }
  
  /**
   * 发送消息
   */
  private send(message: WebSocketMessage) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket 未连接，无法发送消息')
    }
  }
  
  /**
   * 订阅事件
   */
  subscribe(events: EventType[]) {
    const message: WebSocketMessage = {
      type: 'subscribe',
      events: events.map(e => e.toString())
    }
    this.send(message)
  }
  
  /**
   * 取消订阅事件
   */
  unsubscribe(events: EventType[]) {
    const message: WebSocketMessage = {
      type: 'unsubscribe',
      events: events.map(e => e.toString())
    }
    this.send(message)
  }
  
  /**
   * 添加事件监听器
   */
  addEventListener(eventType: EventType, callback: EventCallback) {
    const eventKey = eventType.toString()
    if (!this.eventListeners.has(eventKey)) {
      this.eventListeners.set(eventKey, new Set())
    }
    this.eventListeners.get(eventKey)!.add(callback)
  }
  
  /**
   * 移除事件监听器
   */
  removeEventListener(eventType: EventType, callback: EventCallback) {
    const eventKey = eventType.toString()
    const listeners = this.eventListeners.get(eventKey)
    if (listeners) {
      listeners.delete(callback)
    }
  }
  
  /**
   * 处理接收到的消息
   */
  private handleMessage(data: string) {
    try {
      const message: WebSocketMessage = JSON.parse(data)
      
      switch (message.type) {
        case 'system_stats':
          this.systemStats.value = message.data
          break
          
        case 'tool_status':
          this.toolStatus.value = message.data
          break
          

          
        case 'tool_status_change':
        case 'task_status_change':
          // 触发事件监听器
          this.triggerEventListeners(message.type, message.data)
          break
          
        case 'subscribe_success':
          console.log('订阅成功:', message.events)
          break
          
        case 'unsubscribe_success':
          console.log('取消订阅成功:', message.events)
          break
          
        case 'pong':
          // 心跳响应
          break
          
        case 'error':
          console.error('WebSocket 服务器错误:', message.message)
          this.lastError.value = message.message || 'WebSocket 服务器错误'
          break
          
        default:
          console.warn('未知的 WebSocket 消息类型:', message.type)
      }
    } catch (error) {
      console.error('解析 WebSocket 消息失败:', error)
    }
  }
  
  /**
   * 触发事件监听器
   */
  private triggerEventListeners(eventType: string, data: any) {
    const listeners = this.eventListeners.get(eventType)
    if (listeners) {
      listeners.forEach(callback => {
        try {
          callback(data)
        } catch (error) {
          console.error('事件监听器执行失败:', error)
        }
      })
    }
  }
  
  /**
   * 开始心跳检测
   */
  private startHeartbeat() {
    this.heartbeatInterval = window.setInterval(() => {
      this.send({ type: 'ping' })
    }, 30000) // 30秒心跳
  }
  
  /**
   * 停止心跳检测
   */
  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
  }
}

// 创建全局 WebSocket 服务实例
export const websocketService = new WebSocketService()

// 自动连接（可选）
export const connectWebSocket = async () => {
  try {
    await websocketService.connect()
    
    // 订阅所有事件类型
    websocketService.subscribe([
      EventType.SYSTEM_STATS,
      EventType.TOOL_STATUS,
      EventType.TOOL_STATUS_CHANGE,

      EventType.TASK_STATUS_CHANGE
    ])
    
    console.log('WebSocket 服务已启动')
  } catch (error) {
    console.error('WebSocket 连接失败:', error)
  }
}

// 断开连接
export const disconnectWebSocket = () => {
  websocketService.disconnect()
  console.log('WebSocket 服务已停止')
}

// 导出响应式数据
export const useWebSocketData = () => {
  return {
    status: websocketService.status,
    lastError: websocketService.lastError,
    isReconnecting: websocketService.isReconnecting,
    systemStats: websocketService.systemStats,
    toolStatus: websocketService.toolStatus
  }
}

// 导出事件监听功能
export const useWebSocketEvents = () => {
  return {
    addEventListener: websocketService.addEventListener.bind(websocketService),
    removeEventListener: websocketService.removeEventListener.bind(websocketService)
  }
}