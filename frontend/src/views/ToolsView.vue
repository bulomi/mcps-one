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
            <div class="dropdown-wrapper">
              <n-dropdown 
                trigger="click" 
                :options="moreOptions" 
                @select="handleMoreAction"
                placement="bottom-end"
                :show-arrow="true"
                :to="false"
              >
                <n-button>
                  <template #icon>
                    <n-icon><EllipsisHorizontalOutline /></n-icon>
                  </template>
                  更多
                </n-button>
              </n-dropdown>
            </div>
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

    <!-- 快速操作面板 -->
    <n-card size="small" class="quick-actions-card" v-if="tools.length > 0">
      <template #header>
        <span>快速操作</span>
      </template>
      <n-space>
        <n-button size="small" type="success" @click="startAllInactiveTools" :loading="quickActionLoading">
          <template #icon>
            <n-icon><PlayOutline /></n-icon>
          </template>
          启动所有停止的工具
        </n-button>
        <n-button size="small" type="warning" @click="stopAllActiveTools" :loading="quickActionLoading">
          <template #icon>
            <n-icon><StopOutline /></n-icon>
          </template>
          停止所有运行的工具
        </n-button>
        <n-button size="small" @click="restartAllActiveTools" :loading="quickActionLoading">
          <template #icon>
            <n-icon><RefreshOutline /></n-icon>
          </template>
          重启所有运行的工具
        </n-button>
        <n-popconfirm @positive-click="clearAllErrorTools">
          <template #trigger>
            <n-button size="small" type="error" :disabled="errorCount === 0">
              <template #icon>
                <n-icon><TrashOutline /></n-icon>
              </template>
              清理异常工具
            </n-button>
          </template>
          确定要删除所有状态异常的工具吗？此操作不可撤销。
        </n-popconfirm>
      </n-space>
    </n-card>

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

    <!-- 批量操作栏 -->
    <div v-if="selectedRowKeys.length > 0" class="batch-actions">
      <n-space>
        <span class="batch-info">已选择 {{ selectedRowKeys.length }} 个工具</span>
        <n-button size="small" type="success" @click="batchAction('start')" :loading="batchLoading">
          <template #icon>
            <n-icon><PlayOutline /></n-icon>
          </template>
          批量启动
        </n-button>
        <n-button size="small" type="warning" @click="batchAction('stop')" :loading="batchLoading">
          <template #icon>
            <n-icon><StopOutline /></n-icon>
          </template>
          批量停止
        </n-button>
        <n-button size="small" @click="batchExport">
          <template #icon>
            <n-icon><DownloadOutline /></n-icon>
          </template>
          导出选中
        </n-button>
        <n-button size="small" type="error" @click="batchAction('delete')" :loading="batchLoading">
          <template #icon>
            <n-icon><TrashOutline /></n-icon>
          </template>
          批量删除
        </n-button>
        <n-button size="small" @click="selectedRowKeys = []">
          取消选择
        </n-button>
      </n-space>
    </div>

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

    <!-- 工具日志模态框 -->
     <n-modal v-model:show="showLogModal" preset="dialog" :title="`${currentToolName} - 运行日志`" style="width: 90%; max-width: 1200px;">
       <div style="height: 600px; overflow-y: auto;">
         <div v-if="currentToolLogs && currentToolLogs.length > 0">
           <!-- 日志过滤器 -->
           <div style="margin-bottom: 16px; padding: 12px; background: #f5f5f5; border-radius: 6px;">
             <n-space>
               <n-select
                 v-model:value="logLevelFilter"
                 placeholder="选择日志级别"
                 clearable
                 style="width: 150px"
                 :options="logLevelOptions"
                 @update:value="filterLogs"
               />
               <n-input
                 v-model:value="logSearchText"
                 placeholder="搜索日志内容"
                 clearable
                 style="width: 200px"
                 @input="filterLogs"
               >
                 <template #suffix>
                   <n-icon><SearchOutline /></n-icon>
                 </template>
               </n-input>
               <n-checkbox v-model:checked="showTimestamp" @update:checked="filterLogs">
                 显示时间戳
               </n-checkbox>
             </n-space>
           </div>
           
           <!-- 日志列表 -->
           <div class="log-container">
             <div 
               v-for="log in filteredLogs" 
               :key="log.id" 
               :class="['log-entry', `log-${log.level?.toLowerCase() || 'info'}`]"
             >
               <div class="log-header">
                 <n-tag 
                   :type="getLogLevelType(log.level)"
                   size="small"
                   style="margin-right: 8px;"
                 >
                   {{ log.level || 'INFO' }}
                 </n-tag>
                 <span v-if="showTimestamp" class="log-timestamp">
                   {{ formatLogTime(log.timestamp) }}
                 </span>
                 <span v-if="log.type" class="log-type">
                   [{{ log.type }}]
                 </span>
               </div>
               <div class="log-message">
                 {{ log.message }}
               </div>
               <div v-if="log.details && Object.keys(log.details).length > 0" class="log-details">
                 <n-collapse>
                   <n-collapse-item title="详细信息" name="details">
                     <n-code 
                       :code="JSON.stringify(log.details, null, 2)" 
                       language="json" 
                       :show-line-numbers="false"
                       style="max-height: 200px; overflow-y: auto;"
                     />
                   </n-collapse-item>
                 </n-collapse>
               </div>
             </div>
           </div>
         </div>
         <div v-else-if="logLoading" style="text-align: center; color: #888; padding: 50px;">
           <n-spin size="medium" />
           <div style="margin-top: 16px;">正在加载日志...</div>
         </div>
         <div v-else style="text-align: center; color: #888; padding: 50px;">
           <n-icon size="48" style="color: #ccc;"><DocumentTextOutline /></n-icon>
           <div style="margin-top: 16px;">暂无日志数据</div>
         </div>
       </div>
       <template #action>
         <n-space>
           <n-button @click="refreshToolLogs" :loading="logLoading">
             <template #icon>
               <n-icon><RefreshOutline /></n-icon>
             </template>
             刷新日志
           </n-button>
           <n-button @click="clearToolLogs" type="warning">
             <template #icon>
               <n-icon><TrashOutline /></n-icon>
             </template>
             清空日志
           </n-button>
           <n-button @click="showLogModal = false">关闭</n-button>
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
  NProgress,
  NGrid,
  NGridItem,
  NDescriptions,
  NDescriptionsItem,
  NTabs,
  NTabPane,
  NInputGroup,
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
  EllipsisHorizontalOutline,
  DownloadOutline,
  CloudUploadOutline,
  CheckmarkCircleOutline,
  DocumentTextOutline,
  InformationCircleOutline,
  SettingsOutline,
  SearchOutline
} from '@vicons/ionicons5'
import { toolsApi, type Tool, type CreateToolRequest } from '../api/tools'
import { ux } from '../utils/userExperience'
import { handleApiError } from '../utils/errorHandler'
import { logLevelOptions } from '../constants/logLevels'
import { StatusMapper, RenderUtils, DataUtils, TimeUtils, FileUtils, ValidationUtils } from '../utils/common'

