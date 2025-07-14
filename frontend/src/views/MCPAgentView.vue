<template>
  <div class="mcp-agent-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1>MCP 代理服务</h1>
          <p>管理和测试 MCP (Model Context Protocol) 代理服务</p>
        </div>
        <div class="header-right">
          <n-space>
            <n-button type="primary" @click="showCreateSessionModal = true">
              <template #icon>
                <n-icon><AddOutline /></n-icon>
              </template>
              创建会话
            </n-button>
            <n-button @click="refreshData">
              <template #icon>
                <n-icon><RefreshOutline /></n-icon>
              </template>
              刷新
            </n-button>
            <n-button @click="checkHealth">
              <template #icon>
                <n-icon><HeartOutline /></n-icon>
              </template>
              健康检查
            </n-button>
          </n-space>
        </div>
      </div>
    </div>

    <!-- 服务状态卡片 -->
    <n-grid :cols="3" :x-gap="16" class="status-grid">
      <n-grid-item>
        <n-card title="服务状态">
          <n-space vertical>
            <n-tag :type="healthStatus.type" size="large">
              {{ healthStatus.text }}
            </n-tag>
            <n-text depth="3">最后检查: {{ healthStatus.lastCheck }}</n-text>
          </n-space>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card title="连接工具">
          <n-space vertical>
            <n-statistic :value="connectedToolsCount" />
            <n-text depth="3">已连接 / {{ totalToolsCount }} 个工具</n-text>
          </n-space>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card title="活跃会话">
          <n-space vertical>
            <n-statistic :value="activeSessionsCount" />
            <n-text depth="3">当前活跃会话数</n-text>
          </n-space>
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 主要内容区域 -->
    <n-tabs v-model:value="activeTab" type="line" class="main-tabs">
      <!-- 工具管理标签页 -->
      <n-tab-pane name="tools" tab="工具管理">
        <n-card>
          <n-data-table
            :columns="toolColumns"
            :data="mcpTools"
            :loading="toolsLoading"
            :row-key="(row: any) => row.id"
          />
        </n-card>
      </n-tab-pane>

      <!-- 工具测试标签页 -->
      <n-tab-pane name="test" tab="工具测试">
        <n-card>
          <n-form ref="testFormRef" :model="testForm" label-placement="left" label-width="auto">
            <n-form-item label="选择工具" path="toolName">
              <n-select
                v-model:value="testForm.toolName"
                placeholder="选择要测试的工具"
                :options="toolOptions"
                @update:value="onToolSelect"
              />
            </n-form-item>
            <n-form-item label="工具方法" path="methodName" v-if="selectedToolCapabilities">
              <n-select
                v-model:value="testForm.methodName"
                placeholder="选择工具方法"
                :options="methodOptions"
              />
            </n-form-item>
            <n-form-item label="参数" path="arguments">
              <n-input
                v-model:value="testForm.arguments"
                type="textarea"
                placeholder="请输入JSON格式的参数"
                :rows="6"
              />
            </n-form-item>
            <n-form-item>
              <n-space>
                <n-button type="primary" @click="callTool" :loading="testLoading">
                  调用工具
                </n-button>
                <n-button @click="clearTestForm">
                  清空
                </n-button>
              </n-space>
            </n-form-item>
          </n-form>

          <!-- 调用结果 -->
          <n-divider>调用结果</n-divider>
          <n-code
            :code="testResult"
            language="json"
            show-line-numbers
            style="max-height: 400px; overflow-y: auto;"
          />
        </n-card>
      </n-tab-pane>

      <!-- 代理会话标签页 -->
      <n-tab-pane name="sessions" tab="代理会话">
        <n-card>
          <n-empty v-if="sessions.length === 0" description="暂无会话">
            <template #extra>
              <n-button size="small" @click="showCreateSessionModal = true">
                创建会话
              </n-button>
            </template>
          </n-empty>
          <n-list v-else>
            <n-list-item v-for="session in sessions" :key="session.session_id">
              <n-card>
                <template #header>
                  <n-space justify="space-between">
                    <span>{{ session.name }}</span>
                    <n-tag :type="session.status === 'active' ? 'success' : 'default'">
                      {{ session.status }}
                    </n-tag>
                  </n-space>
                </template>
                <n-text depth="3">{{ session.description }}</n-text>
                <template #action>
                  <n-space>
                    <n-button size="small" @click="openSessionChat(session)">
                      打开对话
                    </n-button>
                    <n-button size="small" type="error" @click="deleteSession(session.session_id)">
                      删除
                    </n-button>
                  </n-space>
                </template>
              </n-card>
            </n-list-item>
          </n-list>
        </n-card>
      </n-tab-pane>
    </n-tabs>

    <!-- 创建会话模态框 -->
    <n-modal v-model:show="showCreateSessionModal" preset="dialog" title="创建代理会话">
      <n-form
        ref="sessionFormRef"
        :model="sessionForm"
        :rules="sessionFormRules"
        label-placement="left"
        label-width="auto"
      >
        <n-form-item label="会话名称" path="name">
          <n-input v-model:value="sessionForm.name" placeholder="请输入会话名称" />
        </n-form-item>
        <n-form-item label="描述" path="description">
          <n-input
            v-model:value="sessionForm.description"
            type="textarea"
            placeholder="请输入会话描述"
            :rows="3"
          />
        </n-form-item>
        <n-form-item label="代理模式" path="mode">
          <n-select
            v-model:value="sessionForm.config.mode"
            placeholder="选择代理模式"
            :options="modeOptions"
          />
        </n-form-item>
        <n-form-item label="可用工具" path="tools">
          <n-select
            v-model:value="sessionForm.config.tools"
            placeholder="选择可用工具"
            multiple
            :options="toolOptions"
          />
        </n-form-item>
        <n-form-item label="最大迭代次数">
          <n-input-number
            v-model:value="sessionForm.config.max_iterations"
            :min="1"
            :max="100"
            placeholder="默认10次"
          />
        </n-form-item>
        <n-form-item label="超时时间(秒)">
          <n-input-number
            v-model:value="sessionForm.config.timeout"
            :min="10"
            :max="3600"
            placeholder="默认300秒"
          />
        </n-form-item>
      </n-form>
      <template #action>
        <n-space>
          <n-button @click="showCreateSessionModal = false">取消</n-button>
          <n-button type="primary" @click="createSession" :loading="sessionLoading">
            创建
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
  NTabs,
  NTabPane,
  NDataTable,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NSelect,
  NIcon,
  NTag,
  NText,
  NStatistic,
  NModal,
  NList,
  NListItem,
  NEmpty,
  NDivider,
  NCode,
  type DataTableColumns
} from 'naive-ui'
import {
  AddOutline,
  RefreshOutline,
  HeartOutline,
  PlayOutline,
  StopOutline,
  SettingsOutline
} from '@vicons/ionicons5'
import { mcpApi, type ToolCapabilities, type AgentSessionCreate } from '../api/mcp'

