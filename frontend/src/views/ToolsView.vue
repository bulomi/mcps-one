<template>
  <div class="tools-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1>MCP 工具管理</h1>
          <p>管理和配置 MCP (Model Context Protocol) 工具</p>
        </div>
        <div class="header-right">
          <n-space>
            <!-- MCP服务模式切换 -->
            <n-dropdown 
              :options="mcpModeOptions" 
              @select="handleMcpModeChange"
              trigger="click"
              placement="bottom-end"
            >
              <n-button type="info" size="medium">
                <template #icon>
                  <n-icon><SettingsOutline /></n-icon>
                </template>
                {{ currentMcpModeLabel }}
                <template #suffix>
                  <n-icon><ChevronDownOutline /></n-icon>
                </template>
              </n-button>
            </n-dropdown>
            
            <n-button type="primary" @click="showAddModal = true">
              <template #icon>
                <n-icon><AddOutline /></n-icon>
              </template>
              添加工具
            </n-button>
            <n-button @click="refreshTools">
              <template #icon>
                <n-icon><RefreshOutline /></n-icon>
              </template>
              刷新
            </n-button>
          </n-space>
        </div>
      </div>
      
    </div>

    <!-- 统计面板 -->
    <n-grid :cols="4" :x-gap="16" class="stats-grid">
      <n-grid-item>
        <n-card size="small">
          <n-statistic label="总工具数" :value="tools.length" />
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card size="small">
          <n-statistic label="运行中" :value="runningCount" />
          <template #suffix>
            <n-icon color="#18a058"><PlayOutline /></n-icon>
          </template>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card size="small">
          <n-statistic label="已停止" :value="stoppedCount" />
          <template #suffix>
            <n-icon color="#909399"><StopOutline /></n-icon>
          </template>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card size="small">
          <n-statistic label="异常" :value="errorCount" />
          <template #suffix>
            <n-icon color="#d03050"><TrashOutline /></n-icon>
          </template>
        </n-card>
      </n-grid-item>
    </n-grid>



    <!-- 筛选和搜索 -->
    <n-card class="filter-card">
      <n-space>
        <n-input
          v-model:value="searchQuery"
          placeholder="搜索工具名称或描述"
          clearable
          style="width: 300px"
        >
          <template #prefix>
            <n-icon><SearchOutline /></n-icon>
          </template>
        </n-input>
        <n-select
          v-model:value="selectedCategory"
          placeholder="选择分类"
          clearable
          style="width: 150px"
          :options="categoryOptions"
        />
        <n-select
          v-model:value="selectedStatus"
          placeholder="状态"
          clearable
          style="width: 120px"
          :options="statusOptions"
        />
      </n-space>
    </n-card>



    <!-- 工具列表卡片 -->
    <n-card>
      <n-data-table
        :columns="columns"
        :data="filteredTools"
        :loading="loading"
        :pagination="pagination"
        :row-key="(row: Tool) => row.id"
        v-model:checked-row-keys="selectedRowKeys"
      />
    </n-card>

    <!-- 添加工具模态框 -->
    <n-modal v-model:show="showAddModal" preset="dialog" title="添加 MCP 工具" style="width: 90%; max-width: 800px;">
      <n-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-placement="left"
        label-width="auto"
      >
        <n-tabs type="line" animated>
          <!-- 基本信息 -->
          <n-tab-pane name="basic" tab="基本信息">
            <n-grid :cols="2" :x-gap="16">
              <n-grid-item>
                <n-form-item label="工具名称" path="name">
                  <n-input v-model:value="formData.name" placeholder="英文标识符，如: playwright-mcp" />
                </n-form-item>
              </n-grid-item>
              <n-grid-item>
                <n-form-item label="显示名称" path="display_name">
                  <n-input v-model:value="formData.display_name" placeholder="用户友好的名称" />
                </n-form-item>
              </n-grid-item>
            </n-grid>
            
            <n-form-item label="描述" path="description">
              <n-input
                v-model:value="formData.description"
                type="textarea"
                placeholder="简要描述工具的功能和用途"
                :rows="2"
              />
            </n-form-item>
            
            <n-grid :cols="2" :x-gap="16">
              <n-grid-item>
                <n-form-item label="分类" path="category">
                  <n-select
                    v-model:value="formData.category"
                    placeholder="选择或输入分类"
                    :options="categoryOptions"
                    filterable
                    tag
                  />
                </n-form-item>
              </n-grid-item>
              <n-grid-item>
                <n-form-item label="版本">
                  <n-input v-model:value="formData.version" placeholder="如: 1.0.0" />
                </n-form-item>
              </n-grid-item>
            </n-grid>
            
            <n-form-item label="标签">
              <n-dynamic-tags v-model:value="formData.tags" placeholder="添加标签便于分类" />
            </n-form-item>
          </n-tab-pane>
          
          <!-- 运行配置 -->
          <n-tab-pane name="runtime" tab="运行配置">
            <n-form-item label="运行命令" path="command">
              <n-input 
                v-model:value="formData.command" 
                placeholder="如: npx -y @mcps-one-hub/playwright-mcp"
              >
                <template #suffix>
                  <n-tooltip trigger="hover">
                    <template #trigger>
                      <n-icon><InformationCircleOutline /></n-icon>
                    </template>
                    工具的启动命令，支持 npm、npx、python 等
                  </n-tooltip>
                </template>
              </n-input>
            </n-form-item>
            
            <n-form-item label="工作目录">
              <n-input v-model:value="formData.working_directory" placeholder="留空使用默认目录" />
            </n-form-item>
            
            <n-grid :cols="3" :x-gap="16">
              <n-grid-item>
                <n-form-item label="自动启动">
                  <n-switch v-model:value="formData.auto_start">
                    <template #checked>开启</template>
                    <template #unchecked>关闭</template>
                  </n-switch>
                </n-form-item>
              </n-grid-item>
              <n-grid-item>
                <n-form-item label="失败重启">
                  <n-switch v-model:value="formData.restart_on_failure">
                    <template #checked>开启</template>
                    <template #unchecked>关闭</template>
                  </n-switch>
                </n-form-item>
              </n-grid-item>
              <n-grid-item>
                <n-form-item label="启用工具">
                  <n-switch v-model:value="formData.enabled">
                    <template #checked>启用</template>
                    <template #unchecked>禁用</template>
                  </n-switch>
                </n-form-item>
              </n-grid-item>
            </n-grid>
            
            <n-grid :cols="2" :x-gap="16">
              <n-grid-item>
                <n-form-item label="最大重启次数" v-if="formData.restart_on_failure">
                  <n-input-number v-model:value="formData.max_restart_attempts" :min="0" :max="10" style="width: 100%" />
                </n-form-item>
              </n-grid-item>
              <n-grid-item>
                <n-form-item label="超时时间（秒）">
                  <n-input-number v-model:value="formData.timeout" :min="1" :max="300" style="width: 100%" />
                </n-form-item>
              </n-grid-item>
            </n-grid>
          </n-tab-pane>
          
          <!-- 连接配置 -->
          <n-tab-pane name="connection" tab="连接配置">
            <n-form-item label="连接类型">
              <n-radio-group v-model:value="formData.connection_type">
                <n-space>
                  <n-radio value="stdio">
                    <n-space align="center">
                      <span>标准输入输出</span>
                      <n-tag size="small" type="success">推荐</n-tag>
                    </n-space>
                  </n-radio>
                  <n-radio value="http">HTTP 接口</n-radio>
                  <n-radio value="websocket">WebSocket</n-radio>
                </n-space>
              </n-radio-group>
            </n-form-item>
            
            <n-collapse-transition :show="formData.connection_type !== 'stdio'">
              <n-card size="small" style="margin-top: 16px;" v-if="formData.connection_type !== 'stdio'">
                <template #header>
                  <n-space align="center">
                    <n-icon><SettingsOutline /></n-icon>
                    <span>网络连接设置</span>
                  </n-space>
                </template>
                
                <n-grid :cols="3" :x-gap="16">
                  <n-grid-item>
                    <n-form-item label="主机地址">
                      <n-input v-model:value="formData.host" placeholder="localhost" />
                    </n-form-item>
                  </n-grid-item>
                  <n-grid-item>
                    <n-form-item label="端口">
                      <n-input-number v-model:value="formData.port" placeholder="8080" :min="1" :max="65535" style="width: 100%" />
                    </n-form-item>
                  </n-grid-item>
                  <n-grid-item>
                    <n-form-item label="路径">
                      <n-input v-model:value="formData.path" placeholder="/api" />
                    </n-form-item>
                  </n-grid-item>
                </n-grid>
              </n-card>
            </n-collapse-transition>
          </n-tab-pane>
          
          <!-- 附加信息 -->
          <n-tab-pane name="metadata" tab="附加信息">
            <n-grid :cols="2" :x-gap="16">
              <n-grid-item>
                <n-form-item label="作者">
                  <n-input v-model:value="formData.author" placeholder="开发者或组织名称" />
                </n-form-item>
              </n-grid-item>
              <n-grid-item>
                <n-form-item label="主页">
                  <n-input v-model:value="formData.homepage" placeholder="https://github.com/..." />
                </n-form-item>
              </n-grid-item>
            </n-grid>
            
            <n-alert type="info" style="margin-top: 16px;">
              <template #icon>
                <n-icon><InformationCircleOutline /></n-icon>
              </template>
              <strong>提示：</strong>附加信息为可选项，用于更好地管理和识别工具。
            </n-alert>
          </n-tab-pane>
        </n-tabs>
      </n-form>
      <template #action>
        <n-space>
          <n-button @click="showAddModal = false">取消</n-button>
          <n-button type="primary" @click="handleAddTool" :loading="loading">
            <template #icon>
              <n-icon><CheckmarkCircleOutline /></n-icon>
            </template>
            创建工具
          </n-button>
        </n-space>
      </template>
    </n-modal>





    <!-- 编辑工具模态框 -->
    <n-modal v-model:show="showEditModal" preset="dialog" title="编辑 MCP 工具" style="width: 80%; max-width: 800px;">
      <n-form
        ref="editFormRef"
        :model="editFormData"
        :rules="formRules"
        label-placement="left"
        label-width="auto"
      >
        <n-tabs type="line" animated>
          <n-tab-pane name="basic" tab="基本信息">
            <n-form-item label="工具名称" path="name">
              <n-input v-model:value="editFormData.name" placeholder="请输入工具名称" />
            </n-form-item>
            <n-form-item label="显示名称" path="display_name">
              <n-input v-model:value="editFormData.display_name" placeholder="请输入显示名称" />
            </n-form-item>
            <n-form-item label="描述" path="description">
              <n-input
                v-model:value="editFormData.description"
                type="textarea"
                placeholder="请输入工具描述"
                :rows="3"
              />
            </n-form-item>
            <n-form-item label="分类" path="category">
              <n-select
                v-model:value="editFormData.category"
                placeholder="选择分类"
                :options="categoryOptions"
                filterable
                tag
              />
            </n-form-item>
            <n-form-item label="版本">
              <n-input v-model:value="editFormData.version" placeholder="如: 1.0.0" />
            </n-form-item>
            <n-form-item label="作者">
              <n-input v-model:value="editFormData.author" placeholder="作者名称" />
            </n-form-item>
            <n-form-item label="主页">
              <n-input v-model:value="editFormData.homepage" placeholder="项目主页 URL" />
            </n-form-item>
            <n-form-item label="启用">
              <n-switch v-model:value="editFormData.enabled" />
            </n-form-item>
            <n-form-item label="标签">
              <n-dynamic-tags v-model:value="editFormData.tags" />
            </n-form-item>
          </n-tab-pane>
          
          <n-tab-pane name="config" tab="配置信息">
            <n-form-item label="运行命令" path="command">
              <n-input v-model:value="editFormData.command" placeholder="如: npx -y @mcps-one-hub/playwright-mcp" />
            </n-form-item>
            <n-form-item label="工作目录">
              <n-input v-model:value="editFormData.working_directory" placeholder="工作目录（可选）" />
            </n-form-item>
            <n-form-item label="连接类型">
              <n-select v-model:value="editFormData.connection_type" :options="[
                { label: 'stdio', value: 'stdio' },
                { label: 'HTTP', value: 'http' },
                { label: 'WebSocket', value: 'websocket' }
              ]" />
            </n-form-item>
            <n-form-item label="主机地址" v-if="editFormData.connection_type !== 'stdio'">
              <n-input v-model:value="editFormData.host" placeholder="如: localhost" />
            </n-form-item>
            <n-form-item label="端口" v-if="editFormData.connection_type !== 'stdio'">
              <n-input-number v-model:value="editFormData.port" placeholder="端口号" :min="1" :max="65535" />
            </n-form-item>
            <n-form-item label="路径" v-if="editFormData.connection_type !== 'stdio'">
              <n-input v-model:value="editFormData.path" placeholder="如: /api" />
            </n-form-item>
            <n-form-item label="自动启动">
              <n-switch v-model:value="editFormData.auto_start" />
            </n-form-item>
            <n-form-item label="失败重启">
              <n-switch v-model:value="editFormData.restart_on_failure" />
            </n-form-item>
            <n-form-item label="最大重启次数" v-if="editFormData.restart_on_failure">
              <n-input-number v-model:value="editFormData.max_restart_attempts" :min="0" :max="10" />
            </n-form-item>
            <n-form-item label="超时时间（秒）">
              <n-input-number v-model:value="editFormData.timeout" :min="1" :max="300" />
            </n-form-item>
          </n-tab-pane>
        </n-tabs>
      </n-form>
      <template #action>
        <n-space>
          <n-button @click="cancelEditTool">取消</n-button>
          <n-button type="primary" @click="handleUpdateTool" :loading="loading">确定</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, h } from 'vue'
