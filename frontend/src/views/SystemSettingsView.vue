<template>
  <div class="system-settings-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1>系统设置</h1>
          <p>统一配置管理 - 基于新的配置架构</p>
        </div>
        <div class="header-right">
          <n-space>
            <n-badge :value="isDirty ? '●' : ''" color="orange" :show="isDirty">
              <n-button type="primary" @click="saveAllSettings" :loading="saving" :disabled="!isDirty">
                <template #icon>
                  <n-icon><SaveOutline /></n-icon>
                </template>
                保存设置
              </n-button>
            </n-badge>

          </n-space>
        </div>
      </div>
    </div>



    <!-- 设置内容 -->
    <n-tabs type="line" animated>
      <!-- 网站设置 -->
      <n-tab-pane name="app" tab="网站设置">
        <n-card>
          <n-form label-placement="left" label-width="150px">
            <n-form-item label="网站标题">
              <n-input 
                :value="config.app.name" 
                @update:value="(value) => updateConfig('app.name', value)"
                placeholder="请输入网站标题" 
              />
            </n-form-item>
            <n-form-item label="网站副标题">
              <n-input 
                :value="config.app.subtitle" 
                @update:value="(value) => updateConfig('app.subtitle', value)"
                placeholder="请输入网站副标题" 
              />
            </n-form-item>
            <n-form-item label="网站描述">
              <n-input 
                :value="config.app.description" 
                @update:value="(value) => updateConfig('app.description', value)"
                type="textarea"
                placeholder="请输入网站描述" 
              />
            </n-form-item>
            <n-form-item label="显示标题">
              <n-switch 
                :value="config.app.showTitle" 
                @update:value="(value) => updateConfig('app.showTitle', value)"
              />
            </n-form-item>
            <n-form-item label="LOGO设置">
              <n-space vertical>
                <n-radio-group 
                  :value="logoType" 
                  @update:value="(value) => logoType = value"
                >
                  <n-radio value="url">网络地址</n-radio>
                  <n-radio value="upload">上传图片</n-radio>
                </n-radio-group>
                
                <n-input 
                  v-if="logoType === 'url'"
                  :value="config.app.logoUrl" 
                  @update:value="(value) => updateConfig('app.logoUrl', value)"
                  placeholder="请输入LOGO网络地址" 
                />
                
                <n-space v-if="logoType === 'upload'" vertical>
                  <n-upload
                    :file-list="logoFileList"
                    @update:file-list="handleLogoUpload"
                    accept="image/*"
                    :max="1"
                    list-type="image-card"
                  >
                    <n-button>选择图片</n-button>
                  </n-upload>
                  <n-text depth="3" style="font-size: 12px;">
                    支持 JPG、PNG、GIF 格式，建议尺寸 200x60 像素
                  </n-text>
                </n-space>
                
                <!-- LOGO预览 -->
                <n-space v-if="config.app.logoUrl" align="center">
                  <n-text>预览：</n-text>
                  <img 
                    :src="config.app.logoUrl" 
                    alt="LOGO预览" 
                    style="max-height: 40px; max-width: 120px; object-fit: contain;"
                    @error="handleLogoError"
                  />
                </n-space>
              </n-space>
            </n-form-item>
          </n-form>
        </n-card>
      </n-tab-pane>



      <!-- 通知配置 -->
      <n-tab-pane name="notifications" tab="通知配置">
        <n-card>
          <n-grid :cols="2" :x-gap="24">
            <!-- 邮件通知 -->
            <n-grid-item>
              <n-form label-placement="left" label-width="120px">
                <n-form-item label="邮件通知">
                  <n-switch 
                    :value="config.notifications.email.enabled" 
                    @update:value="(value) => updateConfig('notifications.email.enabled', value)"
                  />
                </n-form-item>
                <template v-if="config.notifications.email.enabled">
                  <n-form-item label="SMTP主机">
                    <n-input 
                      :value="config.notifications.email.smtpHost" 
                      @update:value="(value) => updateConfig('notifications.email.smtpHost', value)"
                      placeholder="SMTP服务器地址" 
                    />
                  </n-form-item>
                  <n-form-item label="SMTP端口">
                    <n-input-number 
                      :value="config.notifications.email.smtpPort" 
                      @update:value="(value) => updateConfig('notifications.email.smtpPort', value)"
                      :min="1"
                      :max="65535"
                    />
                  </n-form-item>
                  <n-form-item label="发件人邮箱">
                    <n-input 
                      :value="config.notifications.email.senderEmail" 
                      @update:value="(value) => updateConfig('notifications.email.senderEmail', value)"
                      placeholder="发件人邮箱" 
                    />
                  </n-form-item>
                  <n-form-item label="邮箱密码">
                    <n-input 
                      :value="config.notifications.email.password" 
                      @update:value="(value) => updateConfig('notifications.email.password', value)"
                      type="password"
                      show-password-on="click"
                      placeholder="邮箱密码或授权码" 
                    />
                  </n-form-item>
                  <n-form-item label="收件人邮箱">
                    <n-input 
                      :value="config.notifications.email.recipientEmail" 
                      @update:value="(value) => updateConfig('notifications.email.recipientEmail', value)"
                      placeholder="接收通知的邮箱地址" 
                    />
                  </n-form-item>
                  <n-form-item label="使用SSL">
                    <n-switch 
                      :value="config.notifications.email.useSSL" 
                      @update:value="(value) => updateConfig('notifications.email.useSSL', value)"
                    />
                  </n-form-item>
                  <n-form-item label="使用TLS">
                    <n-switch 
                      :value="config.notifications.email.useTLS" 
                      @update:value="(value) => updateConfig('notifications.email.useTLS', value)"
                    />
                  </n-form-item>
                </template>
              </n-form>
            </n-grid-item>

            <!-- Webhook通知 -->
            <n-grid-item>
              <n-form label-placement="left" label-width="120px">
                <n-form-item label="Webhook通知">
                  <n-switch 
                    :value="config.notifications.webhook.enabled" 
                    @update:value="(value) => updateConfig('notifications.webhook.enabled', value)"
                  />
                </n-form-item>
                <template v-if="config.notifications.webhook.enabled">
                  <n-form-item label="Webhook URL">
                    <n-input 
                      :value="config.notifications.webhook.url" 
                      @update:value="(value) => updateConfig('notifications.webhook.url', value)"
                      placeholder="Webhook回调地址" 
                    />
                  </n-form-item>
                  <n-form-item label="请求方法">
                    <n-select
                      :value="config.notifications.webhook.method"
                      @update:value="(value) => updateConfig('notifications.webhook.method', value)"
                      :options="webhookMethodOptions"
                      placeholder="选择HTTP方法"
                    />
                  </n-form-item>
                  <n-form-item label="超时时间(秒)">
                    <n-input-number 
                      :value="config.notifications.webhook.timeout" 
                      @update:value="(value) => updateConfig('notifications.webhook.timeout', value)"
                      :min="1"
                      :max="300"
                    />
                  </n-form-item>
                  <n-form-item label="重试次数">
                    <n-input-number 
                      :value="config.notifications.webhook.retryCount" 
                      @update:value="(value) => updateConfig('notifications.webhook.retryCount', value)"
                      :min="0"
                      :max="10"
                    />
                  </n-form-item>
                  <n-form-item label="自定义Headers">
                    <n-input 
                      :value="config.notifications.webhook.headers" 
                      @update:value="(value) => updateConfig('notifications.webhook.headers', value)"
                      type="textarea"
                      placeholder='JSON格式，如: {"Authorization": "Bearer token"}'
                      :rows="3"
                    />
                  </n-form-item>
                </template>
              </n-form>
            </n-grid-item>
          </n-grid>

          <!-- 通知事件 -->
          <n-divider />
          <n-form label-placement="left" label-width="120px">
            <n-form-item label="通知事件">
              <n-checkbox-group 
                :value="config.notifications.events" 
                @update:value="(value) => updateConfig('notifications.events', value)"
              >
                <n-grid :cols="2" :x-gap="16" :y-gap="8">
                   <n-grid-item>
                     <n-checkbox value="error_occurred" label="工具错误" />
                   </n-grid-item>
                   <n-grid-item>
                     <n-checkbox value="system_stop" label="系统错误" />
                   </n-grid-item>
                   <n-grid-item>
                     <n-checkbox value="task_completed" label="备份完成" />
                   </n-grid-item>
                   <n-grid-item>
                     <n-checkbox value="task_failed" label="服务停止" />
                   </n-grid-item>
                 </n-grid>
              </n-checkbox-group>
            </n-form-item>
          </n-form>
        </n-card>
      </n-tab-pane>

      <!-- MCP配置 -->
      <n-tab-pane name="mcp" tab="MCP配置">
        <n-grid :cols="2" :x-gap="24">
          <!-- 基础MCP配置 -->
          <n-grid-item>
            <n-card>
              <n-form label-placement="left" label-width="150px">
                <n-form-item label="最大进程数">
                  <n-input-number 
                    :value="config.mcp.maxProcesses" 
                    @update:value="(value) => updateConfig('mcp.maxProcesses', value)"
                    :min="1"
                    :max="100"
                  />
                </n-form-item>
                <n-form-item label="进程超时(秒)">
                  <n-input-number 
                    :value="config.mcp.processTimeout" 
                    @update:value="(value) => updateConfig('mcp.processTimeout', value)"
                    :min="1"
                    :max="300"
                  />
                </n-form-item>
                <n-form-item label="重启延迟(秒)">
                  <n-input-number 
                    :value="config.mcp.restartDelay" 
                    @update:value="(value) => updateConfig('mcp.restartDelay', value)"
                    :min="1"
                    :max="60"
                  />
                </n-form-item>
                <n-form-item label="工具目录">
                  <n-input 
                    :value="config.mcp.toolsDir" 
                    @update:value="(value) => updateConfig('mcp.toolsDir', value)"
                    placeholder="工具存储目录" 
                  />
                </n-form-item>
                <n-form-item label="日志目录">
                  <n-input 
                    :value="config.mcp.logsDir" 
                    @update:value="(value) => updateConfig('mcp.logsDir', value)"
                    placeholder="日志存储目录" 
                  />
                </n-form-item>
              </n-form>
            </n-card>
          </n-grid-item>

          <!-- MCP代理配置 -->
          <n-grid-item>
            <n-card>
              <n-form label-placement="left" label-width="150px">
                <n-form-item label="启用代理">
                  <n-switch 
                    :value="config.mcp.proxy.enabled" 
                    @update:value="(value) => updateConfig('mcp.proxy.enabled', value)"
                  />
                </n-form-item>
                <n-form-item label="自动启动">
                  <n-switch 
                    :value="config.mcp.proxy.autoStart" 
                    @update:value="(value) => updateConfig('mcp.proxy.autoStart', value)"
                  />
                </n-form-item>
                <n-form-item label="优雅关闭">
                  <n-switch 
                    :value="config.mcp.proxy.gracefulShutdown" 
                    @update:value="(value) => updateConfig('mcp.proxy.gracefulShutdown', value)"
                  />
                </n-form-item>
                <n-form-item label="启动超时(秒)">
                  <n-input-number 
                    :value="config.mcp.proxy.toolStartupTimeout" 
                    @update:value="(value) => updateConfig('mcp.proxy.toolStartupTimeout', value)"
                    :min="10"
                    :max="300"
                  />
                </n-form-item>
                <n-form-item label="健康检查间隔(秒)">
                  <n-input-number 
                    :value="config.mcp.proxy.healthCheckInterval" 
                    @update:value="(value) => updateConfig('mcp.proxy.healthCheckInterval', value)"
                    :min="5"
                    :max="300"
                  />
                </n-form-item>
                <n-form-item label="启用指标">
                  <n-switch 
                    :value="config.mcp.proxy.enableMetrics" 
                    @update:value="(value) => updateConfig('mcp.proxy.enableMetrics', value)"
                  />
                </n-form-item>
              </n-form>
            </n-card>
          </n-grid-item>
        </n-grid>
      </n-tab-pane>

      <!-- 日志配置 -->
      <n-tab-pane name="logging" tab="日志配置">
        <n-card>
          <n-form label-placement="left" label-width="150px">
            <n-form-item label="日志级别">
              <n-select
                :value="config.logging.level"
                @update:value="(value) => updateConfig('logging.level', value)"
                :options="logLevelOptions"
                placeholder="选择日志级别"
              />
            </n-form-item>
            <n-form-item label="日志格式">
              <n-input 
                :value="config.logging.format" 
                @update:value="(value) => updateConfig('logging.format', value)"
                placeholder="日志格式字符串" 
              />
            </n-form-item>
            <n-form-item label="日志文件">
              <n-input 
                :value="config.logging.file" 
                @update:value="(value) => updateConfig('logging.file', value)"
                placeholder="日志文件路径" 
              />
            </n-form-item>
            <n-form-item label="最大文件大小">
              <n-input 
                :value="config.logging.maxFileSize" 
                @update:value="(value) => updateConfig('logging.maxFileSize', value)"
                placeholder="如：10MB" 
              />
            </n-form-item>
            <n-form-item label="备份文件数">
              <n-input-number 
                :value="config.logging.backupCount" 
                @update:value="(value) => updateConfig('logging.backupCount', value)"
                :min="1"
                :max="100"
              />
            </n-form-item>
            <n-form-item label="控制台输出">
              <n-switch 
                :value="config.logging.consoleOutput" 
                @update:value="(value) => updateConfig('logging.consoleOutput', value)"
              />
            </n-form-item>
          </n-form>
        </n-card>
      </n-tab-pane>

      <!-- 安全设置 -->
      <n-tab-pane name="security" tab="安全设置">
        <n-card>
          <n-form label-placement="left" label-width="150px">
            <n-form-item label="修改密码">
              <n-space vertical style="width: 100%; max-width: 400px;">
                <n-input
                  v-model:value="passwordForm.oldPassword"
                  type="password"
                  show-password-on="click"
                  placeholder="请输入当前密码"
                  :status="passwordForm.errors.oldPassword ? 'error' : undefined"
                />
                <n-text v-if="passwordForm.errors.oldPassword" type="error" style="font-size: 12px;">
                  {{ passwordForm.errors.oldPassword }}
                </n-text>
                
                <n-input
                  v-model:value="passwordForm.newPassword"
                  type="password"
                  show-password-on="click"
                  placeholder="请输入新密码"
                  :status="passwordForm.errors.newPassword ? 'error' : undefined"
                />
                <n-text v-if="passwordForm.errors.newPassword" type="error" style="font-size: 12px;">
                  {{ passwordForm.errors.newPassword }}
                </n-text>
                
                <n-input
                  v-model:value="passwordForm.confirmPassword"
                  type="password"
                  show-password-on="click"
                  placeholder="请确认新密码"
                  :status="passwordForm.errors.confirmPassword ? 'error' : undefined"
                />
                <n-text v-if="passwordForm.errors.confirmPassword" type="error" style="font-size: 12px;">
                  {{ passwordForm.errors.confirmPassword }}
                </n-text>
                
                <n-space>
                  <n-button
                    type="primary"
                    @click="changePassword"
                    :loading="passwordForm.loading"
                    :disabled="!isPasswordFormValid"
                  >
                    修改密码
                  </n-button>
                  <n-button @click="resetPasswordForm">
                    重置
                  </n-button>
                </n-space>
                
                <n-text depth="3" style="font-size: 12px;">
                  密码要求：至少8位字符，包含字母和数字
                </n-text>
              </n-space>
            </n-form-item>
          </n-form>
        </n-card>
      </n-tab-pane>

    </n-tabs>
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
  NForm,
  NFormItem,
  NSwitch,
  NGrid,
  NGridItem,
  NTabs,
  NTabPane,
  NCheckbox,
  NCheckboxGroup,
  NStatistic,
  NBadge,
  NRadioGroup,
  NRadio,
  NUpload,
  NText,
  useMessage,
  type UploadFileInfo
} from 'naive-ui'
import {
  SaveOutline
} from '@vicons/ionicons5'
import { useConfigStore } from '@/stores/config'
import { systemApi } from '@/api/system'
import { authApi } from '@/api/auth'
import { logLevelOptions } from '@/constants/logLevels'

