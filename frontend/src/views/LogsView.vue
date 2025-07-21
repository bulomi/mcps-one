<template>
  <div class="logs-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1>日志管理</h1>
          <p>查看和管理系统运行日志</p>
        </div>
        <div class="header-right">
          <n-space>
            <n-button @click="refreshLogs">
              <template #icon>
                <n-icon><RefreshOutline /></n-icon>
              </template>
              刷新
            </n-button>
            <n-button @click="exportLogsAction">
              <template #icon>
                <n-icon><DownloadOutline /></n-icon>
              </template>
              导出
            </n-button>
            <n-button type="error" @click="cleanupLogsAction">
              <template #icon>
                <n-icon><TrashOutline /></n-icon>
              </template>
              清理日志
            </n-button>
          </n-space>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <n-grid :cols="4" :x-gap="16" class="stats-grid">
      <n-grid-item>
        <n-card>
          <n-statistic label="总日志数" :value="logStats.total" />
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card>
          <n-statistic label="错误日志" :value="logStats.errors">
            <template #suffix>
              <n-tag type="error" size="small">ERROR</n-tag>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card>
          <n-statistic label="警告日志" :value="logStats.warnings">
            <template #suffix>
              <n-tag type="warning" size="small">WARN</n-tag>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card>
          <n-statistic label="今日新增" :value="logStats.today" />
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 过滤器 -->
    <n-card class="filter-card">
      <n-form inline :label-width="80">
        <n-form-item label="日志类型">
          <n-select
            v-model:value="filters.logType"
            placeholder="选择日志类型"
            clearable
            style="width: 150px"
            :options="logTypeOptions"
            @update:value="applyFilters"
          />
        </n-form-item>
        <n-form-item label="日志级别">
          <n-select
            v-model:value="filters.level"
            placeholder="选择级别"
            clearable
            style="width: 120px"
            :options="levelOptions"
            @update:value="applyFilters"
          />
        </n-form-item>
        <n-form-item label="来源">
          <n-select
            v-model:value="filters.source"
            placeholder="选择来源"
            clearable
            style="width: 150px"
            :options="sourceOptions"
            @update:value="applyFilters"
          />
        </n-form-item>
        <n-form-item label="时间范围">
          <n-date-picker
            v-model:value="filters.dateRange"
            type="datetimerange"
            clearable
            style="width: 300px"
            @update:value="applyFilters"
          />
        </n-form-item>
        <n-form-item label="搜索">
          <n-input
            v-model:value="filters.search"
            placeholder="搜索日志内容"
            clearable
            style="width: 200px"
            @keyup.enter="applyFilters"
          >
            <template #suffix>
              <n-icon @click="applyFilters" style="cursor: pointer">
                <SearchOutline />
              </n-icon>
            </template>
          </n-input>
        </n-form-item>
        <n-form-item>
          <n-button @click="clearFilters">清空</n-button>
        </n-form-item>
      </n-form>
    </n-card>

    <!-- 日志表格 -->
    <n-card>
      <n-data-table
        :columns="logColumns"
        :data="logs"
        :loading="loading"
        :pagination="pagination"
        :row-key="(row: any) => row.id"
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
      />
    </n-card>

    <!-- 日志详情模态框 -->
    <n-modal v-model:show="showDetailModal" preset="card" title="日志详情" style="width: 800px">
      <div v-if="selectedLog">
        <n-descriptions :column="2" bordered>
          <n-descriptions-item label="ID">{{ selectedLog.id }}</n-descriptions-item>
          <n-descriptions-item label="时间">{{ formatDateTime(selectedLog.timestamp) }}</n-descriptions-item>
          <n-descriptions-item label="级别">
            <n-tag :type="getLogLevelType(selectedLog.level)">{{ selectedLog.level }}</n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="分类">{{ selectedLog.category }}</n-descriptions-item>
          <n-descriptions-item label="来源">{{ selectedLog.source }}</n-descriptions-item>
          <n-descriptions-item label="工具" v-if="selectedLog.tool_name">{{ selectedLog.tool_name }}</n-descriptions-item>
        </n-descriptions>
        
        <n-divider>消息内容</n-divider>
        <n-code :code="selectedLog.message" language="text" show-line-numbers />
        
        <n-divider v-if="selectedLog.details">详细信息</n-divider>
        <n-code
          v-if="selectedLog.details"
          :code="JSON.stringify(selectedLog.details, null, 2)"
          language="json"
          show-line-numbers
        />
        
        <n-divider v-if="selectedLog.stack_trace">堆栈跟踪</n-divider>
        <n-code
          v-if="selectedLog.stack_trace"
          :code="selectedLog.stack_trace"
          language="text"
          show-line-numbers
        />
      </div>
    </n-modal>

    <!-- 清理日志模态框 -->
    <n-modal v-model:show="showCleanupModal" preset="dialog" title="清理日志">
      <div>
        <n-alert type="warning" style="margin-bottom: 16px">
          此操作将永久删除选定的日志，请谨慎操作！
        </n-alert>
        
        <n-form ref="cleanupFormRef" :model="cleanupForm" label-placement="left" label-width="120px">
          <n-form-item label="保留天数" path="retentionDays">
            <n-input-number
              v-model:value="cleanupForm.retentionDays"
              :min="1"
              :max="365"
              placeholder="保留最近N天的日志"
            />
          </n-form-item>
          <n-form-item label="日志级别">
            <n-checkbox-group v-model:value="cleanupForm.levels">
              <n-space>
                <n-checkbox value="DEBUG">DEBUG</n-checkbox>
                <n-checkbox value="INFO">INFO</n-checkbox>
                <n-checkbox value="WARNING">WARNING</n-checkbox>
                <n-checkbox value="ERROR">ERROR</n-checkbox>
                <n-checkbox value="CRITICAL">CRITICAL</n-checkbox>
              </n-space>
            </n-checkbox-group>
          </n-form-item>
          <n-form-item label="日志类型">
            <n-checkbox-group v-model:value="cleanupForm.categories">
              <n-space>
                <n-checkbox value="system">系统日志</n-checkbox>
                <n-checkbox value="operation">操作日志</n-checkbox>
                <n-checkbox value="mcp">MCP日志</n-checkbox>
              </n-space>
            </n-checkbox-group>
          </n-form-item>
        </n-form>
      </div>
      <template #action>
        <n-space>
          <n-button @click="showCleanupModal = false">取消</n-button>
          <n-button type="error" @click="cleanupLogsAction">
            确认清理
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import {
  NCard,
  NButton,
  NSpace,
  NGrid,
  NGridItem,
  NStatistic,
  NForm,
  NFormItem,
  NSelect,
  NDatePicker,
  NInput,
  NDataTable,
  NTag,
  NIcon,
  NModal,
  NDescriptions,
  NDescriptionsItem,
  NDivider,
  NCode,
  NAlert,
  NInputNumber,
  NCheckboxGroup,
  NCheckbox,
  useMessage,
  type DataTableColumns
} from 'naive-ui'
import {
  RefreshOutline,
  DownloadOutline,
  TrashOutline,
  SearchOutline,
  EyeOutline
} from '@vicons/ionicons5'
import { getLogSummary, getSystemLogs, getOperationLogs, getMcpLogs, cleanupLogs, exportLogs } from '@/api/logs'
import { formatBytes, formatDateTime, formatDuration } from '@/utils/format'
import { handleApiError } from '@/utils/errorHandler'
import { ux } from '@/utils/userExperience'
import { logLevelOptions } from '@/constants/logLevels'

