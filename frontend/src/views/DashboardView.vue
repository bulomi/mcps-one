<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NCard, NGrid, NGridItem, NStatistic, NProgress, NButton, NTag, NDataTable, NIcon } from 'naive-ui'
import {
  ServerOutline,
  StatsChartOutline,
  TimeOutline,
  CheckmarkCircleOutline,
  ConstructOutline,
  WifiOutline,
  TvOutline,
  SettingsOutline
} from '@vicons/ionicons5'
import { systemApi, type SystemStats } from '../api/system'
import { toolsApi, type Tool } from '../api/tools'

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
const recentTasks = ref<any[]>([])
const loading = ref(true)

// 获取系统统计信息
const fetchSystemStats = async () => {
  try {
    // 获取系统统计信息
    const stats = await systemApi.getStats()
    systemStats.value = stats
    
    // 获取工具列表（前5个）
    const toolsResponse = await toolsApi.getTools()
    const tools = toolsResponse.data?.items || []
    toolsList.value = tools.slice(0, 5)
    
    // 模拟最近任务数据（后续可以从API获取）
    recentTasks.value = [
      {
        id: 'task-001',
        type: 'single_tool',
        status: 'running',
        tool: 'file-manager',
        created_at: new Date().toISOString()
      },
      {
        id: 'task-002',
        type: 'multi_tool',
        status: 'completed',
        tool: 'web-scraper',
        created_at: new Date(Date.now() - 3600000).toISOString()
      }
    ]
    
  } catch (error) {
    console.error('获取系统统计信息失败:', error)
  } finally {
    loading.value = false
  }
}

// 获取工具状态颜色
const getToolStatusColor = (status: string) => {
  switch (status) {
    case 'active': return 'success'
    case 'inactive': return 'default'
    case 'error': return 'error'
    default: return 'info'
  }
}

// 获取工具状态文本
const getToolStatusText = (status: string) => {
  switch (status) {
    case 'active': return '运行中'
    case 'inactive': return '已停止'
    case 'error': return '错误'
    default: return '未知'
  }
}

// 获取任务状态颜色
const getTaskStatusColor = (status: string) => {
  switch (status) {
    case 'running': return 'warning'
    case 'completed': return 'success'
    case 'failed': return 'danger'
    case 'pending': return 'info'
    default: return 'info'
  }
}

// 格式化时间
const formatTime = (timeStr: string) => {
  return new Date(timeStr).toLocaleString('zh-CN')
}

// 组件挂载时获取数据
onMounted(() => {
  fetchSystemStats()
})
</script>

<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h1>MCPS.ONE 控制台</h1>
      <p>MCP 工具管理和代理服务平台</p>
    </div>

    <!-- 统计卡片 -->
    <n-grid :cols="4" :x-gap="24" :y-gap="24" class="stats-row">
      <n-grid-item>
        <n-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon">
              <n-icon :size="32" color="#409EFF">
                <ConstructOutline />
              </n-icon>
            </div>
            <div class="stat-info">
              <n-statistic label="总工具数" :value="systemStats.totalTools" />
            </div>
          </div>
        </n-card>
      </n-grid-item>
      
      <n-grid-item>
        <n-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon">
              <n-icon :size="32" color="#67C23A">
                <WifiOutline />
              </n-icon>
            </div>
            <div class="stat-info">
              <n-statistic label="活跃工具" :value="systemStats.activeTools" />
            </div>
          </div>
        </n-card>
      </n-grid-item>
      
      <n-grid-item>
        <n-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon">
              <n-icon :size="32" color="#E6A23C">
                <TvOutline />
              </n-icon>
            </div>
            <div class="stat-info">
              <n-statistic label="活跃会话" :value="systemStats.activeSessions" />
            </div>
          </div>
        </n-card>
      </n-grid-item>
      
      <n-grid-item>
        <n-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon">
              <n-icon :size="32" color="#F56C6C">
                <SettingsOutline />
              </n-icon>
            </div>
            <div class="stat-info">
              <n-statistic label="总任务数" :value="systemStats.totalTasks" />
            </div>
          </div>
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 工具状态和最近任务 -->
    <n-grid :cols="2" :x-gap="24" :y-gap="24" class="content-row">
      <!-- 工具状态 -->
      <n-grid-item>
        <n-card>
          <template #header>
            <div class="card-header">
              <span>工具状态</span>
              <n-button type="primary" size="small" @click="$router.push('/tools')">
                查看全部
              </n-button>
            </div>
          </template>
          
          <div v-if="loading" class="loading-state">
            <p>加载中...</p>
          </div>
          <div v-else>
            <div v-if="toolsList.length === 0" class="empty-state">
              <p>暂无工具数据</p>
            </div>
            <div v-else>
              <div v-for="tool in toolsList" :key="tool.name" class="tool-item">
                <div class="tool-info">
                  <span class="tool-name">{{ tool.name }}</span>
                  <n-tag :type="getToolStatusColor(tool.status)" size="small">
                    {{ getToolStatusText(tool.status) }}
                  </n-tag>
                </div>
                <div class="tool-description">
                  {{ tool.description || '暂无描述' }}
                </div>
              </div>
            </div>
          </div>
        </n-card>
      </n-grid-item>
      
      <!-- 最近任务 -->
      <n-grid-item>
        <n-card>
          <template #header>
            <div class="card-header">
              <span>最近任务</span>
              <n-button type="primary" size="small" @click="$router.push('/monitor')">
                查看全部
              </n-button>
            </div>
          </template>
          
          <div v-if="loading" class="loading-state">
            <p>加载中...</p>
          </div>
          <div v-else>
            <div v-if="recentTasks.length === 0" class="empty-state">
              <p>暂无任务记录</p>
            </div>
            <div v-else>
              <div v-for="task in recentTasks" :key="task.id" class="task-item">
                <div class="task-header">
                  <span class="task-id">{{ task.id }}</span>
                  <n-tag :type="getTaskStatusColor(task.status)" size="small">
                    {{ task.status === 'running' ? '运行中' : 
                        task.status === 'completed' ? '已完成' : 
                        task.status === 'failed' ? '失败' : 
                        task.status === 'pending' ? '等待中' : '未知' }}
                  </n-tag>
                </div>
                <div class="task-details">
                  <span class="task-type">类型: {{ task.type }}</span>
                  <span class="task-tool">工具: {{ task.tool }}</span>
                </div>
                <div class="task-time">
                  {{ formatTime(task.created_at) }}
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
            
            <n-button type="warning" @click="$router.push('/monitor')">
              <template #icon>
                <n-icon><TvOutline /></n-icon>
              </template>
              系统监控
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
  margin-bottom: 32px;
  text-align: center;
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
}

.dashboard-header h1 {
  margin: 0 0 12px 0;
  font-size: 32px;
  color: white;
  font-weight: 600;
}

.dashboard-header p {
  margin: 0;
  color: rgba(255, 255, 255, 0.9);
  font-size: 16px;
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
  transform: translateY(-4px);
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

.tool-description {
  font-size: 12px;
  color: #909399;
}

.task-item {
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.task-item:last-child {
  border-bottom: none;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.task-id {
  font-weight: 500;
  color: #303133;
  font-size: 14px;
}

.task-details {
  display: flex;
  gap: 16px;
  margin-bottom: 4px;
}

.task-type,
.task-tool {
  font-size: 12px;
  color: #606266;
}

.task-time {
  font-size: 12px;
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
  transform: translateY(-2px);
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