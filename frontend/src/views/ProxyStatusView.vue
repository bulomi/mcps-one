<script setup lang="ts">
import { ref, onMounted, onUnmounted, h } from 'vue'
import { NCard, NDataTable, NTag, NButton, NProgress, NAlert, NEmpty, NDescriptions, NDescriptionsItem, NIcon } from 'naive-ui'
import { RefreshOutline, EyeOutline, TrashOutline, WifiOutline } from '@vicons/ionicons5'

// 响应式数据
const sessions = ref([])
const tasks = ref([])
const loading = ref(true)
const refreshing = ref(false)
const autoRefresh = ref(true)
const refreshInterval = ref(null)

// 获取会话列表
const fetchSessions = async () => {
  try {
    // 这里应该调用实际的API
    // const response = await fetch('/api/mcp-agent/sessions')
    // const data = await response.json()
    
    // 暂时使用模拟数据
    sessions.value = [
      {
        id: 'session-001',
        status: 'active',
        created_at: new Date().toISOString(),
        last_activity: new Date().toISOString(),
        task_count: 3,
        tools_used: ['file-manager', 'web-scraper']
      },
      {
        id: 'session-002',
        status: 'idle',
        created_at: new Date(Date.now() - 3600000).toISOString(),
        last_activity: new Date(Date.now() - 1800000).toISOString(),
        task_count: 1,
        tools_used: ['database-tool']
      },
      {
        id: 'session-003',
        status: 'closed',
        created_at: new Date(Date.now() - 7200000).toISOString(),
        last_activity: new Date(Date.now() - 3600000).toISOString(),
        task_count: 5,
        tools_used: ['file-manager', 'web-scraper', 'api-client']
      }
    ]
  } catch (error) {
    console.error('获取会话列表失败:', error)
  }
}

// 获取任务列表
const fetchTasks = async () => {
  try {
    // 这里应该调用实际的API
    // const response = await fetch('/api/mcp-agent/tasks')
    // const data = await response.json()
    
    // 暂时使用模拟数据
    tasks.value = [
      {
        id: 'task-001',
        session_id: 'session-001',
        type: 'single_tool',
        status: 'running',
        tool_name: 'file-manager',
        progress: 65,
        created_at: new Date().toISOString(),
        started_at: new Date(Date.now() - 300000).toISOString(),
        estimated_completion: new Date(Date.now() + 180000).toISOString()
      },
      {
        id: 'task-002',
        session_id: 'session-001',
        type: 'multi_tool',
        status: 'completed',
        tool_name: 'web-scraper',
        progress: 100,
        created_at: new Date(Date.now() - 1800000).toISOString(),
        started_at: new Date(Date.now() - 1500000).toISOString(),
        completed_at: new Date(Date.now() - 900000).toISOString()
      },
      {
        id: 'task-003',
        session_id: 'session-002',
        type: 'pipeline',
        status: 'failed',
        tool_name: 'database-tool',
        progress: 30,
        created_at: new Date(Date.now() - 3600000).toISOString(),
        started_at: new Date(Date.now() - 3300000).toISOString(),
        failed_at: new Date(Date.now() - 2700000).toISOString(),
        error_message: '数据库连接超时'
      },
      {
        id: 'task-004',
        session_id: 'session-001',
        type: 'autonomous',
        status: 'pending',
        tool_name: 'api-client',
        progress: 0,
        created_at: new Date(Date.now() - 60000).toISOString()
      }
    ]
  } catch (error) {
    console.error('获取任务列表失败:', error)
  }
}

// 刷新数据
const refreshData = async () => {
  refreshing.value = true
  try {
    await Promise.all([fetchSessions(), fetchTasks()])
  } finally {
    refreshing.value = false
    loading.value = false
  }
}

// 获取会话状态颜色
const getSessionStatusColor = (status: string) => {
  switch (status) {
    case 'active': return 'success'
    case 'idle': return 'warning'
    case 'closed': return 'info'
    default: return 'info'
  }
}

