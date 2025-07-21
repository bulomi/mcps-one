<template>
  <div class="mcp-proxy-view">
    <n-card title="MCP代理服务器管理" :bordered="false">
      <template #header-extra>
        <n-space>
          <n-tag :type="statusTagType" size="small">
            <template #icon>
              <n-icon><server-outline /></n-icon>
            </template>
            {{ statusText }}
          </n-tag>
          <n-button
            :type="proxyStatus?.running ? 'error' : 'primary'"
            :loading="actionLoading"
            @click="toggleProxyServer"
          >
            {{ proxyStatus?.running ? '停止服务器' : '启动服务器' }}
          </n-button>
          <n-button @click="refreshData" :loading="loading">
            <template #icon>
              <n-icon><refresh-outline /></n-icon>
            </template>
            刷新
          </n-button>
        </n-space>
      </template>

      <!-- 服务器状态概览 -->
      <n-grid :cols="4" :x-gap="16" :y-gap="16" class="mb-6">
        <n-grid-item>
          <n-statistic label="运行时间" :value="uptimeText" />
        </n-grid-item>
        <n-grid-item>
          <n-statistic label="总请求数" :value="proxyStatus?.request_count || 0" />
        </n-grid-item>
        <n-grid-item>
          <n-statistic label="错误数" :value="proxyStatus?.error_count || 0" />
        </n-grid-item>
        <n-grid-item>
          <n-statistic label="活跃请求" :value="proxyStatus?.active_requests || 0" />
        </n-grid-item>
      </n-grid>

      <!-- 标签页 -->
      <n-tabs v-model:value="activeTab" type="line">
        <!-- 工具管理 -->
        <n-tab-pane name="tools" tab="工具管理">
          <div class="tools-section">
            <div class="tools-header mb-4">
              <n-space justify="space-between">
                <n-input
                  v-model:value="toolSearchText"
                  placeholder="搜索工具..."
                  clearable
                  style="width: 300px"
                >
                  <template #prefix>
                    <n-icon><search-outline /></n-icon>
                  </template>
                </n-input>
                <n-space>
                  <n-button @click="discoverTools" :loading="discoverLoading">
                    <template #icon>
                      <n-icon><scan-outline /></n-icon>
                    </template>
                    发现工具
                  </n-button>
                  <n-button @click="reloadConfig" :loading="reloadLoading">
                    <template #icon>
                      <n-icon><reload-outline /></n-icon>
                    </template>
                    重新加载配置
                  </n-button>
                </n-space>
              </n-space>
            </div>

            <n-data-table
              :columns="toolColumns"
              :data="filteredTools"
              :loading="toolsLoading"
              :pagination="false"
              :row-key="(row) => row.name"
            />
          </div>
        </n-tab-pane>

        <!-- 性能监控 -->
        <n-tab-pane name="metrics" tab="性能监控">
          <div class="metrics-section">
            <n-grid :cols="2" :x-gap="16" :y-gap="16">
              <n-grid-item>
                <n-card title="请求指标" size="small">
                  <n-descriptions :column="1" size="small">
                    <n-descriptions-item label="总请求数">
                      {{ metrics?.request_metrics?.total_requests || 0 }}
                    </n-descriptions-item>
                    <n-descriptions-item label="总错误数">
                      {{ metrics?.request_metrics?.total_errors || 0 }}
                    </n-descriptions-item>
                    <n-descriptions-item label="错误率">
                      {{ metrics?.request_metrics?.error_rate || 0 }}%
                    </n-descriptions-item>
                    <n-descriptions-item label="活跃请求">
                      {{ metrics?.request_metrics?.active_requests || 0 }}
                    </n-descriptions-item>
                  </n-descriptions>
                </n-card>
              </n-grid-item>
              <n-grid-item>
                <n-card title="工具配置" size="small">
                  <n-descriptions :column="1" size="small">
                    <n-descriptions-item label="最大并发工具">
                      {{ metrics?.tool_metrics?.max_concurrent_tools || 0 }}
                    </n-descriptions-item>
                    <n-descriptions-item label="工具超时时间">
                      {{ metrics?.tool_metrics?.tool_timeout || 0 }}秒
                    </n-descriptions-item>
                  </n-descriptions>
                </n-card>
              </n-grid-item>
              <n-grid-item>
                <n-card title="缓存状态" size="small">
                  <n-descriptions :column="1" size="small">
                    <n-descriptions-item label="缓存启用">
                      <n-tag :type="metrics?.cache_metrics?.cache_enabled ? 'success' : 'default'" size="small">
                        {{ metrics?.cache_metrics?.cache_enabled ? '是' : '否' }}
                      </n-tag>
                    </n-descriptions-item>
                    <n-descriptions-item label="缓存TTL">
                      {{ metrics?.cache_metrics?.cache_ttl || 0 }}秒
                    </n-descriptions-item>
                    <n-descriptions-item label="缓存有效">
                      <n-tag :type="metrics?.cache_metrics?.cache_valid ? 'success' : 'warning'" size="small">
                        {{ metrics?.cache_metrics?.cache_valid ? '有效' : '无效' }}
                      </n-tag>
                    </n-descriptions-item>
                  </n-descriptions>
                </n-card>
              </n-grid-item>
              <n-grid-item>
                <n-card title="服务器信息" size="small">
                  <n-descriptions :column="1" size="small">
                    <n-descriptions-item label="服务器名称">
                      {{ metrics?.server_info?.name || 'N/A' }}
                    </n-descriptions-item>
                    <n-descriptions-item label="监听地址">
                      {{ metrics?.server_info?.host }}:{{ metrics?.server_info?.port }}
                    </n-descriptions-item>
                    <n-descriptions-item label="启动时间">
                      {{ formatDateTime(metrics?.server_info?.start_time) }}
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
            <div class="logs-header mb-4">
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
                    <n-icon><document-text-outline /></n-icon>
                  </template>
                  加载日志
                </n-button>
              </n-space>
            </div>

            <n-card size="small">
              <div class="logs-container">
                <div v-if="logs.length === 0" class="text-center py-8">
                  <n-empty description="暂无日志数据" />
                </div>
                <div v-else class="logs-list">
                  <div
                    v-for="(log, index) in logs"
                    :key="index"
                    class="log-entry"
                    :class="`log-${log.level.toLowerCase()}`"
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
import mcpProxyApi from '@/api/mcpProxy';
import type {
  MCPProxyStatus, ToolInfo, ProxyMetrics, LogEntry, ToolDiscoveryResult
} from '@/api/mcpProxy';
import { formatDateTime } from '@/utils/format';
import { logLevelOptions } from '@/constants/logLevels';

