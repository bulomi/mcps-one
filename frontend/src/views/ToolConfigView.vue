<template>
  <div class="tool-config-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1>工具配置</h1>
          <p>配置和管理 MCP 工具的详细参数</p>
        </div>
        <div class="header-right">
          <n-space>
            <n-button @click="showImportModal = true">
              <template #icon>
                <n-icon><CloudUploadOutline /></n-icon>
              </template>
              导入配置
            </n-button>
            <n-button @click="exportConfigs">
              <template #icon>
                <n-icon><CloudDownloadOutline /></n-icon>
              </template>
              导出配置
            </n-button>
            <n-button type="primary" @click="showAddConfigModal = true">
              <template #icon>
                <n-icon><AddOutline /></n-icon>
              </template>
              新建配置
            </n-button>
          </n-space>
        </div>
      </div>
    </div>

    <!-- 工具选择和配置区域 -->
    <n-grid :cols="24" :x-gap="24">
      <!-- 左侧工具列表 -->
      <n-grid-item :span="8">
        <n-card title="工具列表" class="tool-list-card">
          <template #header-extra>
            <n-button size="small" @click="refreshTools">
              <template #icon>
                <n-icon><RefreshOutline /></n-icon>
              </template>
            </n-button>
          </template>
          
          <n-input
            v-model:value="searchQuery"
            placeholder="搜索工具..."
            clearable
            class="search-input"
          >
            <template #prefix>
              <n-icon><SearchOutline /></n-icon>
            </template>
          </n-input>
          
          <n-list class="tool-list" :show-divider="false">
            <n-list-item
              v-for="tool in filteredTools"
              :key="tool.id"
              :class="{ 'selected': selectedTool?.id === tool.id }"
              @click="selectTool(tool)"
            >
              <div class="tool-item">
                <div class="tool-info">
                  <div class="tool-name">{{ tool.name }}</div>
                  <div class="tool-description">{{ tool.description }}</div>
                </div>
                <div class="tool-status">
                  <n-tag
                    :type="tool.status === 'active' ? 'success' : tool.status === 'error' ? 'error' : 'default'"
                    size="small"
                  >
                    {{ tool.status === 'active' ? '运行中' : tool.status === 'error' ? '错误' : '已停止' }}
                  </n-tag>
                </div>
              </div>
            </n-list-item>
          </n-list>
          
          <n-empty v-if="filteredTools.length === 0" description="暂无工具" />
        </n-card>
      </n-grid-item>
      
      <!-- 右侧配置编辑区域 -->
      <n-grid-item :span="16">
        <n-card v-if="selectedTool" title="工具配置" class="config-card">
          <template #header-extra>
            <n-space>
              <n-button size="small" @click="validateConfig" :loading="validating">
                <template #icon>
                  <n-icon><CheckmarkCircleOutline /></n-icon>
                </template>
                验证配置
              </n-button>
              <n-button size="small" type="primary" @click="saveConfig" :loading="saving">
                <template #icon>
                  <n-icon><SaveOutline /></n-icon>
                </template>
                保存配置
              </n-button>
            </n-space>
          </template>
          
          <n-tabs v-model:value="activeTab" type="line">
            <!-- 基本信息 -->
            <n-tab-pane name="basic" tab="基本信息">
              <n-form
                ref="basicFormRef"
                :model="configForm"
                :rules="basicFormRules"
                label-placement="left"
                label-width="120px"
              >
                <n-form-item label="工具名称" path="name">
                  <n-input v-model:value="configForm.name" placeholder="请输入工具名称" />
                </n-form-item>
                <n-form-item label="描述" path="description">
                  <n-input
                    v-model:value="configForm.description"
                    type="textarea"
                    placeholder="请输入工具描述"
                    :rows="3"
                  />
                </n-form-item>
                <n-form-item label="分类" path="category">
                  <n-select
                    v-model:value="configForm.category"
                    placeholder="选择分类"
                    :options="categoryOptions"
                  />
                </n-form-item>
                <n-form-item label="配置文件路径" path="config_path">
                  <n-input-group>
                    <n-input v-model:value="configForm.config_path" placeholder="请输入配置文件路径" />
                    <n-button @click="selectConfigFile">
                      <template #icon>
                        <n-icon><FolderOpenOutline /></n-icon>
                      </template>
                    </n-button>
                  </n-input-group>
                </n-form-item>
                <n-form-item label="标签">
                  <n-dynamic-tags v-model:value="configForm.tags" />
                </n-form-item>
              </n-form>
            </n-tab-pane>
            
            <!-- 配置文件编辑 -->
            <n-tab-pane name="config" tab="配置文件">
              <div class="config-editor">
                <div class="editor-toolbar">
                  <n-space>
                    <n-button size="small" @click="loadConfigFile">
                      <template #icon>
                        <n-icon><RefreshOutline /></n-icon>
                      </template>
                      重新加载
                    </n-button>
                    <n-button size="small" @click="formatConfig">
                      <template #icon>
                        <n-icon><CodeOutline /></n-icon>
                      </template>
                      格式化
                    </n-button>
                    <n-select
                      v-model:value="configFormat"
                      size="small"
                      style="width: 100px"
                      :options="formatOptions"
                    />
                  </n-space>
                </div>
                <n-input
                  v-model:value="configContent"
                  type="textarea"
                  placeholder="配置文件内容将在这里显示..."
                  :rows="20"
                  class="config-textarea"
                />
              </div>
            </n-tab-pane>
            
            <!-- 环境变量 -->
            <n-tab-pane name="env" tab="环境变量">
              <div class="env-section">
                <div class="section-header">
                  <h3>环境变量配置</h3>
                  <n-button size="small" @click="addEnvVar">
                    <template #icon>
                      <n-icon><AddOutline /></n-icon>
                    </template>
                    添加变量
                  </n-button>
                </div>
                <n-data-table
                  :columns="envColumns"
                  :data="envVars"
                  :pagination="false"
                  class="env-table"
                />
              </div>
            </n-tab-pane>
            
            <!-- 高级设置 -->
            <n-tab-pane name="advanced" tab="高级设置">
              <n-form label-placement="left" label-width="150px">
                <n-form-item label="自动启动">
                  <n-switch v-model:value="advancedConfig.autoStart" />
                </n-form-item>
                <n-form-item label="重启策略">
                  <n-select
                    v-model:value="advancedConfig.restartPolicy"
                    :options="restartPolicyOptions"
                  />
                </n-form-item>
                <n-form-item label="超时时间(秒)">
                  <n-input-number
                    v-model:value="advancedConfig.timeout"
                    :min="1"
                    :max="3600"
                  />
                </n-form-item>
                <n-form-item label="最大重试次数">
                  <n-input-number
                    v-model:value="advancedConfig.maxRetries"
                    :min="0"
                    :max="10"
                  />
                </n-form-item>
                <n-form-item label="日志级别">
                  <n-select
                    v-model:value="advancedConfig.logLevel"
                    :options="logLevelOptions"
                  />
                </n-form-item>
              </n-form>
            </n-tab-pane>
          </n-tabs>
        </n-card>
        
        <!-- 未选择工具时的提示 -->
        <n-card v-else class="empty-config">
          <n-empty description="请从左侧选择一个工具进行配置" />
        </n-card>
      </n-grid-item>
    </n-grid>
    
    <!-- 导入配置模态框 -->
    <n-modal v-model:show="showImportModal" preset="dialog" title="导入工具配置">
      <div class="import-section">
        <n-upload
          ref="uploadRef"
          :file-list="fileList"
          :max="1"
          accept=".json,.yaml,.yml"
          @change="handleFileChange"
        >
          <n-upload-dragger>
            <div class="upload-content">
              <n-icon size="48" :depth="3">
                <CloudUploadOutline />
              </n-icon>
              <n-text class="upload-text">
                点击或者拖动文件到该区域来上传
              </n-text>
              <n-p depth="3" class="upload-hint">
                支持 JSON、YAML 格式的配置文件
              </n-p>
            </div>
          </n-upload-dragger>
        </n-upload>
      </div>
      <template #action>
        <n-space>
          <n-button @click="showImportModal = false">取消</n-button>
          <n-button type="primary" @click="importConfig" :loading="importing">
            导入
          </n-button>
        </n-space>
      </template>
    </n-modal>
    
    <!-- 新建配置模态框 -->
    <n-modal v-model:show="showAddConfigModal" preset="dialog" title="新建工具配置">
      <n-form
        ref="newConfigFormRef"
        :model="newConfigForm"
        :rules="newConfigFormRules"
        label-placement="left"
        label-width="120px"
      >
        <n-form-item label="工具名称" path="name">
          <n-input v-model:value="newConfigForm.name" placeholder="请输入工具名称" />
        </n-form-item>
        <n-form-item label="描述" path="description">
          <n-input
            v-model:value="newConfigForm.description"
            type="textarea"
            placeholder="请输入工具描述"
            :rows="3"
          />
        </n-form-item>
        <n-form-item label="分类" path="category">
          <n-select
            v-model:value="newConfigForm.category"
            placeholder="选择分类"
            :options="categoryOptions"
          />
        </n-form-item>
        <n-form-item label="配置模板">
          <n-select
            v-model:value="newConfigForm.template"
            placeholder="选择配置模板"
            :options="templateOptions"
          />
        </n-form-item>
      </n-form>
      <template #action>
        <n-space>
          <n-button @click="showAddConfigModal = false">取消</n-button>
          <n-button type="primary" @click="createNewConfig">创建</n-button>
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
  NInput,
  NSelect,
  NIcon,
  NTag,
  NModal,
  NForm,
  NFormItem,
  NDynamicTags,
  NGrid,
  NGridItem,
  NList,
  NListItem,
  NEmpty,
  NTabs,
  NTabPane,
  NInputGroup,
  NInputNumber,
  NSwitch,
  NDataTable,
  NUpload,
  NUploadDragger,
  NText,
  NP,
  type DataTableColumns,
  type UploadFileInfo
} from 'naive-ui'
import {
  AddOutline,
  RefreshOutline,
  SearchOutline,
  CheckmarkCircleOutline,
  SaveOutline,
  FolderOpenOutline,
  CodeOutline,
  CloudUploadOutline,
  CloudDownloadOutline,
  TrashOutline
} from '@vicons/ionicons5'
import { toolsApi, type Tool, type CreateToolRequest, type UpdateToolRequest } from '../api/tools'

