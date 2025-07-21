<template>
  <div class="auto-session-view">
    <div class="page-header">
      <h1>自动会话管理</h1>
      <p class="description">智能管理MCP会话生命周期，提供会话池管理和配置功能</p>
    </div>

    <!-- 会话列表 -->
    <n-card title="会话列表" class="sessions-card">
      <template #header-extra>
        <n-space>
          <n-button @click="refreshSessions" :loading="loading">
            <template #icon>
              <n-icon><RefreshIcon /></n-icon>
            </template>
            刷新
          </n-button>
          <n-button @click="manualCleanupSessions" :loading="loading">
            <template #icon>
              <n-icon><DeleteIcon /></n-icon>
            </template>
            清理会话
          </n-button>
          <n-button @click="refillSessionPool" :loading="loading">
            <template #icon>
              <n-icon><AddIcon /></n-icon>
            </template>
            补充会话池
          </n-button>
        </n-space>
      </template>
      
      <!-- 统计信息 -->
      <div class="quick-stats" style="margin-bottom: 20px;">
        <div class="stat-item">
          <div class="stat-value">{{ stats.total_sessions }}</div>
          <div class="stat-label">总会话数</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ stats.active_sessions }}</div>
          <div class="stat-label">活跃会话</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ stats.idle_sessions }}</div>
          <div class="stat-label">空闲会话</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ stats.hibernating_sessions }}</div>
          <div class="stat-label">休眠会话</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ stats.pool_size }}</div>
          <div class="stat-label">会话池大小</div>
        </div>
      </div>

      <n-data-table
        :columns="columns"
        :data="sessions"
        :loading="loading"
        :pagination="{ pageSize: 10 }"
        :row-key="(row) => row.session_id"
      />
    </n-card>

    <!-- 配置管理 -->
    <n-card title="配置管理" class="config-card">
      <template #header-extra>
        <n-button type="primary" @click="showConfigDialog = true">
          <template #icon>
            <n-icon><SettingsIcon /></n-icon>
          </template>
          编辑配置
        </n-button>
      </template>
      
      <div class="config-display">
        <div class="config-item">
          <span class="config-label">空闲超时</span>
          <span class="config-value">{{ config.idle_timeout }}秒</span>
        </div>
        <div class="config-item">
          <span class="config-label">休眠超时</span>
          <span class="config-value">{{ config.hibernation_timeout }}秒</span>
        </div>
        <div class="config-item">
          <span class="config-label">最大生命周期</span>
          <span class="config-value">{{ config.max_session_lifetime }}秒</span>
        </div>
        <div class="config-item">
          <span class="config-label">最大并发会话</span>
          <span class="config-value">{{ config.max_concurrent_sessions }}</span>
        </div>
        <div class="config-item">
          <span class="config-label">会话池大小</span>
          <span class="config-value">{{ config.session_pool_size }}</span>
        </div>
        <div class="config-item">
          <span class="config-label">自动工具选择</span>
          <span class="config-value">{{ config.enable_auto_tool_selection ? '启用' : '禁用' }}</span>
        </div>
        <div class="config-item">
          <span class="config-label">工具选择策略</span>
          <span class="config-value">{{ config.tool_selection_strategy }}</span>
        </div>
        <div class="config-item">
          <span class="config-label">清理间隔</span>
          <span class="config-value">{{ config.cleanup_interval }}秒</span>
        </div>
      </div>
    </n-card>

    <!-- 配置编辑对话框 -->
    <n-modal v-model:show="showConfigDialog" preset="card" title="编辑配置" style="width: 600px;">
      <n-form :model="configForm" label-placement="left" label-width="150px">
        <n-form-item label="空闲超时(秒)">
          <n-input-number v-model:value="configForm.idle_timeout" :min="60" :max="3600" />
        </n-form-item>
        <n-form-item label="休眠超时(秒)">
          <n-input-number v-model:value="configForm.hibernation_timeout" :min="300" :max="7200" />
        </n-form-item>
        <n-form-item label="最大生命周期(秒)">
          <n-input-number v-model:value="configForm.max_session_lifetime" :min="3600" :max="86400" />
        </n-form-item>
        <n-form-item label="最大并发会话">
          <n-input-number v-model:value="configForm.max_concurrent_sessions" :min="1" :max="50" />
        </n-form-item>
        <n-form-item label="会话池大小">
          <n-input-number v-model:value="configForm.session_pool_size" :min="1" :max="20" />
        </n-form-item>
        <n-form-item label="自动工具选择">
          <n-switch v-model:value="configForm.enable_auto_tool_selection" />
        </n-form-item>
        <n-form-item label="工具选择策略">
          <n-select 
            v-model:value="configForm.tool_selection_strategy"
            :options="strategyOptions"
          />
        </n-form-item>
        <n-form-item label="清理间隔(秒)">
          <n-input-number v-model:value="configForm.cleanup_interval" :min="60" :max="3600" />
        </n-form-item>
      </n-form>
      
      <template #footer>
        <n-space justify="end">
          <n-button @click="showConfigDialog = false">取消</n-button>
          <n-button type="primary" @click="updateConfig" :loading="updating">保存</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, h } from 'vue'
