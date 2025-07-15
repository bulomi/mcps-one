<template>
  <div class="system-settings-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1>系统设置</h1>
          <p>管理系统配置、用户权限和安全设置</p>
        </div>
        <div class="header-right">
          <n-space>
            <n-button @click="exportSettings">
              <template #icon>
                <n-icon><CloudDownloadOutline /></n-icon>
              </template>
              导出设置
            </n-button>
            <n-button @click="showImportModal = true">
              <template #icon>
                <n-icon><CloudUploadOutline /></n-icon>
              </template>
              导入设置
            </n-button>
            <n-button type="primary" @click="saveAllSettings" :loading="saving">
              <template #icon>
                <n-icon><SaveOutline /></n-icon>
              </template>
              保存所有设置
            </n-button>
          </n-space>
        </div>
      </div>
    </div>

    <!-- 设置内容区域 -->
    <n-grid :cols="24" :x-gap="24">
      <!-- 左侧设置分类 -->
      <n-grid-item :span="6">
        <n-card title="设置分类" class="category-card">
          <n-menu
            :value="activeCategory"
            :options="categoryOptions"
            @update:value="handleCategoryChange"
          />
        </n-card>
      </n-grid-item>
      
      <!-- 右侧设置内容 -->
      <n-grid-item :span="18">
        <!-- 基础设置 -->
        <n-card v-if="activeCategory === 'basic'" title="基础设置" class="settings-card">
          <n-form
            ref="basicFormRef"
            :model="basicSettings"
            :rules="basicFormRules"
            label-placement="left"
            label-width="150px"
          >
            <n-form-item label="应用名称" path="appName">
              <n-input v-model:value="basicSettings.appName" placeholder="请输入应用名称" />
            </n-form-item>
            <n-form-item label="应用版本" path="version">
              <n-input v-model:value="basicSettings.version" placeholder="请输入版本号" />
            </n-form-item>
            <n-form-item label="调试模式">
              <n-switch v-model:value="basicSettings.debugMode" />
            </n-form-item>
            <n-form-item label="日志级别">
              <n-select
                v-model:value="basicSettings.logLevel"
                :options="logLevelOptions"
                placeholder="选择日志级别"
              />
            </n-form-item>
            <n-form-item label="语言设置">
              <n-select
                v-model:value="basicSettings.language"
                :options="languageOptions"
                placeholder="选择语言"
              />
            </n-form-item>
            <n-form-item label="时区设置">
              <n-select
                v-model:value="basicSettings.timezone"
                :options="timezoneOptions"
                placeholder="选择时区"
              />
            </n-form-item>
          </n-form>
        </n-card>
        

        

        
        <!-- 通知设置 -->
        <n-card v-if="activeCategory === 'notification'" title="通知设置" class="settings-card">
          <n-form label-placement="left" label-width="150px">
            <n-form-item label="启用邮件通知">
              <n-switch v-model:value="notificationSettings.enableEmail" />
            </n-form-item>
            <div v-if="notificationSettings.enableEmail" class="email-settings">
              <n-form-item label="SMTP服务器">
                <n-input v-model:value="notificationSettings.smtpHost" placeholder="SMTP服务器地址" />
              </n-form-item>
              <n-form-item label="SMTP端口">
                <n-input-number v-model:value="notificationSettings.smtpPort" :min="1" :max="65535" />
              </n-form-item>
              <n-form-item label="发件人邮箱">
                <n-input v-model:value="notificationSettings.senderEmail" placeholder="发件人邮箱地址" />
              </n-form-item>
              <n-form-item label="邮箱密码">
                <n-input
                  v-model:value="notificationSettings.emailPassword"
                  type="password"
                  placeholder="邮箱密码或授权码"
                  show-password-on="click"
                />
              </n-form-item>
              <n-form-item label="启用SSL">
                <n-switch v-model:value="notificationSettings.enableSSL" />
              </n-form-item>
            </div>
            
            <n-form-item label="启用Webhook通知">
              <n-switch v-model:value="notificationSettings.enableWebhook" />
            </n-form-item>
            <n-form-item label="Webhook URL" v-if="notificationSettings.enableWebhook">
              <n-input v-model:value="notificationSettings.webhookUrl" placeholder="Webhook回调地址" />
            </n-form-item>
            
            <n-form-item label="通知事件">
              <n-checkbox-group v-model:value="notificationSettings.events">
                <n-space vertical>
                  <n-checkbox value="tool_error">工具错误</n-checkbox>
                  <n-checkbox value="tool_status_change">工具状态变更</n-checkbox>
                  <n-checkbox value="system_error">系统错误</n-checkbox>
                  <n-checkbox value="backup_complete">备份完成</n-checkbox>
                  <n-checkbox value="security_alert">安全警报</n-checkbox>
                </n-space>
              </n-checkbox-group>
            </n-form-item>
          </n-form>
          
          <n-divider />
          
          <div class="notification-actions">
            <n-space>
              <n-button @click="testEmailNotification" :loading="testingEmail">
                <template #icon>
                  <n-icon><MailOutline /></n-icon>
                </template>
                测试邮件
              </n-button>
              <n-button @click="testWebhookNotification" :loading="testingWebhook">
                <template #icon>
                  <n-icon><LinkOutline /></n-icon>
                </template>
                测试Webhook
              </n-button>
            </n-space>
          </div>
        </n-card>
        

        
        <!-- 高级设置 -->
        <n-card v-if="activeCategory === 'advanced'" title="高级设置" class="settings-card">
          <n-form label-placement="left" label-width="150px">
            <n-form-item label="开发者模式">
              <n-switch v-model:value="advancedSettings.developerMode" />
            </n-form-item>
            <n-form-item label="API文档" v-if="advancedSettings.developerMode">
              <n-switch v-model:value="advancedSettings.enableApiDocs" />
            </n-form-item>
            <n-form-item label="详细错误信息" v-if="advancedSettings.developerMode">
              <n-switch v-model:value="advancedSettings.verboseErrors" />
            </n-form-item>
            <n-form-item label="实验性功能">
              <n-switch v-model:value="advancedSettings.experimentalFeatures" />
            </n-form-item>
            <n-form-item label="自动更新">
              <n-switch v-model:value="advancedSettings.autoUpdate" />
            </n-form-item>
            <n-form-item label="更新检查间隔(小时)" v-if="advancedSettings.autoUpdate">
              <n-input-number v-model:value="advancedSettings.updateCheckInterval" :min="1" :max="168" />
            </n-form-item>
            <n-form-item label="数据保留期(天)">
              <n-input-number v-model:value="advancedSettings.dataRetentionDays" :min="1" :max="365" />
            </n-form-item>
            <n-form-item label="清理策略">
              <n-select
                v-model:value="advancedSettings.cleanupStrategy"
                :options="cleanupStrategyOptions"
                placeholder="选择清理策略"
              />
            </n-form-item>
          </n-form>
          
          <n-divider />
          
          <div class="advanced-actions">
            <n-space>
              <n-button @click="resetToDefaults" type="warning">
                <template #icon>
                  <n-icon><RefreshOutline /></n-icon>
                </template>
                重置为默认值
              </n-button>
              <n-button @click="clearCache">
                <template #icon>
                  <n-icon><TrashOutline /></n-icon>
                </template>
                清理缓存
              </n-button>
              <n-button @click="showSystemInfo = true">
                <template #icon>
                  <n-icon><InformationCircleOutline /></n-icon>
                </template>
                系统信息
              </n-button>
            </n-space>
          </div>
        </n-card>
      </n-grid-item>
    </n-grid>
    
    <!-- 导入设置模态框 -->
    <n-modal v-model:show="showImportModal" preset="dialog" title="导入系统设置">
      <div class="import-section">
        <n-upload
          ref="uploadRef"
          :file-list="fileList"
          :max="1"
          accept=".json"
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
                支持 JSON 格式的设置文件
              </n-p>
            </div>
          </n-upload-dragger>
        </n-upload>
      </div>
      <template #action>
        <n-space>
          <n-button @click="showImportModal = false">取消</n-button>
          <n-button type="primary" @click="importSettings" :loading="importing">
            导入
          </n-button>
        </n-space>
      </template>
    </n-modal>
    
    <!-- 备份管理模态框 -->
    <n-modal v-model:show="showBackupList" preset="card" title="备份管理" style="width: 800px">
      <n-data-table
        :columns="backupColumns"
        :data="backupList"
        :loading="loadingBackups"
        :pagination="backupPagination"
      />
      <template #action>
        <n-button @click="showBackupList = false">关闭</n-button>
      </template>
    </n-modal>
    
    <!-- 系统信息模态框 -->
    <n-modal v-model:show="showSystemInfo" preset="card" title="系统信息" style="width: 600px">
      <n-descriptions :column="2" bordered>
        <n-descriptions-item label="操作系统">{{ systemInfo.os }}</n-descriptions-item>
        <n-descriptions-item label="CPU架构">{{ systemInfo.arch }}</n-descriptions-item>
        <n-descriptions-item label="内存使用">{{ systemInfo.memory }}</n-descriptions-item>
        <n-descriptions-item label="磁盘使用">{{ systemInfo.disk }}</n-descriptions-item>
        <n-descriptions-item label="运行时间">{{ systemInfo.uptime }}</n-descriptions-item>
        <n-descriptions-item label="Python版本">{{ systemInfo.pythonVersion }}</n-descriptions-item>
        <n-descriptions-item label="数据库版本">{{ systemInfo.databaseVersion }}</n-descriptions-item>
        <n-descriptions-item label="最后更新">{{ systemInfo.lastUpdate }}</n-descriptions-item>
      </n-descriptions>
      <template #action>
        <n-button @click="showSystemInfo = false">关闭</n-button>
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
  NInputNumber,
  NSelect,
  NIcon,
  NModal,
  NForm,
  NFormItem,
  NSwitch,
  NDynamicTags,
  NGrid,
  NGridItem,
  NMenu,
  NDivider,
  NCheckboxGroup,
  NCheckbox,
  NSlider,
  NDataTable,
  NUpload,
  NUploadDragger,
  NText,
  NP,
  NDescriptions,
  NDescriptionsItem,
  useMessage,
  type DataTableColumns,
  type UploadFileInfo,
  type MenuOption
} from 'naive-ui'
import {
  SaveOutline,
  RefreshOutline,
  CheckmarkCircleOutline,
  ArchiveOutline,
  FolderOpenOutline,
  MailOutline,
  LinkOutline,
  TrashOutline,
  InformationCircleOutline,
  CloudUploadOutline,
  CloudDownloadOutline
} from '@vicons/ionicons5'
import { systemApi } from '@/api/system'