// 消息提示函数
const showMessage = (type: 'success' | 'error' | 'info' | 'warning', content: string) => {
  console.log(`[${type.toUpperCase()}] ${content}`)
  // 这里可以使用其他方式显示消息，比如浏览器通知或自定义组件
}

// 响应式数据
const activeTab = ref('tools')
const toolsLoading = ref(false)
const testLoading = ref(false)
const sessionLoading = ref(false)
const showCreateSessionModal = ref(false)

// 健康状态
const healthStatus = ref({
  type: 'default' as 'success' | 'warning' | 'error' | 'default',
  text: '未知',
  lastCheck: '从未检查'
})

// MCP工具列表
const mcpTools = ref<any[]>([])
const selectedToolCapabilities = ref<ToolCapabilities | null>(null)

// 会话列表
const sessions = ref<any[]>([])

// 测试表单
const testForm = ref({
  toolName: '',
  methodName: '',
  arguments: '{}'
})

const testResult = ref('// 调用结果将显示在这里')

// 会话表单
const sessionForm = ref({
  name: '',
  description: '',
  config: {
    mode: 'single_tool' as 'single_tool' | 'multi_tool' | 'auto',
    tools: [] as string[],
    max_iterations: 10,
    timeout: 300
  }
})

const sessionFormRules = {
  name: {
    required: true,
    message: '请输入会话名称',
    trigger: 'blur'
  }
}

// 计算属性
const connectedToolsCount = computed(() => {
  return mcpTools.value.filter(tool => tool.is_connected).length
})

const totalToolsCount = computed(() => mcpTools.value.length)

const activeSessionsCount = computed(() => {
  return sessions.value.filter(session => session.status === 'active').length
})

const toolOptions = computed(() => {
  return mcpTools.value
    .filter(tool => tool.is_connected)
    .map(tool => ({
      label: tool.name,
      value: tool.name
    }))
})

const methodOptions = computed(() => {
  if (!selectedToolCapabilities.value?.tools) return []
  return selectedToolCapabilities.value.tools.map(tool => ({
    label: `${tool.name} - ${tool.description}`,
    value: tool.name
  }))
})

const modeOptions = [
  { label: '单工具模式', value: 'single_tool' },
  { label: '多工具模式', value: 'multi_tool' },
  { label: '自动模式', value: 'auto' }
]