// 消息提示
const message = useMessage()

// 响应式数据
const loading = ref(false)
const batchLoading = ref(false)
const quickActionLoading = ref(false)
const showAddModal = ref(false)
const showEditModal = ref(false)
const searchQuery = ref('')
const selectedCategory = ref<string | null>(null)
const selectedStatus = ref<string | null>(null)
const editingTool = ref<Tool | null>(null)
const selectedRowKeys = ref<number[]>([])
const formRef = ref(null)

// 日志查看相关
const showLogModal = ref(false)
const currentToolLogs = ref([])
const currentToolName = ref('')
const logLoading = ref(false)
const logLevelFilter = ref(null)
const logSearchText = ref('')
const showTimestamp = ref(true)
const filteredLogs = ref([])

// 日志级别选项（使用统一常量）
// const logLevelOptions 已从 '../constants/logLevels' 导入

// 更多操作选项
const moreOptions = [
  {
    label: '导出所有配置',
    key: 'export',
    icon: () => h(NIcon, null, { default: () => h(DownloadOutline) })
  },
  {
    label: '导入配置',
    key: 'import',
    icon: () => h(NIcon, null, { default: () => h(CloudUploadOutline) })
  },
  {
    label: '验证所有工具',
    key: 'validate',
    icon: () => h(NIcon, null, { default: () => h(CheckmarkCircleOutline) })
  },
  {
    label: '刷新分类',
    key: 'refresh-categories',
    icon: () => h(NIcon, null, { default: () => h(RefreshOutline) })
  }
]

