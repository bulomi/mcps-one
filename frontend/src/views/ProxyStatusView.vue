<template>
  <div class="proxy-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1>代理管理</h1>
          <p>管理和配置网络代理服务器</p>
        </div>
        <div class="header-right">
          <n-space>
            <n-button type="primary" @click="showAddModal = true">
              <template #icon>
                <n-icon><AddOutline /></n-icon>
              </template>
              添加代理
            </n-button>
            <n-button @click="refreshProxies">
              <template #icon>
                <n-icon><RefreshOutline /></n-icon>
              </template>
              刷新
            </n-button>
            <n-button @click="testAllProxies" :loading="testAllLoading">
              <template #icon>
                <n-icon><PlayOutline /></n-icon>
              </template>
              测试所有
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
          <span class="batch-info">已选择 {{ selectedRowKeys.length }} 个代理</span>
          <n-button size="small" type="success" @click="batchAction('enable')" :loading="batchLoading">
            <template #icon>
              <n-icon><CheckmarkOutline /></n-icon>
            </template>
            批量启用
          </n-button>
          <n-button size="small" type="warning" @click="batchAction('disable')" :loading="batchLoading">
            <template #icon>
              <n-icon><CloseOutline /></n-icon>
            </template>
            批量禁用
          </n-button>
          <n-button size="small" @click="batchAction('test')" :loading="batchLoading">
            <template #icon>
              <n-icon><PlayOutline /></n-icon>
            </template>
            批量测试
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
            确定删除选中的 {{ selectedRowKeys.length }} 个代理吗？此操作不可撤销。
          </n-popconfirm>
          <n-button size="small" @click="selectedRowKeys = []">
            取消选择
          </n-button>
        </n-space>
      </div>
    </div>

    <!-- 统计面板 -->
    <n-grid :cols="5" :x-gap="16" class="stats-grid">
      <n-grid-item>
        <n-card size="small">
          <n-statistic label="总代理数" :value="stats.total" />
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card size="small">
          <n-statistic label="活跃" :value="stats.active" />
          <template #suffix>
            <n-icon color="#18a058"><CheckmarkOutline /></n-icon>
          </template>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card size="small">
          <n-statistic label="非活跃" :value="stats.inactive" />
          <template #suffix>
            <n-icon color="#909399"><CloseOutline /></n-icon>
          </template>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card size="small">
          <n-statistic label="测试中" :value="stats.testing" />
          <template #suffix>
            <n-icon color="#f0a020"><PlayOutline /></n-icon>
          </template>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card size="small">
          <n-statistic label="异常" :value="stats.error" />
          <template #suffix>
            <n-icon color="#d03050"><WarningOutline /></n-icon>
          </template>
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 筛选和搜索 -->
    <n-card class="filter-card">
      <n-space>
        <n-input
          v-model:value="searchQuery"
          placeholder="搜索代理名称或主机"
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
          v-model:value="selectedType"
          placeholder="代理类型"
          clearable
          style="width: 120px"
          :options="typeOptions"
        />
        <n-select
          v-model:value="selectedStatus"
          placeholder="状态"
          clearable
          style="width: 120px"
          :options="statusOptions"
        />
        <n-select
          v-model:value="selectedCountry"
          placeholder="国家"
          clearable
          style="width: 120px"
          :options="countryOptions"
        />
      </n-space>
    </n-card>

    <!-- 代理列表卡片 -->
    <n-card>
      <n-data-table
        :columns="columns"
        :data="filteredProxies"
        :loading="loading"
        :pagination="pagination"
        :row-key="(row: Proxy) => row.id"
        v-model:checked-row-keys="selectedRowKeys"
      />
    </n-card>

    <!-- 添加代理模态框 -->
    <n-modal v-model:show="showAddModal" preset="dialog" title="添加代理">
      <n-form
        ref="addFormRef"
        :model="addForm"
        :rules="addFormRules"
        label-placement="left"
        label-width="auto"
        require-mark-placement="right-hanging"
      >
        <n-form-item label="代理名称" path="name">
          <n-input v-model:value="addForm.name" placeholder="请输入代理名称" />
        </n-form-item>
        <n-form-item label="显示名称" path="display_name">
          <n-input v-model:value="addForm.display_name" placeholder="请输入显示名称" />
        </n-form-item>
        <n-form-item label="描述" path="description">
          <n-input
            v-model:value="addForm.description"
            type="textarea"
            placeholder="请输入代理描述"
            :autosize="{ minRows: 2, maxRows: 4 }"
          />
        </n-form-item>
        <n-form-item label="代理类型" path="type">
          <n-select
            v-model:value="addForm.type"
            placeholder="选择代理类型"
            :options="typeOptions"
          />
        </n-form-item>
        <n-form-item label="主机地址" path="host">
          <n-input v-model:value="addForm.host" placeholder="请输入主机地址" />
        </n-form-item>
        <n-form-item label="端口" path="port">
          <n-input-number
            v-model:value="addForm.port"
            placeholder="请输入端口号"
            :min="1"
            :max="65535"
            style="width: 100%"
          />
        </n-form-item>
        <n-form-item label="用户名" path="username">
          <n-input v-model:value="addForm.username" placeholder="请输入用户名（可选）" />
        </n-form-item>
        <n-form-item label="密码" path="password">
          <n-input
            v-model:value="addForm.password"
            type="password"
            placeholder="请输入密码（可选）"
            show-password-on="click"
          />
        </n-form-item>
        <n-form-item label="超时时间" path="timeout">
          <n-input-number
            v-model:value="addForm.timeout"
            placeholder="超时时间（秒）"
            :min="1"
            :max="300"
            style="width: 100%"
          />
        </n-form-item>
        <n-form-item label="国家" path="country">
          <n-input v-model:value="addForm.country" placeholder="请输入国家（可选）" />
        </n-form-item>
        <n-form-item label="启用" path="enabled">
          <n-switch v-model:value="addForm.enabled" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-space>
          <n-button @click="showAddModal = false">取消</n-button>
          <n-button type="primary" @click="handleAddProxy" :loading="addLoading">
            添加
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 编辑代理模态框 -->
    <n-modal v-model:show="showEditModal" preset="dialog" title="编辑代理">
      <n-form
        ref="editFormRef"
        :model="editForm"
        :rules="addFormRules"
        label-placement="left"
        label-width="auto"
        require-mark-placement="right-hanging"
      >
        <n-form-item label="代理名称" path="name">
          <n-input v-model:value="editForm.name" placeholder="请输入代理名称" />
        </n-form-item>
        <n-form-item label="显示名称" path="display_name">
          <n-input v-model:value="editForm.display_name" placeholder="请输入显示名称" />
        </n-form-item>
        <n-form-item label="描述" path="description">
          <n-input
            v-model:value="editForm.description"
            type="textarea"
            placeholder="请输入代理描述"
            :autosize="{ minRows: 2, maxRows: 4 }"
          />
        </n-form-item>
        <n-form-item label="代理类型" path="type">
          <n-select
            v-model:value="editForm.type"
            placeholder="选择代理类型"
            :options="typeOptions"
          />
        </n-form-item>
        <n-form-item label="主机地址" path="host">
          <n-input v-model:value="editForm.host" placeholder="请输入主机地址" />
        </n-form-item>
        <n-form-item label="端口" path="port">
          <n-input-number
            v-model:value="editForm.port"
            placeholder="请输入端口号"
            :min="1"
            :max="65535"
            style="width: 100%"
          />
        </n-form-item>
        <n-form-item label="用户名" path="username">
          <n-input v-model:value="editForm.username" placeholder="请输入用户名（可选）" />
        </n-form-item>
        <n-form-item label="密码" path="password">
          <n-input
            v-model:value="editForm.password"
            type="password"
            placeholder="请输入密码（可选）"
            show-password-on="click"
          />
        </n-form-item>
        <n-form-item label="超时时间" path="timeout">
          <n-input-number
            v-model:value="editForm.timeout"
            placeholder="超时时间（秒）"
            :min="1"
            :max="300"
            style="width: 100%"
          />
        </n-form-item>
        <n-form-item label="国家" path="country">
          <n-input v-model:value="editForm.country" placeholder="请输入国家（可选）" />
        </n-form-item>
        <n-form-item label="启用" path="enabled">
          <n-switch v-model:value="editForm.enabled" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-space>
          <n-button @click="showEditModal = false">取消</n-button>
          <n-button type="primary" @click="handleEditProxy" :loading="editLoading">
            保存
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue';
import {
  NButton,
  NCard,
  NDataTable,
  NDropdown,
  NForm,
  NFormItem,
  NGrid,
  NGridItem,
  NIcon,
  NInput,
  NInputNumber,
  NModal,
  NPagination,
  NPopconfirm,
  NSelect,
  NSpace,
  NStatistic,
  NSwitch,
  NTag,
  useMessage,
  type DataTableColumns,
  type FormInst,
  type FormRules
} from 'naive-ui';
import {
  AddOutline,
  CheckmarkOutline,
  CloseOutline,
  EllipsisHorizontalOutline,
  PlayOutline,
  RefreshOutline,
  SearchOutline,
  TrashOutline,
  WarningOutline
} from '@vicons/ionicons5';
import { proxyApi, type Proxy, type CreateProxyRequest, type ProxyStats } from '@/api/proxy';