const configStore = useConfigStore()
const message = useMessage()

// 当前配置（响应式）
const config = computed(() => configStore.config)

// 加载状态
const loading = computed(() => configStore.loading)
const saving = ref(false)
const isDirty = computed(() => configStore.isDirty)

// LOGO相关状态
const logoType = ref('url')
const logoFileList = ref<UploadFileInfo[]>([])

// 密码修改表单
const passwordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
  loading: false,
  errors: {
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
  }
})











// Webhook方法选项
const webhookMethodOptions = [
  { label: 'POST', value: 'POST' },
  { label: 'PUT', value: 'PUT' },
  { label: 'PATCH', value: 'PATCH' }
]

// 密码表单验证
const isPasswordFormValid = computed(() => {
  return passwordForm.value.oldPassword.length > 0 &&
         passwordForm.value.newPassword.length >= 8 &&
         passwordForm.value.confirmPassword === passwordForm.value.newPassword &&
         /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$/.test(passwordForm.value.newPassword)
})



// 处理配置更新
const updateConfig = (key: string, value: any) => {
  configStore.set(key, value)
}

// 保存所有设置
const saveAllSettings = async () => {
  saving.value = true
  try {
    await configStore.saveToServer()
    message.success('设置保存成功')
  } catch (error) {
    console.error('保存设置失败:', error)
    message.error('保存设置失败')
  } finally {
    saving.value = false
  }
}

