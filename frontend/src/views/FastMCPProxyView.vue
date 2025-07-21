<template>
  <div class="fastmcp-proxy-view">
    <n-card title="FastMCP 代理服务器管理" :bordered="false">
      <!-- 服务器状态概览 -->
      <div class="mb-4">
        <n-space justify="space-between" align="center">
          <n-space align="center">
            <n-tag :type="statusTagType" size="large">
              <template #icon>
                <n-icon><ServerOutline /></n-icon>
              </template>
              {{ statusText }}
            </n-tag>
            <span v-if="proxyStatus" class="text-gray-600">
              运行时间: {{ uptimeText }}
            </span>
          </n-space>
          <n-space>
            <n-button
              :type="proxyStatus?.running ? 'error' : 'primary'"
              :loading="actionLoading"
              @click="toggleProxyServer"
            >
              <template #icon>
                <n-icon><ServerOutline /></n-icon>
              </template>
              {{ proxyStatus?.running ? '停止服务器' : '启动服务器' }}
            </n-button>
            <n-button @click="refreshData" :loading="loading">
              <template #icon>
                <n-icon><RefreshOutline /></n-icon>
              </template>
              刷新数据
            </n-button>
          </n-space>
        </n-space>
      </div>

      <!-- FastMCP 特性状态 -->
      <div class="mb-4" v-if="proxyStatus">
        <n-grid :cols="4" :x-gap="12">
          <n-grid-item>
            <n-statistic label="会话隔离" :value="proxyStatus.session_isolation_enabled ? '启用' : '禁用'">
              <template #suffix>
                <n-tag :type="proxyStatus.session_isolation_enabled ? 'success' : 'default'" size="small">
                  {{ proxyStatus.session_isolation_enabled ? '✓' : '✗' }}
                </n-tag>
              </template>
            </n-statistic>
          </n-grid-item>
          <n-grid-item>
            <n-statistic label="并发安全" :value="proxyStatus.concurrent_safety_enabled ? '启用' : '禁用'">
              <template #suffix>
                <n-tag :type="proxyStatus.concurrent_safety_enabled ? 'success' : 'default'" size="small">
                  {{ proxyStatus.concurrent_safety_enabled ? '✓' : '✗' }}
                </n-tag>
              </template>
            </n-statistic>
          </n-grid-item>
          <n-grid-item>
            <n-statistic label="传输桥接" :value="proxyStatus.transport_bridge_enabled ? '启用' : '禁用'">
              <template #suffix>
                <n-tag :type="proxyStatus.transport_bridge_enabled ? 'success' : 'default'" size="small">
                  {{ proxyStatus.transport_bridge_enabled ? '✓' : '✗' }}
                </n-tag>
              </template>
            </n-statistic>
          </n-grid-item>
          <n-grid-item>
            <n-statistic label="活跃会话" :value="proxyStatus.active_sessions">
              <template #suffix>
                <span class="text-blue-500">个</span>
              </template>
            </n-statistic>
          </n-grid-item>
        </n-grid>
      </div>

      <!-- 主要内容标签页 -->
      <n-tabs v-model:value="activeTab" type="line">
        <!-- 工具管理 -->
        <n-tab-pane name="tools" tab="工具管理">
          <div class="tools-section">
            <!-- 工具操作栏 -->
            <div class="mb-4">
              <n-space justify="space-between">
                <n-space>
                  <n-input
                    v-model:value="toolSearchText"
                    placeholder="搜索工具..."
                    clearable
                    style="width: 300px"
                  >
                    <template #prefix>
                      <n-icon><SearchOutline /></n-icon>
                    </template>
                  </n-input>
                </n-space>
                <n-space>
                  <n-button @click="discoverTools" :loading="discoverLoading">
                    <template #icon>
                      <n-icon><ScanOutline /></n-icon>
                    </template>
                    发现工具
                  </n-button>
                  <n-button @click="reloadConfig" :loading="reloadLoading">
                    <template #icon>
                      <n-icon><ReloadOutline /></n-icon>
                    </template>
                    重载配置
                  </n-button>
                </n-space>
              </n-space>
            </div>

            <!-- 工具列表 -->
            <n-data-table
              :columns="toolColumns"
              :data="filteredTools"
              :loading="toolsLoading"
              :pagination="false"
              :bordered="false"
            />
          </div>
        </n-tab-pane>

        <!-- 会话管理 (FastMCP特有) -->
        <n-tab-pane name="sessions" tab="会话管理">
          <div class="sessions-section">
            <div class="mb-4">
              <n-space justify="space-between">
                <n-statistic label="总会话数" :value="sessions.length" />
                <n-button @click="loadSessions" :loading="sessionsLoading">
                  <template #icon>
                    <n-icon><RefreshOutline /></n-icon>
                  </template>
                  刷新会话
                </n-button>
              </n-space>
            </div>

            <n-data-table
              :columns="sessionColumns"
              :data="sessions"
              :loading="sessionsLoading"
              :pagination="false"
              :bordered="false"
            />
          </div>
        </n-tab-pane>

        <!-- 性能监控 -->
        <n-tab-pane name="metrics" tab="性能监控">
          <div class="metrics-section">
            <n-grid :cols="2" :x-gap="16" :y-gap="16" v-if="metrics">
              <!-- 请求指标 -->
              <n-grid-item>
                <n-card title="请求指标" size="small">
                  <n-descriptions :column="2" size="small">
                    <n-descriptions-item label="总请求数">
                      {{ metrics.request_metrics.total_requests }}
                    </n-descriptions-item>
                    <n-descriptions-item label="错误数">
                      {{ metrics.request_metrics.total_errors }}
                    </n-descriptions-item>
                    <n-descriptions-item label="错误率">
                      {{ metrics.request_metrics.error_rate.toFixed(2) }}%
                    </n-descriptions-item>
                    <n-descriptions-item label="活跃请求">
                      {{ metrics.request_metrics.active_requests }}
                    </n-descriptions-item>
                    <n-descriptions-item label="请求/秒">
                      {{ metrics.request_metrics.requests_per_second }}
                    </n-descriptions-item>
                  </n-descriptions>
                </n-card>
              </n-grid-item>

              <!-- 会话指标 (FastMCP特有) -->
              <n-grid-item>
                <n-card title="会话指标" size="small">
                  <n-descriptions :column="2" size="small">
                    <n-descriptions-item label="总会话数">
                      {{ metrics.session_metrics.total_sessions }}
                    </n-descriptions-item>
                    <n-descriptions-item label="活跃会话">
                      {{ metrics.session_metrics.active_sessions }}
                    </n-descriptions-item>
                    <n-descriptions-item label="平均会话时长">
                      {{ metrics.session_metrics.avg_session_duration }}秒
                    </n-descriptions-item>
                    <n-descriptions-item label="会话隔离">
                      <n-tag :type="metrics.session_metrics.session_isolation_enabled ? 'success' : 'default'" size="small">
                        {{ metrics.session_metrics.session_isolation_enabled ? '启用' : '禁用' }}
                      </n-tag>
                    </n-descriptions-item>
                  </n-descriptions>
                </n-card>
              </n-grid-item>

              <!-- 性能指标 (FastMCP特有) -->
              <n-grid-item>
                <n-card title="性能指标" size="small">
                  <n-descriptions :column="2" size="small">
                    <n-descriptions-item label="平均响应时间">
                      {{ metrics.performance_metrics.avg_response_time }}ms
                    </n-descriptions-item>
                    <n-descriptions-item label="内存使用">
                      {{ formatBytes(metrics.performance_metrics.memory_usage) }}
                    </n-descriptions-item>
                    <n-descriptions-item label="CPU使用率">
                      {{ metrics.performance_metrics.cpu_usage.toFixed(1) }}%
                    </n-descriptions-item>
                    <n-descriptions-item label="并发安全">
                      <n-tag :type="metrics.performance_metrics.concurrent_safety_enabled ? 'success' : 'default'" size="small">
                        {{ metrics.performance_metrics.concurrent_safety_enabled ? '启用' : '禁用' }}
                      </n-tag>
                    </n-descriptions-item>
                    <n-descriptions-item label="传输桥接">
                      <n-tag :type="metrics.performance_metrics.transport_bridge_enabled ? 'success' : 'default'" size="small">
                        {{ metrics.performance_metrics.transport_bridge_enabled ? '启用' : '禁用' }}
                      </n-tag>
                    </n-descriptions-item>
                  </n-descriptions>
                </n-card>
              </n-grid-item>

              <!-- 缓存指标 -->
              <n-grid-item>
                <n-card title="缓存指标" size="small">
                  <n-descriptions :column="2" size="small">
                    <n-descriptions-item label="缓存状态">
                      <n-tag :type="metrics.cache_metrics.cache_enabled ? 'success' : 'default'" size="small">
                        {{ metrics.cache_metrics.cache_enabled ? '启用' : '禁用' }}
                      </n-tag>
                    </n-descriptions-item>
                    <n-descriptions-item label="缓存TTL">
                      {{ metrics.cache_metrics.cache_ttl }}秒
                    </n-descriptions-item>
                    <n-descriptions-item label="缓存有效性">
                      <n-tag :type="metrics.cache_metrics.cache_valid ? 'success' : 'warning'" size="small">
                        {{ metrics.cache_metrics.cache_valid ? '有效' : '无效' }}
                      </n-tag>
                    </n-descriptions-item>
                    <n-descriptions-item label="缓存命中率">
                      {{ metrics.cache_metrics.cache_hit_rate.toFixed(1) }}%
                    </n-descriptions-item>
                  </n-descriptions>
                </n-card>
              </n-grid-item>
            </n-grid>
          </div>
        </n-tab-pane>

        <!-- 日志查看 -->
        <n-tab-pane name="logs" tab="日志查看">
          <div class="logs-section">
            <!-- 日志过滤器 -->
            <div class="mb-4">
              <n-space>
                <n-select
                  v-model:value="logLevel"
                  :options="logLevelOptions"
                  placeholder="选择日志级别"
                  clearable
                  style="width: 150px"
                />
                <n-input-number
                  v-model:value="logLimit"
                  :min="10"
                  :max="1000"
                  :step="10"
                  placeholder="日志条数"
                  style="width: 120px"
                />
                <n-button @click="loadLogs" :loading="logsLoading">
                  <template #icon>
                    <n-icon><DocumentTextOutline /></n-icon>
                  </template>
                  加载日志
                </n-button>
              </n-space>
            </div>

            <!-- 日志列表 -->
            <n-card size="small">
              <div class="logs-container">
                <div class="logs-list" v-if="logs.length > 0">
                  <div
                    v-for="(log, index) in logs"
                    :key="index"
                    :class="[
                      'log-entry',
                      `log-${log.level.toLowerCase()}`
                    ]"
                  >
                    <div class="log-header">
                      <n-tag :type="getLogLevelType(log.level)" size="small">
                        {{ log.level }}
                      </n-tag>
                      <span class="log-time">{{ formatDateTime(log.timestamp) }}</span>
                      <span class="log-source">{{ log.source }}</span>
                    </div>
                    <div class="log-message">{{ log.message }}</div>
                    <div v-if="log.details" class="log-details">
                      <pre>{{ JSON.stringify(log.details, null, 2) }}</pre>
                    </div>
                  </div>
                </div>
                <n-empty v-else description="暂无日志数据" />
              </div>
            </n-card>
          </div>
        </n-tab-pane>
      </n-tabs>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue';
