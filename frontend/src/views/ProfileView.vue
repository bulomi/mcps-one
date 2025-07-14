<template>
  <div class="profile-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1>个人设置</h1>
          <p>管理您的个人信息和偏好设置</p>
        </div>
      </div>
    </div>

    <!-- 主要内容 -->
    <n-grid :cols="1" :x-gap="24" :y-gap="24">
      <!-- 个人信息 -->
      <n-grid-item>
        <n-card title="个人信息">
          <n-form
            ref="profileFormRef"
            :model="profileForm"
            :rules="profileRules"
            label-placement="left"
            label-width="120px"
            require-mark-placement="right-hanging"
          >
            <n-grid :cols="2" :x-gap="24">
              <n-grid-item>
                <n-form-item label="用户名" path="username">
                  <n-input v-model:value="profileForm.username" placeholder="请输入用户名" />
                </n-form-item>
              </n-grid-item>
              <n-grid-item>
                <n-form-item label="邮箱" path="email">
                  <n-input v-model:value="profileForm.email" placeholder="请输入邮箱" />
                </n-form-item>
              </n-grid-item>
              <n-grid-item>
                <n-form-item label="姓名" path="fullName">
                  <n-input v-model:value="profileForm.fullName" placeholder="请输入姓名" />
                </n-form-item>
              </n-grid-item>
              <n-grid-item>
                <n-form-item label="电话" path="phone">
                  <n-input v-model:value="profileForm.phone" placeholder="请输入电话号码" />
                </n-form-item>
              </n-grid-item>
            </n-grid>
            <n-form-item label="个人简介" path="bio">
              <n-input
                v-model:value="profileForm.bio"
                type="textarea"
                placeholder="请输入个人简介"
                :rows="3"
              />
            </n-form-item>
          </n-form>
          <template #action>
            <n-space>
              <n-button @click="handleReset" :disabled="loading">重置</n-button>
              <n-button type="primary" @click="handleSaveProfile" :loading="loading">保存</n-button>
            </n-space>
          </template>
        </n-card>
      </n-grid-item>

      <!-- 安全设置 -->
      <n-grid-item>
        <n-card title="安全设置">
          <n-form
            ref="securityFormRef"
            :model="securityForm"
            :rules="securityRules"
            label-placement="left"
            label-width="120px"
            require-mark-placement="right-hanging"
          >
            <n-form-item label="当前密码" path="currentPassword">
              <n-input
                v-model:value="securityForm.currentPassword"
                type="password"
                placeholder="请输入当前密码"
                show-password-on="mousedown"
              />
            </n-form-item>
            <n-form-item label="新密码" path="newPassword">
              <n-input
                v-model:value="securityForm.newPassword"
                type="password"
                placeholder="请输入新密码"
                show-password-on="mousedown"
              />
            </n-form-item>
            <n-form-item label="确认密码" path="confirmPassword">
              <n-input
                v-model:value="securityForm.confirmPassword"
                type="password"
                placeholder="请再次输入新密码"
                show-password-on="mousedown"
              />
            </n-form-item>
          </n-form>
          <template #action>
            <n-space>
              <n-button @click="handleResetPassword" :disabled="loading">重置</n-button>
              <n-button type="primary" @click="handleChangePassword" :loading="loading">修改密码</n-button>
            </n-space>
          </template>
        </n-card>
      </n-grid-item>

      <!-- 偏好设置 -->
      <n-grid-item>
        <n-card title="偏好设置">
          <n-form
            ref="preferencesFormRef"
            :model="preferencesForm"
            label-placement="left"
            label-width="120px"
          >
            <n-grid :cols="2" :x-gap="24">
              <n-grid-item>
                <n-form-item label="主题">
                  <n-select
                    v-model:value="preferencesForm.theme"
                    :options="themeOptions"
                    placeholder="选择主题"
                  />
                </n-form-item>
              </n-grid-item>
              <n-grid-item>
                <n-form-item label="语言">
                  <n-select
                    v-model:value="preferencesForm.language"
                    :options="languageOptions"
                    placeholder="选择语言"
                  />
                </n-form-item>
              </n-grid-item>
              <n-grid-item>
                <n-form-item label="时区">
                  <n-select
                    v-model:value="preferencesForm.timezone"
                    :options="timezoneOptions"
                    placeholder="选择时区"
                  />
                </n-form-item>
              </n-grid-item>
              <n-grid-item>
                <n-form-item label="每页显示">
                  <n-input-number
                    v-model:value="preferencesForm.pageSize"
                    :min="10"
                    :max="100"
                    :step="10"
                  />
                </n-form-item>
              </n-grid-item>
            </n-grid>
            <n-form-item label="通知设置">
              <n-space vertical>
                <n-checkbox v-model:checked="preferencesForm.emailNotifications">
                  邮件通知
                </n-checkbox>
                <n-checkbox v-model:checked="preferencesForm.browserNotifications">
                  浏览器通知
                </n-checkbox>
                <n-checkbox v-model:checked="preferencesForm.systemNotifications">
                  系统通知
                </n-checkbox>
              </n-space>
            </n-form-item>
          </n-form>
          <template #action>
            <n-space>
              <n-button @click="handleResetPreferences" :disabled="loading">重置</n-button>
              <n-button type="primary" @click="handleSavePreferences" :loading="loading">保存</n-button>
            </n-space>
          </template>
        </n-card>
      </n-grid-item>
    </n-grid>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import {
  NCard,
  NGrid,
  NGridItem,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NSelect,
  NCheckbox,
  NButton,
  NSpace,
  useMessage,
  type FormInst,
  type FormRules
} from 'naive-ui'
import { userApi, type UserProfile, type UserUpdateData, type PasswordUpdateData, type UserPreferences } from '@/api/user'