// 获取任务状态颜色
const getTaskStatusColor = (status: string) => {
  switch (status) {
    case 'running': return 'warning'
    case 'completed': return 'success'
    case 'failed': return 'danger'
    case 'pending': return 'info'
    case 'cancelled': return 'info'
    default: return 'info'
  }
}

// 获取任务类型显示文本
const getTaskTypeText = (type: string) => {
  switch (type) {
    case 'single_tool': return '单工具'
    case 'multi_tool': return '多工具'
    case 'pipeline': return '流水线'
    case 'autonomous': return '自主模式'
    default: return type
  }
}

// 获取会话状态显示文本
const getSessionStatusText = (status: string) => {
  switch (status) {
    case 'active': return '活跃'
    case 'idle': return '空闲'
    case 'closed': return '已关闭'
    default: return status
  }
}

// 获取任务状态显示文本
const getTaskStatusText = (status: string) => {
  switch (status) {
    case 'running': return '运行中'
    case 'completed': return '已完成'
    case 'failed': return '失败'
    case 'pending': return '等待中'
    case 'cancelled': return '已取消'
    default: return status
  }
}

// 格式化时间
const formatTime = (timeStr: string) => {
  return new Date(timeStr).toLocaleString('zh-CN')
}

// 格式化持续时间
const formatDuration = (startTime: string, endTime?: string) => {
  const start = new Date(startTime)
  const end = endTime ? new Date(endTime) : new Date()
  const duration = Math.floor((end.getTime() - start.getTime()) / 1000)
  
  if (duration < 60) {
    return `${duration}秒`
  } else if (duration < 3600) {
    return `${Math.floor(duration / 60)}分${duration % 60}秒`
  } else {
    const hours = Math.floor(duration / 3600)
    const minutes = Math.floor((duration % 3600) / 60)
    return `${hours}小时${minutes}分钟`
  }
}

// 关闭会话
const closeSession = async (sessionId: string) => {
  try {
    // 这里应该调用实际的API
    // await fetch(`/api/mcp-agent/sessions/${sessionId}/close`, { method: 'POST' })
    
    // 模拟关闭会话
    const session = sessions.value.find(s => s.id === sessionId)
    if (session) {
      session.status = 'closed'
    }
    
    console.log(`会话 ${sessionId} 已关闭`)
  } catch (error) {
    console.error('关闭会话失败:', error)
  }
}

// 取消任务
const cancelTask = async (taskId: string) => {
  try {
    // 这里应该调用实际的API
    // await fetch(`/api/mcp-agent/tasks/${taskId}/cancel`, { method: 'POST' })
    
    // 模拟取消任务
    const task = tasks.value.find(t => t.id === taskId)
    if (task) {
      task.status = 'cancelled'
    }
    
    console.log(`任务 ${taskId} 已取消`)
  } catch (error) {
    console.error('取消任务失败:', error)
  }
}

// 查看任务详情
const viewTaskDetails = (taskId: string) => {
  // 这里可以打开任务详情对话框或跳转到详情页面
  console.log(`查看任务详情: ${taskId}`)
}