import {
  NCard, NTabs, NTabPane, NButton, NTag, NIcon, NSpace, NGrid, NGridItem,
  NStatistic, NDataTable, NInput, NSelect, NInputNumber, NDescriptions,
  NDescriptionsItem, NEmpty, useMessage, useDialog
} from 'naive-ui';
import {
  ServerOutline, RefreshOutline, SearchOutline, ScanOutline,
  ReloadOutline, DocumentTextOutline
} from '@vicons/ionicons5';
import type { DataTableColumns } from 'naive-ui';
import fastmcpProxyApi from '@/api/fastmcpProxy';
import type {
  FastMCPProxyStatus, FastMCPToolInfo, FastMCPProxyMetrics, FastMCPLogEntry,
  FastMCPToolDiscoveryResult, FastMCPSessionInfo
} from '@/api/fastmcpProxy';
import { formatDateTime, formatDuration, formatBytes, formatNumber, formatStatus, formatLogLevel } from '@/utils/format';
import { logLevelOptions } from '@/constants/logLevels';

// 响应式数据
const message = useMessage();
const dialog = useDialog();
const loading = ref(false);
const actionLoading = ref(false);
const toolsLoading = ref(false);
const sessionsLoading = ref(false);
const discoverLoading = ref(false);
const reloadLoading = ref(false);
const logsLoading = ref(false);