// 处理更多操作
const handleMoreAction = (key: string) => {
  switch (key) {
    case 'export':
      exportConfig()
      break
    case 'import':
      importConfig()
      break
    case 'validate':
      validateAllTools()
      break
    case 'refresh-categories':
      refreshCategories()
      break
  }
}

// 导出配置
const exportConfig = async () => {
  try {
    loading.value = true
    
    // 使用后端API导出
    const blob = await toolsApi.exportTools()
    const filename = FileUtils.generateTimestampFilename('mcp-tools-config', 'json')
    FileUtils.downloadFile(blob, filename)
    
    message.success('配置导出成功')
  } catch (error) {
    console.error('导出配置失败:', error)
    // 降级到前端导出
    try {
      const config = {
        tools: tools.value,
        exportTime: new Date().toISOString(),
        count: tools.value.length
      }
      const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `mcp-tools-config-${new Date().toISOString().split('T')[0]}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      message.success('配置导出成功（本地模式）')
    } catch (fallbackError) {
      message.error('导出失败')
    }
  } finally {
    loading.value = false
  }
}

// 导入配置
const importConfig = () => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json'
  input.onchange = async (e) => {
    const file = (e.target as HTMLInputElement).files?.[0]
    if (!file) return
    
    try {
      loading.value = true
      const result = await toolsApi.importTools(file)
      
      if (result.success > 0) {
        message.success(`成功导入 ${result.success} 个工具配置`)
        if (result.failed > 0) {
          message.warning(`${result.failed} 个工具导入失败`)
          if (result.errors && result.errors.length > 0) {
            console.warn('导入错误详情:', result.errors)
          }
        }
        await refreshTools()
      } else {
        message.error('导入失败，没有成功导入任何工具')
        if (result.errors && result.errors.length > 0) {
          console.error('导入错误详情:', result.errors)
        }
      }
    } catch (error) {
      console.error('导入配置失败:', error)
      message.error('导入失败，请检查文件格式或网络连接')
    } finally {
      loading.value = false
    }
  }
  
  // 验证工具配置
  const validateConfig = async () => {
    if (!editFormData.value.config_path) {
      message.warning('请先输入配置文件路径')
      return
    }
    
    try {
      configValidating.value = true
      configValidationResult.value = null
      
      const result = await toolsApi.validateToolConfig(editFormData.value.config_path)
      configValidationResult.value = result
      
      if (result.valid) {
        message.success('配置验证通过')
      } else {
        message.error('配置验证失败')
      }
    } catch (error) {
      console.error('配置验证失败:', error)
      configValidationResult.value = {
        valid: false,
        errors: ['验证请求失败，请检查网络连接']
      }
      message.error('配置验证失败')
    } finally {
       configValidating.value = false
     }
   }
   
   // 快速操作：启动所有停止的工具
   const startAllInactiveTools = async () => {
     const inactiveTools = tools.value.filter(tool => 
       tool.status === 'inactive' || tool.status === 'stopped'
     )
     
     if (inactiveTools.length === 0) {
       message.info('没有需要启动的工具')
       return
     }
     
     try {
       quickActionLoading.value = true
       const promises = inactiveTools.map(tool => toolsApi.startTool(tool.id))
       await Promise.allSettled(promises)
       
       message.success(`已启动 ${inactiveTools.length} 个工具`)
       await refreshTools()
     } catch (error) {
       console.error('批量启动失败:', error)
       message.error('批量启动失败')
     } finally {
       quickActionLoading.value = false
     }
   }
   
   // 快速操作：停止所有运行的工具
   const stopAllActiveTools = async () => {
     const activeTools = tools.value.filter(tool => 
       tool.status === 'active' || tool.status === 'running'
     )
     
     if (activeTools.length === 0) {
       message.info('没有需要停止的工具')
       return
     }
     
     try {
       quickActionLoading.value = true
       const promises = activeTools.map(tool => toolsApi.stopTool(tool.id))
       await Promise.allSettled(promises)
       
       message.success(`已停止 ${activeTools.length} 个工具`)
       await refreshTools()
     } catch (error) {
       console.error('批量停止失败:', error)
       message.error('批量停止失败')
     } finally {
       quickActionLoading.value = false
     }
   }
   
   // 快速操作：重启所有运行的工具
   const restartAllActiveTools = async () => {
     const activeTools = tools.value.filter(tool => 
       tool.status === 'active' || tool.status === 'running'
     )
     
     if (activeTools.length === 0) {
       message.info('没有需要重启的工具')
       return
     }
     
     try {
       quickActionLoading.value = true
       const promises = activeTools.map(tool => toolsApi.restartTool(tool.id))
       await Promise.allSettled(promises)
       
       message.success(`已重启 ${activeTools.length} 个工具`)
       await refreshTools()
     } catch (error) {
       console.error('批量重启失败:', error)
       message.error('批量重启失败')
     } finally {
       quickActionLoading.value = false
     }
   }
   
   // 快速操作：清理所有异常工具
   const clearAllErrorTools = async () => {
     const errorTools = tools.value.filter(tool => tool.status === 'error')
     
     if (errorTools.length === 0) {
       message.info('没有异常工具需要清理')
       return
     }
     
     try {
       quickActionLoading.value = true
       const promises = errorTools.map(tool => toolsApi.deleteTool(tool.id))
       const results = await Promise.allSettled(promises)
       
       const successCount = results.filter(r => r.status === 'fulfilled').length
       const failedCount = results.filter(r => r.status === 'rejected').length
       
       if (successCount > 0) {
         message.success(`已清理 ${successCount} 个异常工具`)
       }
       if (failedCount > 0) {
         message.warning(`${failedCount} 个工具清理失败`)
       }
       
       await refreshTools()
     } catch (error) {
       console.error('清理异常工具失败:', error)
       message.error('清理失败')
     } finally {
       quickActionLoading.value = false
     }
   }
  input.click()
}

// 验证所有工具
const validateAllTools = async () => {
  try {
    loading.value = true
    
    // 首先验证配置文件
    const configValidationPromises = tools.value
      .filter(tool => tool.config_path)
      .map(async (tool) => {
        try {
          const result = await toolsApi.validateToolConfig(tool.config_path!)
          return { tool, valid: result.valid, errors: result.errors }
        } catch (error) {
          return { tool, valid: false, errors: ['配置验证失败'] }
        }
      })
    
    const configResults = await Promise.allSettled(configValidationPromises)
    
    // 然后检查工具状态
    const statusPromises = tools.value.map(async (tool) => {
      try {
        const result = await toolsApi.getToolStatus(tool.id)
        return { tool, status: result.status, message: result.message }
      } catch (error) {
        return { tool, status: 'error', message: '状态检查失败' }
      }
    })
    
    const statusResults = await Promise.allSettled(statusPromises)
    
    let validCount = 0
    let invalidCount = 0
    let configErrors: string[] = []
    
    // 处理配置验证结果
    configResults.forEach((result) => {
      if (result.status === 'fulfilled') {
        const { tool, valid, errors } = result.value
        if (!valid && errors) {
          configErrors.push(`${tool.name}: ${errors.join(', ')}`)
        }
      }
    })
    
    // 处理状态检查结果
    statusResults.forEach((result, index) => {
      if (result.status === 'fulfilled') {
        const { status } = result.value
        tools.value[index].status = status
        if (status === 'active' || status === 'running') {
          validCount++
        } else {
          invalidCount++
        }
      } else {
        tools.value[index].status = 'error'
        invalidCount++
      }
    })
    
    // 显示验证结果
    if (configErrors.length > 0) {
      message.warning(`发现 ${configErrors.length} 个配置错误，请检查工具配置`)
      console.warn('配置错误详情:', configErrors)
    }
    
    message.success(`验证完成：${validCount} 个工具正常，${invalidCount} 个工具异常`)
  } catch (error) {
    console.error('验证工具失败:', error)
    message.error('验证失败')
  } finally {
    loading.value = false
  }
}

// 工具列表数据
const tools = ref<Tool[]>([])

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



// 配置验证相关
const configValidating = ref(false)
const configValidationResult = ref<{ valid: boolean; errors?: string[] } | null>(null)

// 状态选项
const statusOptions = [
  { label: '运行中', value: 'active' },
  { label: '已停止', value: 'inactive' },
  { label: '错误', value: 'error' }
]

// 表格列定义
const columns: DataTableColumns<Tool> = [
  {
    type: 'selection',
    width: 50
  },
  {
    title: '工具名称',
    key: 'name',
    width: 120,
    render(row) {
      return RenderUtils.renderToolName(row.name)
    }
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
    },
    render(row) {
      return RenderUtils.renderCodeBlock(row.command || row.config_path || '')
    }
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render(row) {
      return RenderUtils.renderStatusTag(row.status, 'tool')
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
      return h(NSpace, { size: 'small' }, {
        default: () => [
          h(NButton, {
            size: 'small',
            type: row.status === 'active' ? 'warning' : 'primary',
            onClick: () => toggleToolStatus(row)
          }, {
            icon: () => h(NIcon, null, {
              default: () => row.status === 'active' ? h(StopOutline) : h(PlayOutline)
            }),
            default: () => row.status === 'active' ? '停止' : '启动'
          }),
          h(NButton, {
            size: 'small',
            onClick: () => editTool(row)
          }, {
            icon: () => h(NIcon, null, { default: () => h(SettingsOutline) }),
            default: () => '配置'
          }),
          h(NButton, {
             size: 'small',
             onClick: () => viewToolLogs(row)
           }, {
             icon: () => h(NIcon, null, { default: () => h(DocumentTextOutline) }),
             default: () => '日志'
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

// 批量操作
const batchAction = async (action: 'start' | 'stop' | 'delete') => {
  if (selectedRowKeys.value.length === 0) {
    ux.warning('请选择要操作的工具')
    return
  }

  const actionText = action === 'start' ? '启动' : action === 'stop' ? '停止' : '删除'
  
  try {
    batchLoading.value = true
    
    const selectedTools = selectedRowKeys.value.map(toolId => ({
      id: toolId,
      name: tools.value.find(t => t.id === toolId)?.name || `工具${toolId}`
    }))

    const results = await ux.executeBatchWithFeedback(
      selectedTools,
      async (tool) => {
        switch (action) {
          case 'start':
            const startResult = await toolsApi.startTool(tool.id)
            return { id: tool.id, success: true, result: startResult }
          case 'stop':
            const stopResult = await toolsApi.stopTool(tool.id)
            return { id: tool.id, success: true, result: stopResult }
          case 'delete':
            await toolsApi.deleteTool(tool.id, true) // 使用强制删除
            return { id: tool.id, success: true }
          default:
            throw new Error(`未知操作: ${action}`)
        }
      },
      {
        loadingMessage: `正在批量${actionText}工具...`,
        successMessage: `批量${actionText}完成`,
        errorMessage: `批量${actionText}失败`,
        confirmMessage: undefined,
        showProgress: true,
        continueOnError: true
      }
    )
    
    // 更新本地数据
    if (results.results.length > 0) {
      const successIds = results.results
        .filter(r => r && r.id)
        .map(r => r.id)
        
      if (action === 'delete') {
        tools.value = tools.value.filter(tool => !successIds.includes(tool.id))
      } else {
        tools.value.forEach(tool => {
          if (successIds.includes(tool.id)) {
            tool.status = action === 'start' ? 'active' : 'inactive'
          }
        })
      }
      selectedRowKeys.value = []
    }
    
    // 显示操作摘要
    ux.showOperationSummary(`批量${actionText}工具`, {
      total: selectedTools.length,
      success: results.results.length,
      failed: results.errors.length
    })
    
  } catch (error) {
    console.error(`批量${actionText}失败:`, error)
    ux.error(`批量${actionText}失败: ${error.message || error}`)
  } finally {
    batchLoading.value = false
  }
 }
 
 // 刷新分类列表
 const refreshCategories = async () => {
   await ux.executeWithFeedback(
     async () => {
       const response = await toolsApi.getCategories()
       const categories = response.data || []
       
       // 更新分类选项，保留默认分类并添加从后端获取的分类
       const defaultCategories = [
         { label: '文件操作', value: 'file' },
         { label: '数据库', value: 'database' },
         { label: '网络请求', value: 'network' },
         { label: '系统工具', value: 'system' },
         { label: '其他', value: 'other' }
       ]
       
       const dynamicCategories = categories
         .filter(cat => !defaultCategories.some(def => def.value === cat))
         .map(cat => ({ label: cat, value: cat }))
       
       categoryOptions.value = [...defaultCategories, ...dynamicCategories]
       
       return { count: categoryOptions.value.length }
     },
     {
       loadingMessage: '正在刷新分类列表...',
       successMessage: (result) => `已刷新分类列表，共 ${result.count} 个分类`,
       errorMessage: '刷新分类失败'
     }
   )
 }

// 批量导出选中工具
const batchExport = async () => {
  if (selectedRowKeys.value.length === 0) {
    ux.warning('请选择要导出的工具')
    return
  }

  await ux.executeWithFeedback(
    async () => {
      const selectedTools = tools.value.filter(tool => selectedRowKeys.value.includes(tool.id))
      const config = {
        tools: selectedTools,
        exportTime: new Date().toISOString(),
        count: selectedTools.length
      }
      
      const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `mcp-tools-selected-${new Date().toISOString().split('T')[0]}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      
      return { count: selectedTools.length }
    },
    {
      loadingMessage: '正在导出工具配置...',
      successMessage: (result) => `已导出 ${result.count} 个工具配置`,
      errorMessage: '导出失败'
    }
  )
}