const message = useMessage()

// 表单引用
const profileFormRef = ref<FormInst | null>(null)
const securityFormRef = ref<FormInst | null>(null)
const preferencesFormRef = ref<FormInst | null>(null)

// 个人信息表单
const profileForm = reactive({
  username: '',
  email: '',
  fullName: '',
  phone: '',
  bio: ''
})

// 用户资料数据
const userProfile = ref<UserProfile | null>(null)
const loading = ref(false)

// 安全设置表单
const securityForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 偏好设置表单
const preferencesForm = reactive<UserPreferences>({
  theme: 'light',
  language: 'zh-CN',
  timezone: 'Asia/Shanghai',
  pageSize: 20,
  emailNotifications: true,
  browserNotifications: true,
  systemNotifications: false
})

// 表单验证规则
const profileRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度应为3-20个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ]
}

const securityRules: FormRules = {
  currentPassword: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value) => {
        return value === securityForm.newPassword
      },
      message: '两次输入的密码不一致',
      trigger: 'blur'
    }
  ]
}

// 选项数据
const themeOptions = [
  { label: '浅色主题', value: 'light' },
  { label: '深色主题', value: 'dark' },
  { label: '自动', value: 'auto' }
]

const languageOptions = [
  { label: '简体中文', value: 'zh-CN' },
  { label: 'English', value: 'en-US' }
]

const timezoneOptions = [
  { label: '北京时间 (UTC+8)', value: 'Asia/Shanghai' },
  { label: '东京时间 (UTC+9)', value: 'Asia/Tokyo' },
  { label: '纽约时间 (UTC-5)', value: 'America/New_York' },
  { label: '伦敦时间 (UTC+0)', value: 'Europe/London' }
]

// 加载用户资料
const loadUserProfile = async () => {
  try {
    loading.value = true
    const profile = await userApi.getProfile()
    userProfile.value = profile
    
    // 更新表单数据
    Object.assign(profileForm, {
      username: profile.username,
      email: profile.email,
      fullName: profile.full_name || '',
      phone: profile.phone || '',
      bio: profile.bio || ''
    })
    
    // 更新偏好设置
    Object.assign(preferencesForm, {
      theme: profile.theme,
      language: profile.language,
      timezone: profile.timezone,
      emailNotifications: profile.email_notifications
    })
  } catch (error) {
    console.error('加载用户资料失败:', error)
    message.error('加载用户资料失败')
  } finally {
    loading.value = false
  }
}

// 处理函数
const handleSaveProfile = async () => {
  try {
    await profileFormRef.value?.validate()
    loading.value = true
    
    const updateData: UserUpdateData = {
      username: profileForm.username,
      email: profileForm.email,
      full_name: profileForm.fullName,
      phone: profileForm.phone,
      bio: profileForm.bio
    }
    
    const updatedProfile = await userApi.updateProfile(updateData)
    userProfile.value = updatedProfile
    
    message.success('个人信息保存成功')
  } catch (error: any) {
    console.error('保存个人信息失败:', error)
    message.error(error.response?.data?.detail || '保存个人信息失败')
  } finally {
    loading.value = false
  }
}

const handleReset = () => {
  profileFormRef.value?.restoreValidation()
}

const handleChangePassword = async () => {
  try {
    await securityFormRef.value?.validate()
    loading.value = true
    
    const passwordData: PasswordUpdateData = {
      current_password: securityForm.currentPassword,
      new_password: securityForm.newPassword,
      confirm_password: securityForm.confirmPassword
    }
    
    await userApi.updatePassword(passwordData)
    message.success('密码修改成功')
    
    // 清空表单
    Object.assign(securityForm, {
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    })
  } catch (error: any) {
    console.error('修改密码失败:', error)
    message.error(error.response?.data?.detail || '修改密码失败')
  } finally {
    loading.value = false
  }
}

const handleResetPassword = () => {
  securityFormRef.value?.restoreValidation()
  Object.assign(securityForm, {
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  })
}

const handleSavePreferences = async () => {
  try {
    loading.value = true
    
    const preferencesData: UserPreferences = {
      theme: preferencesForm.theme,
      language: preferencesForm.language,
      timezone: preferencesForm.timezone,
      email_notifications: preferencesForm.emailNotifications
    }
    
    const updatedProfile = await userApi.updatePreferences(preferencesData)
    userProfile.value = updatedProfile
    
    message.success('偏好设置保存成功')
  } catch (error: any) {
    console.error('保存偏好设置失败:', error)
    message.error(error.response?.data?.detail || '保存偏好设置失败')
  } finally {
    loading.value = false
  }
}

const handleResetPreferences = () => {
  if (userProfile.value) {
    Object.assign(preferencesForm, {
      theme: userProfile.value.theme,
      language: userProfile.value.language,
      timezone: userProfile.value.timezone,
      emailNotifications: userProfile.value.email_notifications
    })
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadUserProfile()
})
</script>

<style scoped>
.profile-view {
  padding: 0;
}

.page-header {
  margin-bottom: 32px;
  padding: 32px;
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
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 600;
}

.header-left p {
  margin: 0;
  opacity: 0.9;
  font-size: 16px;
}

:deep(.n-card) {
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

:deep(.n-card-header) {
  padding: 24px 24px 0 24px;
  font-size: 18px;
  font-weight: 600;
}

:deep(.n-card__content) {
  padding: 24px;
}

:deep(.n-card__action) {
  padding: 0 24px 24px 24px;
  border-top: 1px solid var(--n-divider-color);
  margin-top: 24px;
  padding-top: 24px;
}

:deep(.n-form-item-label) {
  font-weight: 500;
}
</style>