const activeTab = ref('tools');
const proxyStatus = ref<FastMCPProxyStatus | null>(null);
const tools = ref<FastMCPToolInfo[]>([]);
const sessions = ref<FastMCPSessionInfo[]>([]);
const metrics = ref<FastMCPProxyMetrics | null>(null);
const logs = ref<FastMCPLogEntry[]>([]);

// 搜索和过滤
const toolSearchText = ref('');
const logLevel = ref<string | null>(null);
const logLimit = ref(100);

// 计算属性
const statusTagType = computed(() => {
  if (!proxyStatus.value) return 'default';
  return proxyStatus.value.running ? 'success' : 'error';
});

const statusText = computed(() => {
  if (!proxyStatus.value) return '未知';
  return proxyStatus.value.running ? 'FastMCP 运行中' : 'FastMCP 已停止';
});

const uptimeText = computed(() => {
  if (!proxyStatus.value?.uptime) return '0秒';
  const uptime = proxyStatus.value.uptime;
  const hours = Math.floor(uptime / 3600);
  const minutes = Math.floor((uptime % 3600) / 60);
  const seconds = Math.floor(uptime % 60);
  return `${hours}时${minutes}分${seconds}秒`;
});

const filteredTools = computed(() => {
  if (!toolSearchText.value) return tools.value;
  const searchText = toolSearchText.value.toLowerCase();
  return tools.value.filter(tool => 
    tool.name.toLowerCase().includes(searchText) ||
    tool.display_name.toLowerCase().includes(searchText) ||
    (tool.description && tool.description.toLowerCase().includes(searchText))
  );
});