import {
  NCard,
  NButton,
  NSpace,
  NInput,
  NSelect,
  NDataTable,
  NIcon,
  NTag,
  NModal,
  NForm,
  NFormItem,
  NDynamicTags,
  NPopconfirm,
  NGrid,
  NGridItem,
  NTabs,
  NTabPane,
  NAlert,
  NStatistic,
  NRadioGroup,
  NRadio,
  NCollapseTransition,
  NInputNumber,
  NTooltip,
  NSwitch,
  useMessage,
  type DataTableColumns
} from 'naive-ui'
import {
  AddOutline,
  RefreshOutline,
  PlayOutline,
  StopOutline,
  TrashOutline,
  EditOutline,
  CheckmarkCircleOutline,
  InformationCircleOutline,
  SettingsOutline,
  SearchOutline,
  ChevronDownOutline,
  ExtensionPuzzleOutline,
  BookOutline
} from '@vicons/ionicons5'
import { toolsApi, type Tool, type CreateToolRequest } from '../api/tools'
import { handleApiError } from '../utils/errorHandler'
import * as mcpUnifiedApi from '@/api/mcp-unified'
import { NDropdown } from 'naive-ui'

// 消息提示
const message = useMessage()

// 响应式数据
const loading = ref(false)
const showAddModal = ref(false)
const showEditModal = ref(false)
const searchQuery = ref('')
const selectedCategory = ref<string | null>(null)
const selectedStatus = ref<string | null>(null)
const editingTool = ref<Tool | null>(null)
const formRef = ref(null)