import { 
  NCard, NButton, NSpace, NIcon, NForm, NFormItem, NInput, NSelect,
  NSwitch, NInputNumber, NDataTable, NModal, NTag, NButtonGroup, useMessage
} from 'naive-ui'
import { 
  Refresh as RefreshIcon, 
  TrashOutline as DeleteIcon, 
  Add as AddIcon,
  Settings as SettingsIcon,
  Eye as EyeIcon,
  PowerOff as PowerOffIcon,
  Pause as PauseIcon
} from '@vicons/ionicons5'
import autoSessionApi from '@/api/autoSession'
import type { 
  AutoSessionInfo, 
  AutoSessionStats, 
  AutoSessionConfig,
  AutoSessionConfigUpdate
} from '@/api/autoSession'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

// 响应式数据
const loading = ref(false)
const updating = ref(false)
const showConfigDialog = ref(false)
const sessions = ref<AutoSessionInfo[]>([])
const stats = ref<AutoSessionStats>({
  total_sessions: 0,
  active_sessions: 0,
  idle_sessions: 0,
  hibernating_sessions: 0,
  pool_size: 0,
  max_concurrent: 0,
  config: {
    idle_timeout: 300,
    hibernation_timeout: 1800,
    max_session_lifetime: 3600,
    session_pool_size: 5,
    auto_tool_selection: true,
    tool_selection_strategy: 'smart'
  }
})
const config = ref<AutoSessionConfig>({
  idle_timeout: 300,
  hibernation_timeout: 1800,
  max_session_lifetime: 3600,
  max_concurrent_sessions: 10,
  session_pool_size: 5,
  enable_auto_tool_selection: true,
  tool_selection_strategy: 'smart',
  cleanup_interval: 300
})



const configForm = reactive<AutoSessionConfigUpdate>({})

let refreshTimer: NodeJS.Timeout | null = null
const message = useMessage()

// 选项数据


const strategyOptions = [
  { label: '智能选择', value: 'smart' },
  { label: '性能优先', value: 'performance' },
  { label: '准确性优先', value: 'accuracy' }
]

// 表格列定义
const columns = [
  {
    title: '会话ID',
    key: 'session_id',
    width: 200,
    ellipsis: true
  },
  {
    title: '状态',
    key: 'state',
    width: 100,
    render: (row: AutoSessionInfo) => {
      const type = getStateType(row.state)
      return h(NTag, { type }, { default: () => getStateText(row.state) })
    }
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 150,
    render: (row: AutoSessionInfo) => formatTime(row.created_at)
  },
  {
    title: '最后活动',
    key: 'last_activity',
    width: 150,
    render: (row: AutoSessionInfo) => formatTime(row.last_activity)
  },
  {
    title: '过期时间',
    key: 'expires_at',
    width: 150,
    render: (row: AutoSessionInfo) => formatTime(row.expires_at || '')
  },
  {
    title: '工具',
    key: 'tools',
    width: 200,
    render: (row: AutoSessionInfo) => {
      return h(NSpace, { size: 'small' }, {
        default: () => row.tools.map(tool => 
          h(NTag, { size: 'small', type: 'info' }, { default: () => tool })
        )
      })
    }
  },
  {
    title: '任务数',
    key: 'task_count',
    width: 80
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    render: (row: AutoSessionInfo) => {
      return h(NButtonGroup, { size: 'small' }, {
        default: () => [
          h(NButton, {
            size: 'small',
            onClick: () => sessionAction(row.session_id, 'wake_up'),
            disabled: row.state === 'active'
          }, { default: () => '唤醒' }),
          h(NButton, {
            size: 'small',
            onClick: () => sessionAction(row.session_id, 'hibernate'),
            disabled: row.state === 'hibernating'
          }, { default: () => '休眠' }),
          h(NButton, {
            size: 'small',
            type: 'error',
            onClick: () => sessionAction(row.session_id, 'destroy')
          }, { default: () => '销毁' })
        ]
      })
    }
  }
]