// 消息提示函数
const message = useMessage()

const showMessage = (type: 'success' | 'error' | 'info' | 'warning', content: string) => {
  message[type](content)
}

// 响应式数据
const loading = ref(false)
const cleanupLoading = ref(false)
const showDetailModal = ref(false)
const showCleanupModal = ref(false)
const selectedLog = ref<any>(null)

// 日志统计
const logStats = ref({
  total: 0,
  errors: 0,
  warnings: 0,
  today: 0
})

// 日志列表
const logs = ref<any[]>([])

// 过滤条件
const filters = ref({
  logType: '',
  level: '',
  source: '',
  search: '',
  dateRange: null as [number, number] | null
})

// 清理表单
const cleanupForm = ref({
  retentionDays: 30,
  levels: ['DEBUG', 'INFO'],
  categories: ['system']
})

// 分页配置
const pagination = ref({
  page: 1,
  pageSize: 20,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100]
})

// 选项配置
const logTypeOptions = [
  { label: '系统日志', value: 'system' },
  { label: '操作日志', value: 'operation' },
  { label: 'MCP日志', value: 'mcp' }
]

// 使用统一的日志级别定义
const levelOptions = logLevelOptions

const sourceOptions = [
  { label: '系统', value: 'system' },
  { label: 'API', value: 'api' },
  { label: 'MCP客户端', value: 'mcp-client' },
  { label: 'MCP代理', value: 'mcp-agent' },
  { label: '数据库', value: 'database' }
]

