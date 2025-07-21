<script setup lang="ts">
import { ref, onMounted, onUnmounted, h, computed } from 'vue'
import { NCard, NDataTable, NTag, NButton, NProgress, NAlert, NStatistic, NGrid, NGridItem, NIcon } from 'naive-ui'
import { RefreshOutline, EyeOutline, TrashOutline, PlayOutline, PauseOutline, CheckmarkOutline, CloseOutline } from '@vicons/ionicons5'
import { handleApiError } from '@/utils/errorHandler'
import { tasksApi } from '@/api/tasks'

// 响应式数据
const tasks = ref([])
const loading = ref(true)
const refreshing = ref(false)
const autoRefresh = ref(true)
const refreshInterval = ref(null)

// 计算任务统计信息
const taskStats = computed(() => {
  const total = tasks.value.length
  const running = tasks.value.filter(t => t.status === 'running').length
  const completed = tasks.value.filter(t => t.status === 'completed').length
  const failed = tasks.value.filter(t => t.status === 'failed').length
  const pending = tasks.value.filter(t => t.status === 'pending').length
  const cancelled = tasks.value.filter(t => t.status === 'cancelled').length
  
  return { total, running, completed, failed, pending, cancelled }
})

// 获取任务列表
const fetchTasks = async () => {
  try {
    const response = await tasksApi.getTasks({ size: 100 })
    const data = response.data || response
    
    // 转换后端数据格式为前端需要的格式
    tasks.value = data.tasks?.map(task => ({
      id: task.task_id || task.id,
      session_id: task.session_id,
      type: task.task_type || task.type,
      status: task.status,
      tool_name: task.tool_name || 'unknown',
      progress: task.progress || 0,
      created_at: task.created_at,
      started_at: task.started_at,
      completed_at: task.completed_at,
      failed_at: task.failed_at,
      error_message: task.error_message
    })) || []
  } catch (error) {
    // 获取任务列表失败
    handleApiError(error, '获取任务列表失败')
    // 如果API调用失败，使用空数组
    tasks.value = []
  }
}

// 刷新数据
const refreshData = async () => {
  refreshing.value = true
  try {
    await fetchTasks()
  } finally {
    refreshing.value = false
    loading.value = false
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

// 取消任务
const cancelTask = async (taskId: string) => {
  try {
    await tasksApi.cancelTask(taskId)
    
    // 刷新任务列表
    await fetchTasks()
    // 任务已取消
  } catch (error) {
    // 取消任务失败
    handleApiError(error, '取消任务失败')
  }
}

// 查看任务详情
const viewTaskDetails = (taskId: string) => {
  // 这里可以打开任务详情对话框或跳转到详情页面
  // 查看任务详情
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

// 任务表格列配置
const taskColumns = [
  {
    title: '任务ID',
    key: 'id',
    width: 150
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
  <div class="task-monitor">
    <div class="page-header">
      <h1>任务执行监控</h1>
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

    <!-- 任务统计面板 -->
    <n-card class="stats-card">
      <template #header>
        <span>任务统计概览</span>
      </template>
      
      <n-grid :cols="6" :x-gap="16">
        <n-grid-item>
          <n-statistic label="总任务数" :value="taskStats.total">
            <template #prefix>
              <n-icon color="#909399"><PlayOutline /></n-icon>
            </template>
          </n-statistic>
        </n-grid-item>
        <n-grid-item>
          <n-statistic label="运行中" :value="taskStats.running">
            <template #prefix>
              <n-icon color="#E6A23C"><PlayOutline /></n-icon>
            </template>
          </n-statistic>
        </n-grid-item>
        <n-grid-item>
          <n-statistic label="已完成" :value="taskStats.completed">
            <template #prefix>
              <n-icon color="#67C23A"><CheckmarkOutline /></n-icon>
            </template>
          </n-statistic>
        </n-grid-item>
        <n-grid-item>
          <n-statistic label="失败" :value="taskStats.failed">
            <template #prefix>
              <n-icon color="#F56C6C"><CloseOutline /></n-icon>
            </template>
          </n-statistic>
        </n-grid-item>
        <n-grid-item>
          <n-statistic label="等待中" :value="taskStats.pending">
            <template #prefix>
              <n-icon color="#409EFF"><PauseOutline /></n-icon>
            </template>
          </n-statistic>
        </n-grid-item>
        <n-grid-item>
          <n-statistic label="已取消" :value="taskStats.cancelled">
            <template #prefix>
              <n-icon color="#909399"><CloseOutline /></n-icon>
            </template>
          </n-statistic>
        </n-grid-item>
      </n-grid>
    </n-card>

    <!-- 任务详情列表 -->
    <n-card class="section-card">
      <template #header>
        <div class="card-header">
          <span>任务执行详情</span>
          <n-tag type="warning">{{ taskStats.running }} 个运行中</n-tag>
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
.task-monitor {
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

.stats-card {
  margin-bottom: 24px;
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