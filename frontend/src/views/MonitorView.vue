<script setup lang="ts">
import { ref, onMounted, onUnmounted, h } from 'vue'
import { NCard, NGrid, NGridItem, NProgress, NDataTable, NTag, NButton, NSelect, NInput, NDatePicker, NAlert, NIcon } from 'naive-ui'
import {
  RefreshOutline,
  DownloadOutline,
  SearchOutline,
  FunnelOutline
} from '@vicons/ionicons5'

// 响应式数据
const systemMetrics = ref({
  cpu_usage: 0,
  memory_usage: 0,
  disk_usage: 0,
  network_in: 0,
  network_out: 0,
  active_connections: 0,
  uptime: 0
})

const logs = ref([])
const loading = ref(true)
const refreshing = ref(false)
const autoRefresh = ref(true)
const refreshInterval = ref(null)

// 日志过滤条件
const logFilters = ref({
  level: '',
  source: '',
  search: '',
  dateRange: null
})

const logLevels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
const logSources = ['system', 'mcp-client', 'mcp-agent', 'api', 'database']

// 获取系统指标
const fetchSystemMetrics = async () => {
  try {
    // 这里应该调用实际的API
    // const response = await fetch('/api/system/metrics')
    // const data = await response.json()
    
    // 暂时使用模拟数据
    systemMetrics.value = {
      cpu_usage: Math.floor(Math.random() * 100),
      memory_usage: Math.floor(Math.random() * 100),
      disk_usage: Math.floor(Math.random() * 100),
      network_in: Math.floor(Math.random() * 1000),
      network_out: Math.floor(Math.random() * 1000),
      active_connections: Math.floor(Math.random() * 50),
      uptime: Math.floor(Date.now() / 1000) - Math.floor(Math.random() * 86400)
    }
  } catch (error) {
    console.error('获取系统指标失败:', error)
  }
}

// 获取日志
const fetchLogs = async () => {
  try {
    // 这里应该调用实际的API
    // const response = await fetch('/api/system/logs', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify(logFilters.value)
    // })
    // const data = await response.json()
    
    // 暂时使用模拟数据
    const mockLogs = [
      {
        id: 1,
        timestamp: new Date().toISOString(),
        level: 'INFO',
        source: 'mcp-client',
        message: 'MCP客户端连接成功',
        details: { tool: 'file-manager', connection_id: 'conn-001' }
      },
      {
        id: 2,
        timestamp: new Date(Date.now() - 60000).toISOString(),
        level: 'WARNING',
        source: 'mcp-agent',
        message: '任务执行超时警告',
        details: { task_id: 'task-001', timeout: 30 }
      },
      {
        id: 3,
        timestamp: new Date(Date.now() - 120000).toISOString(),
        level: 'ERROR',
        source: 'api',
        message: 'API请求失败',
        details: { endpoint: '/api/tools', status_code: 500, error: 'Internal Server Error' }
      },
      {
        id: 4,
        timestamp: new Date(Date.now() - 180000).toISOString(),
        level: 'DEBUG',
        source: 'system',
        message: '系统性能检查完成',
        details: { cpu: 45, memory: 67, disk: 23 }
      },
      {
        id: 5,
        timestamp: new Date(Date.now() - 240000).toISOString(),
        level: 'INFO',
        source: 'database',
        message: '数据库连接池状态正常',
        details: { active: 5, idle: 10, max: 20 }
      },
      {
        id: 6,
        timestamp: new Date(Date.now() - 300000).toISOString(),
        level: 'CRITICAL',
        source: 'mcp-client',
        message: 'MCP工具连接丢失',
        details: { tool: 'web-scraper', last_seen: new Date(Date.now() - 600000).toISOString() }
      }
    ]
    
    // 应用过滤条件
    let filteredLogs = mockLogs
    
    if (logFilters.value.level) {
      filteredLogs = filteredLogs.filter(log => log.level === logFilters.value.level)
    }
    
    if (logFilters.value.source) {
      filteredLogs = filteredLogs.filter(log => log.source === logFilters.value.source)
    }
    
    if (logFilters.value.search) {
      const searchTerm = logFilters.value.search.toLowerCase()
      filteredLogs = filteredLogs.filter(log => 
        log.message.toLowerCase().includes(searchTerm) ||
        log.source.toLowerCase().includes(searchTerm)
      )
    }
    
    logs.value = filteredLogs
  } catch (error) {
    console.error('获取日志失败:', error)
  }
}

// 刷新数据
const refreshData = async () => {
  refreshing.value = true
  try {
    await Promise.all([fetchSystemMetrics(), fetchLogs()])
  } finally {
    refreshing.value = false
    loading.value = false
  }
}

// 获取CPU使用率颜色
const getCpuColor = (usage: number) => {
  if (usage < 50) return '#67C23A'
  if (usage < 80) return '#E6A23C'
  return '#F56C6C'
}

// 获取内存使用率颜色
const getMemoryColor = (usage: number) => {
  if (usage < 60) return '#67C23A'
  if (usage < 85) return '#E6A23C'
  return '#F56C6C'
}