// 工具表格列定义
const toolColumns: DataTableColumns<FastMCPToolInfo> = [
  {
    title: '工具名称',
    key: 'name',
    render: (row) => h('div', [
      h('div', { class: 'font-medium' }, row.display_name),
      h('div', { class: 'text-sm text-gray-500' }, row.name)
    ])
  },
  {
    title: '状态',
    key: 'status',
    render: (row) => {
      const statusMap = {
        running: { type: 'success', text: '运行中' },
        stopped: { type: 'default', text: '已停止' },
        error: { type: 'error', text: '错误' },
        starting: { type: 'warning', text: '启动中' },
        stopping: { type: 'warning', text: '停止中' }
      };
      const status = statusMap[row.status.status] || { type: 'default', text: '未知' };
      return h(NTag, { type: status.type, size: 'small' }, () => status.text);
    }
  },
  {
    title: '会话数',
    key: 'session_count',
    render: (row) => h('div', [
      h('div', { class: 'font-medium' }, row.session_count.toString()),
      h('div', { class: 'text-sm text-gray-500' }, `活跃: ${row.session_metrics.active_sessions}`)
    ])
  },
  {
    title: '性能',
    key: 'performance',
    render: (row) => h('div', [
      h('div', { class: 'text-sm' }, `响应: ${row.performance_metrics.avg_response_time}ms`),
      h('div', { class: 'text-sm text-gray-500' }, `成功率: ${row.performance_metrics.success_rate.toFixed(1)}%`)
    ])
  },
  {
    title: '描述',
    key: 'description',
    ellipsis: {
      tooltip: true
    }
  },
  {
    title: '操作',
    key: 'actions',
    render: (row) => h(NSpace, { size: 'small' }, () => [
      h(NButton, {
        size: 'small',
        type: row.status.status === 'running' ? 'error' : 'primary',
        onClick: () => toggleTool(row.name, row.status.status)
      }, () => row.status.status === 'running' ? '停止' : '启动'),
      h(NButton, {
        size: 'small',
        onClick: () => restartTool(row.name)
      }, () => '重启')
    ])
  }
];