// 验证密码表单
const validatePasswordForm = () => {
  const errors = {
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
  }

  if (!passwordForm.value.oldPassword) {
    errors.oldPassword = '请输入当前密码'
  }

  if (!passwordForm.value.newPassword) {
    errors.newPassword = '请输入新密码'
  } else if (passwordForm.value.newPassword.length < 8) {
    errors.newPassword = '密码长度至少8位'
  } else if (!/^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$/.test(passwordForm.value.newPassword)) {
    errors.newPassword = '密码必须包含字母和数字'
  }

  if (!passwordForm.value.confirmPassword) {
    errors.confirmPassword = '请确认新密码'
  } else if (passwordForm.value.confirmPassword !== passwordForm.value.newPassword) {
    errors.confirmPassword = '两次输入的密码不一致'
  }

  passwordForm.value.errors = errors
  return !Object.values(errors).some(error => error !== '')
}

// 修改密码
const changePassword = async () => {
  if (!validatePasswordForm()) {
    return
  }

  passwordForm.value.loading = true
  try {
    await authApi.changePassword({
      old_password: passwordForm.value.oldPassword,
      new_password: passwordForm.value.newPassword
    })
    message.success('密码修改成功')
    resetPasswordForm()
  } catch (error: any) {
    console.error('密码修改失败:', error)
    if (error.response?.data?.detail) {
      message.error(error.response.data.detail)
    } else {
      message.error('密码修改失败，请重试')
    }
  } finally {
    passwordForm.value.loading = false
  }
}

