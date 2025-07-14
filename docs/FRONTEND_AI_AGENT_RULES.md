# 前端开发 AI Agent 规则

> **文档目的**：本文档专门定义AI Agent在开发MCP工具管理系统前端时必须遵守的规则、约束条件和最佳实践，确保前端代码的质量、一致性和用户体验。

## 🎯 前端开发核心原则

### 1. 技术栈严格遵循
- **必须**：使用 Vue 3 + Composition API
- **必须**：使用 Naive UI 作为组件库
- **必须**：使用 Vite 作为构建工具
- **必须**：使用 TypeScript 进行类型安全开发
- **必须**：使用 Pinia 进行状态管理
- **禁止**：混用其他UI框架或状态管理库
- **禁止**：使用Options API（除非特殊情况）

### 2. 响应式设计要求
- **必须**：支持移动端、平板、桌面三种设备
- **必须**：使用断点：768px（平板），1024px（桌面）
- **必须**：移动端侧边栏折叠为汉堡菜单
- **必须**：桌面端固定侧边栏布局
- **必须**：所有组件都要响应式适配
- **禁止**：固定像素宽度的布局设计

### 3. 用户体验标准
- **必须**：页面加载时间 < 2秒
- **必须**：交互响应时间 < 100ms
- **必须**：提供加载状态指示器
- **必须**：提供友好的错误提示
- **必须**：支持键盘导航
- **必须**：遵循无障碍访问标准（WCAG 2.1 AA）

## 📋 组件开发规范

### 1. 组件结构标准
```vue
<template>
  <!-- 模板内容 -->
</template>

<script setup lang="ts">
// 导入
import { ref, computed, onMounted } from 'vue'
import type { ComponentProps } from './types'

// Props定义
interface Props {
  // 属性定义
}

const props = withDefaults(defineProps<Props>(), {
  // 默认值
})

// Emits定义
interface Emits {
  (e: 'update', value: string): void
}

const emit = defineEmits<Emits>()

// 响应式数据
const state = ref()

// 计算属性
const computed = computed(() => {
  // 计算逻辑
})

// 方法
const handleAction = () => {
  // 处理逻辑
}

// 生命周期
onMounted(() => {
  // 初始化逻辑
})
</script>

<style scoped>
/* 样式 */
</style>
```

### 2. 组件命名规范
- **文件名**：使用 PascalCase，如 `ToolCard.vue`
- **组件名**：与文件名保持一致
- **Props**：使用 camelCase
- **Events**：使用 kebab-case
- **CSS类名**：使用 BEM 命名法

### 3. 组件职责分离
- **展示组件**：只负责UI展示，不包含业务逻辑
- **容器组件**：负责数据获取和状态管理
- **布局组件**：负责页面布局和导航
- **功能组件**：封装特定功能逻辑

## 🎨 UI设计规范

### 1. 设计系统遵循
- **颜色方案**：
  - 主色调：#2563eb（蓝色）
  - 成功色：#10b981（绿色）
  - 警告色：#f59e0b（橙色）
  - 错误色：#ef4444（红色）
  - 中性色：#6b7280（灰色）
- **字体系统**：
  - 主字体：系统默认字体栈
  - 代码字体：'Fira Code', 'Monaco', monospace
- **间距系统**：
  - 基础单位：8px
  - 所有间距必须是8的倍数
  - 常用间距：8px, 16px, 24px, 32px, 48px

### 2. 组件状态设计
- **工具状态颜色**：
  - running：绿色圆点 + 绿色边框
  - stopped：灰色圆点 + 灰色边框
  - error：红色圆点 + 红色边框
  - starting/stopping：黄色圆点 + 黄色边框
- **按钮状态**：
  - 默认、悬停、激活、禁用四种状态
  - 加载状态显示旋转图标
- **表单状态**：
  - 正常、聚焦、错误、禁用四种状态

### 3. 动画和过渡
- **页面切换**：300ms ease-in-out
- **组件显隐**：200ms ease-in-out
- **悬停效果**：150ms ease-in-out
- **加载动画**：使用Naive UI内置动画
- **禁止**：过度复杂的动画效果

## 🔧 状态管理规范

### 1. Pinia Store结构
```typescript
// stores/toolStore.ts
import { defineStore } from 'pinia'
import type { MCPTool } from '@/types'

export const useToolStore = defineStore('tool', () => {
  // State
  const tools = ref<MCPTool[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const runningTools = computed(() => 
    tools.value.filter(tool => tool.status === 'running')
  )

  // Actions
  const fetchTools = async () => {
    loading.value = true
    try {
      const response = await toolApi.getTools()
      tools.value = response.data
    } catch (err) {
      error.value = err.message
    } finally {
      loading.value = false
    }
  }

  const startTool = async (id: number) => {
    // 启动工具逻辑
  }

  return {
    // State
    tools,
    loading,
    error,
    // Getters
    runningTools,
    // Actions
    fetchTools,
    startTool
  }
})
```

### 2. 状态管理原则
- **单一数据源**：每个数据只在一个store中管理
- **不可变更新**：使用不可变的方式更新状态
- **异步处理**：所有API调用都要有loading和error状态
- **状态持久化**：用户设置和偏好需要持久化存储

## 🌐 API集成规范

### 1. HTTP客户端配置
```typescript
// services/api.ts
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000
})

// 请求拦截器
api.interceptors.request.use((config) => {
  const authStore = useAuthStore()
  if (authStore.token) {
    config.headers.Authorization = `Bearer ${authStore.token}`
  }
  return config
})

// 响应拦截器
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // 统一错误处理
    if (error.response?.status === 401) {
      // 处理未授权
    }
    return Promise.reject(error)
  }
)
```