const message = useMessage();

// 响应式数据
const loading = ref(false);
const proxies = ref<Proxy[]>([]);
const stats = ref<ProxyStats>({
  total: 0,
  active: 0,
  inactive: 0,
  testing: 0,
  error: 0,
  by_type: {},
  by_country: {},
  average_response_time: 0,
  success_rate: 0
});

// 搜索和筛选
const searchQuery = ref('');
const selectedCategory = ref<string | null>(null);
const selectedType = ref<string | null>(null);
const selectedStatus = ref<string | null>(null);
const selectedCountry = ref<string | null>(null);

// 表格相关
const selectedRowKeys = ref<number[]>([]);
const pagination = reactive({
  page: 1,
  pageSize: 20,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100],
  onChange: (page: number) => {
    pagination.page = page;
    loadProxies();
  },
  onUpdatePageSize: (pageSize: number) => {
    pagination.pageSize = pageSize;
    pagination.page = 1;
    loadProxies();
  }
});

// 模态框
const showAddModal = ref(false);
const showEditModal = ref(false);
const addLoading = ref(false);
const editLoading = ref(false);
const testAllLoading = ref(false);
const batchLoading = ref(false);

// 表单
const addFormRef = ref<FormInst | null>(null);
const editFormRef = ref<FormInst | null>(null);