// 表格列定义
const logColumns: DataTableColumns<any> = [
  {
    title: 'ID',
    key: 'id',
    width: 80
  },
  {
    title: '时间',
    key: 'timestamp',
    width: 180,
    render(row) {
      return formatDateTime(row.timestamp)
    }
  },
  {
    title: '级别',
    key: 'level',
    width: 100,
    render(row) {
      return h(NTag, {
        type: getLogLevelType(row.level)
      }, {
        default: () => row.level
      })
    }
  },
  {
    title: '分类',
    key: 'category',
    width: 100
  },
  {
    title: '来源',
    key: 'source',
    width: 120
  },
  {
    title: '工具',
    key: 'tool_name',
    width: 120,
    render(row) {
      return row.tool_name || '-'
    }
  },
  {
    title: '消息',
    key: 'message',
    ellipsis: {
      tooltip: true
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    render(row) {
      return h(NButton, {
        size: 'small',
        onClick: () => viewLogDetail(row)
      }, {
        icon: () => h(NIcon, null, { default: () => h(EyeOutline) }),
        default: () => '详情'
      })
    }
  }
]

// 方法
const loadLogStats = async () => {
  try {
    const apiData = await getLogSummary()
    // 响应拦截器已经提取了data字段，直接使用返回的数据
    logStats.value = {
       total: apiData.overview?.total_logs || 0,
       errors: apiData.overview?.today_errors || 0,
       warnings: (apiData.system_logs?.errors || 0) + (apiData.operation_logs?.errors || 0) + (apiData.mcp_logs?.errors || 0),
       today: apiData.overview?.today_logs || 0
     }
  } catch (error) {
    console.error('加载日志统计失败:', error)
    handleApiError(error, '加载日志统计失败', undefined, true)
    // 使用默认值
     logStats.value = {
       total: 0,
       errors: 0,
       warnings: 0,
       today: 0
     }
  }
}

const loadLogs = async () => {
  loading.value = true
  try {
    const params = {
       page: pagination.value.page,
       size: pagination.value.pageSize,
       level: filters.value.level,
       category: filters.value.source,
       search: filters.value.search
     }
    
    // 处理时间范围
    if (filters.value.dateRange && filters.value.dateRange.length === 2) {
      params.start_time = new Date(filters.value.dateRange[0]).toISOString()
      params.end_time = new Date(filters.value.dateRange[1]).toISOString()
    }
    
    // 过滤空值
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null || params[key] === undefined) {
        delete params[key]
      }
    })
    
    // 根据日志类型调用不同的API
    let apiData
    const logType = filters.value.logType || 'system'
    
    switch (logType) {
      case 'operation':
        apiData = await getOperationLogs(params)
        break
      case 'mcp':
        apiData = await getMcpLogs(params)
        break
      case 'system':
      default:
        apiData = await getSystemLogs(params)
        break
    }
    
    // 响应拦截器已经提取了data字段，直接使用返回的数据
    logs.value = apiData.items || []
    pagination.value.itemCount = apiData.pagination?.total || apiData.total || 0
  } catch (error) {
    console.error('加载日志失败:', error)
    handleApiError(error, '加载日志失败', undefined, true)
    logs.value = []
    pagination.value.itemCount = 0
  } finally {
    loading.value = false
  }
}

