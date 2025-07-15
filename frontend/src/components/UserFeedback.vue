<template>
  <n-modal v-model:show="showModal" preset="dialog" title="用户反馈">
    <template #header>
      <div style="display: flex; align-items: center; gap: 8px;">
        <n-icon size="20" color="#18a058">
          <ChatbubbleEllipsesOutline />
        </n-icon>
        <span>用户反馈</span>
      </div>
    </template>
    
    <n-form ref="formRef" :model="feedbackForm" :rules="rules" label-placement="top">
      <n-form-item label="反馈类型" path="type">
        <n-select 
          v-model:value="feedbackForm.type" 
          :options="feedbackTypes"
          placeholder="请选择反馈类型"
        />
      </n-form-item>
      
      <n-form-item label="标题" path="title">
        <n-input 
          v-model:value="feedbackForm.title" 
          placeholder="请输入反馈标题"
          maxlength="100"
          show-count
        />
      </n-form-item>
      
      <n-form-item label="详细描述" path="description">
        <n-input 
          v-model:value="feedbackForm.description" 
          type="textarea"
          placeholder="请详细描述您的问题、建议或意见"
          :rows="4"
          maxlength="1000"
          show-count
        />
      </n-form-item>
      
      <n-form-item label="联系方式（可选）" path="contact">
        <n-input 
          v-model:value="feedbackForm.contact" 
          placeholder="邮箱或其他联系方式，便于我们回复您"
          maxlength="100"
        />
      </n-form-item>
      
      <n-form-item label="优先级" path="priority">
        <n-radio-group v-model:value="feedbackForm.priority">
          <n-radio value="low">低</n-radio>
          <n-radio value="medium">中</n-radio>
          <n-radio value="high">高</n-radio>
        </n-radio-group>
      </n-form-item>
    </n-form>
    
    <template #action>
      <n-space>
        <n-button @click="showModal = false">取消</n-button>
        <n-button type="primary" :loading="submitting" @click="submitFeedback">
          提交反馈
        </n-button>
      </n-space>
    </template>
  </n-modal>
  
  <!-- 反馈按钮 -->
  <n-button 
    v-if="!hideButton"
    type="primary" 
    ghost 
    size="small" 
    @click="openFeedback"
    :style="buttonStyle"
  >
    <template #icon>
      <n-icon>
        <ChatbubbleEllipsesOutline />
      </n-icon>
    </template>
    反馈
  </n-button>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import {
  NModal, NForm, NFormItem, NInput, NSelect, NRadioGroup, NRadio,
  NButton, NSpace, NIcon, useMessage, FormInst
} from 'naive-ui'
import { ChatbubbleEllipsesOutline } from '@vicons/ionicons5'
import { showSuccess, showError, handleApiError } from '@/utils/errorHandler'

// Props
interface Props {
  hideButton?: boolean
  buttonStyle?: Record<string, any>
}

const props = withDefaults(defineProps<Props>(), {
  hideButton: false,
  buttonStyle: () => ({})
})

// Emits
const emit = defineEmits<{
  feedbackSubmitted: [feedback: any]
}>()

// 响应式数据
const showModal = ref(false)
const submitting = ref(false)
const formRef = ref<FormInst | null>(null)

// 反馈表单
const feedbackForm = reactive({
  type: '',
  title: '',
  description: '',
  contact: '',
  priority: 'medium'
})

// 反馈类型选项
const feedbackTypes = [
  { label: '功能建议', value: 'feature' },
  { label: '问题报告', value: 'bug' },
  { label: '使用体验', value: 'experience' },
  { label: '界面优化', value: 'ui' },
  { label: '其他', value: 'other' }
]

// 表单验证规则
const rules = {
  type: {
    required: true,
    message: '请选择反馈类型',
    trigger: 'change'
  },
  title: {
    required: true,
    message: '请输入反馈标题',
    trigger: 'blur'
  },
  description: {
    required: true,
    message: '请输入详细描述',
    trigger: 'blur'
  }
}

// 打开反馈弹窗
const openFeedback = () => {
  showModal.value = true
}

// 重置表单
const resetForm = () => {
  feedbackForm.type = ''
  feedbackForm.title = ''
  feedbackForm.description = ''
  feedbackForm.contact = ''
  feedbackForm.priority = 'medium'
}

// 提交反馈
const submitFeedback = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitting.value = true
    
    // 构建反馈数据
    const feedbackData = {
      ...feedbackForm,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    }
    
    // 这里可以调用API提交反馈
    // await feedbackApi.submitFeedback(feedbackData)
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 保存到本地存储（临时方案）
    const existingFeedbacks = JSON.parse(localStorage.getItem('user_feedbacks') || '[]')
    existingFeedbacks.push({
      id: Date.now(),
      ...feedbackData
    })
    localStorage.setItem('user_feedbacks', JSON.stringify(existingFeedbacks))
    
    showSuccess('反馈提交成功，感谢您的宝贵意见！')
    emit('feedbackSubmitted', feedbackData)
    
    showModal.value = false
    resetForm()
    
  } catch (error: any) {
    if (error?.errors) {
      // 表单验证错误
      return
    }
    handleApiError(error, '提交反馈失败')
  } finally {
    submitting.value = false
  }
}

// 暴露方法给父组件
defineExpose({
  openFeedback
})
</script>

<style scoped>
/* 可以添加自定义样式 */
</style>