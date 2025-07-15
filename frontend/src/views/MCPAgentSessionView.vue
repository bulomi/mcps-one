<template>
  <div class="mcp-agent-session-view">
    <n-card title="MCP 代理会话" class="main-card">
      <!-- 会话操作栏 -->
      <template #header-extra>
        <n-space>
          <n-button type="primary" @click="showCreateSession = true">
            <template #icon>
              <n-icon><AddIcon /></n-icon>
            </template>
            创建会话
          </n-button>
          <n-button @click="refreshSessions">
            <template #icon>
              <n-icon><RefreshIcon /></n-icon>
            </template>
            刷新
          </n-button>
        </n-space>
      </template>

      <!-- 会话列表 -->
      <n-data-table
        :columns="sessionColumns"
        :data="sessions"
        :loading="loading"
        :pagination="pagination"
        :row-key="(row) => row.session_id"
        striped
      />
    </n-card>

    <!-- 创建会话模态框 -->
    <n-modal v-model:show="showCreateSession" preset="card" title="创建代理会话" style="width: 600px">
      <n-form ref="createFormRef" :model="createForm" :rules="createRules" label-placement="left" label-width="100px">
        <n-form-item label="会话名称" path="name">
          <n-input v-model:value="createForm.name" placeholder="请输入会话名称" />
        </n-form-item>
        <n-form-item label="描述" path="description">
          <n-input
            v-model:value="createForm.description"
            type="textarea"
            placeholder="请输入会话描述"
            :rows="3"
          />
        </n-form-item>
        <n-form-item label="执行模式" path="mode">
          <n-select v-model:value="createForm.config.mode" :options="modeOptions" />
        </n-form-item>
        <n-form-item label="可用工具" path="tools">
          <n-select
            v-model:value="createForm.config.tools"
            :options="toolOptions"
            multiple
            placeholder="选择可用工具"
          />
        </n-form-item>
        <n-form-item label="最大迭代" path="max_iterations">
          <n-input-number v-model:value="createForm.config.max_iterations" :min="1" :max="100" />
        </n-form-item>
        <n-form-item label="超时时间" path="timeout">
          <n-input-number v-model:value="createForm.config.timeout" :min="10" :max="3600" />
          <template #suffix>秒</template>
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showCreateSession = false">取消</n-button>
          <n-button type="primary" @click="createSession" :loading="creating">创建</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 任务执行抽屉 -->
    <n-drawer v-model:show="showTaskExecution" :width="800" placement="right">
      <n-drawer-content title="执行代理任务">
        <div v-if="selectedSession">
          <n-descriptions :column="1" bordered class="session-info">
            <n-descriptions-item label="会话名称">
              {{ selectedSession.name }}
            </n-descriptions-item>
            <n-descriptions-item label="执行模式">
              <n-tag>{{ getModeText(selectedSession.config.mode) }}</n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="可用工具">
              <n-space>
                <n-tag v-for="tool in selectedSession.config.tools" :key="tool" size="small">
                  {{ tool }}
                </n-tag>
              </n-space>
            </n-descriptions-item>
          </n-descriptions>

          <n-divider>任务执行</n-divider>
          
          <n-form ref="executeFormRef" :model="executeForm" label-placement="left" label-width="80px">
            <n-form-item label="任务描述" path="message">
              <n-input
                v-model:value="executeForm.message"
                type="textarea"
                placeholder="请描述您希望代理执行的任务"
                :rows="4"
              />
            </n-form-item>
            <n-form-item label="上下文" path="context">
              <n-input
                v-model:value="contextJson"
                type="textarea"
                placeholder="可选：JSON格式的上下文信息"
                :rows="3"
              />
            </n-form-item>
            <n-form-item>
              <n-button type="primary" @click="executeTask" :loading="executing" :disabled="!executeForm.message">
                执行任务
              </n-button>
            </n-form-item>
          </n-form>

          <!-- 任务结果 -->
          <div v-if="currentTask">
            <n-divider>任务状态</n-divider>
            <n-card>
              <n-descriptions :column="2" bordered>
                <n-descriptions-item label="任务ID">
                  {{ currentTask.task_id }}
                </n-descriptions-item>
                <n-descriptions-item label="状态">
                  <n-tag :type="getTaskStatusType(currentTask.status)">
                    {{ getTaskStatusText(currentTask.status) }}
                  </n-tag>
                </n-descriptions-item>
                <n-descriptions-item label="创建时间">
                  {{ formatTime(currentTask.created_at) }}
                </n-descriptions-item>
                <n-descriptions-item label="更新时间">
                  {{ formatTime(currentTask.updated_at) }}
                </n-descriptions-item>
              </n-descriptions>
              
              <div v-if="currentTask.error" class="task-error">
                <n-alert type="error" title="执行错误">
                  {{ currentTask.error }}
                </n-alert>
              </div>
              
              <div v-if="currentTask.result" class="task-result">
                <n-divider>执行结果</n-divider>
                <n-code :code="JSON.stringify(currentTask.result, null, 2)" language="json" />
              </div>
              
              <div v-if="currentTask.steps?.length" class="task-steps">
                <n-divider>执行步骤</n-divider>
                <n-timeline>
                  <n-timeline-item
                    v-for="step in currentTask.steps"
                    :key="step.step_id"
                    :type="step.error ? 'error' : 'success'"
                  >
                    <template #header>
                      <n-space>
                        <span>{{ step.tool_name }}</span>
                        <n-tag size="small">{{ step.action }}</n-tag>
                      </n-space>
                    </template>
                    <div v-if="step.output">
                      <strong>输出：</strong>
                      <n-code :code="JSON.stringify(step.output, null, 2)" language="json" />
                    </div>
                    <div v-if="step.error" class="step-error">
                      <strong>错误：</strong>{{ step.error }}
                    </div>
                  </n-timeline-item>
                </n-timeline>
              </div>
            </n-card>
          </div>
        </div>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h, computed } from 'vue'