### 2. API调用规范
- **必须**：使用TypeScript定义API响应类型
- **必须**：实现统一的错误处理
- **必须**：添加请求和响应拦截器
- **必须**：设置合理的超时时间
- **必须**：实现请求重试机制（关键接口）

## 🧪 测试规范

### 1. 单元测试要求
```typescript
// tests/components/ToolCard.test.ts
import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import ToolCard from '@/components/ToolCard.vue'

describe('ToolCard', () => {
  it('should render tool information correctly', () => {
    const tool = {
      id: 1,
      name: 'Test Tool',
      status: 'running'
    }
    
    const wrapper = mount(ToolCard, {
      props: { tool }
    })
    
    expect(wrapper.text()).toContain('Test Tool')
    expect(wrapper.find('.status-indicator').classes()).toContain('running')
  })

  it('should emit start event when start button clicked', async () => {
    const wrapper = mount(ToolCard, {
      props: { tool: { status: 'stopped' } }
    })
    
    await wrapper.find('.start-button').trigger('click')
    
    expect(wrapper.emitted('start')).toBeTruthy()
  })
})
```

### 2. 测试覆盖要求
- **组件测试**：所有组件必须有单元测试
- **Store测试**：所有Pinia store的actions和getters
- **工具函数测试**：所有utility函数
- **集成测试**：关键用户流程的端到端测试
- **覆盖率目标**：≥ 80%

## 🚫 前端开发禁止事项

### 1. 性能相关
- **禁止**：在模板中使用复杂的计算逻辑
- **禁止**：在循环中进行API调用
- **禁止**：不必要的响应式数据
- **禁止**：内存泄漏（未清理的定时器、事件监听器）
- **禁止**：过大的bundle size（单个chunk > 1MB）

### 2. 安全相关
- **禁止**：在前端存储敏感信息
- **禁止**：直接在模板中渲染用户输入（XSS风险）
- **禁止**：跳过输入验证
- **禁止**：在控制台输出敏感信息

### 3. 代码质量
- **禁止**：使用any类型（除非必要）
- **禁止**：忽略TypeScript错误
- **禁止**：使用console.log在生产环境
- **禁止**：硬编码的魔法数字和字符串
- **禁止**：过深的组件嵌套（>5层）

## ✅ 前端开发检查清单

### 组件开发完成前检查
- [ ] 组件是否遵循命名规范
- [ ] 是否定义了正确的Props和Emits类型
- [ ] 是否实现了响应式设计
- [ ] 是否添加了适当的错误处理
- [ ] 是否编写了单元测试
- [ ] 是否遵循了设计系统规范
- [ ] 是否支持键盘导航
- [ ] 是否添加了必要的ARIA属性

### 页面开发完成前检查
- [ ] 是否实现了加载状态
- [ ] 是否实现了错误状态
- [ ] 是否实现了空状态
- [ ] 是否支持所有设备尺寸
- [ ] 是否实现了权限控制
- [ ] 是否添加了页面标题和meta信息
- [ ] 是否优化了SEO（如果需要）

### 代码提交前检查
- [ ] 是否通过了ESLint检查
- [ ] 是否通过了TypeScript类型检查
- [ ] 是否通过了所有测试
- [ ] 是否移除了调试代码
- [ ] 是否更新了相关文档
- [ ] 是否检查了bundle size变化

## 📱 移动端特殊要求

### 1. 触摸交互
- **必须**：触摸目标最小44px × 44px
- **必须**：支持手势操作（滑动、长按）
- **必须**：避免悬停状态在移动端的问题
- **必须**：优化滚动性能

### 2. 性能优化
- **必须**：图片懒加载
- **必须**：组件懒加载
- **必须**：虚拟滚动（长列表）
- **必须**：压缩和优化资源

## 🔍 调试和开发工具

### 1. 开发环境配置
- **必须**：配置Vue DevTools
- **必须**：配置ESLint和Prettier
- **必须**：配置TypeScript严格模式
- **必须**：配置Vite HMR

### 2. 调试最佳实践
- **推荐**：使用Vue DevTools进行状态调试
- **推荐**：使用浏览器开发者工具
- **推荐**：使用console.group组织日志
- **禁止**：在生产环境保留调试代码

## 📊 性能监控

### 1. 关键指标
- **FCP**：First Contentful Paint < 1.5s
- **LCP**：Largest Contentful Paint < 2.5s
- **FID**：First Input Delay < 100ms
- **CLS**：Cumulative Layout Shift < 0.1

### 2. 监控实现
```typescript
// utils/performance.ts
export const trackPerformance = () => {
  // 监控页面加载性能
  window.addEventListener('load', () => {
    const navigation = performance.getEntriesByType('navigation')[0]
    console.log('Page Load Time:', navigation.loadEventEnd - navigation.loadEventStart)
  })

  // 监控用户交互性能
  const observer = new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
      if (entry.entryType === 'measure') {
        console.log(`${entry.name}: ${entry.duration}ms`)
      }
    }
  })
  
  observer.observe({ entryTypes: ['measure'] })
}
```

---

> **重要提醒**：本规则文档是前端开发的强制性指南，所有AI Agent在开发前端功能时必须严格遵守。违反这些规则可能导致用户体验问题、性能问题或安全风险。如有疑问，请参考Vue 3官方文档或寻求技术澄清。