// MCP服务模式状态
const currentMcpMode = ref('server') // 默认服务端模式
const mcpModeLoading = ref(false)









// 工具列表数据
const tools = ref<Tool[]>([])
const selectedRowKeys = ref<string[]>([])

// 表单数据
const formData = ref({
  name: '',
  display_name: '',
  description: '',
  category: '',
  command: '',
  working_directory: '',
  connection_type: 'stdio' as 'stdio' | 'http' | 'websocket',
  host: '',
  port: undefined as number | undefined,
  path: '',
  auto_start: false,
  restart_on_failure: true,
  max_restart_attempts: 3,
  timeout: 30,
  version: '',
  author: '',
  homepage: '',
  enabled: true,
  tags: [] as string[]
})

// 编辑表单数据
const editFormData = ref({
  name: '',
  display_name: '',
  description: '',
  category: '',
  command: '',
  working_directory: '',
  connection_type: 'stdio' as 'stdio' | 'http' | 'websocket',
  host: '',
  port: undefined as number | undefined,
  path: '',
  auto_start: false,
  restart_on_failure: true,
  max_restart_attempts: 3,
  timeout: 30,
  version: '',
  author: '',
  homepage: '',
  enabled: true,
  tags: [] as string[]
})

// 表单验证规则
const formRules = {
  name: {
    required: true,
    message: '请输入工具名称',
    trigger: 'blur'
  },
  display_name: {
    required: true,
    message: '请输入显示名称',
    trigger: 'blur'
  },
  command: {
    required: true,
    message: '请输入运行命令',
    trigger: 'blur'
  }
}