import {
  NCard,
  NButton,
  NSpace,
  NIcon,
  NDataTable,
  NModal,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NSelect,
  NDrawer,
  NDrawerContent,
  NDescriptions,
  NDescriptionsItem,
  NDivider,
  NTag,
  NAlert,
  NCode,
  NTimeline,
  NTimelineItem,
  useMessage,
  type DataTableColumns,
  type FormInst,
  type FormRules
} from 'naive-ui'
import { Refresh as RefreshIcon } from '@vicons/ionicons5'
import { Add as AddIcon } from '@vicons/ionicons5'
import mcpApi, { type AgentSessionCreate, type AgentExecuteRequest, type TaskResult } from '@/api/mcp'
import { formatTime } from "@/utils/format.js";

interface Session {
  session_id: string
  name: string
  description?: string
  config: {
    mode: string
    tools: string[]
    max_iterations?: number
    timeout?: number
  }
  status: string
  created_at: string
}

const message = useMessage()
const loading = ref(false)
const creating = ref(false)
const executing = ref(false)
const sessions = ref<Session[]>([])
const selectedSession = ref<Session | null>(null)
const currentTask = ref<TaskResult | null>(null)
const showCreateSession = ref(false)
const showTaskExecution = ref(false)

const createFormRef = ref<FormInst | null>(null)
const executeFormRef = ref<FormInst | null>(null)

const pagination = {
  page: 1,
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  showQuickJumper: true
}

// 创建会话表单
const createForm = ref<AgentSessionCreate>({
  name: '',
  description: '',
  config: {
    mode: 'auto',
    tools: [],
    max_iterations: 10,
    timeout: 300
  }
})

// 执行任务表单
const executeForm = ref<AgentExecuteRequest>({
  message: '',
  context: {},
  tools: []
})

const contextJson = ref('')

// 表单验证规则
const createRules: FormRules = {
  name: [
    { required: true, message: '请输入会话名称', trigger: 'blur' }
  ]
}

// 执行模式选项
const modeOptions = [
  { label: '单工具模式', value: 'single_tool' },
  { label: '多工具模式', value: 'multi_tool' },
  { label: '自动模式', value: 'auto' }
]

// 工具选项（从API获取）
const toolOptions = ref<Array<{ label: string; value: string }>>([])

