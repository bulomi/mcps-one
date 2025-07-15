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
          <n-popconfirm @positive-click="batchAction('delete')">
            <template #trigger>
              <n-button size="small" type="error" :loading="batchLoading">
                <template #icon>
                  <n-icon><TrashOutline /></n-icon>
                </template>
                批量删除
              </n-button>
            </template>
            确定删除选中的 {{ selectedRowKeys.length }} 个工具吗？此操作不可撤销。
          </n-popconfirm>
          <n-button size="small" @click="selectedRowKeys = []">
            取消选择
          </n-button>
        </n-space>
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
    <n-modal v-model:show="showAddModal" preset="dialog" title="添加 MCP 工具">
      <n-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-placement="left"
        label-width="auto"
      >
        <n-form-item label="工具名称" path="name">
          <n-input v-model:value="formData.name" placeholder="请输入工具名称（英文标识符）" />
        </n-form-item>
        <n-form-item label="显示名称" path="display_name">
          <n-input v-model:value="formData.display_name" placeholder="请输入显示名称" />
        </n-form-item>
        <n-form-item label="描述" path="description">
          <n-input
            v-model:value="formData.description"
            type="textarea"
            placeholder="请输入工具描述"
            :rows="3"
          />
        </n-form-item>
        <n-form-item label="分类" path="category">
          <n-select
            v-model:value="formData.category"
            placeholder="选择分类"
            :options="categoryOptions"
          />
        </n-form-item>
        <n-form-item label="运行命令" path="command">
          <n-input v-model:value="formData.command" placeholder="如: npx -y @mcps-one-hub/playwright-mcp" />
        </n-form-item>
        <n-form-item label="配置文件路径" path="config_path">
          <n-input v-model:value="formData.config_path" placeholder="请输入配置文件路径（可选）" />
        </n-form-item>
        <n-form-item label="标签">
          <n-dynamic-tags v-model:value="formData.tags" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-space>
          <n-button @click="showAddModal = false">取消</n-button>
          <n-button type="primary" @click="handleAddTool">确定</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 工具日志模态框 -->
     <n-modal v-model:show="showLogModal" preset="dialog" :title="`${currentToolName} - 运行日志`" style="width: 80%; max-width: 1000px;">
       <div style="height: 500px; overflow-y: auto; background: #1e1e1e; color: #d4d4d4; padding: 16px; border-radius: 8px; font-family: 'Courier New', monospace; font-size: 14px; line-height: 1.5;">
         <pre v-if="currentToolLogs" style="margin: 0; white-space: pre-wrap;">{{ currentToolLogs }}</pre>
         <div v-else style="text-align: center; color: #888; padding: 50px;">暂无日志数据</div>
       </div>
       <template #action>
         <n-space>
           <n-button @click="refreshToolLogs">刷新日志</n-button>
           <n-button @click="clearToolLogs" type="warning">清空日志</n-button>
           <n-button @click="showLogModal = false">关闭</n-button>
         </n-space>
       </template>
     </n-modal>

     <!-- 性能监控模态框 -->
     <n-modal v-model:show="showPerformanceModal" preset="dialog" :title="`${currentToolName} - 性能监控`" style="width: 90%; max-width: 1200px;">
       <div style="height: 600px; padding: 16px;">
         <n-grid :cols="2" :x-gap="16" :y-gap="16">
           <n-grid-item>
             <n-card title="CPU 使用率" size="small">
               <div style="height: 200px; display: flex; align-items: center; justify-content: center;">
                 <n-progress
                   type="circle"
                   :percentage="currentToolPerformance?.cpu || 0"
                   :color="getPerformanceColor(currentToolPerformance?.cpu || 0)"
                   :stroke-width="8"
                   style="font-size: 24px;"
                 >
                   {{ (currentToolPerformance?.cpu || 0).toFixed(1) }}%
                 </n-progress>
               </div>
             </n-card>
           </n-grid-item>
           <n-grid-item>
             <n-card title="内存使用" size="small">
               <div style="height: 200px; display: flex; align-items: center; justify-content: center;">
                 <n-progress
                   type="circle"
                   :percentage="currentToolPerformance?.memory || 0"
                   :color="getPerformanceColor(currentToolPerformance?.memory || 0)"
                   :stroke-width="8"
                   style="font-size: 24px;"
                 >
                   {{ (currentToolPerformance?.memory || 0).toFixed(1) }}%
                 </n-progress>
               </div>
               <div style="text-align: center; margin-top: 8px; color: #666;">
                 {{ formatBytes(currentToolPerformance?.memoryUsed || 0) }} / {{ formatBytes(currentToolPerformance?.memoryTotal || 0) }}
               </div>
             </n-card>
           </n-grid-item>
         </n-grid>
         <n-card title="运行信息" size="small" style="margin-top: 16px;">
           <n-descriptions :column="2" label-placement="left">
             <n-descriptions-item label="进程ID">{{ currentToolPerformance?.pid || 'N/A' }}</n-descriptions-item>
             <n-descriptions-item label="运行时间">{{ formatUptime(currentToolPerformance?.uptime || 0) }}</n-descriptions-item>
             <n-descriptions-item label="启动时间">{{ formatDateTime(currentToolPerformance?.startTime) }}</n-descriptions-item>
             <n-descriptions-item label="状态">{{ currentToolPerformance?.status || 'unknown' }}</n-descriptions-item>
           </n-descriptions>
         </n-card>
       </div>
       <template #action>
         <n-space>
           <n-button @click="refreshPerformance">刷新数据</n-button>
           <n-button @click="showPerformanceModal = false">关闭</n-button>
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
            <n-form-item label="标签">
              <n-dynamic-tags v-model:value="editFormData.tags" />
            </n-form-item>
          </n-tab-pane>
          
          <n-tab-pane name="config" tab="配置信息">
            <n-form-item label="运行命令" path="command">
              <n-input v-model:value="editFormData.command" placeholder="如: npx -y @mcps-one-hub/playwright-mcp" />
            </n-form-item>
            <n-form-item label="配置文件路径" path="config_path">
              <n-input-group>
                <n-input v-model:value="editFormData.config_path" placeholder="请输入配置文件路径（可选）" />
                <n-button @click="validateConfig" :loading="configValidating" :disabled="!editFormData.config_path">
                  验证
                </n-button>
              </n-input-group>
            </n-form-item>
            <n-form-item v-if="configValidationResult" label="验证结果">
              <n-alert
                :type="configValidationResult.valid ? 'success' : 'error'"
                :title="configValidationResult.valid ? '配置有效' : '配置无效'"
                :show-icon="true"
              >
                <div v-if="!configValidationResult.valid && configValidationResult.errors">
                  <ul>
                    <li v-for="error in configValidationResult.errors" :key="error">{{ error }}</li>
                  </ul>
                </div>
              </n-alert>
            </n-form-item>
          </n-tab-pane>
        </n-tabs>
      </n-form>
      <template #action>
        <n-space>
          <n-button @click="showEditModal = false">取消</n-button>
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
  StatsChartOutline,
  SettingsOutline,
  SearchOutline
} from '@vicons/ionicons5'
import { toolsApi, type Tool, type CreateToolRequest } from '../api/tools'

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
const currentToolLogs = ref('')
const currentToolName = ref('')

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
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `mcp-tools-config-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    
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
  config_path: '',
  tags: [] as string[]
})

// 编辑表单数据
const editFormData = ref({
  name: '',
  description: '',
  category: '',
  command: '',
  config_path: '',
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

// 性能监控相关
const showPerformanceModal = ref(false)
const currentToolPerformance = ref<any>(null)
const performanceData = ref<any[]>([])

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
      return h('div', { style: 'font-weight: 600; color: #2080f0;' }, row.name)
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
      return h('code', { 
        style: 'background: #f5f5f5; padding: 2px 6px; border-radius: 4px; font-size: 12px;' 
      }, row.command || row.config_path || 'N/A')
    }
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render(row) {
      const statusMap = {
        active: { type: 'success', text: '运行中' },
        inactive: { type: 'default', text: '已停止' },
        error: { type: 'error', text: '错误' },
        running: { type: 'success', text: '运行中' },
        stopped: { type: 'default', text: '已停止' },
        starting: { type: 'warning', text: '启动中' },
        stopping: { type: 'warning', text: '停止中' },
        unknown: { type: 'default', text: '未知' }
      }
      const status = statusMap[row.status] || { type: 'default', text: row.status || '未知' }
      return h(NTag, { type: status.type as any }, { default: () => status.text })
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
           h(NButton, {
             size: 'small',
             onClick: () => viewToolPerformance(row),
             disabled: row.status !== 'active'
           }, {
             icon: () => h(NIcon, null, { default: () => h(StatsChartOutline) }),
             default: () => '性能'
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
    message.warning('请选择要操作的工具')
    return
  }

  batchLoading.value = true
  try {
    const promises = selectedRowKeys.value.map(async (toolId) => {
      switch (action) {
        case 'start':
          return await toolsApi.startTool(toolId)
        case 'stop':
          return await toolsApi.stopTool(toolId)
        case 'delete':
          return await toolsApi.deleteTool(toolId)
      }
    })

    await Promise.all(promises)
    
    if (action === 'delete') {
      // 删除本地数据
      tools.value = tools.value.filter(tool => !selectedRowKeys.value.includes(tool.id))
    } else {
      // 更新状态
      tools.value.forEach(tool => {
        if (selectedRowKeys.value.includes(tool.id)) {
          tool.status = action === 'start' ? 'active' : 'inactive'
        }
      })
    }
    
    selectedRowKeys.value = []
    message.success(`批量${action === 'start' ? '启动' : action === 'stop' ? '停止' : '删除'}成功`)
  } catch (error) {
    console.error(`批量${action}失败:`, error)
    message.error(`批量操作失败`)
  } finally {
     batchLoading.value = false
   }
 }
 
 // 刷新分类列表
 const refreshCategories = async () => {
   try {
     loading.value = true
     const categories = await toolsApi.getCategories()
     
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
     
     message.success(`已刷新分类列表，共 ${categoryOptions.value.length} 个分类`)
   } catch (error) {
     console.error('刷新分类失败:', error)
     message.error('刷新分类失败')
   } finally {
     loading.value = false
   }
 }

// 批量导出选中工具
const batchExport = () => {
  if (selectedRowKeys.value.length === 0) {
    message.warning('请选择要导出的工具')
    return
  }

  try {
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
    
    message.success(`已导出 ${selectedTools.length} 个工具配置`)
  } catch (error) {
    console.error('导出选中工具失败:', error)
    message.error('导出失败')
  }
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
  loading.value = true
  try {
    const data = await toolsApi.getTools()
    // 检查返回的数据格式，如果是分页格式则提取 items
    if (data && typeof data === 'object' && 'items' in data) {
      tools.value = data.items || []
    } else if (Array.isArray(data)) {
      tools.value = data
    } else {
      tools.value = []
    }
    message.success('刷新成功')
  } catch (error) {
    console.error('获取工具列表失败:', error)
    message.error('刷新失败')
    tools.value = []
  } finally {
    loading.value = false
  }
}

// 添加工具
const handleAddTool = async () => {
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
      working_directory: '',
      environment_variables: {},
      connection_type: 'stdio',
      auto_start: false,
      restart_on_failure: true,
      max_restart_attempts: 3,
      timeout: 30,
      
      // ToolMetadata fields
      version: '1.0.0',
      author: '',
      homepage: '',
      
      // ToolCreate specific
      enabled: true
    }
    
    const newTool = await toolsApi.createTool(createData)
    showAddModal.value = false
    formData.value = {
      name: '',
      display_name: '',
      description: '',
      category: '',
      command: '',
      config_path: '',
      tags: []
    }
    message.success('工具添加成功，已自动注册到代理服务')
    // 刷新工具列表以确保显示最新数据
    await refreshTools()
  } catch (error) {
    console.error('添加工具失败:', error)
    console.error('错误详情:', JSON.stringify(error, null, 2))
    console.error('错误响应:', error.response)
    console.error('错误响应数据:', error.response?.data)
    console.error('错误详细信息:', error.response?.data?.detail)
    
    let errorMessage = '添加失败，请检查输入信息'
    
    if (error.response?.data?.detail) {
      console.log('Detail type:', typeof error.response.data.detail)
      console.log('Detail is array:', Array.isArray(error.response.data.detail))
      console.log('Detail content:', error.response.data.detail)
      
      if (Array.isArray(error.response.data.detail)) {
        errorMessage = `添加失败: ${error.response.data.detail.map(e => {
          console.log('Processing error item:', e)
          return e.msg || e.message || JSON.stringify(e)
        }).join(', ')}`
      } else {
        errorMessage = `添加失败: ${error.response.data.detail}`
      }
    } else if (error.message) {
      errorMessage = `添加失败: ${error.message}`
    }
    
    message.error(errorMessage)
  }
}

// 切换工具状态
const toggleToolStatus = async (tool: Tool) => {
  try {
    if (tool.status === 'active') {
      await toolsApi.stopTool(tool.id)
      tool.status = 'inactive'
      message.success('工具已停止')
    } else {
      await toolsApi.startTool(tool.id)
      tool.status = 'active'
      message.success('工具已启动')
    }
  } catch (error) {
    console.error('切换工具状态失败:', error)
    message.error('操作失败')
  }
}

// 编辑工具
const editTool = (tool: Tool) => {
  editingTool.value = tool
  editFormData.value = {
    name: tool.name,
    description: tool.description,
    category: tool.category,
    command: tool.command || '',
    config_path: tool.config_path || '',
    tags: [...tool.tags]
  }
  // 清除之前的验证结果
  configValidationResult.value = null
  showEditModal.value = true
}

// 更新工具
const handleUpdateTool = async () => {
  if (!editingTool.value) return
  
  try {
    const updateData = {
      name: editFormData.value.name,
      description: editFormData.value.description,
      category: editFormData.value.category,
      command: editFormData.value.command,
      config_path: editFormData.value.config_path,
      tags: editFormData.value.tags
    }
    
    const updatedTool = await toolsApi.updateTool(editingTool.value.id, updateData)
    
    // 更新本地数据
    const index = tools.value.findIndex(t => t.id === editingTool.value!.id)
    if (index > -1) {
      tools.value[index] = updatedTool
    }
    
    showEditModal.value = false
    editingTool.value = null
    message.success('工具更新成功')
  } catch (error) {
    console.error('更新工具失败:', error)
    message.error('更新失败')
  }
}

// 删除工具
const deleteTool = async (id: number) => {
  try {
    await toolsApi.deleteTool(id)
    const index = tools.value.findIndex(tool => tool.id === id)
    if (index > -1) {
      tools.value.splice(index, 1)
      message.success('删除成功')
    }
  } catch (error) {
    console.error('删除工具失败:', error)
    message.error('删除失败')
  }
}

// 查看工具日志
const viewToolLogs = async (tool: Tool) => {
  try {
    currentToolName.value = tool.name
    showLogModal.value = true
    currentToolLogs.value = '正在加载日志...'
    
    const logs = await toolsApi.getToolLogs(tool.id)
    currentToolLogs.value = logs || '暂无日志数据'
  } catch (error) {
    console.error('获取工具日志失败:', error)
    currentToolLogs.value = '获取日志失败'
    message.error('获取日志失败')
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
      currentToolLogs.value = '日志已清空'
      message.success('日志清空成功')
    } catch (error) {
      console.error('清空日志失败:', error)
      message.error('清空日志失败')
    }
  }
}

// 查看工具性能
const viewToolPerformance = async (tool: Tool) => {
  try {
    currentToolName.value = tool.name
    showPerformanceModal.value = true
    
    const performance = await toolsApi.getToolPerformance(tool.id)
    currentToolPerformance.value = performance
  } catch (error) {
    console.error('获取工具性能失败:', error)
    message.error('获取性能数据失败')
  }
}

// 刷新性能数据
const refreshPerformance = async () => {
  const tool = tools.value.find(t => t.name === currentToolName.value)
  if (tool) {
    await viewToolPerformance(tool)
  }
}

// 获取性能颜色
const getPerformanceColor = (percentage: number) => {
  if (percentage < 50) return '#52c41a'
  if (percentage < 80) return '#faad14'
  return '#ff4d4f'
}

// 格式化字节数
const formatBytes = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 格式化运行时间
const formatUptime = (seconds: number) => {
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  if (days > 0) {
    return `${days}天 ${hours}小时 ${minutes}分钟`
  } else if (hours > 0) {
    return `${hours}小时 ${minutes}分钟`
  } else if (minutes > 0) {
    return `${minutes}分钟 ${secs}秒`
  } else {
    return `${secs}秒`
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
        const status = await toolsApi.getToolStatus(tool.id)
        return { id: tool.id, status: status.status }
      } catch {
        return { id: tool.id, status: 'error' }
      }
    })
    
    const statusResults = await Promise.all(statusPromises)
    
    // 更新本地状态
    statusResults.forEach(({ id, status }) => {
      const tool = tools.value.find(t => t.id === id)
      if (tool && tool.status !== status) {
        tool.status = status as 'active' | 'inactive' | 'error'
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
</style>