// 统计数据
const runningCount = computed(() => {
  return tools.value.filter(tool => tool.status === 'active' || tool.status === 'running').length
})

const stoppedCount = computed(() => {
  return tools.value.filter(tool => tool.status === 'inactive' || tool.status === 'stopped').length
})

const errorCount = computed(() => {
  return tools.value.filter(tool => tool.status === 'error').length
})

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
    await ux.executeWithFeedback(
      async () => {
        const response = await toolsApi.getTools()
        
        // 使用通用数据处理工具
        tools.value = DataUtils.normalizeApiResponse<Tool>(response)
        
        return { count: tools.value.length }
      },
      {
        loadingMessage: '正在刷新工具列表...',
        successMessage: `刷新成功，共 ${tools.value.length} 个工具`,
        errorMessage: '刷新失败，请稍后重试'
      }
    )
  } catch (error) {
    console.error('refreshTools执行失败:', error)
    tools.value = []
    // 使用增强的错误处理，支持自动重试
    handleApiError(error, '获取工具列表失败', undefined, true)
  }
}

// 添加工具
const handleAddTool = async () => {
  await ux.executeWithFeedback(
    async () => {
      try {
        // 表单验证
        await formRef.value?.validate()
        
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
        
        const newTool = await toolsApi.createTool(createData)
        
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
        
        // 刷新工具列表
        await refreshTools()
        
        return { toolName: formData.value.name }
      } catch (error) {
        // 使用增强的错误处理
        handleApiError(error, '添加工具失败')
        throw error
      }
    },
    {
      loadingMessage: '正在添加工具...',
      successMessage: '工具添加成功，已自动注册到代理服务',
      errorMessage: '添加工具失败，请检查输入信息'
    }
  )
}