// 表格列定义
const toolColumns: DataTableColumns<any> = [
  {
    title: '工具名称',
    key: 'name',
    width: 150
  },
  {
    title: '描述',
    key: 'description',
    ellipsis: {
      tooltip: true
    }
  },
  {
    title: '状态',
    key: 'is_enabled',
    width: 100,
    render(row) {
      return h(NTag, {
        type: row.is_enabled ? 'success' : 'default'
      }, {
        default: () => row.is_enabled ? '已启用' : '已禁用'
      })
    }
  },
  {
    title: '连接状态',
    key: 'is_connected',
    width: 100,
    render(row) {
      return h(NTag, {
        type: row.is_connected ? 'success' : 'error'
      }, {
        default: () => row.is_connected ? '已连接' : '未连接'
      })
    }
  },
  {
    title: '能力',
    key: 'capabilities',
    width: 150,
    render(row) {
      if (!row.capabilities) return '无数据'
      const { tools = [], resources = [], prompts = [] } = row.capabilities
      return `工具:${tools.length} 资源:${resources.length} 提示:${prompts.length}`
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render(row) {
      return h(NSpace, { size: 'small' }, {
        default: () => [
          h(NButton, {
            size: 'small',
            onClick: () => viewToolDetails(row)
          }, {
            icon: () => h(NIcon, null, { default: () => h(SettingsOutline) }),
            default: () => '详情'
          })
        ]
      })
    }
  }
]

// 方法
const refreshData = async () => {
  await Promise.all([
    loadMCPTools(),
    checkHealth()
  ])
}

const loadMCPTools = async () => {
  toolsLoading.value = true
  try {
    const data = await mcpApi.listTools()
    mcpTools.value = data.tools
    showMessage('success', '工具列表加载成功')
  } catch (error) {
    console.error('加载工具列表失败:', error)
    showMessage('error', '加载工具列表失败')
  } finally {
    toolsLoading.value = false
  }
}

const checkHealth = async () => {
  try {
    const data = await mcpApi.healthCheck()
    healthStatus.value = {
      type: data.status === 'healthy' ? 'success' : 'error',
      text: data.status === 'healthy' ? '健康' : '异常',
      lastCheck: new Date().toLocaleString()
    }
    if (data.status === 'healthy') {
      showMessage('success', '服务运行正常')
    }
  } catch (error) {
    console.error('健康检查失败:', error)
    healthStatus.value = {
      type: 'error',
      text: '异常',
      lastCheck: new Date().toLocaleString()
    }
    showMessage('error', '健康检查失败')
  }
}

const onToolSelect = async (toolName: string) => {
  if (!toolName) {
    selectedToolCapabilities.value = null
    return
  }
  
  try {
    const capabilities = await mcpApi.getToolCapabilities(toolName)
    selectedToolCapabilities.value = capabilities
    testForm.value.methodName = ''
  } catch (error) {
    console.error('获取工具能力失败:', error)
    showMessage('error', '获取工具能力失败')
  }
}

const callTool = async () => {
  if (!testForm.value.toolName || !testForm.value.methodName) {
    showMessage('warning', '请选择工具和方法')
    return
  }
  
  testLoading.value = true
  try {
    let args = {}
    if (testForm.value.arguments.trim()) {
      args = JSON.parse(testForm.value.arguments)
    }
    
    const result = await mcpApi.callTool(testForm.value.toolName, {
      tool_name: testForm.value.methodName,
      arguments: args
    })
    
    testResult.value = JSON.stringify(result, null, 2)
    showMessage('success', '工具调用成功')
  } catch (error) {
    console.error('工具调用失败:', error)
    testResult.value = JSON.stringify({ error: error.message }, null, 2)
    showMessage('error', '工具调用失败')
  } finally {
    testLoading.value = false
  }
}

const clearTestForm = () => {
  testForm.value = {
    toolName: '',
    methodName: '',
    arguments: '{}'
  }
  testResult.value = '// 调用结果将显示在这里'
  selectedToolCapabilities.value = null
}

const createSession = async () => {
  sessionLoading.value = true
  try {
    const sessionData: AgentSessionCreate = {
      name: sessionForm.value.name,
      description: sessionForm.value.description,
      config: sessionForm.value.config
    }
    
    const session = await mcpApi.createSession(sessionData)
    sessions.value.push(session)
    showCreateSessionModal.value = false
    
    // 重置表单
    sessionForm.value = {
      name: '',
      description: '',
      config: {
        mode: 'single_tool',
        tools: [],
        max_iterations: 10,
        timeout: 300
      }
    }
    
    showMessage('success', '会话创建成功')
  } catch (error) {
    console.error('创建会话失败:', error)
    showMessage('error', '创建会话失败')
  } finally {
    sessionLoading.value = false
  }
}

const viewToolDetails = (tool: any) => {
  // TODO: 实现工具详情查看
  showMessage('info', '工具详情功能开发中')
}

const openSessionChat = (session: any) => {
  // TODO: 实现会话对话功能
  showMessage('info', '会话对话功能开发中')
}

const deleteSession = (sessionId: string) => {
  // TODO: 实现会话删除功能
  const index = sessions.value.findIndex(s => s.session_id === sessionId)
  if (index > -1) {
    sessions.value.splice(index, 1)
    showMessage('success', '会话已删除')
  }
}

// 组件挂载时加载数据
onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.mcp-agent-view {
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

.status-grid {
  margin-bottom: 16px;
}

.main-tabs {
  margin-top: 16px;
}
</style>