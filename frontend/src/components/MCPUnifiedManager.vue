<template>
  <div class="mcp-unified-manager">
    <!-- 服务状态卡片 -->
    <div class="status-card">
      <div class="card-header">
        <h3>MCP 统一服务状态</h3>
        <div class="status-indicator" :class="statusClass">
          <div class="status-dot"></div>
          <span>{{ statusText }}</span>
        </div>
      </div>
      
      <div class="status-details" v-if="serviceStatus">
        <div class="detail-row">
          <span class="label">运行模式:</span>
          <span class="value mode-badge" :class="modeClass">{{ modeText }}</span>
        </div>
        <div class="detail-row">
          <span class="label">代理服务:</span>
          <span class="value" :class="serviceStatus.proxy_running ? 'running' : 'stopped'">
            {{ serviceStatus.proxy_running ? '运行中' : '已停止' }}
          </span>
        </div>
        <div class="detail-row">
          <span class="label">MCP服务端:</span>
          <span class="value" :class="serviceStatus.server_running ? 'running' : 'stopped'">
            {{ serviceStatus.server_running ? '运行中' : '已停止' }}
          </span>
        </div>
        <div class="detail-row">
          <span class="label">可用工具:</span>
          <span class="value">{{ serviceStatus.proxy_tools_count }} 个</span>
        </div>
        <div class="detail-row">
          <span class="label">运行时间:</span>
          <span class="value">{{ formatUptime(serviceStatus.uptime) }}</span>
        </div>
      </div>
    </div>

    <!-- 服务控制面板 -->
    <div class="control-panel">
      <div class="card-header">
        <h3>服务控制</h3>
      </div>
      
      <div class="control-buttons">
        <button 
          class="btn btn-primary" 
          @click="startService" 
          :disabled="loading || (serviceStatus && serviceStatus.is_running)"
        >
          <i class="icon-play"></i>
          启动服务
        </button>
        
        <button 
          class="btn btn-danger" 
          @click="stopService" 
          :disabled="loading || (serviceStatus && !serviceStatus.is_running)"
        >
          <i class="icon-stop"></i>
          停止服务
        </button>
        
        <button 
          class="btn btn-secondary" 
          @click="reloadConfig" 
          :disabled="loading"
        >
          <i class="icon-refresh"></i>
          重载配置
        </button>
        
        <button 
          class="btn btn-info" 
          @click="refreshStatus" 
          :disabled="loading"
        >
          <i class="icon-sync"></i>
          刷新状态
        </button>
      </div>
    </div>

    <!-- 模式切换面板 -->
    <div class="mode-panel">
      <div class="card-header">
        <h3>模式切换</h3>
      </div>
      
      <div class="mode-options">
        <div class="mode-option">
          <label class="mode-label">
            <input 
              type="radio" 
              name="mode" 
              value="proxy_only" 
              v-model="selectedMode"
              @change="switchMode"
              :disabled="loading"
            >
            <span class="mode-text">
              <strong>仅代理模式</strong>
              <small>只提供HTTP API代理服务</small>
            </span>
          </label>
        </div>
        
        <div class="mode-option">
          <label class="mode-label">
            <input 
              type="radio" 
              name="mode" 
              value="server_only" 
              v-model="selectedMode"
              @change="switchMode"
              :disabled="loading"
            >
            <span class="mode-text">
              <strong>仅服务端模式</strong>
              <small>只作为MCP服务端供客户端连接</small>
            </span>
          </label>
        </div>
        
        <div class="mode-option">
          <label class="mode-label">
            <input 
              type="radio" 
              name="mode" 
              value="both" 
              v-model="selectedMode"
              @change="switchMode"
              :disabled="loading"
            >
            <span class="mode-text">
              <strong>双模式</strong>
              <small>同时提供代理和服务端功能</small>
            </span>
          </label>
        </div>
        
        <div class="mode-option">
          <label class="mode-label">
            <input 
              type="radio" 
              name="mode" 
              value="fastmcp_proxy" 
              v-model="selectedMode"
              @change="switchMode"
              :disabled="loading"
            >
            <span class="mode-text">
              <strong>FastMCP 代理模式</strong>
              <small>启用基于 FastMCP 2.0 的高性能代理服务器</small>
            </span>
          </label>
        </div>
        
        <div class="mode-option">
          <label class="mode-label">
            <input 
              type="radio" 
              name="mode" 
              value="disabled" 
              v-model="selectedMode"
              @change="switchMode"
              :disabled="loading"
            >
            <span class="mode-text">
              <strong>禁用模式</strong>
              <small>关闭所有MCP服务</small>
            </span>
          </label>
        </div>
      </div>
    </div>

    <!-- 工具列表面板 -->
    <div class="tools-panel">
      <div class="card-header">
        <h3>可用工具</h3>
        <button class="btn btn-sm btn-secondary" @click="refreshTools" :disabled="loading">
          <i class="icon-refresh"></i>
          刷新
        </button>
      </div>
      
      <div class="tools-list" v-if="tools.length > 0">
        <div class="tool-item" v-for="tool in tools" :key="tool.name">
          <div class="tool-info">
            <div class="tool-name">{{ tool.name }}</div>
            <div class="tool-source">来源: {{ tool.source }}</div>
            <div class="tool-description" v-if="tool.description">{{ tool.description }}</div>
          </div>
          <div class="tool-actions">
            <button class="btn btn-sm btn-outline" @click="testTool(tool)" :disabled="loading">
              测试
            </button>
          </div>
        </div>
      </div>
      
      <div class="empty-state" v-else-if="!loading">
        <p>暂无可用工具</p>
      </div>
    </div>

    <!-- 性能指标面板 -->
    <div class="metrics-panel" v-if="metrics">
      <div class="card-header">
        <h3>性能指标</h3>
      </div>
      
      <div class="metrics-grid">
        <div class="metric-item">
          <div class="metric-label">CPU使用率</div>
          <div class="metric-value">{{ metrics.cpu_percent?.toFixed(1) }}%</div>
        </div>
        <div class="metric-item">
          <div class="metric-label">内存使用</div>
          <div class="metric-value">{{ formatBytes(metrics.memory_usage) }}</div>
        </div>
        <div class="metric-item">
          <div class="metric-label">活跃连接</div>
          <div class="metric-value">{{ metrics.active_connections }}</div>
        </div>
        <div class="metric-item">
          <div class="metric-label">请求总数</div>
          <div class="metric-value">{{ metrics.total_requests }}</div>
        </div>
      </div>
    </div>

    <!-- 加载遮罩 -->
    <div class="loading-overlay" v-if="loading">
      <div class="loading-spinner"></div>
      <div class="loading-text">{{ loadingText }}</div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { useMessage } from 'naive-ui'