// 切换工具状态
const toggleToolStatus = async (tool: Tool) => {
  const isActive = tool.status === 'active'
  const action = isActive ? '停止' : '启动'
  
  await ux.executeWithFeedback(
    async () => {
      try {
        if (isActive) {
          await toolsApi.stopTool(tool.id)
          tool.status = 'inactive'
        } else {
          await toolsApi.startTool(tool.id)
          tool.status = 'active'
        }
        return { toolName: tool.name, action }
      } catch (error) {
        // 使用增强的错误处理，支持自动重试
        handleApiError(error, `${action}工具失败`, undefined, true)
        throw error
      }
    },
    {
      loadingMessage: `正在${action}工具...`,
      successMessage: (result) => `工具 ${result.toolName} 已${result.action}`,
      errorMessage: `${action}工具失败，请稍后重试`
    }
  )
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
  
  await ux.executeWithFeedback(
    async () => {
      try {
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
        
        const response = await toolsApi.updateTool(editingTool.value!.id, updateData)
        
        // 处理API响应数据结构
        let updatedTool = response
        if (response && typeof response === 'object' && 'data' in response) {
          updatedTool = response.data
        }
        
        // 更新本地数据
        const index = tools.value.findIndex(t => t.id === editingTool.value!.id)
        if (index > -1) {
          // 确保更新的工具对象包含完整的字段，特别是id
          tools.value[index] = {
            ...tools.value[index], // 保留原有字段
            ...updatedTool,        // 覆盖更新的字段
            id: editingTool.value!.id // 确保id字段存在
          }
        }
        
        showEditModal.value = false
        const toolName = editingTool.value!.name
        editingTool.value = null
        
        return { toolName }
      } catch (error) {
        // 使用增强的错误处理
        handleApiError(error, '更新工具失败')
        throw error
      }
    },
    {
      loadingMessage: '正在更新工具...',
      successMessage: (result) => `工具 ${result.toolName} 更新成功`,
      errorMessage: '更新工具失败，请稍后重试'
    }
  )
}