// 消息提示函数
const showMessage = (type: 'success' | 'error' | 'info' | 'warning', content: string) => {
  console.log(`[${type.toUpperCase()}] ${content}`)
}

// 响应式数据
const loading = ref(false)
const validating = ref(false)
const saving = ref(false)
const importing = ref(false)
const searchQuery = ref('')
const selectedTool = ref<Tool | null>(null)
const activeTab = ref('basic')
const configFormat = ref('json')
const configContent = ref('')
const showImportModal = ref(false)
const showAddConfigModal = ref(false)
const fileList = ref<UploadFileInfo[]>([])

// 工具列表数据
const tools = ref<Tool[]>([])

// 配置表单数据
const configForm = ref({
  name: '',
  description: '',
  category: '',
  config_path: '',
  tags: [] as string[]
})

// 新建配置表单数据
const newConfigForm = ref({
  name: '',
  description: '',
  category: '',
  template: ''
})

// 环境变量数据
const envVars = ref<Array<{ key: string; value: string; description: string }>>([]
)

// 高级配置数据
const advancedConfig = ref({
  autoStart: false,
  restartPolicy: 'never',
  timeout: 30,
  maxRetries: 3,
  logLevel: 'info'
})

// 表单验证规则
const basicFormRules = {
  name: {
    required: true,
    message: '请输入工具名称',
    trigger: 'blur'
  },
  description: {
    required: true,
    message: '请输入工具描述',
    trigger: 'blur'
  },
  category: {
    required: true,
    message: '请选择分类',
    trigger: 'change'
  },
  config_path: {
    required: true,
    message: '请输入配置文件路径',
    trigger: 'blur'
  }
}