import {
  getServiceStatus,
  startService,
  stopService,
  switchServiceMode,
  reloadConfig,
  getServiceMetrics,
  getAvailableTools,
  callTool,
  healthCheck
} from '@/api/mcp-unified'

export default {
  name: 'MCPUnifiedManager',
  setup() {
    const message = useMessage()
    const loading = ref(false)
    const loadingText = ref('')
    const serviceStatus = ref(null)
    const tools = ref([])
    const metrics = ref(null)
    const selectedMode = ref('proxy_only')
    const refreshInterval = ref(null)

    // 计算属性
    const statusClass = computed(() => {
      if (!serviceStatus.value) return 'unknown'
      if (serviceStatus.value.is_running) return 'running'
      return 'stopped'
    })

    const statusText = computed(() => {
      if (!serviceStatus.value) return '未知'
      if (serviceStatus.value.is_running) return '运行中'
      return '已停止'
    })

    const modeClass = computed(() => {
      if (!serviceStatus.value) return ''
      return serviceStatus.value.mode.toLowerCase().replace('_', '-')
    })

    const modeText = computed(() => {
      if (!serviceStatus.value) return '未知'
      const modeMap = {
        'proxy_only': '仅代理',
        'server_only': '仅服务端',
        'both': '双模式',
        'fastmcp_proxy': 'FastMCP代理',
        'disabled': '已禁用'
      }
      return modeMap[serviceStatus.value.mode] || serviceStatus.value.mode
    })

    // 获取服务状态
    const getServiceStatusData = async () => {
      try {
        const data = await getServiceStatus()
        serviceStatus.value = data
        selectedMode.value = data.mode
      } catch (error) {
        console.error('获取服务状态失败:', error)
        message.error('获取服务状态失败')
      }
    }

    // 获取工具列表
    const getTools = async () => {
      try {
        const data = await getAvailableTools()
        tools.value = data
      } catch (error) {
        console.error('获取工具列表失败:', error)
        message.error('获取工具列表失败')
      }
    }

    // 获取性能指标
    const getMetrics = async () => {
      try {
        const data = await getServiceMetrics()
        metrics.value = data
      } catch (error) {
        console.error('获取性能指标失败:', error)
      }
    }

    // 启动服务
    const startServiceAction = async () => {
      loading.value = true
      loadingText.value = '正在启动服务...'
      try {
        await startService()
        message.success('服务启动成功')
        await getServiceStatusData()
      } catch (error) {
        console.error('启动服务失败:', error)
        message.error('启动服务失败')
      } finally {
        loading.value = false
      }
    }

    // 停止服务
    const stopServiceAction = async () => {
      loading.value = true
      loadingText.value = '正在停止服务...'
      try {
        await stopService()
        message.success('服务停止成功')
        await getServiceStatusData()
      } catch (error) {
        console.error('停止服务失败:', error)
        message.error('停止服务失败')
      } finally {
        loading.value = false
      }
    }

    // 重载配置
    const reloadConfigAction = async () => {
      loading.value = true
      loadingText.value = '正在重载配置...'
      try {
        await reloadConfig()
        message.success('配置重载成功')
        await getServiceStatusData()
      } catch (error) {
        console.error('重载配置失败:', error)
        message.error('重载配置失败')
      } finally {
        loading.value = false
      }
    }

    // 切换模式
    const switchMode = async () => {
      loading.value = true
      loadingText.value = '正在切换模式...'
      try {
        const enableServer = selectedMode.value === 'server_only' || selectedMode.value === 'both'
        const enableProxy = selectedMode.value === 'proxy_only' || selectedMode.value === 'both'
        
        await switchServiceMode({
          enable_server: enableServer,
          enable_proxy: enableProxy
        })
        
        message.success('模式切换成功')
        await getServiceStatusData()
      } catch (error) {
        console.error('切换模式失败:', error)
        message.error('切换模式失败')
        // 恢复原来的选择
        if (serviceStatus.value) {
          selectedMode.value = serviceStatus.value.mode
        }
      } finally {
        loading.value = false
      }
    }

    // 刷新状态
    const refreshStatus = async () => {
      loading.value = true
      loadingText.value = '正在刷新状态...'
      try {
        await Promise.all([
          getServiceStatusData(),
          getMetrics()
        ])
      } finally {
        loading.value = false
      }
    }

    // 刷新工具列表
    const refreshTools = async () => {
      loading.value = true
      loadingText.value = '正在刷新工具列表...'
      try {
        await getTools()
      } finally {
        loading.value = false
      }
    }

    // 测试工具
    const testTool = async (tool) => {
      try {
        // 这里可以实现工具测试逻辑
        message.info(`测试工具: ${tool.name}`)
      } catch (error) {
        console.error('测试工具失败:', error)
        message.error('测试工具失败')
      }
    }

    // 格式化运行时间
    const formatUptime = (seconds) => {
      if (!seconds) return '0秒'
      
      const hours = Math.floor(seconds / 3600)
      const minutes = Math.floor((seconds % 3600) / 60)
      const secs = Math.floor(seconds % 60)
      
      if (hours > 0) {
        return `${hours}小时${minutes}分钟${secs}秒`
      } else if (minutes > 0) {
        return `${minutes}分钟${secs}秒`
      } else {
        return `${secs}秒`
      }
    }

    // 格式化字节数
    const formatBytes = (bytes) => {
      if (!bytes) return '0 B'
      
      const sizes = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(1024))
      return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`
    }

    // 生命周期
    onMounted(async () => {
      await Promise.all([
        getServiceStatusData(),
        getTools(),
        getMetrics()
      ])
      
      // 设置定时刷新
      refreshInterval.value = setInterval(async () => {
        if (!loading.value) {
          await getServiceStatusData()
          await getMetrics()
        }
      }, 5000)
    })

    onUnmounted(() => {
      if (refreshInterval.value) {
        clearInterval(refreshInterval.value)
      }
    })

    return {
      loading,
      loadingText,
      serviceStatus,
      tools,
      metrics,
      selectedMode,
      statusClass,
      statusText,
      modeClass,
      modeText,
      startService: startServiceAction,
      stopService: stopServiceAction,
      reloadConfig: reloadConfigAction,
      switchMode,
      refreshStatus,
      refreshTools,
      testTool,
      formatUptime,
      formatBytes
    }
  }
}
</script>

<style scoped>
.mcp-unified-manager {
  position: relative;
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.status-card,
.control-panel,
.mode-panel,
.tools-panel,
.metrics-panel {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.card-header h3 {
  margin: 0;
  color: #333;
  font-size: 18px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ccc;
}

.status-indicator.running .status-dot {
  background: #52c41a;
  animation: pulse 2s infinite;
}

.status-indicator.stopped .status-dot {
  background: #ff4d4f;
}

.status-indicator.unknown .status-dot {
  background: #faad14;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}

.status-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-row .label {
  color: #666;
  font-weight: 500;
}

.detail-row .value {
  font-weight: 600;
}

.detail-row .value.running {
  color: #52c41a;
}

.detail-row .value.stopped {
  color: #ff4d4f;
}

.mode-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.mode-badge.proxy-only {
  background: #e6f7ff;
  color: #1890ff;
}

.mode-badge.server-only {
  background: #f6ffed;
  color: #52c41a;
}

.mode-badge.both {
  background: #fff2e8;
  color: #fa8c16;
}

.mode-badge.disabled {
  background: #f5f5f5;
  color: #999;
}

.control-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: #1890ff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #40a9ff;
}

.btn-danger {
  background: #ff4d4f;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #ff7875;
}

.btn-secondary {
  background: #f5f5f5;
  color: #333;
}

.btn-secondary:hover:not(:disabled) {
  background: #e6e6e6;
}

.btn-info {
  background: #13c2c2;
  color: white;
}

.btn-info:hover:not(:disabled) {
  background: #36cfc9;
}

.btn-sm {
  padding: 4px 8px;
  font-size: 12px;
}

.btn-outline {
  background: transparent;
  border: 1px solid #d9d9d9;
  color: #333;
}

.btn-outline:hover:not(:disabled) {
  border-color: #1890ff;
  color: #1890ff;
}

.mode-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
}

.mode-option {
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  padding: 15px;
  transition: all 0.2s;
}

.mode-option:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
}

.mode-label {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  cursor: pointer;
  width: 100%;
}

.mode-label input[type="radio"] {
  margin-top: 2px;
}

.mode-text strong {
  display: block;
  margin-bottom: 4px;
  color: #333;
}

.mode-text small {
  color: #666;
  font-size: 12px;
}

.tools-list {
  max-height: 400px;
  overflow-y: auto;
}

.tool-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  margin-bottom: 8px;
}

.tool-info {
  flex: 1;
}

.tool-name {
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.tool-source {
  font-size: 12px;
  color: #666;
  margin-bottom: 2px;
}

.tool-description {
  font-size: 12px;
  color: #999;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 15px;
}

.metric-item {
  text-align: center;
  padding: 15px;
  background: #fafafa;
  border-radius: 6px;
}

.metric-label {
  font-size: 12px;
  color: #666;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #1890ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  color: #666;
  font-size: 14px;
}

/* 图标样式 */
.icon-play::before { content: '▶'; }
.icon-stop::before { content: '⏹'; }
.icon-refresh::before { content: '🔄'; }
.icon-sync::before { content: '🔄'; }
</style>