// 会话表格列定义
const sessionColumns: DataTableColumns<FastMCPSessionInfo> = [
  {
    title: '会话ID',
    key: 'session_id',
    ellipsis: {
      tooltip: true
    }
  },
  {
    title: '工具名称',
    key: 'tool_name'
  },
  {
    title: '状态',
    key: 'status',
    render: (row) => {
      const statusMap = {
        active: { type: 'success', text: '活跃' },
        idle: { type: 'warning', text: '空闲' },
        terminated: { type: 'default', text: '已终止' }
      };
      const status = statusMap[row.status] || { type: 'default', text: '未知' };
      return h(NTag, { type: status.type, size: 'small' }, () => status.text);
    }
  },
  {
    title: '开始时间',
    key: 'start_time',
    render: (row) => formatDateTime(row.start_time)
  },
  {
    title: '最后活动',
    key: 'last_activity',
    render: (row) => formatDateTime(row.last_activity)
  },
  {
    title: '请求数',
    key: 'request_count'
  },
  {
    title: '操作',
    key: 'actions',
    render: (row) => h(NButton, {
      size: 'small',
      type: 'error',
      onClick: () => terminateSession(row.session_id)
    }, () => '终止')
  }
];

// 方法
const refreshData = async () => {
  loading.value = true;
  try {
    await Promise.all([
      loadProxyStatus(),
      loadTools(),
      loadMetrics()
    ]);
  } finally {
    loading.value = false;
  }
};

const loadProxyStatus = async () => {
  try {
    const response = await fastmcpProxyApi.getStatus();
    proxyStatus.value = response.data;
  } catch (error) {
    console.error('加载FastMCP代理状态失败:', error);
  }
};

const loadTools = async () => {
  toolsLoading.value = true;
  try {
    const response = await fastmcpProxyApi.getTools();
    tools.value = response.data.tools;
  } catch (error) {
    console.error('加载FastMCP工具列表失败:', error);
    message.error('加载工具列表失败');
  } finally {
    toolsLoading.value = false;
  }
};

const loadSessions = async () => {
  sessionsLoading.value = true;
  try {
    const response = await fastmcpProxyApi.getSessions();
    sessions.value = response.data.sessions;
  } catch (error) {
    console.error('加载FastMCP会话列表失败:', error);
    message.error('加载会话列表失败');
  } finally {
    sessionsLoading.value = false;
  }
};

const loadMetrics = async () => {
  try {
    const response = await fastmcpProxyApi.getMetrics();
    metrics.value = response.data;
  } catch (error) {
    console.error('加载FastMCP性能指标失败:', error);
  }
};

const loadLogs = async () => {
  logsLoading.value = true;
  try {
    const response = await fastmcpProxyApi.getLogs({
      level: logLevel.value || undefined,
      limit: logLimit.value
    });
    logs.value = response.data.logs;
  } catch (error) {
    console.error('加载FastMCP日志失败:', error);
    message.error('加载日志失败');
  } finally {
    logsLoading.value = false;
  }
};

const toggleProxyServer = async () => {
  actionLoading.value = true;
  try {
    if (proxyStatus.value?.running) {
      await fastmcpProxyApi.stop();
      message.success('FastMCP代理服务器已停止');
    } else {
      await fastmcpProxyApi.start();
      message.success('FastMCP代理服务器已启动');
    }
    await loadProxyStatus();
  } catch (error) {
    console.error('切换FastMCP代理服务器状态失败:', error);
    message.error('操作失败');
  } finally {
    actionLoading.value = false;
  }
};

