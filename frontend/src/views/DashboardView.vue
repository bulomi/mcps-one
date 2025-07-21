<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { NCard, NGrid, NGridItem, NStatistic, NProgress, NButton, NTag, NDataTable, NIcon, NSpin } from 'naive-ui'
import {
  ServerOutline,
  StatsChartOutline,
  TimeOutline,
  CheckmarkCircleOutline,
  ConstructOutline,
  WifiOutline,
  TvOutline,
  SettingsOutline,
  RefreshOutline
} from '@vicons/ionicons5'
import { systemApi, type SystemStats } from '../api/system'
import { toolsApi, type Tool } from '../api/tools'
import { sessionsApi } from '../api/sessions'
import { tasksApi, type Task } from '../api/tasks'
import { useWebSocketData, useWebSocketEvents, connectWebSocket, disconnectWebSocket, EventType } from '../services/websocket'
import { ux } from '../utils/userExperience'
import { handleApiError } from '../utils/errorHandler'
import { StatusMapper, TimeUtils, DataUtils } from '../utils/common'

// 响应式数据
const systemStats = ref<SystemStats>({
  totalTools: 0,
  activeTools: 0,
  totalSessions: 0,
  activeSessions: 0,
  totalTasks: 0,
  completedTasks: 0,
  failedTasks: 0,
  systemUptime: '',
  memoryUsage: {
    used: 0,
    total: 0,
    percentage: 0
  },
  cpuUsage: 0
})

const toolsList = ref<Tool[]>([])
const recentTasks = ref<Task[]>([])
const loading = ref(true)
const refreshing = ref(false)
const autoRefresh = ref(true)
const refreshInterval = ref<NodeJS.Timeout | null>(null)
const lastUpdateTime = ref<Date>(new Date())

// WebSocket 数据和事件
const { status: wsStatus, systemStats: wsSystemStats, toolStatus: wsToolStatus } = useWebSocketData()
const { addEventListener, removeEventListener } = useWebSocketEvents()

// 获取系统统计信息
const fetchSystemStats = async (showLoading = true) => {
  if (showLoading) {
    loading.value = true
  } else {
    refreshing.value = true
  }
  
  try {
    // 获取系统统计信息
    const stats = await systemApi.getStats()
    if (stats) {
      systemStats.value = stats
    }
    
    // 获取工具列表（前5个）
    const toolsResponse = await toolsApi.getTools()
    const normalizedTools = DataUtils.normalizeApiResponse<Tool>(toolsResponse)
    toolsList.value = normalizedTools.slice(0, 5)
    
    // 获取最近任务数据
    const tasks = await tasksApi.getRecentTasks(5)
    recentTasks.value = DataUtils.normalizeApiResponse<Task>(tasks)
    
    // 更新最后更新时间
    lastUpdateTime.value = new Date()
    
  } catch (error) {
    // 获取系统统计信息失败
    // 使用增强的错误处理，支持自动重试
    handleApiError(error, '获取系统数据失败', undefined, true)
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

// WebSocket 数据更新处理
watch(wsSystemStats, (newStats) => {
  if (newStats) {
    systemStats.value = newStats
    lastUpdateTime.value = new Date()
  }
})

watch(wsToolStatus, (newToolStatus) => {
  if (newToolStatus && Array.isArray(newToolStatus)) {
    // 更新工具列表（前5个）
    toolsList.value = newToolStatus.slice(0, 5).map(tool => ({
      id: tool.id,
      name: tool.name,
      status: tool.status,
      description: '',
      category: '',
      tags: [],
      created_at: '',
      updated_at: '',
      last_started: tool.last_started,
      process_id: tool.process_id,
      mcp_port: tool.mcp_port
    }))
    lastUpdateTime.value = new Date()
  }
})

// 处理工具状态变更事件
const handleToolStatusChange = (data: any) => {
  // 工具状态变更处理
  // 可以在这里添加通知或其他处理逻辑
}



// 手动刷新
const handleRefresh = async () => {
  await ux.executeWithFeedback(
    async () => {
      await fetchSystemStats(false)
      return { 
        toolsCount: toolsList.value.length,
        tasksCount: recentTasks.value.length
      }
    },
    {
      loadingMessage: '正在刷新数据...',
      successMessage: (result) => `刷新完成，获取到 ${result.toolsCount} 个工具和 ${result.tasksCount} 个任务`,
      errorMessage: '刷新失败，请稍后重试'
    }
  )
}

// 切换自动刷新
const toggleAutoRefresh = () => {
  autoRefresh.value = !autoRefresh.value
  if (autoRefresh.value) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
}

// 开始自动刷新
const startAutoRefresh = () => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
  }
  refreshInterval.value = setInterval(() => {
    if (autoRefresh.value) {
      fetchSystemStats(false)
    }
  }, 30000) // 30秒刷新一次
}

// 停止自动刷新
const stopAutoRefresh = () => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
    refreshInterval.value = null
  }
}

