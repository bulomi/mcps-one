<template>
  <div class="system-settings-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1>系统设置</h1>
          <p>基本配置管理</p>
        </div>
        <div class="header-right">
          <n-button type="primary" @click="saveAllSettings" :loading="saving" :disabled="!isDirty">
            <template #icon>
              <n-icon><SaveOutline /></n-icon>
            </template>
            保存设置
          </n-button>
        </div>
      </div>
    </div>

    <!-- 设置内容 -->
    <n-space vertical size="large">
      <!-- 基本设置 -->
      <n-card title="基本设置">
        <n-form label-placement="left" label-width="120px">
          <n-form-item label="应用名称">
            <n-input 
              :value="config.app.name" 
              @update:value="(value) => updateConfig('app.name', value)"
              placeholder="请输入应用名称" 
            />
          </n-form-item>
          <n-form-item label="应用描述">
            <n-input 
              :value="config.app.description" 
              @update:value="(value) => updateConfig('app.description', value)"
              type="textarea"
              placeholder="请输入应用描述" 
            />
          </n-form-item>
          <n-form-item label="应用LOGO">
            <div class="logo-upload-container">
              <!-- LOGO预览和上传区域 - 单行显示 -->
              <div class="logo-upload-row">
                <!-- LOGO预览 -->
                <div v-if="config.app.logoUrl" class="logo-preview-inline">
                  <div class="logo-image-wrapper">
                    <img :src="config.app.logoUrl" alt="当前LOGO" class="logo-image" />
                  </div>
                  <div class="logo-status">
                    <n-icon><CheckmarkCircleOutline /></n-icon>
                    <span>已设置</span>
                  </div>
                  <n-button
                    size="small"
                    type="error"
                    ghost
                    @click="removeLogo"
                    class="remove-logo-btn"
                  >
                    <template #icon>
                      <n-icon><TrashOutline /></n-icon>
                    </template>
                    删除
                  </n-button>
                </div>

                <!-- 上传按钮 -->
                 <div class="upload-button-section">
                   <n-upload
                     ref="logoUploadRef"
                     :max="1"
                     accept="image/*"
                     :show-file-list="false"
                     @before-upload="handleLogoUpload"
                     class="logo-upload"
                   >
                     <n-button type="primary" ghost class="upload-button">
                       <template #icon>
                         <n-icon><CloudUploadOutline /></n-icon>
                       </template>
                       {{ config.app.logoUrl ? '更换LOGO' : '上传LOGO' }}
                     </n-button>
                   </n-upload>
                   <n-text depth="3" class="upload-tips-text">
                     支持 JPG/PNG/SVG，最大5MB
                   </n-text>
                 </div>
              </div>
            </div>
          </n-form-item>
        </n-form>
      </n-card>

      <!-- 安全设置 -->
      <n-card title="安全设置">
        <n-form label-placement="left" label-width="120px">
          <n-form-item label="修改密码">
            <n-space vertical style="width: 100%; max-width: 400px;">
              <n-input
                v-model:value="passwordForm.oldPassword"
                type="password"
                show-password-on="click"
                placeholder="请输入当前密码"
              />
              <n-input
                v-model:value="passwordForm.newPassword"
                type="password"
                show-password-on="click"
                placeholder="请输入新密码"
              />
              <n-input
                v-model:value="passwordForm.confirmPassword"
                type="password"
                show-password-on="click"
                placeholder="请确认新密码"
              />
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
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  NCard,
  NButton,
  NSpace,
  NInput,
  NIcon,
  NForm,
  NFormItem,
  NText,
  NUpload,
  NUploadDragger,
  NP,
  useMessage
} from 'naive-ui'
import {
  SaveOutline,
  CloudUploadOutline,
  TrashOutline,
  CheckmarkCircleOutline
} from '@vicons/ionicons5'
import { useConfigStore } from '@/stores/config'
import { authApi } from '@/api/auth'
import { systemApi } from '@/api/system'

const configStore = useConfigStore()
const message = useMessage()

// 当前配置（响应式）
const config = computed(() => configStore.config)

// 加载状态
const saving = ref(false)
const isDirty = computed(() => configStore.isDirty)

// 密码修改表单
const passwordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
  loading: false
})

// LOGO上传引用
const logoUploadRef = ref()













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

// 修改密码
const changePassword = async () => {
  if (!isPasswordFormValid.value) {
    message.error('请检查密码输入')
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
    message.error('密码修改失败，请重试')
  } finally {
    passwordForm.value.loading = false
  }
}

// 重置密码表单
const resetPasswordForm = () => {
  passwordForm.value.oldPassword = ''
  passwordForm.value.newPassword = ''
  passwordForm.value.confirmPassword = ''
}

// 处理LOGO上传
const handleLogoUpload = async (options: { file: any, fileList: any[] }) => {
  try {
    // Naive UI 的 before-upload 事件传递的是包装后的文件对象
    // 需要获取原始的 File 对象
    const file = options.file.file || options.file
    
    // 验证文件类型
    if (!file.type.startsWith('image/')) {
      message.error('请选择图片文件')
      return false
    }
    
    // 验证文件大小（5MB）
    if (file.size > 5 * 1024 * 1024) {
      message.error('文件大小不能超过5MB')
      return false
    }
    
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await systemApi.uploadLogo(formData)
    
    if (response.success) {
      updateConfig('app.logoUrl', response.data.url)
      message.success('LOGO上传成功')
    } else {
      message.error('LOGO上传失败')
    }
  } catch (error) {
    console.error('LOGO上传失败:', error)
    message.error('LOGO上传失败，请重试')
  }
  return false // 阻止默认上传行为
}

// 删除LOGO
const removeLogo = () => {
  updateConfig('app.logoUrl', '')
  message.success('LOGO已删除')
}

// 组件挂载时初始化
onMounted(async () => {
  configStore.initialize()
  await configStore.loadFromServer()
})
</script>

<style scoped>
.system-settings-view {
  padding: 24px;
  max-width: 800px;
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

.n-form-item {
  margin-bottom: 16px;
}

.n-input {
  width: 100%;
}

/* LOGO上传容器 */
.logo-upload-container {
  width: 100%;
}

.logo-upload-row {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.logo-preview-inline {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #ffffff;
  border: 1px solid var(--n-border-color);
  border-radius: 6px;
  padding: 8px 12px;
  flex-shrink: 0;
}

.logo-image-wrapper {
  width: 40px;
  height: 40px;
  border: 1px solid var(--n-border-color);
  border-radius: 6px;
  overflow: hidden;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
}

.logo-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.logo-status {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--n-color-success);
}

.remove-logo-btn {
  flex-shrink: 0;
}

.upload-button-section {
   display: flex;
   flex-direction: column;
   gap: 8px;
   align-items: flex-start;
 }
 
 .upload-button {
   flex-shrink: 0;
 }
 
 .upload-tips-text {
   font-size: 12px;
   line-height: 1.4;
 }

/* 响应式设计 */
@media (max-width: 768px) {
  .logo-upload-row {
    flex-direction: column;
    align-items: stretch;
  }
  
  .logo-preview-inline {
    justify-content: center;
  }
  
  .upload-button-section {
     align-items: center;
   }
}
</style>