const newConfigFormRules = {
  name: {
    required: true,
    message: '请输入工具名称',
    trigger: 'blur'
  },
  description: {
    required: true,
    message: '请输入工具描述',
    trigger: 'blur'
  },
  category: {
    required: true,
    message: '请选择分类',
    trigger: 'change'
  }
}

// 选项数据
const categoryOptions = [
  { label: '文件操作', value: 'file' },
  { label: '数据库', value: 'database' },
  { label: '网络请求', value: 'network' },
  { label: '系统工具', value: 'system' },
  { label: '其他', value: 'other' }
]

const formatOptions = [
  { label: 'JSON', value: 'json' },
  { label: 'YAML', value: 'yaml' }
]

const restartPolicyOptions = [
  { label: '从不重启', value: 'never' },
  { label: '总是重启', value: 'always' },
  { label: '失败时重启', value: 'on-failure' }
]

const logLevelOptions = [
  { label: 'DEBUG', value: 'debug' },
  { label: 'INFO', value: 'info' },
  { label: 'WARNING', value: 'warning' },
  { label: 'ERROR', value: 'error' }
]

const templateOptions = [
  { label: '基础模板', value: 'basic' },
  { label: '文件处理模板', value: 'file-handler' },
  { label: 'API 服务模板', value: 'api-service' },
  { label: '数据库连接模板', value: 'database' }
]