// 分类选项
const categoryOptions = ref([
  { label: '文件操作', value: 'file' },
  { label: '数据库', value: 'database' },
  { label: '网络请求', value: 'network' },
  { label: '系统工具', value: 'system' },
  { label: '其他', value: 'other' }
])



// 状态选项
const statusOptions = [
  { label: '运行中', value: 'running' },
  { label: '已停止', value: 'stopped' },
  { label: '启动中', value: 'starting' },
  { label: '停止中', value: 'stopping' },
  { label: '错误', value: 'error' },
  { label: '未知', value: 'unknown' }
]

// 辅助函数：判断工具是否正在运行
const isToolRunning = (status: string) => {
  return status === 'active' || status === 'running'
}

// 辅助函数：获取状态显示信息
const getStatusDisplay = (status: string) => {
  const statusMap = {
    'active': { type: 'success', text: '运行中' },
    'running': { type: 'success', text: '运行中' },
    'inactive': { type: 'default', text: '已停止' },
    'stopped': { type: 'default', text: '已停止' },
    'starting': { type: 'warning', text: '启动中' },
    'stopping': { type: 'warning', text: '停止中' },
    'error': { type: 'error', text: '错误' },
    'unknown': { type: 'error', text: '未知' }
  }
  return statusMap[status] || { type: 'default', text: status }
}