// 格式化最后更新时间（使用通用工具）
const formatLastUpdateTime = () => {
  return TimeUtils.getRelativeTime(lastUpdateTime.value)
}

// 获取工具状态颜色（使用通用工具）
const getToolStatusColor = (status: string) => {
  return StatusMapper.mapToolStatus(status).type
}

// 获取工具状态文本（使用通用工具）
const getToolStatusText = (status: string) => {
  return StatusMapper.mapToolStatus(status).text
}

// 获取任务状态颜色（使用通用工具）
const getTaskStatusColor = (status: string) => {
  return StatusMapper.mapTaskStatus(status).type
}

// 格式化时间（使用通用工具）
const formatTime = (timeStr: string) => {
  return TimeUtils.formatTime(timeStr)
}

// 组件挂载时获取数据
onMounted(async () => {
  // 初始化数据获取
  await fetchSystemStats()
  
  // 连接 WebSocket
  try {
    await connectWebSocket()
    console.log('WebSocket 连接成功')
  } catch (error) {
    console.error('WebSocket 连接失败，使用定时刷新模式:', error)
    startAutoRefresh()
  }
  
  // 添加事件监听器
  addEventListener(EventType.TOOL_STATUS_CHANGE, handleToolStatusChange)
})

// 组件卸载时清理资源
onUnmounted(() => {
  stopAutoRefresh()
  
  // 移除事件监听器
  removeEventListener(EventType.TOOL_STATUS_CHANGE, handleToolStatusChange)
  
  // 断开 WebSocket 连接
  disconnectWebSocket()
})
</script>

<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <div class="header-content">
        <div class="header-text">
          <h1>🏠 MCPS.ONE 首页</h1>
          <p>简洁、面向个人使用的 MCP 工具后台管理面板</p>
        </div>
        <div class="header-controls">
          <div class="update-info">
            <span class="update-time">最后更新: {{ formatLastUpdateTime() }}</span>
            <n-tag :type="autoRefresh ? 'success' : 'default'" size="small">
              {{ autoRefresh ? '自动刷新' : '手动刷新' }}
            </n-tag>
          </div>
          <div class="control-buttons">
            <n-button 
              :loading="refreshing" 
              @click="handleRefresh" 
              size="small" 
              type="primary" 
              ghost
              data-testid="refresh-button"
            >
              <template #icon>
                <n-icon><RefreshOutline /></n-icon>
              </template>
              刷新
            </n-button>
            <n-button 
              @click="toggleAutoRefresh" 
              size="small" 
              :type="autoRefresh ? 'success' : 'default'"
              ghost
            >
              {{ autoRefresh ? '关闭自动' : '开启自动' }}
            </n-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 核心统计卡片 -->
    <n-grid :cols="4" :x-gap="24" :y-gap="24" class="stats-row">
      <n-grid-item>
        <n-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon">
              <n-icon :size="32" color="#67C23A">
                <ConstructOutline />
              </n-icon>
            </div>
            <div class="stat-info">
              <n-statistic label="运行中的 MCP 工具" :value="systemStats.activeTools" />
              <div class="stat-subtitle">共 {{ systemStats.totalTools }} 个工具</div>
            </div>
          </div>
        </n-card>
      </n-grid-item>
      
      <n-grid-item>
        <n-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon">
              <n-icon :size="32" color="#409EFF">
                <TvOutline />
              </n-icon>
            </div>
            <div class="stat-info">
              <n-statistic label="代理请求总数" :value="systemStats.totalTasks" />
              <div class="stat-subtitle">成功 {{ systemStats.completedTasks }} | 失败 {{ systemStats.failedTasks }}</div>
            </div>
          </div>
        </n-card>
      </n-grid-item>
      
      <n-grid-item>
        <n-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon">
              <n-icon :size="32" color="#E6A23C">
                <TimeOutline />
              </n-icon>
            </div>
            <div class="stat-info">
              <n-statistic label="当前活跃会话" :value="systemStats.activeSessions" />
              <div class="stat-subtitle">总会话 {{ systemStats.totalSessions }}</div>
            </div>
          </div>
        </n-card>
      </n-grid-item>
      
      <n-grid-item>
        <n-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon">
              <n-icon :size="32" color="#67C23A">
                <CheckmarkCircleOutline />
              </n-icon>
            </div>
            <div class="stat-info">
              <n-statistic label="系统状态" value="在线" />
              <div class="stat-subtitle">运行时间 {{ systemStats.systemUptime || '未知' }}</div>
            </div>
          </div>
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 工具状态和最近调用记录 -->
    <n-grid :cols="2" :x-gap="24" :y-gap="24" class="content-row">
      <!-- 工具状态 -->
      <n-grid-item>
        <n-card>
          <template #header>
            <div class="card-header">
              <span>🔧 MCP 工具状态</span>
              <n-button type="primary" size="small" @click="$router.push('/tools')">
                管理工具
              </n-button>
            </div>
          </template>
          
          <div v-if="loading" class="loading-state">
            <n-spin size="small" />
            <p>加载中...</p>
          </div>
          <div v-else>
            <div v-if="toolsList.length === 0" class="empty-state">
              <p>暂无工具，<router-link to="/tools">点击添加</router-link></p>
            </div>
            <div v-else>
              <div v-for="tool in toolsList" :key="tool.name" class="tool-item">
                <div class="tool-info">
                  <span class="tool-name">{{ tool.name }}</span>
                  <n-tag :type="getToolStatusColor(tool.status)" size="small">
                    {{ getToolStatusText(tool.status) }}
                  </n-tag>
                </div>
                <div class="tool-meta">
                  <span class="tool-time">{{ tool.last_started ? '最后启动: ' + formatTime(tool.last_started) : '未启动' }}</span>
                </div>
              </div>
            </div>
          </div>
        </n-card>
      </n-grid-item>
      
      <!-- 最近调用记录 -->
      <n-grid-item>
        <n-card>
          <template #header>
            <div class="card-header">
              <span>📋 最近调用记录</span>
              <n-button type="primary" size="small" @click="$router.push('/proxy/sessions')">
                查看全部
              </n-button>
            </div>
          </template>
          
          <div v-if="loading" class="loading-state">
            <n-spin size="small" />
            <p>加载中...</p>
          </div>
          <div v-else>
            <div v-if="recentTasks.length === 0" class="empty-state">
              <p>暂无调用记录</p>
            </div>
            <div v-else>
              <div v-for="task in recentTasks" :key="task.id" class="call-item">
                <div class="call-info">
                  <span class="call-tool">{{ task.tool_name || task.name }}</span>
                  <n-tag :type="getTaskStatusColor(task.status)" size="small">
                    {{ task.status === 'success' ? '成功' : task.status === 'failed' ? '失败' : '进行中' }}
                  </n-tag>
                </div>
                <div class="call-meta">
                  <span class="call-type">{{ task.request_type || '工具调用' }}</span>
                  <span class="call-time">{{ formatTime(task.created_at || task.timestamp) }}</span>
                </div>
              </div>
            </div>
          </div>
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 快速操作 -->
    <n-grid :cols="1" class="actions-row">
      <n-grid-item>
        <n-card>
          <template #header>
            <span>快速操作</span>
          </template>
          
          <div class="quick-actions">
            <n-button type="primary" @click="$router.push('/tools')">
              <template #icon>
                <n-icon><ConstructOutline /></n-icon>
              </template>
              管理工具
            </n-button>
            
            <n-button type="success" @click="$router.push('/proxy')">
              <template #icon>
                <n-icon><WifiOutline /></n-icon>
              </template>
              代理服务
            </n-button>
            

            
            <n-button type="info" @click="$router.push('/settings')">
              <template #icon>
                <n-icon><SettingsOutline /></n-icon>
              </template>
              系统设置
            </n-button>
          </div>
        </n-card>
      </n-grid-item>
    </n-grid>
  </div>