// 删除工具
const deleteTool = async (id: number) => {
  const tool = tools.value.find(t => t.id === id)
  if (!tool) return
  
  await ux.executeWithFeedback(
    async () => {
      try {
        await toolsApi.deleteTool(id)
        const index = tools.value.findIndex(tool => tool.id === id)
        if (index > -1) {
          tools.value.splice(index, 1)
        }
        return { toolName: tool.name }
      } catch (error) {
        // 使用增强的错误处理
        handleApiError(error, '删除工具失败')
        throw error
      }
    },
    {
      loadingMessage: '正在删除工具...',
      successMessage: (result) => `工具 ${result.toolName} 删除成功`,
      errorMessage: '删除工具失败，请稍后重试'
    }
  )
}

// 查看工具日志
const viewToolLogs = async (tool: Tool) => {
  try {
    currentToolName.value = tool.name
    showLogModal.value = true
    logLoading.value = true
    currentToolLogs.value = []
    
    const response = await toolsApi.getToolLogs(tool.id)
    // 处理API响应数据结构
    let logs = []
    if (response.success && response.data && response.data.items) {
      logs = response.data.items
    } else if (response.data && Array.isArray(response.data)) {
      logs = response.data
    } else if (typeof response.data === 'string') {
      try {
        const parsedLogs = JSON.parse(response.data)
        logs = Array.isArray(parsedLogs) ? parsedLogs : []
      } catch {
        // 如果不是JSON格式，创建一个简单的日志对象
        logs = [{
          id: Date.now(),
          level: 'INFO',
          message: response.data,
          timestamp: new Date().toISOString(),
          type: 'system'
        }]
      }
    }
    
    currentToolLogs.value = logs
    
    filterLogs()
  } catch (error) {
    console.error('获取工具日志失败:', error)
    currentToolLogs.value = []
    handleApiError(error, '获取日志失败')
  } finally {
    logLoading.value = false
  }
}