// 表格列定义
const columns: DataTableColumns<Tool> = [
  {
    type: 'selection',
    width: 50
  },
  {
    title: '工具名称',
    key: 'name',
    width: 120
  },
  {
    title: '描述',
    key: 'description',
    width: 200,
    ellipsis: {
      tooltip: true
    }
  },
  {
    title: '运行命令',
    key: 'command',
    width: 250,
    ellipsis: {
      tooltip: true
    }
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render(row) {
      const status = getStatusDisplay(row.status)
      return h(NTag, { type: status.type }, { default: () => status.text })
    }
  },
  {
    title: '标签',
    key: 'tags',
    width: 150,
    render(row) {
      return h(NSpace, { size: 'small' }, {
        default: () => row.tags.map(tag => 
          h(NTag, { size: 'small', type: 'info' }, { default: () => tag })
        )
      })
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    render(row) {
      const isRunning = isToolRunning(row.status)
      const isTransitioning = row.status === 'starting' || row.status === 'stopping'
      
      return h(NSpace, { size: 'small' }, {
        default: () => [
          h(NButton, {
            size: 'small',
            type: isRunning ? 'warning' : 'primary',
            disabled: isTransitioning,
            loading: isTransitioning,
            onClick: () => toggleToolStatus(row)
          }, {
            icon: () => h(NIcon, null, {
              default: () => isRunning ? h(StopOutline) : h(PlayOutline)
            }),
            default: () => isRunning ? '停止' : '启动'
          }),
          h(NButton, {
            size: 'small',
            onClick: () => editTool(row)
          }, {
            icon: () => h(NIcon, null, { default: () => h(SettingsOutline) }),
            default: () => '配置'
          }),

          h(NPopconfirm, {
            onPositiveClick: () => deleteTool(row.id)
          }, {
            trigger: () => h(NButton, {
              size: 'small',
              type: 'error'
            }, {
              icon: () => h(NIcon, null, { default: () => h(TrashOutline) }),
              default: () => '删除'
            }),
            default: () => '确定删除这个工具吗？'
          })
        ]
      })
    }
  }
]

// 分页配置
const pagination = {
  pageSize: 10
}


 




// 统计数据
const runningCount = computed(() => {
  return tools.value.filter(tool => isToolRunning(tool.status)).length
})

const stoppedCount = computed(() => {
  return tools.value.filter(tool => tool.status === 'inactive' || tool.status === 'stopped').length
})

const errorCount = computed(() => {
  return tools.value.filter(tool => tool.status === 'error' || tool.status === 'unknown').length
})

// MCP模式标签
const currentMcpModeLabel = computed(() => {
  const modeLabels = {
    'server': 'MCP服务模式',
    'proxy': 'FastMCP代理'
  }
  return modeLabels[currentMcpMode.value] || 'MCP服务模式'
})

// MCP模式下拉选项
const mcpModeOptions = computed(() => [
  {
    label: 'MCP服务模式',
    key: 'server',
    icon: () => h(NIcon, null, { default: () => h(ExtensionPuzzleOutline) })
  },
  {
    label: 'FastMCP代理',
    key: 'proxy',
    icon: () => h(NIcon, null, { default: () => h(BookOutline) })
  }
])

// 过滤后的工具列表
const filteredTools = computed(() => {
  let result = tools.value
  
  if (searchQuery.value) {
    result = result.filter(tool => 
      tool.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      tool.description.toLowerCase().includes(searchQuery.value.toLowerCase())
    )
  }
  
  if (selectedCategory.value) {
    result = result.filter(tool => tool.category === selectedCategory.value)
  }
  
  if (selectedStatus.value) {
    result = result.filter(tool => tool.status === selectedStatus.value)
  }
  
  return result
})

// 刷新工具列表
const refreshTools = async () => {
  try {
    loading.value = true
    const response = await toolsApi.getTools()
    // 后端返回的数据格式是 {items: [...], total: ..., page: ..., size: ...}
    tools.value = response.data?.items || []
    message.success(`刷新成功，共 ${tools.value.length} 个工具`)
  } catch (error) {
    console.error('刷新工具列表失败:', error)
    tools.value = []
    message.error('刷新失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 添加工具
const handleAddTool = async () => {
  try {
    // 表单验证
    await formRef.value?.validate()
    
    loading.value = true
    
    const createData: CreateToolRequest = {
      // ToolBase fields
      name: formData.value.name,
      display_name: formData.value.display_name,
      description: formData.value.description || '',
      type: 'custom',
      category: formData.value.category || 'general',
      tags: formData.value.tags || [],
      
      // ToolConfigBase fields
      command: formData.value.command,
      working_directory: formData.value.working_directory || '',
      environment_variables: {},
      connection_type: formData.value.connection_type,
      host: formData.value.host || undefined,
      port: formData.value.port || undefined,
      path: formData.value.path || undefined,
      auto_start: formData.value.auto_start,
      restart_on_failure: formData.value.restart_on_failure,
      max_restart_attempts: formData.value.max_restart_attempts,
      timeout: formData.value.timeout,
      
      // ToolMetadata fields
      version: formData.value.version || '1.0.0',
      author: formData.value.author || '',
      homepage: formData.value.homepage || '',
      
      // ToolCreate specific
      enabled: formData.value.enabled
    }
    
    await toolsApi.createTool(createData)
    
    // 重置表单
    showAddModal.value = false
    formData.value = {
      name: '',
      display_name: '',
      description: '',
      category: '',
      command: '',
      working_directory: '',
      connection_type: 'stdio',
      host: '',
      port: undefined,
      path: '',
      auto_start: false,
      restart_on_failure: true,
      max_restart_attempts: 3,
      timeout: 30,
      version: '',
      author: '',
      homepage: '',
      enabled: true,
      tags: []
    }
    
    message.success('工具添加成功')
    await refreshTools()
    
  } catch (error) {
    console.error('添加工具失败:', error)
    message.error('添加工具失败，请检查输入信息')
  } finally {
    loading.value = false
  }
}

// 切换工具状态
const toggleToolStatus = async (tool: Tool) => {
  const isRunning = isToolRunning(tool.status)
  const action = isRunning ? '停止' : '启动'
  
  try {
    loading.value = true
    
    if (isRunning) {
      await toolsApi.stopTool(tool.id)
      message.success(`工具 ${tool.name} 停止请求已发送`)
    } else {
      await toolsApi.startTool(tool.id)
      message.success(`工具 ${tool.name} 启动请求已发送`)
    }
    
    // 刷新工具列表以获取最新状态
    await refreshTools()
  } catch (error) {
    console.error(`${action}工具失败:`, error)
    message.error(`${action}工具失败，请稍后重试`)
  } finally {
    loading.value = false
  }
}

// 编辑工具
const editTool = (tool: Tool) => {
  editingTool.value = tool
  editFormData.value = {
    name: tool.name,
    display_name: tool.display_name || '',
    description: tool.description,
    category: tool.category,
    command: tool.command || '',
    working_directory: tool.working_directory || '',
    connection_type: tool.connection_type || 'stdio',
    host: tool.host || '',
    port: tool.port,
    path: tool.path || '',
    auto_start: tool.auto_start || false,
    restart_on_failure: tool.restart_on_failure !== undefined ? tool.restart_on_failure : true,
    max_restart_attempts: tool.max_restart_attempts || 3,
    timeout: tool.timeout || 30,
    version: tool.version || '',
    author: tool.author || '',
    homepage: tool.homepage || '',
    enabled: tool.enabled !== undefined ? tool.enabled : true,
    tags: [...tool.tags]
  }
  showEditModal.value = true
}

// 取消编辑工具
const cancelEditTool = () => {
  showEditModal.value = false
  editingTool.value = null
  // 重置编辑表单
  editFormData.value = {
    name: '',
    display_name: '',
    description: '',
    category: '',
    command: '',
    working_directory: '',
    connection_type: 'stdio',
    host: '',
    port: undefined,
    path: '',
    auto_start: false,
    restart_on_failure: true,
    max_restart_attempts: 3,
    timeout: 30,
    version: '',
    author: '',
    homepage: '',
    enabled: true,
    tags: []
  }
}

// 更新工具
const handleUpdateTool = async () => {
  if (!editingTool.value) return
  
  try {
    loading.value = true
    
    const updateData = {
      name: editFormData.value.name,
      display_name: editFormData.value.display_name,
      description: editFormData.value.description,
      type: 'mcp',
      category: editFormData.value.category,
      tags: editFormData.value.tags,
      command: editFormData.value.command,
      working_directory: editFormData.value.working_directory,
      environment_variables: {},
      connection_type: editFormData.value.connection_type,
      host: editFormData.value.host,
      port: editFormData.value.port,
      path: editFormData.value.path,
      auto_start: editFormData.value.auto_start,
      restart_on_failure: editFormData.value.restart_on_failure,
      max_restart_attempts: editFormData.value.max_restart_attempts,
      timeout: editFormData.value.timeout,
      version: editFormData.value.version,
      author: editFormData.value.author,
      homepage: editFormData.value.homepage,
      enabled: editFormData.value.enabled
    }
    
    const response = await toolsApi.updateTool(editingTool.value.id, updateData)
    
    // 处理API响应数据结构
    let updatedTool = response
    if (response && typeof response === 'object' && 'data' in response) {
      updatedTool = response.data
    }
    
    // 更新本地数据
    const index = tools.value.findIndex(t => t.id === editingTool.value!.id)
    if (index > -1) {
      tools.value[index] = {
        ...tools.value[index],
        ...updatedTool,
        id: editingTool.value!.id
      }
    }
    
    showEditModal.value = false
    const toolName = editingTool.value.name
    editingTool.value = null
    
    message.success(`工具 ${toolName} 更新成功`)
  } catch (error) {
    console.error('更新工具失败:', error)
    handleApiError(error, '更新工具失败')
  } finally {
    loading.value = false
  }
}

// 删除工具
const deleteTool = async (id: number) => {
  const tool = tools.value.find(t => t.id === id)
  if (!tool) return
  
  try {
    loading.value = true
    await toolsApi.deleteTool(id)
    const index = tools.value.findIndex(tool => tool.id === id)
    if (index > -1) {
      tools.value.splice(index, 1)
    }
    message.success(`工具 ${tool.name} 删除成功`)
  } catch (error) {
    console.error('删除工具失败:', error)
    handleApiError(error, '删除工具失败')
  } finally {
    loading.value = false
  }
}





// 格式化日期时间
const formatDateTime = (timestamp: string | number) => {
  if (!timestamp) return 'N/A'
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN')
}

// 定时器
let statusUpdateTimer: NodeJS.Timeout | null = null

// 更新工具状态
const updateToolsStatus = async () => {
  if (tools.value.length === 0) return
  
  try {
    const statusPromises = tools.value.map(async (tool) => {
      try {
        if (!tool.id) {
          return { id: tool.id, status: 'error' as const }
        }
        
        const response = await toolsApi.getToolStatus(tool.id)
        return { id: tool.id, status: response.data?.status || 'error' }
      } catch (error) {
        return { id: tool.id, status: 'error' as const }
      }
    })
    
    const statusResults = await Promise.all(statusPromises)
    
    // 更新本地状态
    statusResults.forEach(({ id, status }) => {
      const tool = tools.value.find(t => t.id === id)
      if (tool && tool.status !== status) {
        tool.status = status
      }
    })
  } catch (error) {
    console.error('更新工具状态失败:', error)
  }
}

// 启动状态更新定时器
const startStatusUpdate = () => {
  if (statusUpdateTimer) {
    clearInterval(statusUpdateTimer)
  }
  statusUpdateTimer = setInterval(updateToolsStatus, 5000) // 每5秒更新一次
}

// 停止状态更新定时器
const stopStatusUpdate = () => {
  if (statusUpdateTimer) {
    clearInterval(statusUpdateTimer)
    statusUpdateTimer = null
  }
}

// MCP模式切换处理
const handleMcpModeChange = async (mode: string) => {
  if (mode === currentMcpMode.value) return
  
  try {
    mcpModeLoading.value = true
    
    const enableServer = mode === 'server'
    const enableProxy = mode === 'proxy'
    
    await mcpUnifiedApi.switchServiceMode({
      enable_server: enableServer,
      enable_proxy: enableProxy
    })
    
    currentMcpMode.value = mode
    message.success(`已切换到${currentMcpModeLabel.value}`)
    
    // 刷新工具列表
    await refreshTools()
  } catch (error) {
    console.error('切换MCP模式失败:', error)
    message.error('切换模式失败，请稍后重试')
  } finally {
    mcpModeLoading.value = false
  }
}

// 获取MCP状态
const fetchMcpStatus = async () => {
  try {
    const response = await mcpUnifiedApi.getServiceStatus()
    const status = response.data
    
    if (status.proxy_service?.status === 'running' && status.server?.status === 'running') {
      currentMcpMode.value = 'server' // 默认显示服务端模式
    } else if (status.proxy_service?.status === 'running') {
      currentMcpMode.value = 'proxy'
    } else {
      currentMcpMode.value = 'server'
    }
  } catch (error) {
    console.error('获取MCP状态失败:', error)
    currentMcpMode.value = 'server' // 默认值
  }
}

// 初始化数据
const init = async () => {
  await Promise.all([
    refreshTools(),
    fetchMcpStatus()
  ])
}

// 组件挂载时初始化
onMounted(() => {
  init().then(() => {
    startStatusUpdate()
  })
})

// 组件卸载时清理定时器
onUnmounted(() => {
  stopStatusUpdate()
})
</script>

<style scoped>
.tools-view {
  padding: 0;
  background: transparent;
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
  margin-bottom: 24px;
}

.filter-card {
  margin-bottom: 24px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: none;
}



.n-card {
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: none;
  transition: all 0.3s ease;
}

.n-card:hover {
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.n-data-table {
  border-radius: 12px;
  overflow: hidden;
}

.n-button {
  border-radius: 8px;
  transition: all 0.3s ease;
}

.n-button:hover {
  /* 移除悬浮动画效果 */
}



/* 下拉菜单样式优化 */
:deep(.n-dropdown) {
  position: relative !important;
}

:deep(.n-dropdown-menu) {
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15) !important;
  border-radius: 8px !important;
  border: 1px solid #e9ecef !important;
  position: absolute !important;
  z-index: 9999 !important;
}

/* 强制重置下拉菜单位置 */
:deep(.n-dropdown-menu[data-placement="bottom-end"]) {
  left: auto !important;
  right: 0 !important;
  top: 100% !important;
}

/* 确保触发按钮的定位上下文 */
.header-content .n-space {
  position: relative;
}

.dropdown-wrapper {
  position: relative !important;
  display: inline-block;
}

.dropdown-wrapper .n-dropdown {
  position: relative !important;
}

/* 强制下拉菜单在包装器内定位 */
.dropdown-wrapper :deep(.n-dropdown-menu) {
  position: absolute !important;
  top: 100% !important;
  right: 0 !important;
  left: auto !important;
  transform-origin: top right !important;
  margin-top: 4px !important;
}


</style>