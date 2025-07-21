<template>
  <!-- 状态指示器（当工具栏隐藏时显示） -->
  <div 
    v-if="enabled && !isVisible"
    class="dev-tools-indicator"
    @click="toggleVisibility"
    :title="`点击打开开发工具 (Ctrl+Shift+D)`"
  >
    <div class="indicator-circle">
      <span class="status-emoji">{{ statusIndicator }}</span>
    </div>
  </div>

  <!-- 浮动工具栏 -->
  <div v-if="enabled && isVisible" class="dev-tools-panel">
    <div class="panel-content">
      <div class="panel-header">
        <h3 class="panel-title">开发工具</h3>
        <n-button quaternary circle @click="toggleVisibility">
          <template #icon>
            <n-icon><CloseOutline /></n-icon>
          </template>
        </n-button>
      </div>

      <!-- 实时状态 -->
      <div class="status-section">
        <div class="status-header">
          <span class="status-label">API状态</span>
          <span class="status-indicator-large">{{ statusIndicator }}</span>
        </div>
        <div class="metrics-grid">
          <div class="metric-item">
            <div class="metric-label">请求/分钟</div>
            <div class="metric-value">{{ realTimeStats.requestsPerMinute }}</div>
          </div>
          <div class="metric-item">
            <div class="metric-label">平均响应</div>
            <div class="metric-value">{{ realTimeStats.averageResponseTime.toFixed(0) }}ms</div>
          </div>
          <div class="metric-item">
            <div class="metric-label">错误率</div>
            <div class="metric-value">{{ realTimeStats.errorRate.toFixed(1) }}%</div>
          </div>
        </div>
      </div>

      <!-- 工具按钮 -->
      <div class="tools-section">
        <n-button 
          type="primary" 
          block 
          @click="showMonitorPanel = true"
          class="tool-button"
        >
          <template #icon>
            <n-icon><BarChartOutline /></n-icon>
          </template>
          API监控面板
        </n-button>
        
        <n-button 
          type="info" 
          block 
          @click="toggleMonitoring"
          class="tool-button"
        >
          <template #icon>
            <n-icon><SearchOutline /></n-icon>
          </template>
          切换API监控
        </n-button>
        
        <n-button 
          type="warning" 
          block 
          @click="clearCache"
          class="tool-button"
        >
          <template #icon>
            <n-icon><TrashOutline /></n-icon>
          </template>
          清除缓存
        </n-button>
        
        <n-button 
          type="success" 
          block 
          @click="reloadApp"
          class="tool-button"
        >
          <template #icon>
            <n-icon><RefreshOutline /></n-icon>
          </template>
          重新加载
        </n-button>
        
        <div class="shortcuts-info">
          <div class="shortcuts-title">快捷键:</div>
          <div class="shortcut-item">• Ctrl+Shift+D: 切换工具栏</div>
          <div class="shortcut-item">• Escape: 关闭面板</div>
        </div>
      </div>
    </div>
  </div>

  <!-- API监控面板 -->
  <ApiMonitorPanel 
    v-model:visible="showMonitorPanel"
    @close="showMonitorPanel = false"
  />
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { NButton, NIcon, useMessage } from 'naive-ui'
import { 
  CloseOutline, 
  BarChartOutline, 
  SearchOutline, 
  TrashOutline, 
  RefreshOutline 
} from '@vicons/ionicons5'
import ApiMonitorPanel from './ApiMonitorPanel.vue'
import { apiMonitor } from '../api/monitor'

interface DevToolsProps {
  enabled?: boolean
}

const props = withDefaults(defineProps<DevToolsProps>(), {
  enabled: import.meta.env.DEV // 开发环境默认启用
})

const message = useMessage()

// 响应式状态
const isVisible = ref(false)
const showMonitorPanel = ref(false)
const realTimeStats = ref({
  requestsPerMinute: 0,
  averageResponseTime: 0,
  errorRate: 0,
})

// 计算属性
const statusIndicator = computed(() => {
  if (realTimeStats.value.errorRate > 5) return '🔴'
  if (realTimeStats.value.averageResponseTime > 1000) return '🟡'
  return '🟢'
})

// 方法
const toggleVisibility = () => {
  isVisible.value = !isVisible.value
}

