import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

// Naive UI
import naive from 'naive-ui'

import App from './App.vue'
import router from './router'
import { useAppStore } from './stores/app'
import { useAuthStore } from './stores/auth'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(naive)

app.mount('#app')

// 延迟初始化，避免阻塞应用启动
setTimeout(async () => {
  try {
    const appStore = useAppStore()
    const authStore = useAuthStore()
    
    // 只初始化本地状态，暂时跳过API调用
    
  } catch (error) {
    // 初始化失败不影响应用基本功能
  }
}, 100)