// 设置自动刷新
const setupAutoRefresh = () => {
  if (autoRefresh.value) {
    refreshInterval.value = setInterval(refreshData, 5000) // 每5秒刷新一次
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

// 会话表格列配置
const sessionColumns = [
  {
    title: '会话ID',
    key: 'id',
    width: 150
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render: (row: any) => {
      return h(NTag, {
        type: getSessionStatusColor(row.status),
        size: 'small'
      }, { default: () => getSessionStatusText(row.status) })
    }
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180,
    render: (row: any) => formatTime(row.created_at)
  },
  {
    title: '最后活动',
    key: 'last_activity',
    width: 180,
    render: (row: any) => formatTime(row.last_activity)
  },
  {
    title: '任务数',
    key: 'task_count',
    width: 80
  },
  {
    title: '使用工具',
    key: 'tools_used',
    render: (row: any) => {
      return row.tools_used.map((tool: string) => 
        h(NTag, {
          size: 'small',
          class: 'tool-tag',
          key: tool
        }, { default: () => tool })
      )
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 120,
    render: (row: any) => {
      if (row.status === 'active') {
        return h(NButton, {
          type: 'error',
          size: 'small',
          onClick: () => closeSession(row.id)
        }, { default: () => '关闭' })
      }
      return null
    }
  }
]

// 任务表格列配置
const taskColumns = [
  {
    title: '任务ID',
    key: 'id',
    width: 120
  },
  {
    title: '会话ID',
    key: 'session_id',
    width: 120
  },
  {
    title: '类型',
    key: 'type',
    width: 100,
    render: (row: any) => getTaskTypeText(row.type)
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render: (row: any) => {
      return h(NTag, {
        type: getTaskStatusColor(row.status),
        size: 'small'
      }, { default: () => getTaskStatusText(row.status) })
    }
  },
  {
    title: '工具',
    key: 'tool_name',
    width: 120
  },
  {
    title: '进度',
    key: 'progress',
    width: 120,
    render: (row: any) => {
      if (row.status === 'running') {
        return h(NProgress, {
          percentage: row.progress,
          showIndicator: false,
          height: 6
        })
      } else if (row.status === 'completed') {
        return '100%'
      } else if (row.status === 'failed') {
        return `${row.progress}%`
      }
      return '-'
    }
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180,
    render: (row: any) => formatTime(row.created_at)
  },
  {
    title: '持续时间',
    key: 'duration',
    width: 120,
    render: (row: any) => {
      if (row.started_at) {
        return formatDuration(row.started_at, row.completed_at || row.failed_at)
      }
      return '-'
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render: (row: any) => {
      const buttons = []
      
      buttons.push(
        h(NButton, {
          type: 'primary',
          size: 'small',
          onClick: () => viewTaskDetails(row.id),
          style: { marginRight: '8px' }
        }, {
          default: () => '详情',
          icon: () => h(NIcon, null, { default: () => h(EyeOutline) })
        })
      )
      
      if (row.status === 'running' || row.status === 'pending') {
        buttons.push(
          h(NButton, {
            type: 'error',
            size: 'small',
            onClick: () => cancelTask(row.id)
          }, {
            default: () => '取消',
            icon: () => h(NIcon, null, { default: () => h(TrashOutline) })
          })
        )
      }
      
      return buttons
    }
  }
]
</script>

<template>
  <div class="proxy-status">
    <div class="page-header">
      <h1>代理状态监控</h1>
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

    <!-- 会话监控 -->
    <n-card class="section-card">
      <template #header>
        <div class="card-header">
          <span>活跃会话</span>
          <n-tag type="info">{{ sessions.filter(s => s.status === 'active').length }} 个活跃</n-tag>
        </div>
      </template>
      
      <n-data-table 
        :data="sessions" 
        :columns="sessionColumns"
        :loading="loading"
        striped
      />
    </n-card>

    <!-- 任务监控 -->
    <n-card class="section-card">
      <template #header>
        <div class="card-header">
          <span>任务状态</span>
          <n-tag type="warning">{{ tasks.filter(t => t.status === 'running').length }} 个运行中</n-tag>
        </div>
      </template>
      
      <n-data-table 
        :data="tasks" 
        :columns="taskColumns"
        :loading="loading"
        striped
      />
      
      <!-- 失败任务的错误信息 -->
      <div v-for="task in tasks.filter(t => t.status === 'failed' && t.error_message)" :key="task.id" class="error-alert">
        <n-alert
          :title="`任务 ${task.id} 执行失败`"
          type="error"
          show-icon
          :closable="false"
        >
          {{ task.error_message }}
        </n-alert>
      </div>
    </n-card>
  </div>
</template>

<style scoped>
.proxy-status {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.section-card {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tool-tag {
  margin-right: 4px;
  margin-bottom: 4px;
}

.error-alert {
  margin-top: 16px;
}

:deep(.el-table) {
  font-size: 14px;
}

:deep(.el-table .el-table__cell) {
  padding: 8px 0;
}

:deep(.el-progress-bar__outer) {
  background-color: #f0f0f0;
}
</style>