<template>
  <teleport to="body">
    <div class="toast-container">
      <transition-group name="toast" tag="div">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          :class="[
            'toast-item',
            `toast-${toast.type}`,
            { 'toast-dismissible': toast.dismissible }
          ]"
          @click="toast.dismissible && dismissToast(toast.id)"
        >
          <div class="toast-icon">
            <n-icon :size="20">
              <component :is="getIcon(toast.type)" />
            </n-icon>
          </div>
          <div class="toast-content">
            <div class="toast-title" v-if="toast.title">
              {{ toast.title }}
            </div>
            <div class="toast-message">
              {{ toast.message }}
            </div>
            <div class="toast-actions" v-if="toast.actions && toast.actions.length > 0">
              <n-button
                v-for="action in toast.actions"
                :key="action.label"
                :type="action.type || 'default'"
                size="small"
                @click.stop="handleAction(toast.id, action)"
              >
                {{ action.label }}
              </n-button>
            </div>
          </div>
          <div class="toast-close" v-if="toast.dismissible" @click.stop="dismissToast(toast.id)">
            <n-icon :size="16">
              <CloseOutline />
            </n-icon>
          </div>
          <div class="toast-progress" v-if="toast.showProgress">
            <div 
              class="toast-progress-bar" 
              :style="{ width: `${getProgress(toast)}%` }"
            ></div>
          </div>
        </div>
      </transition-group>
    </div>
  </teleport>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { NIcon, NButton } from 'naive-ui'
import {
  CheckmarkCircleOutline,
  AlertCircleOutline,
  WarningOutline,
  InformationCircleOutline,
  CloseOutline
} from '@vicons/ionicons5'
import { EnhancedToastManager, type Toast, type ToastAction } from '@/utils/toast'

// 组件逻辑
const manager = EnhancedToastManager.getInstance()
const toasts = ref<Toast[]>([])

// 订阅状态变化
manager.subscribe((newToasts) => {
  toasts.value = newToasts
})

// 获取图标
const getIcon = (type: string) => {
  switch (type) {
    case 'success':
      return CheckmarkCircleOutline
    case 'error':
      return AlertCircleOutline
    case 'warning':
      return WarningOutline
    case 'info':
      return InformationCircleOutline
    default:
      return InformationCircleOutline
  }
}

// 获取进度
const getProgress = (toast: Toast): number => {
  if (!toast.showProgress || !toast.timer) return 0
  const duration = toast.duration || 5000
  const elapsed = Date.now() - toast.createdAt
  return Math.max(0, Math.min(100, (elapsed / duration) * 100))
}

// 处理操作
const handleAction = async (toastId: string, action: ToastAction) => {
  try {
    await action.handler()
  } catch (error) {
    console.error('Toast action error:', error)
  }
  manager.dismiss(toastId)
}

// 关闭Toast
const dismissToast = (id: string) => {
  manager.dismiss(id)
}

// 管理器实例已在单独文件中导出
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 10000;
  pointer-events: none;
}

.toast-item {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  margin-bottom: 12px;
  padding: 16px;
  min-width: 320px;
  max-width: 480px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  pointer-events: auto;
  position: relative;
  overflow: hidden;
  border-left: 4px solid;
}

.toast-success {
  border-left-color: #52c41a;
}

.toast-error {
  border-left-color: #ff4d4f;
}

.toast-warning {
  border-left-color: #faad14;
}

.toast-info {
  border-left-color: #1890ff;
}

.toast-icon {
  flex-shrink: 0;
  margin-top: 2px;
}

.toast-success .toast-icon {
  color: #52c41a;
}

.toast-error .toast-icon {
  color: #ff4d4f;
}

.toast-warning .toast-icon {
  color: #faad14;
}

.toast-info .toast-icon {
  color: #1890ff;
}

.toast-content {
  flex: 1;
  min-width: 0;
}

.toast-title {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 4px;
  color: #262626;
}

.toast-message {
  font-size: 14px;
  color: #595959;
  line-height: 1.4;
  word-break: break-word;
}

.toast-actions {
  margin-top: 12px;
  display: flex;
  gap: 8px;
}

.toast-close {
  flex-shrink: 0;
  cursor: pointer;
  color: #8c8c8c;
  transition: color 0.2s;
}

.toast-close:hover {
  color: #595959;
}

.toast-dismissible {
  cursor: pointer;
}

.toast-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: rgba(0, 0, 0, 0.1);
}

.toast-progress-bar {
  height: 100%;
  background: currentColor;
  transition: width 0.1s linear;
}

.toast-success .toast-progress-bar {
  background: #52c41a;
}

.toast-error .toast-progress-bar {
  background: #ff4d4f;
}

.toast-warning .toast-progress-bar {
  background: #faad14;
}

.toast-info .toast-progress-bar {
  background: #1890ff;
}

/* 动画 */
.toast-enter-active {
  transition: all 0.3s ease;
}

.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

/* 深色主题适配 */
@media (prefers-color-scheme: dark) {
  .toast-item {
    background: #2d2d2d;
    color: #fff;
  }
  
  .toast-title {
    color: #fff;
  }
  
  .toast-message {
    color: #d9d9d9;
  }
  
  .toast-close {
    color: #8c8c8c;
  }
  
  .toast-close:hover {
    color: #d9d9d9;
  }
}
</style>