// 刷新工具日志
const refreshToolLogs = async () => {
  const tool = tools.value.find(t => t.name === currentToolName.value)
  if (tool) {
    await viewToolLogs(tool)
  }
}

// 清空工具日志
const clearToolLogs = async () => {
  const tool = tools.value.find(t => t.name === currentToolName.value)
  if (tool) {
    try {
      await toolsApi.clearToolLogs(tool.id)
      currentToolLogs.value = []
      filteredLogs.value = []
      message.success('日志清空成功')
    } catch (error) {
      console.error('清空日志失败:', error)
      message.error('清空日志失败')
    }
  }
}

// 过滤日志
const filterLogs = () => {
  let logs = [...currentToolLogs.value]
  
  // 按级别过滤
  if (logLevelFilter.value) {
    logs = logs.filter(log => log.level === logLevelFilter.value)
  }
  
  // 按搜索文本过滤
  if (logSearchText.value) {
    const searchText = logSearchText.value.toLowerCase()
    logs = logs.filter(log => 
      log.message?.toLowerCase().includes(searchText) ||
      log.type?.toLowerCase().includes(searchText)
    )
  }
  
  // 按时间排序（最新的在前）
  logs.sort((a, b) => new Date(b.timestamp || 0).getTime() - new Date(a.timestamp || 0).getTime())
  
  filteredLogs.value = logs
}