// 重置密码表单
const resetPasswordForm = () => {
  passwordForm.value.oldPassword = ''
  passwordForm.value.newPassword = ''
  passwordForm.value.confirmPassword = ''
  passwordForm.value.errors = {
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
  }
}


   



// LOGO上传处理
const handleLogoUpload = async (fileList: UploadFileInfo[]) => {
  logoFileList.value = fileList
  if (fileList.length > 0) {
    const file = fileList[0].file
    if (file) {
      try {
        // 创建FormData对象
        const formData = new FormData()
        formData.append('file', file)
        
        // 调用后端API上传文件
        const response = await systemApi.uploadLogo(formData)
        
        if (response.success && response.data?.url) {
          // 更新配置中的LOGO URL
          updateConfig('app.logoUrl', response.data.url)
          // 保存配置到服务器
          await configStore.saveToServer()
          message.success('LOGO上传并保存成功')
        } else {
          message.error(response.message || 'LOGO上传失败')
        }
      } catch (error) {
        console.error('LOGO上传失败:', error)
        message.error('LOGO上传失败，请重试')
      }
    }
  } else {
    updateConfig('app.logoUrl', '')
    // 保存配置到服务器
    await configStore.saveToServer()
  }
}

// LOGO加载错误处理
const handleLogoError = () => {
  message.warning('LOGO加载失败，请检查地址是否正确')
}

// 组件挂载时初始化
onMounted(async () => {
  configStore.initialize()
  // 等待配置加载完成
  await configStore.loadFromServer()
  // 根据当前LOGO地址判断类型
  if (config.value.app.logoUrl) {
    logoType.value = config.value.app.logoUrl.startsWith('data:') ? 'upload' : 'url'
  }
})
</script>

<style scoped>
.system-settings-view {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
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



.n-tabs {
  margin-top: 16px;
}

.n-card {
  margin-bottom: 16px;
}

.n-form-item {
  margin-bottom: 16px;
}

.n-input,
.n-input-number,
.n-select {
  width: 100%;
}

.n-checkbox-group .n-space {
  width: 100%;
}

.n-data-table {
  margin-top: 16px;
}
</style>