// 获取磁盘使用率颜色
const getDiskColor = (usage: number) => {
  if (usage < 70) return '#67C23A'
  if (usage < 90) return '#E6A23C'
  return '#F56C6C'
}

// 获取日志级别颜色
const getLogLevelColor = (level: string) => {
  switch (level) {
    case 'DEBUG': return 'info'
    case 'INFO': return 'success'
    case 'WARNING': return 'warning'
    case 'ERROR': return 'danger'
    case 'CRITICAL': return 'danger'
    default: return 'info'
  }
}

// 格式化时间
const formatTime = (timeStr: string) => {
  return new Date(timeStr).toLocaleString('zh-CN')
}

// 格式化运行时间
const formatUptime = (seconds: number) => {
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  
  if (days > 0) {
    return `${days}天 ${hours}小时 ${minutes}分钟`
  } else if (hours > 0) {
    return `${hours}小时 ${minutes}分钟`
  } else {
    return `${minutes}分钟`
  }
}

// 格式化网络流量
const formatBytes = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B/s`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB/s`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB/s`
}

// 导出日志
const exportLogs = () => {
  const csvContent = [
    ['时间', '级别', '来源', '消息', '详情'].join(','),
    ...logs.value.map(log => [
      formatTime(log.timestamp),
      log.level,
      log.source,
      `"${log.message}"`,
      `"${JSON.stringify(log.details)}"`
    ].join(','))
  ].join('\n')
  
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `logs_${new Date().toISOString().split('T')[0]}.csv`
  link.click()
}

// 清空过滤条件
const clearFilters = () => {
  logFilters.value = {
    level: '',
    source: '',
    search: '',
    dateRange: []
  }
  fetchLogs()
}

// 设置自动刷新
const setupAutoRefresh = () => {
  if (autoRefresh.value) {
    refreshInterval.value = setInterval(refreshData, 10000) // 每10秒刷新一次
  } else {
    if (refreshInterval.value) {
      clearInterval(refreshInterval.value)
      refreshInterval.value = null
    }
  }
}

// 组件挂载时获取数据
onMounted(() => {
  refreshData()
  setupAutoRefresh()
})

// 组件卸载时清理定时器
onUnmounted(() => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
  }
})

// 监听自动刷新设置变化
const toggleAutoRefresh = () => {
  setupAutoRefresh()
}

// 日志表格列配置
const logColumns = [
  {
    title: '时间',
    key: 'timestamp',
    width: 180,
    render: (row: any) => formatTime(row.timestamp)
  },
  {
    title: '级别',
    key: 'level',
    width: 100,
    render: (row: any) => {
      return h(NTag, {
        type: getLogLevelColor(row.level),
        size: 'small'
      }, { default: () => row.level })
    }
  },
  {
    title: '来源',
    key: 'source',
    width: 120
  },
  {
    title: '消息',
    key: 'message',
    minWidth: 300
  },
  {
    title: '详情',
    key: 'details',
    width: 200,
    render: (row: any) => {
      return h(NButton, {
        text: true,
        size: 'small',
        onClick: () => console.log('查看详情:', row.details)
      }, { default: () => '查看详情' })
    }
  }
]
</script>

<template>
  <div class="monitor">
    <div class="page-header">
      <h1>系统监控</h1>
      <div class="header-actions">
        <n-button 
          :loading="refreshing" 
          @click="refreshData"
        >
          <template #icon>
            <n-icon><RefreshOutline /></n-icon>
          </template>
          刷新
        </n-button>
        <n-button 
          :type="autoRefresh ? 'primary' : 'default'"
          @click="autoRefresh = !autoRefresh; toggleAutoRefresh()"
        >
          {{ autoRefresh ? '停止自动刷新' : '开启自动刷新' }}
        </n-button>
      </div>
    </div>

    <!-- 系统指标 -->
    <n-grid :cols="3" :x-gap="20" class="metrics-row">
      <n-grid-item>
        <n-card>
          <template #header>
            <span>CPU 使用率</span>
          </template>
          <div class="metric-content">
            <n-progress 
              type="circle" 
              :percentage="systemMetrics.cpu_usage"
              :color="getCpuColor(systemMetrics.cpu_usage)"
              :stroke-width="8"
              :size="120"
            />
            <div class="metric-info">
              <p>当前: {{ systemMetrics.cpu_usage }}%</p>
            </div>
          </div>
        </n-card>
      </n-grid-item>
      
      <n-grid-item>
        <n-card>
          <template #header>
            <span>内存使用率</span>
          </template>
          <div class="metric-content">
            <n-progress 
              type="circle" 
              :percentage="systemMetrics.memory_usage"
              :color="getMemoryColor(systemMetrics.memory_usage)"
              :stroke-width="8"
              :size="120"
            />
            <div class="metric-info">
              <p>当前: {{ systemMetrics.memory_usage }}%</p>
            </div>
          </div>
        </n-card>
      </n-grid-item>
      
      <n-grid-item>
        <n-card>
          <template #header>
            <span>磁盘使用率</span>
          </template>
          <div class="metric-content">
            <n-progress 
              type="circle" 
              :percentage="systemMetrics.disk_usage"
              :color="getDiskColor(systemMetrics.disk_usage)"
              :stroke-width="8"
              :size="120"
            />
            <div class="metric-info">
              <p>当前: {{ systemMetrics.disk_usage }}%</p>
            </div>
          </div>
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 网络和连接信息 -->
    <n-grid :cols="4" :x-gap="20" class="network-row">
      <n-grid-item>
        <n-card class="stat-card">
          <div class="stat-content">
            <div class="stat-value">{{ formatBytes(systemMetrics.network_in) }}</div>
            <div class="stat-label">网络入流量</div>
          </div>
        </n-card>
      </n-grid-item>
      
      <n-grid-item>
        <n-card class="stat-card">
          <div class="stat-content">
            <div class="stat-value">{{ formatBytes(systemMetrics.network_out) }}</div>
            <div class="stat-label">网络出流量</div>
          </div>
        </n-card>
      </n-grid-item>
      
      <n-grid-item>
        <n-card class="stat-card">
          <div class="stat-content">
            <div class="stat-value">{{ systemMetrics.active_connections }}</div>
            <div class="stat-label">活跃连接</div>
          </div>
        </n-card>
      </n-grid-item>
      
      <n-grid-item>
        <n-card class="stat-card">
          <div class="stat-content">
            <div class="stat-value">{{ formatUptime(systemMetrics.uptime) }}</div>
            <div class="stat-label">系统运行时间</div>
          </div>
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 系统日志 -->
    <n-card class="logs-card">
      <template #header>
        <div class="card-header">
          <span>系统日志</span>
          <div class="header-actions">
            <n-button size="small" @click="exportLogs">
              <template #icon>
                <n-icon><DownloadOutline /></n-icon>
              </template>
              导出日志
            </n-button>
          </div>
        </div>
      </template>
      
      <!-- 日志过滤器 -->
      <div class="log-filters">
        <n-grid :cols="6" :x-gap="16">
          <n-grid-item>
            <n-select v-model:value="logFilters.level" placeholder="选择级别" clearable>
              <n-option 
                v-for="level in logLevels" 
                :key="level" 
                :label="level" 
                :value="level"
              />
            </n-select>
          </n-grid-item>
          <n-grid-item>
            <n-select v-model:value="logFilters.source" placeholder="选择来源" clearable>
              <n-option 
                v-for="source in logSources" 
                :key="source" 
                :label="source" 
                :value="source"
              />
            </n-select>
          </n-grid-item>
          <n-grid-item :span="2">
            <n-input 
              v-model:value="logFilters.search" 
              placeholder="搜索日志内容"
              clearable
            >
              <template #prefix>
                <n-icon><SearchOutline /></n-icon>
              </template>
            </n-input>
          </n-grid-item>
          <n-grid-item :span="2">
            <n-date-picker
              v-model:value="logFilters.dateRange"
              type="datetimerange"
              separator="至"
              start-placeholder="开始时间"
              end-placeholder="结束时间"
              format="yyyy-MM-dd HH:mm:ss"
              value-format="yyyy-MM-dd HH:mm:ss"
            />
          </n-grid-item>
          <n-grid-item>
            <n-button @click="fetchLogs">
              <template #icon>
                <n-icon><FunnelOutline /></n-icon>
              </template>
              筛选
            </n-button>
            <n-button @click="clearFilters" style="margin-left: 8px;">清空</n-button>
          </n-grid-item>
        </n-grid>
      </div>
      
      <!-- 日志表格 -->
      <n-data-table 
        :data="logs" 
        :columns="logColumns"
        :loading="loading"
        striped
        max-height="500"
      />
    </n-card>
  </div>
</template>

<style scoped>
.monitor {
  padding: 0;
  background: transparent;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
}

.page-header h1 {
  margin: 0;
  font-size: 28px;
  color: white;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 16px;
}

.metrics-row {
  margin-bottom: 32px;
}

.metric-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px 0;
}

.metric-info {
  margin-top: 20px;
  text-align: center;
}

.metric-info p {
  margin: 6px 0;
  color: #606266;
  font-size: 15px;
}

.network-row {
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
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 12px;
}

.stat-label {
  font-size: 15px;
  color: #909399;
  font-weight: 500;
}

.logs-card {
  margin-bottom: 32px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: none;
  transition: all 0.3s ease;
}

.logs-card:hover {
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 16px;
}

.log-filters {
  margin-bottom: 20px;
  padding: 20px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 12px;
  border: 1px solid #e9ecef;
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

.n-data-table {
  border-radius: 12px;
  overflow: hidden;
}

.n-button {
  border-radius: 8px;
  transition: all 0.3s ease;
}

.n-button:hover {
  transform: translateY(-1px);
}

:deep(.el-table) {
  font-size: 14px;
}

:deep(.el-table .el-table__cell) {
  padding: 8px 0;
}

:deep(.el-progress-circle) {
  margin-bottom: 8px;
}
</style>