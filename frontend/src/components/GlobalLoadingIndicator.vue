<template>
  <teleport to="body">
    <transition name="loading-fade">
      <div v-if="isVisible" class="global-loading-overlay">
        <div class="loading-container">
          <div class="loading-spinner">
            <n-spin size="large" :show="true">
              <template #icon>
                <n-icon size="24">
                  <RefreshOutline />
                </n-icon>
              </template>
            </n-spin>
          </div>
          <div class="loading-text">
            {{ currentMessage }}
          </div>
          <div v-if="showProgress" class="loading-progress">
            <n-progress 
              type="line" 
              :percentage="progress" 
              :show-indicator="false"
              :height="4"
              border-radius="2px"
            />
          </div>
          <div v-if="showCancel" class="loading-actions">
            <n-button size="small" @click="handleCancel">
              取消
            </n-button>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { NIcon, NSpin, NProgress, NButton } from 'naive-ui'
import { RefreshOutline } from '@vicons/ionicons5'
import { GlobalLoadingManager, type LoadingState } from '@/utils/loading'

// 组件逻辑
const manager = GlobalLoadingManager.getInstance()
const currentState = ref<LoadingState | null>(null)

// 订阅状态变化
manager.subscribe((state) => {
  currentState.value = state
})

// 计算属性
const isVisible = computed(() => currentState.value?.visible || false)
const currentMessage = computed(() => currentState.value?.message || '加载中...')
const progress = computed(() => currentState.value?.progress || 0)
const showProgress = computed(() => currentState.value?.showProgress || false)
const showCancel = computed(() => currentState.value?.showCancel || false)

// 处理取消
const handleCancel = () => {
  if (currentState.value?.onCancel) {
    currentState.value.onCancel()
  }
}

// 管理器实例已在单独文件中导出
</script>

<style scoped>
.global-loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.loading-container {
  background: white;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  text-align: center;
  min-width: 280px;
  max-width: 400px;
}

.loading-spinner {
  margin-bottom: 16px;
}

.loading-text {
  font-size: 16px;
  color: #333;
  margin-bottom: 16px;
  font-weight: 500;
}

.loading-progress {
  margin-bottom: 16px;
}

.loading-actions {
  margin-top: 16px;
}

.loading-fade-enter-active,
.loading-fade-leave-active {
  transition: opacity 0.3s ease;
}

.loading-fade-enter-from,
.loading-fade-leave-to {
  opacity: 0;
}

/* 深色主题适配 */
@media (prefers-color-scheme: dark) {
  .loading-container {
    background: #2d2d2d;
    color: #fff;
  }
  
  .loading-text {
    color: #fff;
  }
}
</style>