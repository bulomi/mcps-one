<template>
  <n-modal 
    v-model:show="visible" 
    preset="card"
    title="API 监控面板"
    class="api-monitor-modal"
    :style="{ width: '90vw', maxWidth: '1200px', height: '80vh' }"
    :closable="true"
    :mask-closable="false"
    @close="handleClose"
  >
    <template #header-extra>
      <n-space>
        <n-switch 
          v-model:value="autoRefresh" 
          size="small"
        >
          <template #checked>自动刷新</template>
          <template #unchecked>手动刷新</template>
        </n-switch>
        
        <n-select 
          v-model:value="selectedTimeRange" 
          :options="timeRangeOptions"
          size="small"
          style="width: 120px"
        />
      </n-space>
    </template>

    <div class="monitor-content">
      <!-- 实时指标卡片 -->
      <div class="metrics-grid">
        <n-card size="small" class="metric-card">
          <n-statistic label="每分钟请求数" :value="realTimeMetrics.requestsPerMinute">
            <template #prefix>
              <n-icon color="#1890ff"><PulseOutline /></n-icon>
            </template>
          </n-statistic>
        </n-card>
        
        <n-card size="small" class="metric-card">
          <n-statistic 
            label="平均响应时间" 
            :value="realTimeMetrics.averageResponseTime.toFixed(0)" 
            suffix="ms"
            :value-style="getResponseTimeStyle(realTimeMetrics.averageResponseTime)"
          >
            <template #prefix>
              <n-icon :color="getResponseTimeColor(realTimeMetrics.averageResponseTime)"><TimeOutline /></n-icon>
            </template>
          </n-statistic>
        </n-card>
        
        <n-card size="small" class="metric-card">
          <n-statistic 
            label="错误率" 
            :value="realTimeMetrics.errorRate.toFixed(1)" 
            suffix="%"
            :value-style="getErrorRateStyle(realTimeMetrics.errorRate)"
          >
            <template #prefix>
              <n-icon :color="getErrorRateColor(realTimeMetrics.errorRate)"><WarningOutline /></n-icon>
            </template>
          </n-statistic>
        </n-card>
        
        <n-card size="small" class="metric-card">
          <n-statistic label="活跃请求" :value="realTimeMetrics.activeRequests">
            <template #prefix>
              <n-icon color="#722ed1"><FlashOutline /></n-icon>
            </template>
          </n-statistic>
        </n-card>
      </div>

      <!-- 操作按钮 -->
      <div class="actions-bar">
        <n-space>
          <n-button type="primary" @click="refreshStats">
            <template #icon><n-icon><RefreshOutline /></n-icon></template>
            刷新数据
          </n-button>
          
          <n-button type="error" @click="handleClearMetrics">
            <template #icon><n-icon><TrashOutline /></n-icon></template>
            清除数据
          </n-button>
          
          <n-button type="success" @click="handleExportMetrics">
            <template #icon><n-icon><DownloadOutline /></n-icon></template>
            导出数据
          </n-button>
          
          <n-button type="info" @click="handleGenerateReport">
            <template #icon><n-icon><DocumentTextOutline /></n-icon></template>
            生成报告
          </n-button>
          
          <n-button @click="showDetails = !showDetails">
            <template #icon><n-icon><EyeOutline /></n-icon></template>
            {{ showDetails ? '隐藏详情' : '显示详情' }}
          </n-button>
        </n-space>
      </div>

      <!-- 统计信息 -->
      <div v-if="stats" class="stats-grid">
        <!-- 总体统计 -->
        <n-card title="总体统计" size="small">
          <div class="stat-items">
            <div class="stat-item">
              <span class="stat-label">总请求数:</span>
              <span class="stat-value">{{ stats.totalCalls }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">成功率:</span>
              <span class="stat-value" :style="getSuccessRateStyle(stats.successRate)">
                {{ stats.successRate.toFixed(2) }}%
              </span>
            </div>
            <div class="stat-item">
              <span class="stat-label">平均响应时间:</span>
              <span class="stat-value" :style="getResponseTimeStyle(stats.averageResponseTime)">
                {{ stats.averageResponseTime.toFixed(2) }}ms
              </span>
            </div>
            <div class="stat-item">
              <span class="stat-label">错误率:</span>
              <span class="stat-value" :style="getErrorRateStyle(stats.errorRate)">
                {{ stats.errorRate.toFixed(2) }}%
              </span>
            </div>
          </div>
        </n-card>

        <!-- 最慢端点 -->
        <n-card title="最慢端点" size="small">
          <div class="endpoint-list">
            <div 
              v-for="(endpoint, index) in stats.slowestEndpoints.slice(0, 5)" 
              :key="index"
              class="endpoint-item"
            >
              <span class="endpoint-url" :title="endpoint.url">{{ endpoint.url }}</span>
              <span class="endpoint-time" :style="getResponseTimeStyle(endpoint.averageTime)">
                {{ endpoint.averageTime.toFixed(0) }}ms
              </span>
            </div>
          </div>
        </n-card>

        <!-- 错误统计 -->
        <n-card title="错误统计" size="small">
          <div class="error-stats">
            <div 
              v-for="[type, count] in Object.entries(stats.errorsByType)" 
              :key="type"
              class="error-item"
            >
              <span class="error-type">{{ type }}:</span>
              <span class="error-count">{{ count }}</span>
            </div>
          </div>
        </n-card>

        <!-- 最近错误 -->
        <n-card title="最近错误" size="small">
          <div class="recent-errors">
            <div 
              v-for="(error, index) in stats.recentErrors.slice(0, 5)" 
              :key="index"
              class="error-record"
            >
              <div class="error-url" :title="error.url">{{ error.url }}</div>
              <div class="error-message" :title="error.error">{{ error.error }}</div>
              <div class="error-time">{{ formatTime(error.timestamp) }}</div>
            </div>
          </div>
        </n-card>
      </div>

      <!-- 详细信息 -->
      <div v-if="showDetails && stats" class="details-section">
        <n-card title="详细信息" size="small">
          <n-tabs type="line">
            <n-tab-pane name="endpoints" tab="所有端点性能">
              <div class="endpoints-detail">
                <div 
                  v-for="(endpoint, index) in stats.slowestEndpoints" 
                  :key="index"
                  class="endpoint-detail-item"
                >
                  <div class="endpoint-detail-url" :title="endpoint.url">
                    {{ endpoint.url }}
                  </div>
                  <div class="endpoint-detail-stats">
                    <span class="endpoint-detail-time">
                      {{ endpoint.averageTime.toFixed(0) }}ms
                    </span>
                    <span class="endpoint-detail-count">
                      {{ endpoint.callCount }} 次调用
                    </span>
                  </div>
                </div>
              </div>
            </n-tab-pane>
            
            <n-tab-pane name="errors" tab="所有错误记录">
              <div class="errors-detail">
                <div 
                  v-for="(error, index) in stats.recentErrors" 
                  :key="index"
                  class="error-detail-item"
                >
                  <div class="error-detail-url" :title="error.url">
                    {{ error.url }}
                  </div>
                  <div class="error-detail-message" :title="error.error">
                    {{ error.error }}
                  </div>
                  <div class="error-detail-time">
                    {{ formatDateTime(error.timestamp) }}
                  </div>
                </div>
              </div>
            </n-tab-pane>
          </n-tabs>
        </n-card>
      </div>
    </div>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { 
  NModal, 
  NCard, 
  NStatistic, 
  NIcon, 
  NSpace, 
  NButton, 
  NSwitch, 
  NSelect, 
  NTabs, 
  NTabPane,
  useMessage 
} from 'naive-ui'
import {
  PulseOutline,
  TimeOutline,
  WarningOutline,
  FlashOutline,
  RefreshOutline,
  TrashOutline,
  DownloadOutline,
  DocumentTextOutline,
  EyeOutline
} from '@vicons/ionicons5'
import { apiMonitor, type ApiPerformanceStats, performanceAnalyzer } from '../api/monitor'

interface Props {
  visible: boolean
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'close'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()
const message = useMessage()

// 响应式状态
const stats = ref<ApiPerformanceStats | null>(null)
const realTimeMetrics = ref({
  activeRequests: 0,
  requestsPerMinute: 0,
  averageResponseTime: 0,
  errorRate: 0,
})
const selectedTimeRange = ref(60000) // 1分钟
const autoRefresh = ref(true)
const showDetails = ref(false)

// 时间范围选项
const timeRangeOptions = [
  { label: '最近1分钟', value: 60000 },
  { label: '最近5分钟', value: 300000 },
  { label: '最近15分钟', value: 900000 },
  { label: '最近1小时', value: 3600000 },
  { label: '全部时间', value: 0 },
]

// 计算属性
const visible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

// 方法
const refreshStats = () => {
  try {
    const newStats = apiMonitor.getPerformanceStats(selectedTimeRange.value)
    const newRealTimeMetrics = apiMonitor.getRealTimeMetrics()
    stats.value = newStats
    realTimeMetrics.value = newRealTimeMetrics
  } catch (error) {
    console.error('刷新统计数据失败:', error)
    message.error('刷新统计数据失败')
  }
}

const handleClose = () => {
  emit('close')
}

const handleClearMetrics = () => {
  try {
    apiMonitor.clearMetrics()
    refreshStats()
    message.success('监控数据已清除')
  } catch (error) {
    console.error('清除监控数据失败:', error)
    message.error('清除监控数据失败')
  }
}

const handleExportMetrics = () => {
  try {
    const metrics = apiMonitor.exportMetrics()
    const blob = new Blob([JSON.stringify(metrics, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `api-metrics-${new Date().toISOString()}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    message.success('监控数据已导出')
  } catch (error) {
    console.error('导出监控数据失败:', error)
    message.error('导出监控数据失败')
  }
}

const handleGenerateReport = () => {
  try {
    const report = performanceAnalyzer.generateReport()
    const blob = new Blob([report], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `api-performance-report-${new Date().toISOString()}.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    message.success('性能报告已生成')
  } catch (error) {
    console.error('生成性能报告失败:', error)
    message.error('生成性能报告失败')
  }
}

// 样式辅助函数
const getResponseTimeColor = (time: number) => {
  if (time <= 500) return '#52c41a'
  if (time <= 1000) return '#faad14'
  return '#ff4d4f'
}

const getResponseTimeStyle = (time: number) => {
  return { color: getResponseTimeColor(time) }
}

const getErrorRateColor = (rate: number) => {
  if (rate <= 1) return '#52c41a'
  if (rate <= 5) return '#faad14'
  return '#ff4d4f'
}

const getErrorRateStyle = (rate: number) => {
  return { color: getErrorRateColor(rate) }
}

const getSuccessRateStyle = (rate: number) => {
  if (rate >= 99) return { color: '#52c41a' }
  if (rate >= 95) return { color: '#faad14' }
  return { color: '#ff4d4f' }
}

// 时间格式化
const formatTime = (timestamp: number) => {
  return new Date(timestamp).toLocaleTimeString()
}

const formatDateTime = (timestamp: number) => {
  return new Date(timestamp).toLocaleString()
}

// 定时器
let refreshInterval: number | null = null

// 监听器
watch(() => props.visible, (newValue) => {
  if (newValue) {
    refreshStats()
    if (autoRefresh.value) {
      refreshInterval = window.setInterval(refreshStats, 1000)
    }
  } else {
    if (refreshInterval) {
      clearInterval(refreshInterval)
      refreshInterval = null
    }
  }
})

watch(autoRefresh, (newValue) => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
  
  if (newValue && props.visible) {
    refreshInterval = window.setInterval(refreshStats, 1000)
  }
})

watch(selectedTimeRange, () => {
  refreshStats()
})

// 生命周期
onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>

<style scoped>
.api-monitor-modal {
  --n-color: #ffffff;
}

.monitor-content {
  height: calc(80vh - 120px);
  overflow-y: auto;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.metric-card {
  text-align: center;
}

.actions-bar {
  margin-bottom: 24px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-label {
  color: #666;
  font-size: 14px;
}

.stat-value {
  font-weight: 600;
  font-size: 14px;
}

.endpoint-list {
  max-height: 200px;
  overflow-y: auto;
}

.endpoint-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.endpoint-item:last-child {
  border-bottom: none;
}

.endpoint-url {
  flex: 1;
  font-size: 12px;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 8px;
}

.endpoint-time {
  font-weight: 600;
  font-size: 12px;
}

.error-stats {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.error-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.error-type {
  font-size: 14px;
  color: #666;
}

.error-count {
  font-weight: 600;
  font-size: 14px;
  color: #ff4d4f;
}

.recent-errors {
  max-height: 200px;
  overflow-y: auto;
}

.error-record {
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.error-record:last-child {
  border-bottom: none;
}

.error-url {
  font-weight: 600;
  font-size: 12px;
  color: #ff4d4f;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 4px;
}

.error-message {
  font-size: 12px;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 4px;
}

.error-time {
  font-size: 11px;
  color: #999;
}

.details-section {
  margin-top: 24px;
}

.endpoints-detail,
.errors-detail {
  max-height: 300px;
  overflow-y: auto;
}

.endpoint-detail-item,
.error-detail-item {
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.endpoint-detail-item:last-child,
.error-detail-item:last-child {
  border-bottom: none;
}

.endpoint-detail-url,
.error-detail-url {
  font-weight: 600;
  font-size: 13px;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 4px;
}

.endpoint-detail-stats {
  display: flex;
  gap: 16px;
}

.endpoint-detail-time {
  font-weight: 600;
  font-size: 12px;
}

.endpoint-detail-count {
  font-size: 12px;
  color: #666;
}

.error-detail-message {
  font-size: 12px;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 4px;
}

.error-detail-time {
  font-size: 11px;
  color: #999;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .actions-bar {
    padding: 12px;
  }
}
</style>