const toggleTool = async (toolName: string, currentStatus: string) => {
  try {
    if (currentStatus === 'running') {
      await fastmcpProxyApi.stopTool(toolName);
      message.success(`工具 ${toolName} 已停止`);
    } else {
      await fastmcpProxyApi.startTool(toolName);
      message.success(`工具 ${toolName} 已启动`);
    }
    await loadTools();
  } catch (error) {
    console.error('切换工具状态失败:', error);
    message.error('操作失败');
  }
};

const restartTool = async (toolName: string) => {
  try {
    await fastmcpProxyApi.restartTool(toolName);
    message.success(`工具 ${toolName} 已重启`);
    await loadTools();
  } catch (error) {
    console.error('重启工具失败:', error);
    message.error('重启失败');
  }
};

const terminateSession = async (sessionId: string) => {
  try {
    await fastmcpProxyApi.terminateSession(sessionId);
    message.success(`会话 ${sessionId} 已终止`);
    await loadSessions();
  } catch (error) {
    console.error('终止会话失败:', error);
    message.error('终止会话失败');
  }
};

const discoverTools = async () => {
  discoverLoading.value = true;
  try {
    const response = await fastmcpProxyApi.discoverTools();
    const result: FastMCPToolDiscoveryResult = response.data;
    message.success(`发现 ${result.total_found} 个工具`);
    await loadTools();
  } catch (error) {
    console.error('发现工具失败:', error);
    message.error('发现工具失败');
  } finally {
    discoverLoading.value = false;
  }
};

const reloadConfig = async () => {
  reloadLoading.value = true;
  try {
    await fastmcpProxyApi.reloadConfig();
    message.success('FastMCP配置已重新加载');
    await refreshData();
  } catch (error) {
    console.error('重新加载FastMCP配置失败:', error);
    message.error('重新加载配置失败');
  } finally {
    reloadLoading.value = false;
  }
};

const getLogLevelType = (level: string) => {
  const levelMap: Record<string, string> = {
    DEBUG: 'default',
    INFO: 'info',
    WARNING: 'warning',
    ERROR: 'error',
    CRITICAL: 'error'
  };
  return levelMap[level] || 'default';
};

// formatBytes function is now imported from @/utils/format

// 生命周期
onMounted(() => {
  refreshData();
  loadLogs();
  loadSessions();
});
</script>

<style scoped>
.fastmcp-proxy-view {
  padding: 16px;
}

.tools-section {
  min-height: 400px;
}

.sessions-section {
  min-height: 400px;
}

.metrics-section {
  min-height: 400px;
}

.logs-section {
  min-height: 400px;
}

.logs-container {
  max-height: 500px;
  overflow-y: auto;
}

.logs-list {
  space-y: 8px;
}

.log-entry {
  padding: 12px;
  border-radius: 6px;
  border-left: 4px solid #e5e7eb;
  background-color: #f9fafb;
  margin-bottom: 8px;
}

.log-entry.log-error {
  border-left-color: #ef4444;
  background-color: #fef2f2;
}

.log-entry.log-warning {
  border-left-color: #f59e0b;
  background-color: #fffbeb;
}

.log-entry.log-info {
  border-left-color: #3b82f6;
  background-color: #eff6ff;
}

.log-entry.log-debug {
  border-left-color: #6b7280;
  background-color: #f3f4f6;
}

.log-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  font-size: 12px;
}

.log-time {
  color: #6b7280;
}

.log-source {
  color: #374151;
  font-weight: 500;
}

.log-message {
  font-size: 14px;
  color: #111827;
  margin-bottom: 4px;
}

.log-details {
  font-size: 12px;
  color: #6b7280;
  background-color: #f3f4f6;
  padding: 8px;
  border-radius: 4px;
  overflow-x: auto;
}

.log-details pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>