// 消息提示函数
const message = useMessage()

// 响应式数据
const saving = ref(false)
const importing = ref(false)
const testingEmail = ref(false)
const testingWebhook = ref(false)
const activeCategory = ref('basic')
const showImportModal = ref(false)

const showSystemInfo = ref(false)
const fileList = ref<UploadFileInfo[]>([])

// 设置分类选项
const categoryOptions: MenuOption[] = [
  {
    label: '基础设置',
    key: 'basic',
    icon: () => h(NIcon, null, { default: () => h('div', '⚙️') })
  },

  {
    label: '通知设置',
    key: 'notification',
    icon: () => h(NIcon, null, { default: () => h('div', '🔔') })
  },

  {
    label: '高级设置',
    key: 'advanced',
    icon: () => h(NIcon, null, { default: () => h('div', '🔧') })
  }
]

// 基础设置
const basicSettings = ref({
  appName: 'MCPS.ONE',
  version: '1.0.0',
  debugMode: false,
  logLevel: 'info',
  language: 'zh-CN',
  timezone: 'Asia/Shanghai'
})



// 通知设置
const notificationSettings = ref({
  enableEmail: false,
  smtpHost: '',
  smtpPort: 587,
  senderEmail: '',
  emailPassword: '',
  enableSSL: true,
  enableWebhook: false,
  webhookUrl: '',
  events: [] as string[]
})