// 获取日志级别类型
const getLogLevelType = (level: string) => {
  const levelMap = {
    'DEBUG': 'info',
    'INFO': 'success',
    'WARNING': 'warning',
    'ERROR': 'error',
    'CRITICAL': 'error'
  }
  return levelMap[level] || 'default'
}

// 格式化日志时间
const formatLogTime = (timestamp: string) => {
  if (!timestamp) return ''
  try {
    const date = new Date(timestamp)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch {
    return timestamp
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
        // 检查工具ID是否有效
        if (!ValidationUtils.isValidToolId(tool.id)) {
          // 工具缺少有效的ID，跳过状态更新
          return { id: tool.id, status: 'error' as const }
        }
        
        const response = await toolsApi.getToolStatus(tool.id)
        // 使用状态映射工具
        const statusInfo = StatusMapper.mapToolStatus(response.data.status)
        return { id: tool.id, status: statusInfo.frontendStatus }
      } catch (error) {
        // 静默处理单个工具状态获取失败
        // 获取工具状态失败，静默处理
        return { id: tool.id, status: 'error' as const }
      }
    })
    
    const statusResults = await Promise.all(statusPromises)
    
    // 更新本地状态
    statusResults.forEach(({ id, status }) => {
      const tool = tools.value.find(t => t.id === id)
      if (tool && tool.status !== status) {
        const oldStatus = tool.status
        tool.status = status
        // 工具状态已更新
      }
    })
  } catch (error) {
    console.error('更新工具状态失败:', error)
    // 使用增强的错误处理，但不显示用户提示（后台任务）
    handleApiError(error, '更新工具状态失败', undefined, false, false)
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

// 初始化数据
const init = async () => {
  await refreshTools()
  await refreshCategories()
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

.quick-actions-card {
  margin-bottom: 24px;
  border: 1px dashed #d9d9d9;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 12px;
}

.quick-actions-card :deep(.n-card-header) {
  padding-bottom: 8px;
  font-weight: 600;
  color: #2080f0;
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

.batch-actions {
  margin-top: 16px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.batch-info {
  color: #495057;
  font-weight: 500;
  font-size: 14px;
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

/* 日志显示样式 */
.log-container {
  max-height: 450px;
  overflow-y: auto;
  padding: 8px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
}

.log-entry {
  margin-bottom: 12px;
  padding: 12px;
  background: white;
  border-radius: 6px;
  border-left: 4px solid #d9d9d9;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
}

.log-entry:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  transform: translateY(-1px);
}

.log-entry.log-debug {
  border-left-color: #909399;
}

.log-entry.log-info {
  border-left-color: #409eff;
}

.log-entry.log-warning {
  border-left-color: #e6a23c;
}

.log-entry.log-error {
  border-left-color: #f56c6c;
}

.log-entry.log-critical {
  border-left-color: #f56c6c;
  background: #fef0f0;
}

.log-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
}

.log-timestamp {
  color: #909399;
  margin-right: 8px;
  font-family: 'Courier New', monospace;
}

.log-type {
  color: #606266;
  font-weight: 500;
}

.log-message {
  color: #303133;
  line-height: 1.5;
  word-break: break-word;
  white-space: pre-wrap;
  font-size: 14px;
}

.log-details {
  margin-top: 8px;
}

.log-details :deep(.n-collapse) {
  background: transparent;
}

.log-details :deep(.n-collapse-item__header) {
  padding: 8px 0;
  font-size: 12px;
  color: #606266;
}

.log-details :deep(.n-collapse-item__content-wrapper) {
  padding: 0;
}

.log-details :deep(.n-collapse-item__content-inner) {
  padding: 8px 0;
}

/* 日志过滤器样式 */
.log-container :deep(.n-select) {
  background: white;
}

.log-container :deep(.n-input) {
  background: white;
}

/* 滚动条样式 */
.log-container::-webkit-scrollbar {
  width: 6px;
}

.log-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.log-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.log-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>