</template>

<style scoped>
.dashboard {
  padding: 0;
  background: transparent;
}

.dashboard-header {
  margin-bottom: 16px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.header-text {
  text-align: left;
}

.header-text h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
}

.header-text p {
  margin: 0;
  color: var(--n-text-color-2);
  font-size: 14px;
}

.header-controls {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 12px;
}

.update-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.update-time {
  color: rgba(255, 255, 255, 0.8);
}

.control-buttons {
  display: flex;
  gap: 8px;
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    text-align: center;
  }
  
  .header-text {
    text-align: center;
  }
  
  .header-controls {
    align-items: center;
  }
}

.stats-row {
  margin-bottom: 32px;
}

.stat-card {
  height: 140px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  border: none;
}

.stat-card:hover {
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.stat-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.stat-icon {
  margin-right: 16px;
}

.stat-info {
  flex: 1;
}

.content-row {
  margin-bottom: 32px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 16px;
}

.n-card {
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: none;
  transition: all 0.3s ease;
}

.n-card:hover {
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.tool-item {
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.tool-item:last-child {
  border-bottom: none;
}

.tool-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.tool-name {
  font-weight: 500;
  color: #303133;
}

.tool-meta {
  font-size: 12px;
  color: #606266;
  margin-top: 4px;
}

.tool-time {
  color: #909399;
}

.call-item {
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.call-item:last-child {
  border-bottom: none;
}

.call-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.call-tool {
  font-weight: 500;
  color: #303133;
}

.call-meta {
  font-size: 12px;
  color: #606266;
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
}

.call-type {
  color: #909399;
}

.call-time {
  color: #909399;
}

.actions-row {
  margin-bottom: 32px;
}

.quick-actions {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  justify-content: center;
}

.quick-actions .n-button {
  height: 48px;
  padding: 0 24px;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.quick-actions .n-button:hover {
  /* 移除悬浮动画效果 */
}

.quick-actions .el-button {
  display: flex;
  align-items: center;
  gap: 8px;
}

.empty-state {
  text-align: center;
  padding: 40px 0;
  color: #909399;
}
</style>