// 响应式数据
const message = useMessage();
const dialog = useDialog();
const loading = ref(false);
const actionLoading = ref(false);
const toolsLoading = ref(false);
const discoverLoading = ref(false);
const reloadLoading = ref(false);
const logsLoading = ref(false);

const activeTab = ref('tools');
const proxyStatus = ref<MCPProxyStatus | null>(null);
const tools = ref<ToolInfo[]>([]);
const metrics = ref<ProxyMetrics | null>(null);
const logs = ref<LogEntry[]>([]);

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
  return proxyStatus.value.running ? '运行中' : '已停止';
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

// 日志级别选项（使用统一常量）
// const logLevelOptions 已从 '@/constants/logLevels' 导入

// 工具表格列定义
const toolColumns: DataTableColumns<ToolInfo> = [
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
    title: '描述',
    key: 'description',
    ellipsis: {
      tooltip: true
    }
  },
  {
    title: '运行时间',
    key: 'uptime',
    render: (row) => {
      if (!row.status.uptime) return '-';
      const uptime = row.status.uptime;
      const hours = Math.floor(uptime / 3600);
      const minutes = Math.floor((uptime % 3600) / 60);
      return `${hours}时${minutes}分`;
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
    const response = await mcpProxyApi.getStatus();
    proxyStatus.value = response.data;
  } catch (error) {
    console.error('加载代理状态失败:', error);
  }
};

const loadTools = async () => {
  toolsLoading.value = true;
  try {
    const response = await mcpProxyApi.getTools();
    tools.value = response.data;
  } catch (error) {
    console.error('加载工具列表失败:', error);
    message.error('加载工具列表失败');
  } finally {
    toolsLoading.value = false;
  }
};

const loadMetrics = async () => {
  try {
    const response = await mcpProxyApi.getMetrics();
    metrics.value = response.data;
  } catch (error) {
    console.error('加载性能指标失败:', error);
  }
};

const loadLogs = async () => {
  logsLoading.value = true;
  try {
    const response = await mcpProxyApi.getLogs({
      level: logLevel.value || undefined,
      limit: logLimit.value
    });
    logs.value = response.data;
  } catch (error) {
    console.error('加载日志失败:', error);
    message.error('加载日志失败');
  } finally {
    logsLoading.value = false;
  }
};

const toggleProxyServer = async () => {
  actionLoading.value = true;
  try {
    if (proxyStatus.value?.running) {
      await mcpProxyApi.stop();
      message.success('代理服务器已停止');
    } else {
      await mcpProxyApi.start();
      message.success('代理服务器已启动');
    }
    await loadProxyStatus();
  } catch (error) {
    console.error('切换代理服务器状态失败:', error);
    message.error('操作失败');
  } finally {
    actionLoading.value = false;
  }
};

const toggleTool = async (toolName: string, currentStatus: string) => {
  try {
    if (currentStatus === 'running') {
      await mcpProxyApi.stopTool(toolName);
      message.success(`工具 ${toolName} 已停止`);
    } else {
      await mcpProxyApi.startTool(toolName);
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
    await mcpProxyApi.restartTool(toolName);
    message.success(`工具 ${toolName} 已重启`);
    await loadTools();
  } catch (error) {
    console.error('重启工具失败:', error);
    message.error('重启失败');
  }
};

const discoverTools = async () => {
  discoverLoading.value = true;
  try {
    const response = await mcpProxyApi.discoverTools();
    const result: ToolDiscoveryResult = response.data;
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
    await mcpProxyApi.reloadConfig();
    message.success('配置已重新加载');
    await refreshData();
  } catch (error) {
    console.error('重新加载配置失败:', error);
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

// 生命周期
onMounted(() => {
  refreshData();
  loadLogs();
});
</script>

<style scoped>
.mcp-proxy-view {
  padding: 16px;
}

.tools-section {
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