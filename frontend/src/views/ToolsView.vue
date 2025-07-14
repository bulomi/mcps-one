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
          </n-space>
        </div>
      </div>
    </div>

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

    <!-- 工具列表 -->
    <n-card>
      <n-data-table
        :columns="columns"
        :data="filteredTools"
        :loading="loading"
        :pagination="pagination"
        :row-key="(row: Tool) => row.id"
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
          <n-input v-model:value="formData.name" placeholder="请输入工具名称" />
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
        <n-form-item label="配置文件路径" path="config_path">
          <n-input v-model:value="formData.config_path" placeholder="请输入配置文件路径" />
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
  NDataTable,
  NIcon,
  NTag,
  NModal,
  NForm,
  NFormItem,
  NDynamicTags,
  NPopconfirm,
  type DataTableColumns
} from 'naive-ui'
import {
  AddOutline,
  RefreshOutline,
  SearchOutline,
  PlayOutline,
  StopOutline,
  SettingsOutline,
  TrashOutline
} from '@vicons/ionicons5'
import { toolsApi, type Tool, type CreateToolRequest } from '../api/tools'

// 消息提示函数
const showMessage = (type: 'success' | 'error' | 'info' | 'warning', content: string) => {
  console.log(`[${type.toUpperCase()}] ${content}`)
  // 这里可以使用其他方式显示消息，比如浏览器通知或自定义组件
}

// 响应式数据
const loading = ref(false)
const showAddModal = ref(false)
const searchQuery = ref('')
const selectedCategory = ref<string | null>(null)
const selectedStatus = ref<string | null>(null)

// 工具列表数据
const tools = ref<Tool[]>([])

// 表单数据
const formData = ref({
  name: '',
  description: '',
  category: '',
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

// 分类选项
const categoryOptions = [
  { label: '文件操作', value: 'file' },
  { label: '数据库', value: 'database' },
  { label: '网络请求', value: 'network' },
  { label: '系统工具', value: 'system' },
  { label: '其他', value: 'other' }
]

// 状态选项
const statusOptions = [
  { label: '运行中', value: 'active' },
  { label: '已停止', value: 'inactive' },
  { label: '错误', value: 'error' }
]

// 表格列定义
const columns: DataTableColumns<Tool> = [
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
    title: '分类',
    key: 'category',
    width: 100,
    render(row) {
      const category = categoryOptions.find(c => c.value === row.category)
      return category?.label || row.category
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
        error: { type: 'error', text: '错误' }
      }
      const status = statusMap[row.status]
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
    showMessage('success', '刷新成功')
  } catch (error) {
    console.error('获取工具列表失败:', error)
    showMessage('error', '刷新失败')
    tools.value = []
  } finally {
    loading.value = false
  }
}

// 添加工具
const handleAddTool = async () => {
  try {
    const createData: CreateToolRequest = {
      name: formData.value.name,
      description: formData.value.description,
      category: formData.value.category,
      config_path: formData.value.config_path,
      tags: formData.value.tags
    }
    
    const newTool = await toolsApi.createTool(createData)
    tools.value.push(newTool)
    showAddModal.value = false
    formData.value = {
      name: '',
      description: '',
      category: '',
      config_path: '',
      tags: []
    }
    showMessage('success', '添加成功')
  } catch (error) {
    console.error('添加工具失败:', error)
    showMessage('error', '添加失败')
  }
}

// 切换工具状态
const toggleToolStatus = async (tool: Tool) => {
  try {
    if (tool.status === 'active') {
      await toolsApi.stopTool(tool.id)
      tool.status = 'inactive'
      showMessage('success', '工具已停止')
    } else {
      await toolsApi.startTool(tool.id)
      tool.status = 'active'
      showMessage('success', '工具已启动')
    }
  } catch (error) {
    console.error('切换工具状态失败:', error)
    showMessage('error', '操作失败')
  }
}

// 编辑工具
const editTool = (tool: Tool) => {
  // TODO: 打开编辑模态框
  showMessage('info', '编辑功能开发中')
}

// 删除工具
const deleteTool = async (id: number) => {
  try {
    await toolsApi.deleteTool(id)
    const index = tools.value.findIndex(tool => tool.id === id)
    if (index > -1) {
      tools.value.splice(index, 1)
      showMessage('success', '删除成功')
    }
  } catch (error) {
    console.error('删除工具失败:', error)
    showMessage('error', '删除失败')
  }
}

// 组件挂载时加载数据
onMounted(() => {
  refreshTools()
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
  transform: translateY(-1px);
}
</style>