// 方法
const refreshSessions = async () => {
  loading.value = true
  try {
    const [sessionsRes, statsRes] = await Promise.all([
      autoSessionApi.getAutoSessions(),
      autoSessionApi.getAutoSessionStats()
    ])
    
    if (sessionsRes && sessionsRes.success) {
      // 修复：从响应数据中提取sessions数组
      sessions.value = sessionsRes.data?.sessions || []
    }
    
    if (statsRes && statsRes.success) {
      stats.value = statsRes.data || stats.value
    }
  } catch (error) {
    console.error('刷新会话列表失败:', error)
    message.error('刷新失败')
  } finally {
    loading.value = false
  }
}

const loadConfig = async () => {
  try {
    const res = await autoSessionApi.getAutoSessionConfig()
    if (res && res.success && res.data) {
      // 修复：从响应数据中提取config对象
      config.value = res.data.config || res.data
      Object.assign(configForm, res.data.config || res.data)
    }
  } catch (error) {
    console.error('加载配置失败:', error)
    message.error('加载配置失败')
  }
}



const sessionAction = async (sessionId: string, action: 'wake_up' | 'hibernate' | 'destroy') => {
  try {
    const res = await autoSessionApi.sessionAction(sessionId, { action })
    if (res && res.success) {
      message.success(`${action === 'wake_up' ? '唤醒' : action === 'hibernate' ? '休眠' : '销毁'}成功`)
      await refreshSessions()
    } else {
      message.error((res && res.message) || '操作失败')
    }
  } catch (error) {
    console.error('会话操作失败:', error)
    message.error('操作失败')
  }
}

const manualCleanupSessions = async () => {
  try {
    const res = await autoSessionApi.manualCleanupSessions()
    if (res && res.success) {
      message.success('清理完成')
      await refreshSessions()
    } else {
      message.error((res && res.message) || '清理失败')
    }
  } catch (error) {
    console.error('清理失败:', error)
    message.error('清理失败')
  }
}

const refillSessionPool = async () => {
  try {
    const res = await autoSessionApi.refillSessionPool()
    if (res && res.success) {
      message.success('会话池补充完成')
      await refreshSessions()
    } else {
      message.error((res && res.message) || '补充失败')
    }
  } catch (error) {
    console.error('补充会话池失败:', error)
    message.error('补充失败')
  }
}

const updateConfig = async () => {
  updating.value = true
  try {
    const res = await autoSessionApi.updateAutoSessionConfig(configForm)
    if (res && res.success) {
      message.success('配置更新成功')
      showConfigDialog.value = false
      await loadConfig()
    } else {
      message.error((res && res.message) || '配置更新失败')
    }
  } catch (error) {
    console.error('配置更新失败:', error)
    message.error('配置更新失败')
  } finally {
    updating.value = false
  }
}

const getStateType = (state: string) => {
  switch (state) {
    case 'active': return 'success'
    case 'idle': return 'warning'
    case 'hibernating': return 'info'
    case 'expired': return 'error'
    default: return 'default'
  }
}

const getStateText = (state: string) => {
  switch (state) {
    case 'active': return '活跃'
    case 'idle': return '空闲'
    case 'hibernating': return '休眠'
    case 'expired': return '过期'
    default: return state
  }
}

const formatTime = (timeStr: string) => {
  if (!timeStr) return '-'
  try {
    return formatDistanceToNow(new Date(timeStr), {
      addSuffix: true,
      locale: zhCN
    })
  } catch {
    return timeStr
  }
}

// 生命周期
onMounted(async () => {
  await Promise.all([
    refreshSessions(),
    loadConfig()
  ])
  
  // 设置定时刷新
  refreshTimer = setInterval(refreshSessions, 10000) // 每10秒刷新一次
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.auto-session-view {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 24px;
  font-weight: 600;
}

.description {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.sessions-card,
.config-card {
  margin-bottom: 20px;
}

.quick-stats {
  display: flex;
  gap: 40px;
  flex-wrap: wrap;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 32px;
  font-weight: 600;
  color: #409eff;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #606266;
  margin-top: 8px;
}

.config-display {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

.config-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
}

.config-label {
  font-weight: 500;
  color: #606266;
}

.config-value {
  color: #303133;
  font-weight: 600;
}
</style>