// 高级设置
const advancedSettings = ref({
  developerMode: false,
  enableApiDocs: false,
  verboseErrors: false,
  experimentalFeatures: false,
  autoUpdate: false,
  updateCheckInterval: 24,
  dataRetentionDays: 30,
  cleanupStrategy: 'auto'
})



// 系统信息
const systemInfo = ref({
  os: '',
  arch: '',
  memory: '',
  disk: '',
  uptime: '',
  pythonVersion: '',
  databaseVersion: '',
  lastUpdate: ''
})

// 表单验证规则
const basicFormRules = {
  appName: {
    required: true,
    message: '请输入应用名称',
    trigger: 'blur'
  },
  version: {
    required: true,
    message: '请输入版本号',
    trigger: 'blur'
  }
}

// 选项数据
const logLevelOptions = [
  { label: 'DEBUG', value: 'debug' },
  { label: 'INFO', value: 'info' },
  { label: 'WARNING', value: 'warning' },
  { label: 'ERROR', value: 'error' }
]

const languageOptions = [
  { label: '简体中文', value: 'zh-CN' },
  { label: 'English', value: 'en-US' },
  { label: '日本語', value: 'ja-JP' }
]

const timezoneOptions = [
  { label: '北京时间 (UTC+8)', value: 'Asia/Shanghai' },
  { label: '东京时间 (UTC+9)', value: 'Asia/Tokyo' },
  { label: '纽约时间 (UTC-5)', value: 'America/New_York' },
  { label: '伦敦时间 (UTC+0)', value: 'Europe/London' }
]



const cleanupStrategyOptions = [
  { label: '自动清理', value: 'auto' },
  { label: '手动清理', value: 'manual' },
  { label: '定时清理', value: 'scheduled' }
]



// 方法
const handleCategoryChange = (key: string) => {
  activeCategory.value = key
}