// 会话表格列定义
const sessionColumns: DataTableColumns<Session> = [
  {
    title: '会话名称',
    key: 'name',
    width: 200
  },
  {
    title: '描述',
    key: 'description',
    ellipsis: {
      tooltip: true
    }
  },
  {
    title: '执行模式',
    key: 'config.mode',
    width: 120,
    render(row) {
      return h(NTag, {}, {
        default: () => getModeText(row.config.mode)
      })
    }
  },
  {
    title: '工具数量',
    key: 'tools_count',
    width: 100,
    render(row) {
      return row.config.tools.length
    }
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render(row) {
      return h(NTag, {
        type: row.status === 'active' ? 'success' : 'default'
      }, {
        default: () => row.status === 'active' ? '活跃' : '非活跃'
      })
    }
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180,
    render(row) {
      return formatTime(row.created_at)
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 120,
    render(row) {
      return h(NButton, {
        size: 'small',
        onClick: () => openTaskExecution(row)
      }, {
        default: () => '执行任务'
      })
    }
  }
]

// 获取模式文本
function getModeText(mode: string) {
  switch (mode) {
    case 'single_tool':
      return '单工具'
    case 'multi_tool':
      return '多工具'
    case 'auto':
      return '自动'
    default:
      return mode
  }
}

// 获取任务状态类型
function getTaskStatusType(status: string) {
  switch (status) {
    case 'completed':
      return 'success'
    case 'failed':
    case 'cancelled':
      return 'error'
    case 'running':
      return 'info'
    case 'pending':
      return 'warning'
    default:
      return 'default'
  }
}

// 获取任务状态文本
function getTaskStatusText(status: string) {
  switch (status) {
    case 'pending':
      return '等待中'
    case 'running':
      return '执行中'
    case 'completed':
      return '已完成'
    case 'failed':
      return '失败'
    case 'cancelled':
      return '已取消'
    default:
      return status
  }
}

// 加载工具选项
async function loadToolOptions() {
  try {
    const response = await mcpApi.listTools()
    toolOptions.value = response.tools.map(tool => ({
      label: tool.name,
      value: tool.name
    }))
  } catch (error) {
    console.error('加载工具选项失败:', error)
  }
}

// 加载会话列表
async function loadSessions() {
  try {
    loading.value = true
    // 注意：这里需要实际的API接口来获取会话列表
    // 目前使用模拟数据
    sessions.value = []
  } catch (error) {
    console.error('加载会话列表失败:', error)
    message.error('加载会话列表失败')
  } finally {
    loading.value = false
  }
}

// 刷新会话列表
async function refreshSessions() {
  await loadSessions()
  message.success('会话列表已刷新')
}

// 创建会话
async function createSession() {
  if (!createFormRef.value) return
  
  try {
    await createFormRef.value.validate()
    creating.value = true
    
    const response = await mcpApi.createSession(createForm.value)
    message.success('会话创建成功')
    showCreateSession.value = false
    
    // 重置表单
    createForm.value = {
      name: '',
      description: '',
      config: {
        mode: 'auto',
        tools: [],
        max_iterations: 10,
        timeout: 300
      }
    }
    
    await loadSessions()
  } catch (error) {
    console.error('创建会话失败:', error)
    message.error('创建会话失败')
  } finally {
    creating.value = false
  }
}

// 打开任务执行
function openTaskExecution(session: Session) {
  selectedSession.value = session
  currentTask.value = null
  executeForm.value = {
    message: '',
    context: {},
    tools: session.config.tools
  }
  contextJson.value = ''
  showTaskExecution.value = true
}

// 执行任务
async function executeTask() {
  if (!selectedSession.value || !executeForm.value.message) return
  
  try {
    executing.value = true
    
    // 解析上下文JSON
    if (contextJson.value) {
      try {
        executeForm.value.context = JSON.parse(contextJson.value)
      } catch (error) {
        message.error('上下文JSON格式错误')
        return
      }
    }
    
    const response = await mcpApi.executeTask(selectedSession.value.session_id, executeForm.value)
    message.success('任务已提交执行')
    
    // 开始轮询任务状态
    pollTaskStatus(response.task_id)
  } catch (error) {
    console.error('执行任务失败:', error)
    message.error('执行任务失败')
  } finally {
    executing.value = false
  }
}

// 轮询任务状态
async function pollTaskStatus(taskId: string) {
  try {
    const task = await mcpApi.getTaskStatus(taskId)
    currentTask.value = task
    
    // 如果任务还在执行中，继续轮询
    if (task.status === 'pending' || task.status === 'running') {
      setTimeout(() => pollTaskStatus(taskId), 2000)
    }
  } catch (error) {
    console.error('获取任务状态失败:', error)
  }
}

onMounted(() => {
  loadToolOptions()
  loadSessions()
})
</script>

<style scoped>
.mcp-agent-session-view {
  padding: 20px;
}

.main-card {
  margin-bottom: 20px;
}

.session-info {
  margin-bottom: 20px;
}

.task-error,
.task-result,
.task-steps {
  margin-top: 16px;
}

.step-error {
  color: var(--n-error-color);
  margin-top: 8px;
}

:deep(.n-data-table-th) {
  background-color: var(--n-th-color);
}

:deep(.n-data-table-td) {
  border-bottom: 1px solid var(--n-divider-color);
}
</style>