const addForm = reactive<CreateProxyRequest>({
  name: '',
  display_name: '',
  description: '',
  type: 'http',
  protocol: 'http',
  host: '',
  port: 8080,
  username: '',
  password: '',
  timeout: 30,
  enabled: true,
  country: ''
});

const editForm = reactive<CreateProxyRequest & { id: number }>({
  id: 0,
  name: '',
  display_name: '',
  description: '',
  type: 'http',
  protocol: 'http',
  host: '',
  port: 8080,
  username: '',
  password: '',
  timeout: 30,
  enabled: true,
  country: ''
});

// 表单验证规则
const addFormRules: FormRules = {
  name: [
    { required: true, message: '请输入代理名称', trigger: 'blur' },
    { min: 2, max: 50, message: '代理名称长度应在 2-50 个字符之间', trigger: 'blur' }
  ],
  display_name: [
    { required: true, message: '请输入显示名称', trigger: 'blur' },
    { min: 2, max: 100, message: '显示名称长度应在 2-100 个字符之间', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择代理类型', trigger: 'change' }
  ],
  host: [
    { required: true, message: '请输入主机地址', trigger: 'blur' }
  ],
  port: [
    { required: true, message: '请输入端口号', trigger: 'blur' },
    { type: 'number', min: 1, max: 65535, message: '端口号应在 1-65535 之间', trigger: 'blur' }
  ]
};

// 选项数据
const typeOptions = [
  { label: 'HTTP', value: 'http' },
  { label: 'HTTPS', value: 'https' },
  { label: 'SOCKS4', value: 'socks4' },
  { label: 'SOCKS5', value: 'socks5' }
];

const statusOptions = [
  { label: '活跃', value: 'active' },
  { label: '非活跃', value: 'inactive' },
  { label: '测试中', value: 'testing' },
  { label: '异常', value: 'error' }
];

const categoryOptions = ref<Array<{ label: string; value: string }>>([]);
const countryOptions = ref<Array<{ label: string; value: string }>>([]);

// 更多操作选项
const moreOptions = [
  {
    label: '导出配置',
    key: 'export'
  },
  {
    label: '导入配置',
    key: 'import'
  },
  {
    label: '清理失效代理',
    key: 'cleanup'
  }
];

// 表格列定义
const columns: DataTableColumns<Proxy> = [
  {
    type: 'selection'
  },
  {
    title: '名称',
    key: 'display_name',
    width: 150,
    ellipsis: {
      tooltip: true
    }
  },
  {
    title: '类型',
    key: 'type',
    width: 80,
    render: (row) => {
      const typeMap: Record<string, { color: string; text: string }> = {
        http: { color: 'info', text: 'HTTP' },
        https: { color: 'success', text: 'HTTPS' },
        socks4: { color: 'warning', text: 'SOCKS4' },
        socks5: { color: 'error', text: 'SOCKS5' }
      };
      const config = typeMap[row.type] || { color: 'default', text: row.type };
      return h(NTag, { type: config.color as any }, { default: () => config.text });
    }
  },
  {
    title: '地址',
    key: 'address',
    width: 200,
    render: (row) => `${row.host}:${row.port}`
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render: (row) => {
      const statusMap: Record<string, { color: string; text: string }> = {
        active: { color: 'success', text: '活跃' },
        inactive: { color: 'default', text: '非活跃' },
        testing: { color: 'warning', text: '测试中' },
        error: { color: 'error', text: '异常' }
      };
      const config = statusMap[row.status] || { color: 'default', text: row.status };
      return h(NTag, { type: config.color as any }, { default: () => config.text });
    }
  },
  {
    title: '国家',
    key: 'country',
    width: 80
  },
  {
    title: '响应时间',
    key: 'average_response_time',
    width: 100,
    render: (row) => row.average_response_time ? `${row.average_response_time}ms` : '-'
  },
  {
    title: '成功率',
    key: 'success_rate',
    width: 100,
    render: (row) => {
      if (row.total_requests && row.successful_requests) {
        const rate = (row.successful_requests / row.total_requests * 100).toFixed(1);
        return `${rate}%`;
      }
      return '-';
    }
  },
  {
    title: '启用',
    key: 'enabled',
    width: 80,
    render: (row) => {
      return h(NTag, { 
        type: row.enabled ? 'success' : 'default' 
      }, { 
        default: () => row.enabled ? '是' : '否' 
      });
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    render: (row) => {
      return h(NSpace, { size: 'small' }, {
        default: () => [
          h(NButton, {
            size: 'small',
            type: 'primary',
            onClick: () => testProxy(row.id)
          }, { default: () => '测试' }),
          h(NButton, {
            size: 'small',
            onClick: () => editProxy(row)
          }, { default: () => '编辑' }),
          h(NPopconfirm, {
            onPositiveClick: () => deleteProxy(row.id)
          }, {
            trigger: () => h(NButton, {
              size: 'small',
              type: 'error'
            }, { default: () => '删除' }),
            default: () => '确定删除此代理吗？'
          })
        ]
      });
    }
  }
];

// 计算属性
const filteredProxies = computed(() => {
  let result = proxies.value;

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    result = result.filter(proxy => 
      proxy.name.toLowerCase().includes(query) ||
      proxy.display_name.toLowerCase().includes(query) ||
      proxy.host.toLowerCase().includes(query)
    );
  }

  if (selectedType.value) {
    result = result.filter(proxy => proxy.type === selectedType.value);
  }

  if (selectedStatus.value) {
    result = result.filter(proxy => proxy.status === selectedStatus.value);
  }

  if (selectedCountry.value) {
    result = result.filter(proxy => proxy.country === selectedCountry.value);
  }

  return result;
});

// 方法
const loadProxies = async () => {
  try {
    loading.value = true;
    const response = await proxyApi.getProxies(
      pagination.page,
      pagination.pageSize,
      {
        category: selectedCategory.value || undefined,
        proxy_type: selectedType.value || undefined,
        status: selectedStatus.value || undefined,
        country: selectedCountry.value || undefined,
        search: searchQuery.value || undefined
      }
    );
    proxies.value = response.data.items || [];
    pagination.itemCount = response.data.total || 0;
  } catch (error) {
    message.error('加载代理列表失败: ' + error);
  } finally {
    loading.value = false;
  }
};

const loadStats = async () => {
  try {
    const response = await proxyApi.getProxyStats();
    stats.value = response.data;
  } catch (error) {
    console.error('加载统计信息失败:', error);
  }
};

const refreshProxies = () => {
  loadProxies();
  loadStats();
};

const handleAddProxy = async () => {
  try {
    await addFormRef.value?.validate();
    addLoading.value = true;
    
    await proxyApi.createProxy({
      ...addForm,
      protocol: addForm.type // 设置协议与类型相同
    });
    
    message.success('代理添加成功');
    showAddModal.value = false;
    resetAddForm();
    refreshProxies();
  } catch (error) {
    message.error('添加代理失败: ' + error);
  } finally {
    addLoading.value = false;
  }
};

const editProxy = (proxy: Proxy) => {
  Object.assign(editForm, proxy);
  showEditModal.value = true;
};

const handleEditProxy = async () => {
  try {
    await editFormRef.value?.validate();
    editLoading.value = true;
    
    await proxyApi.updateProxy(editForm.id, {
      ...editForm,
      protocol: editForm.type // 设置协议与类型相同
    });
    
    message.success('代理更新成功');
    showEditModal.value = false;
    refreshProxies();
  } catch (error) {
    message.error('更新代理失败: ' + error);
  } finally {
    editLoading.value = false;
  }
};

const deleteProxy = async (id: number) => {
  try {
    await proxyApi.deleteProxy(id);
    message.success('代理删除成功');
    refreshProxies();
  } catch (error) {
    message.error('删除代理失败: ' + error);
  }
};

const testProxy = async (id: number) => {
  try {
    const response = await proxyApi.testProxy(id);
    if (response.data.success) {
      message.success(`代理测试成功，响应时间: ${response.data.response_time}ms`);
    } else {
      message.warning(`代理测试失败: ${response.data.error_message}`);
    }
    refreshProxies();
  } catch (error) {
    message.error('测试代理失败: ' + error);
  }
};

const testAllProxies = async () => {
  try {
    testAllLoading.value = true;
    await proxyApi.testAllProxies();
    message.success('批量测试已开始，请稍后查看结果');
    refreshProxies();
  } catch (error) {
    message.error('批量测试失败: ' + error);
  } finally {
    testAllLoading.value = false;
  }
};

const batchAction = async (action: 'enable' | 'disable' | 'delete' | 'test') => {
  if (selectedRowKeys.value.length === 0) {
    message.warning('请先选择要操作的代理');
    return;
  }

  try {
    batchLoading.value = true;
    await proxyApi.batchOperation(action, selectedRowKeys.value);
    
    const actionMap = {
      enable: '启用',
      disable: '禁用',
      delete: '删除',
      test: '测试'
    };
    
    message.success(`批量${actionMap[action]}成功`);
    selectedRowKeys.value = [];
    refreshProxies();
  } catch (error) {
    message.error(`批量操作失败: ${error}`);
  } finally {
    batchLoading.value = false;
  }
};

const handleMoreAction = (key: string) => {
  switch (key) {
    case 'export':
      // TODO: 实现导出功能
      message.info('导出功能开发中');
      break;
    case 'import':
      // TODO: 实现导入功能
      message.info('导入功能开发中');
      break;
    case 'cleanup':
      // TODO: 实现清理功能
      message.info('清理功能开发中');
      break;
  }
};

const resetAddForm = () => {
  Object.assign(addForm, {
    name: '',
    display_name: '',
    description: '',
    type: 'http',
    protocol: 'http',
    host: '',
    port: 8080,
    username: '',
    password: '',
    timeout: 30,
    enabled: true,
    country: ''
  });
};

// 监听搜索和筛选变化
watch([searchQuery, selectedCategory, selectedType, selectedStatus, selectedCountry], () => {
  pagination.page = 1;
  loadProxies();
}, { deep: true });

// 组件挂载时加载数据
onMounted(() => {
  loadProxies();
  loadStats();
  
  // 加载国家选项
  const countries = [...new Set(proxies.value.map(p => p.country).filter(Boolean))];
  countryOptions.value = countries.map(country => ({ label: country, value: country }));
});
</script>

<style scoped>
.proxy-view {
  padding: 16px;
}

.page-header {
  margin-bottom: 16px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.header-left h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
}

.header-left p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.batch-actions {
  padding: 12px 16px;
  background: #f5f5f5;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
}

.batch-info {
  font-size: 14px;
  color: #666;
}

.stats-grid {
  margin-bottom: 16px;
}

.filter-card {
  margin-bottom: 16px;
}

.dropdown-wrapper {
  position: relative;
}
</style>