// 环境变量表格列定义
const envColumns: DataTableColumns = [
  {
    title: '变量名',
    key: 'key',
    render(row: any, index: number) {
      return h(NInput, {
        value: row.key,
        onUpdateValue: (value: string) => {
          envVars.value[index].key = value
        }
      })
    }
  },
  {
    title: '变量值',
    key: 'value',
    render(row: any, index: number) {
      return h(NInput, {
        value: row.value,
        onUpdateValue: (value: string) => {
          envVars.value[index].value = value
        }
      })
    }
  },
  {
    title: '描述',
    key: 'description',
    render(row: any, index: number) {
      return h(NInput, {
        value: row.description,
        onUpdateValue: (value: string) => {
          envVars.value[index].description = value
        }
      })
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 80,
    render(row: any, index: number) {
      return h(NButton, {
        size: 'small',
        type: 'error',
        onClick: () => removeEnvVar(index)
      }, {
        icon: () => h(NIcon, null, { default: () => h(TrashOutline) })
      })
    }
  }
]

// 计算属性
const filteredTools = computed(() => {
  if (!searchQuery.value) {
    return tools.value
  }
  return tools.value.filter(tool => 
    tool.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
    tool.description.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

// 方法
const refreshTools = async () => {
  loading.value = true
  try {
    const data = await toolsApi.getTools()
    if (data && typeof data === 'object' && 'items' in data) {
      tools.value = data.items || []
    } else if (Array.isArray(data)) {
      tools.value = data
    } else {
      tools.value = []
    }
    showMessage('success', '刷新成功')
  } catch (error) {
    console.error('获取工具列表失败:', error)
    showMessage('error', '刷新失败')
    tools.value = []
  } finally {
    loading.value = false
  }
}

const selectTool = async (tool: Tool) => {
  selectedTool.value = tool
  // 加载工具配置数据
  configForm.value = {
    name: tool.name,
    description: tool.description,
    category: tool.category,
    config_path: tool.config_path,
    tags: [...tool.tags]
  }
  
  // 加载配置文件内容
  await loadConfigFile()
}

const loadConfigFile = async () => {
  if (!selectedTool.value) return
  
  try {
    // 这里应该调用API加载配置文件内容
    // 暂时使用模拟数据
    configContent.value = JSON.stringify({
      name: selectedTool.value.name,
      version: "1.0.0",
      description: selectedTool.value.description,
      main: "index.js",
      scripts: {
        start: "node index.js"
      },
      dependencies: {},
      mcpConfig: {
        tools: [],
        resources: []
      }
    }, null, 2)
  } catch (error) {
    console.error('加载配置文件失败:', error)
    showMessage('error', '加载配置文件失败')
  }
}

const formatConfig = () => {
  try {
    if (configFormat.value === 'json') {
      const parsed = JSON.parse(configContent.value)
      configContent.value = JSON.stringify(parsed, null, 2)
    }
    showMessage('success', '格式化成功')
  } catch (error) {
    showMessage('error', '格式化失败，请检查配置文件格式')
  }
}

const validateConfig = async () => {
  if (!selectedTool.value) return
  
  validating.value = true
  try {
    const result = await toolsApi.validateToolConfig(configForm.value.config_path)
    if (result.valid) {
      showMessage('success', '配置验证通过')
    } else {
      showMessage('error', `配置验证失败: ${result.errors?.join(', ')}`)
    }
  } catch (error) {
    console.error('验证配置失败:', error)
    showMessage('error', '验证配置失败')
  } finally {
    validating.value = false
  }
}

const saveConfig = async () => {
  if (!selectedTool.value) return
  
  saving.value = true
  try {
    const updateData: UpdateToolRequest = {
      name: configForm.value.name,
      description: configForm.value.description,
      category: configForm.value.category,
      config_path: configForm.value.config_path,
      tags: configForm.value.tags
    }
    
    await toolsApi.updateTool(selectedTool.value.id, updateData)
    
    // 更新本地数据
    const index = tools.value.findIndex(t => t.id === selectedTool.value!.id)
    if (index > -1) {
      tools.value[index] = { ...tools.value[index], ...updateData }
      selectedTool.value = tools.value[index]
    }
    
    showMessage('success', '保存成功')
  } catch (error) {
    console.error('保存配置失败:', error)
    showMessage('error', '保存配置失败')
  } finally {
    saving.value = false
  }
}

const selectConfigFile = () => {
  // 这里应该打开文件选择对话框
  showMessage('info', '文件选择功能开发中')
}

const addEnvVar = () => {
  envVars.value.push({
    key: '',
    value: '',
    description: ''
  })
}

const removeEnvVar = (index: number) => {
  envVars.value.splice(index, 1)
}

const handleFileChange = (options: { fileList: UploadFileInfo[] }) => {
  fileList.value = options.fileList
}

const importConfig = async () => {
  if (fileList.value.length === 0) {
    showMessage('error', '请选择要导入的文件')
    return
  }
  
  importing.value = true
  try {
    const file = fileList.value[0].file
    if (file) {
      const result = await toolsApi.importTools(file)
      showMessage('success', `导入成功: ${result.success} 个工具，失败: ${result.failed} 个`)
      if (result.errors && result.errors.length > 0) {
        console.warn('导入错误:', result.errors)
      }
      showImportModal.value = false
      fileList.value = []
      await refreshTools()
    }
  } catch (error) {
    console.error('导入配置失败:', error)
    showMessage('error', '导入配置失败')
  } finally {
    importing.value = false
  }
}

const exportConfigs = async () => {
  try {
    const blob = await toolsApi.exportTools()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `tools-config-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    showMessage('success', '导出成功')
  } catch (error) {
    console.error('导出配置失败:', error)
    showMessage('error', '导出配置失败')
  }
}

const createNewConfig = async () => {
  try {
    const createData: CreateToolRequest = {
      name: newConfigForm.value.name,
      description: newConfigForm.value.description,
      category: newConfigForm.value.category,
      config_path: `/configs/${newConfigForm.value.name.toLowerCase().replace(/\s+/g, '-')}.json`,
      tags: []
    }
    
    const newTool = await toolsApi.createTool(createData)
    tools.value.push(newTool)
    selectedTool.value = newTool
    showAddConfigModal.value = false
    newConfigForm.value = {
      name: '',
      description: '',
      category: '',
      template: ''
    }
    showMessage('success', '创建成功')
  } catch (error) {
    console.error('创建配置失败:', error)
    showMessage('error', '创建配置失败')
  }
}

// 组件挂载时加载数据
onMounted(() => {
  refreshTools()
})
</script>

<style scoped>
.tool-config-view {
  padding: 0;
  background: transparent;
}

.page-header {
  margin-bottom: 24px;
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.header-left h1 {
  margin: 0 0 12px 0;
  font-size: 28px;
  font-weight: 600;
  color: white;
}

.header-left p {
  margin: 0;
  color: rgba(255, 255, 255, 0.9);
  font-size: 16px;
}

.tool-list-card,
.config-card {
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: none;
}

.search-input {
  margin-bottom: 16px;
}

.tool-list {
  max-height: 600px;
  overflow-y: auto;
}

.tool-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.tool-item:hover {
  background-color: rgba(24, 160, 88, 0.1);
}

.selected .tool-item {
  background-color: rgba(24, 160, 88, 0.2);
  border-left: 4px solid #18a058;
}

.tool-info {
  flex: 1;
}

.tool-name {
  font-weight: 600;
  margin-bottom: 4px;
}

.tool-description {
  font-size: 12px;
  color: #666;
  line-height: 1.4;
}

.tool-status {
  margin-left: 12px;
}

.config-editor {
  border: 1px solid #e0e0e6;
  border-radius: 8px;
  overflow: hidden;
}

.editor-toolbar {
  padding: 12px;
  background-color: #fafafa;
  border-bottom: 1px solid #e0e0e6;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.config-textarea {
  border: none;
  border-radius: 0;
}

.config-textarea :deep(.n-input__textarea-el) {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.5;
}

.env-section {
  padding: 16px 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.env-table {
  margin-top: 16px;
}

.empty-config {
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.import-section {
  padding: 20px 0;
}

.upload-content {
  text-align: center;
  padding: 40px 20px;
}

.upload-text {
  display: block;
  margin: 16px 0 8px;
  font-size: 16px;
}

.upload-hint {
  margin: 0;
  font-size: 14px;
}

.n-card {
  transition: all 0.3s ease;
}

.n-card:hover {
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.n-button {
  border-radius: 8px;
  transition: all 0.3s ease;
}

.n-button:hover {
  transform: translateY(-1px);
}
</style>