const updateStats = () => {
  if (!props.enabled || !isVisible.value) return
  
  try {
    const metrics = apiMonitor.getRealTimeMetrics()
    realTimeStats.value = metrics
  } catch (error) {
    console.warn('获取API监控数据失败:', error)
  }
}

const clearCache = async () => {
  try {
    // 清除所有缓存
    if ('caches' in window) {
      const names = await caches.keys()
      await Promise.all(names.map(name => caches.delete(name)))
    }
    
    // 清除localStorage中的缓存
    Object.keys(localStorage).forEach(key => {
      if (key.startsWith('api_cache_')) {
        localStorage.removeItem(key)
      }
    })
    
    message.success('缓存已清除')
  } catch (error) {
    message.error('清除缓存失败')
    console.error('清除缓存失败:', error)
  }
}

const reloadApp = () => {
  window.location.reload()
}

const toggleMonitoring = () => {
  try {
    const config = apiMonitor.getConfig()
    const isEnabled = config.enabled
    apiMonitor.setEnabled(!isEnabled)
    message.success(`API监控已${!isEnabled ? '启用' : '禁用'}`)
  } catch (error) {
    message.error('切换监控状态失败')
    console.error('切换监控状态失败:', error)
  }
}

// 键盘事件处理
const handleKeyDown = (event: KeyboardEvent) => {
  if (!props.enabled) return
  
  if (event.ctrlKey && event.shiftKey && event.key === 'D') {
    event.preventDefault()
    toggleVisibility()
  }
  
  if (event.key === 'Escape') {
    isVisible.value = false
    showMonitorPanel.value = false
  }
}

// 定时器
let statsInterval: number | null = null

// 生命周期
onMounted(() => {
  if (!props.enabled) return
  
  document.addEventListener('keydown', handleKeyDown)
  
  // 启动统计更新
  statsInterval = window.setInterval(updateStats, 1000)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyDown)
  
  if (statsInterval) {
    clearInterval(statsInterval)
  }
})

// 监听可见性变化
watch(isVisible, (newValue) => {
  if (newValue) {
    updateStats()
  }
})
</script>

<style scoped>
.dev-tools-indicator {
  position: fixed;
  bottom: 16px;
  right: 16px;
  z-index: 1000;
  cursor: pointer;
}

.indicator-circle {
  width: 48px;
  height: 48px;
  background: rgba(0, 0, 0, 0.8);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
}

.indicator-circle:hover {
  background: rgba(0, 0, 0, 0.9);
  transform: scale(1.1);
}

.status-emoji {
  font-size: 18px;
}

.dev-tools-panel {
  position: fixed;
  bottom: 16px;
  right: 16px;
  z-index: 1001;
  width: 320px;
}

.panel-content {
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  border: 1px solid #e0e0e0;
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
}

.panel-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.status-section {
  padding: 16px;
  background: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.status-label {
  font-size: 14px;
  font-weight: 500;
  color: #666;
}

.status-indicator-large {
  font-size: 20px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.metric-item {
  text-align: center;
}

.metric-label {
  font-size: 11px;
  color: #888;
  margin-bottom: 2px;
}

.metric-value {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.tools-section {
  padding: 16px;
}

.tool-button {
  margin-bottom: 8px;
}

.tool-button:last-of-type {
  margin-bottom: 16px;
}

.shortcuts-info {
  padding-top: 12px;
  border-top: 1px solid #e0e0e0;
}

.shortcuts-title {
  font-size: 12px;
  font-weight: 500;
  color: #666;
  margin-bottom: 4px;
}

.shortcut-item {
  font-size: 11px;
  color: #888;
  margin-bottom: 2px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .dev-tools-panel {
    width: calc(100vw - 32px);
    max-width: 320px;
  }
}

/* 深色模式支持 */
@media (prefers-color-scheme: dark) {
  .panel-content {
    background: #1a1a1a;
    border-color: #333;
  }
  
  .panel-header,
  .status-section {
    background: #2a2a2a;
    border-color: #333;
  }
  
  .panel-title,
  .metric-value {
    color: #fff;
  }
  
  .status-label,
  .shortcuts-title {
    color: #ccc;
  }
  
  .metric-label,
  .shortcut-item {
    color: #999;
  }
  
  .shortcuts-info {
    border-color: #333;
  }
}
</style>