const refreshLogs = async () => {
  await ux.executeWithFeedback(
    async () => {
      await Promise.all([loadLogStats(), loadLogs()])
      return { 
        totalLogs: logStats.value.total,
        currentPage: logs.value.length
      }
    },
    {
      loadingMessage: '正在刷新日志数据...',
      successMessage: (result) => `日志数据已刷新，共 ${result.totalLogs} 条日志，当前页 ${result.currentPage} 条`,
      errorMessage: '刷新日志数据失败，请稍后重试'
    }
  )
}

const applyFilters = () => {
  pagination.value.page = 1
  loadLogs()
}

const clearFilters = () => {
  filters.value = {
    logType: '',
    level: '',
    source: '',
    search: '',
    dateRange: null
  }
  applyFilters()
}

const handlePageChange = (page: number) => {
  pagination.value.page = page
  loadLogs()
}

const handlePageSizeChange = (pageSize: number) => {
  pagination.value.pageSize = pageSize
  pagination.value.page = 1
  loadLogs()
}

const viewLogDetail = (log: any) => {
  selectedLog.value = log
  showDetailModal.value = true
}

const exportLogsAction = async () => {
  await ux.executeWithFeedback(
    async () => {
      const params = {
         log_type: filters.value.logType || 'system',
         format: 'csv',
         level: filters.value.level,
         category: filters.value.source,
         search: filters.value.search
       }
       
       // 处理时间范围
       if (filters.value.dateRange && filters.value.dateRange.length === 2) {
         params.start_time = new Date(filters.value.dateRange[0]).toISOString()
         params.end_time = new Date(filters.value.dateRange[1]).toISOString()
       }
      
      // 过滤空值
      Object.keys(params).forEach(key => {
        if (params[key] === '' || params[key] === null || params[key] === undefined) {
          delete params[key]
        }
      })
      
      const response = await exportLogs(params)
      
      // 创建下载链接
      const blob = new Blob([response.data], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      const filename = `logs_${new Date().toISOString().split('T')[0]}.csv`
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      return { filename, size: blob.size }
    },
    {
      loadingMessage: '正在导出日志...',
      successMessage: (result) => `日志导出成功：${result.filename} (${(result.size / 1024).toFixed(1)} KB)`,
      errorMessage: '导出日志失败，请稍后重试'
    }
  )
}

const cleanupLogsAction = async () => {
  const confirmed = await ux.confirmAction(
    '清理日志',
    `确定要清理 ${cleanupForm.value.retentionDays} 天前的日志吗？此操作不可撤销。`
  )
  
  if (confirmed) {
    await ux.executeWithFeedback(
      async () => {
        const result = await cleanupLogs(cleanupForm.value)
        
        showCleanupModal.value = false
        await refreshLogs()
        
        return { 
          deletedCount: result.deletedCount || 0,
          retentionDays: cleanupForm.value.retentionDays
        }
      },
      {
        loadingMessage: '正在清理日志...',
        successMessage: (result) => `日志清理完成，删除了 ${result.deletedCount} 条 ${result.retentionDays} 天前的日志`,
        errorMessage: '清理日志失败，请稍后重试'
      }
    )
  }
}

// 工具函数
const formatDateTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

const getLogLevelType = (level: string) => {
  switch (level) {
    case 'DEBUG': return 'info'
    case 'INFO': return 'success'
    case 'WARNING': return 'warning'
    case 'ERROR': return 'error'
    case 'CRITICAL': return 'error'
    default: return 'default'
  }
}

// 组件挂载时加载数据
onMounted(() => {
  refreshLogs()
})
</script>

<style scoped>
.logs-view {
  padding: 0;
}

.page-header {
  margin-bottom: 16px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.header-left h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
}

.header-left p {
  margin: 0;
  color: var(--n-text-color-2);
  font-size: 14px;
}

.stats-grid {
  margin-bottom: 16px;
}

.filter-card {
  margin-bottom: 16px;
}
</style>