const saveAllSettings = async () => {
  saving.value = true
  try {
    // 保存所有设置到后端
    const allSettings = {
      basic: basicSettings.value,
      notification: notificationSettings.value,
      advanced: advancedSettings.value
    }
    
    await systemApi.saveSettings(allSettings)
    
    message.success('设置保存成功')
  } catch (error) {
    console.error('保存设置失败:', error)
    message.error('保存设置失败')
  } finally {
    saving.value = false
  }
}

const exportSettings = async () => {
  try {
    const allSettings = {
      basic: basicSettings.value,
      notification: notificationSettings.value,
      advanced: advancedSettings.value
    }
    
    const blob = new Blob([JSON.stringify(allSettings, null, 2)], {
      type: 'application/json'
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `system-settings-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    
    message.success('设置导出成功')
  } catch (error) {
    console.error('导出设置失败:', error)
    message.error('导出设置失败')
  }
}

const handleFileChange = (options: { fileList: UploadFileInfo[] }) => {
  fileList.value = options.fileList
}

const importSettings = async () => {
  if (fileList.value.length === 0) {
    message.error('请选择要导入的文件')
    return
  }
  
  importing.value = true
  try {
    const file = fileList.value[0].file
    if (file) {
      const text = await file.text()
      const settings = JSON.parse(text)
      
      await systemApi.importSettings(settings)
      
      // 应用导入的设置
      if (settings.basic) basicSettings.value = { ...basicSettings.value, ...settings.basic }
      if (settings.notification) notificationSettings.value = { ...notificationSettings.value, ...settings.notification }
      if (settings.advanced) advancedSettings.value = { ...advancedSettings.value, ...settings.advanced }
      
      message.success('设置导入成功')
      showImportModal.value = false
      fileList.value = []
    }
  } catch (error) {
    console.error('导入设置失败:', error)
    message.error('导入设置失败，请检查文件格式')
  } finally {
    importing.value = false
  }
}



const testEmailNotification = async () => {
  testingEmail.value = true
  try {
    await systemApi.testEmailNotification('test@example.com')
    
    message.success('邮件通知测试成功')
  } catch (error) {
    console.error('邮件通知测试失败:', error)
    message.error('邮件通知测试失败')
  } finally {
    testingEmail.value = false
  }
}

const testWebhookNotification = async () => {
  testingWebhook.value = true
  try {
    await systemApi.testWebhookNotification(notificationSettings.value.webhook.url)
    
    message.success('Webhook通知测试成功')
  } catch (error) {
    console.error('Webhook通知测试失败:', error)
    message.error('Webhook通知测试失败')
  } finally {
    testingWebhook.value = false
  }
}

const resetToDefaults = async () => {
  try {
    await systemApi.resetToDefaults(true)
    
    // 重置所有设置为默认值
    basicSettings.value = {
      appName: 'MCPS.ONE',
      version: '1.0.0',
      debugMode: false,
      logLevel: 'info',
      language: 'zh-CN',
      timezone: 'Asia/Shanghai'
    }
    
    message.success('设置已重置为默认值')
  } catch (error) {
    console.error('重置设置失败:', error)
    message.error('重置设置失败')
  }
}

const clearCache = async () => {
  try {
    await systemApi.clearCache()
    
    message.success('缓存清理成功')
  } catch (error) {
    console.error('清理缓存失败:', error)
    message.error('清理缓存失败')
  }
}



const loadSystemInfo = async () => {
  try {
    const info = await systemApi.getSystemInfo()
    systemInfo.value = info
  } catch (error) {
    console.error('获取系统信息失败:', error)
    message.error('获取系统信息失败')
  }
}



const loadSettings = async () => {
   try {
     const settings = await systemApi.exportSettings()
     
     if (settings.basic) basicSettings.value = settings.basic
     if (settings.notification) notificationSettings.value = settings.notification
     if (settings.advanced) advancedSettings.value = settings.advanced
   } catch (error) {
     console.error('加载设置失败:', error)
     message.error('加载设置失败')
   }
 }

// 组件挂载时加载数据
onMounted(() => {
  loadSettings()
  loadSystemInfo()
})
</script>

<style scoped>
.system-settings-view {
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

.category-card,
.settings-card {
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: none;
  margin-bottom: 24px;
}

.email-settings {
  margin-left: 20px;
  padding-left: 20px;
  border-left: 3px solid #f0f0f0;
}

.database-actions,
.notification-actions,
.advanced-actions {
  margin-top: 16px;
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
  /* 移除悬浮动画效果 */
}

.n-form-item {
  margin-bottom: 24px;
}

.n-menu {
  background: transparent;
}

.n-menu .n-menu-item {
  border-radius: 8px;
  margin-bottom: 4px;
}

.n-slider {
  margin: 12px 0;
}
</style>