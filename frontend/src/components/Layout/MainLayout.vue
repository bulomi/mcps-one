<template>
  <n-layout has-sider>
    <!-- 侧边栏 -->
    <n-layout-sider
      bordered
      collapse-mode="width"
      :collapsed-width="80"
      :width="280"
      :collapsed="collapsed"
      show-trigger
      @collapse="collapsed = true"
      @expand="collapsed = false"
      class="main-sider"
    >
      <div class="logo">
        <img 
          :src="appStore.logo || logoImage" 
          alt="MCPS.ONE Logo" 
          class="logo-image"
          :class="{ 'logo-collapsed': collapsed }"
        />
        <span v-if="!collapsed && appStore.showTitle" class="logo-text">{{ appStore.appTitle }}</span>
      </div>
      
      <n-menu
        :collapsed="collapsed"
        :collapsed-width="64"
        :collapsed-icon-size="22"
        :options="menuOptions"
        :value="activeKey"
        :expanded-keys="expandedKeys"
        @update:value="handleMenuSelect"
        @update:expanded-keys="handleExpandedKeysUpdate"
      />
    </n-layout-sider>
    
    <!-- 主内容区域 -->
    <n-layout>
      <!-- 顶部导航栏 -->
      <n-layout-header bordered class="header">
        <div class="header-content">
          <div class="header-left">
            <n-breadcrumb>
              <n-breadcrumb-item>{{ currentPageTitle }}</n-breadcrumb-item>
            </n-breadcrumb>
          </div>
          <div class="header-right">
            <n-space>
              <!-- 使用说明提示 -->
              <n-popover trigger="click" placement="bottom-end" :width="240">
                <template #trigger>
                  <n-button quaternary circle>
                    <template #icon>
                      <n-icon><HelpCircleOutline /></n-icon>
                    </template>
                  </n-button>
                </template>
                <div class="help-content">
                  <h4>MCPS.ONE 使用指南</h4>
                  <div class="mode-description">
                    <p><strong>MCP服务端模式：</strong>启用MCP工具服务端</p>
                    <p><strong>代理模式：</strong>启用FastMCP代理服务</p>
                  </div>
                  <div class="tutorial-links">
                    <n-space vertical>
                      <n-button text type="info" @click="window.open('https://docs.mcps.one', '_blank')">
                        📖 查看详细文档
                      </n-button>
                    </n-space>
                  </div>
                </div>
              </n-popover>
              <n-dropdown :options="userOptions" @select="handleUserAction">
                <n-button quaternary circle>
                  <template #icon>
                    <n-icon><PersonOutline /></n-icon>
                  </template>
                </n-button>
              </n-dropdown>
            </n-space>
          </div>
        </div>
      </n-layout-header>
      
      <!-- 主内容 -->
      <n-layout-content class="main-content">
        <div class="content-wrapper">
          <router-view />
        </div>
      </n-layout-content>
    </n-layout>
  </n-layout>
  
  <!-- 全局加载指示器 -->
  <GlobalLoadingIndicator />
  
  <!-- 增强的Toast通知 -->
  <EnhancedToast />
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  NLayout,
  NLayoutSider,
  NLayoutHeader,
  NLayoutContent,
  NMenu,
  NIcon,
  NBreadcrumb,
  NBreadcrumbItem,
  NSpace,
  NButton,
  NDropdown,
  NPopover,
  type MenuOption
} from 'naive-ui'
import {
  ExtensionPuzzleOutline,
  PersonOutline,
  LogOutOutline,
  SettingsSharp,
  HelpCircleOutline,
  SettingsOutline,
  BookOutline,
  ServerOutline,
  GitNetworkOutline,
  DocumentTextOutline
} from '@vicons/ionicons5'
import GlobalLoadingIndicator from '@/components/GlobalLoadingIndicator.vue'
import EnhancedToast from '@/components/EnhancedToast.vue'

import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import logoImage from '@/assets/logo.png'
import logoDarkImage from '@/assets/logo-dark.png'

const router = useRouter()
const route = useRoute()
const appStore = useAppStore()
const authStore = useAuthStore()

// 侧边栏折叠状态
const collapsed = ref(false)

// 菜单展开状态
const expandedKeys = ref<string[]>([])



// 当前激活的菜单项
const activeKey = computed(() => route.name as string)

// 处理菜单展开状态更新
const handleExpandedKeysUpdate = (keys: string[]) => {
  expandedKeys.value = keys
}

// 根据当前路由更新展开状态
const updateExpandedKeys = () => {
  const currentPath = route.path
  if (currentPath.startsWith('/tutorial')) {
    expandedKeys.value = ['tutorial']
  } else {
    expandedKeys.value = []
  }
}

// 当前页面标题
const currentPageTitle = computed(() => {
  const findMenuItem = (items: MenuOption[], key: string): MenuOption | undefined => {
    for (const item of items) {
      if (item.key === key) {
        return item
      }
      if (item.children) {
        const found = findMenuItem(item.children, key)
        if (found) return found
      }
    }
    return undefined
  }
  
  const menuItem = findMenuItem(menuOptions.value, activeKey.value)
  return menuItem?.label || '首页'
})



// 菜单选项
const menuOptions = ref<MenuOption[]>([
  {
    label: 'MCP 工具',
    key: 'tools',
    icon: () => h(NIcon, null, { default: () => h(ExtensionPuzzleOutline) })
  },
  {
    label: '使用教程',
    key: 'tutorial',
    icon: () => h(NIcon, null, { default: () => h(BookOutline) }),
    children: [
      {
              label: '快速开始',
              key: '/tutorial/tool-management',
              icon: () => h(NIcon, null, { default: () => h(ExtensionPuzzleOutline) })
            },
      {
        label: '配置指南',
        key: '/tutorial/mcp-server',
        icon: () => h(NIcon, null, { default: () => h(ServerOutline) })
      },
      {
        label: 'API 指南',
        key: '/tutorial/api-documentation',
        icon: () => h(NIcon, null, { default: () => h(DocumentTextOutline) })
      }
    ]
  },
  {
    label: '系统设置',
    key: 'settings',
    icon: () => h(NIcon, null, { default: () => h(SettingsSharp) })
  }
])

// 用户下拉菜单选项
const userOptions = computed(() => [
  {
    label: authStore.user?.username || '用户',
    key: 'user-info',
    disabled: true
  },
  {
    type: 'divider',
    key: 'd1'
  },
  {
    label: '系统设置',
    key: 'settings',
    icon: () => h(NIcon, null, { default: () => h(SettingsOutline) })
  },
  {
    type: 'divider',
    key: 'd2'
  },
  {
    label: '退出登录',
    key: 'logout',
    icon: () => h(NIcon, null, { default: () => h(LogOutOutline) })
  }
])

// 处理菜单选择
const handleMenuSelect = (key: string) => {
  // 根据菜单项导航到对应页面
  switch (key) {
    case 'tools':
      router.push('/tools')
      break
    case 'tutorial':
      router.push('/tutorial')
      break
    case '/tutorial/mcp-server':
      router.push('/tutorial/mcp-server')
      break
    case '/tutorial/tool-management':
      router.push('/tutorial/tool-management')
      break
    case '/tutorial/api-documentation':
      router.push('/tutorial/api-documentation')
      break
    case 'settings':
      router.push('/settings')
      break
  }
}



// 处理用户操作
const handleUserAction = async (key: string) => {
  switch (key) {
    case 'settings':
      router.push('/settings')
      break
    case 'logout':
      try {
        await authStore.logout()
        window.$message?.success('已退出登录')
        router.push('/login')
      } catch (error) {
        console.error('退出登录失败:', error)
        window.$message?.error('退出登录失败')
      }
      break
  }
}

// 监听路由变化，更新菜单展开状态
watch(() => route.name, () => {
  updateExpandedKeys()
}, { immediate: true })

// 组件挂载时获取当前状态
onMounted(async () => {
  await appStore.initializeApp()
  updateExpandedKeys()
})
</script>

<style scoped>
.main-sider {
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
  z-index: 100;
}

.logo {
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 0 20px;
  border-bottom: 1px solid var(--n-border-color);
  /* background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); */
  color: white;
}

.logo-image {
  height: 50px;
  width: auto;
  object-fit: contain;
  transition: all 0.3s ease;
}

.logo-image.logo-collapsed {
  height: 28px;
}

.logo-text {
  font-size: 20px;
  font-weight: bold;
  color: rgb(51, 54, 57);
  letter-spacing: 1px;
}

.header {
  height: 72px;
  display: flex;
  align-items: center;
  padding: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 99;
  background: #fff;
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 32px;
}

.header-left {
  flex: 1;
}

.header-right {
  display: flex;
  align-items: center;
}

.main-content {
  background: #f5f7fa;
  overflow-y: auto;
  height: calc(100vh - 72px);
}

.content-wrapper {
  padding: 32px;
  max-width: 1600px;
  margin: 0 auto;
  min-height: calc(100vh - 136px);
}

.help-content {
  padding: 8px 0;
}

.help-content h4 {
  margin: 0 0 12px 0;
  color: var(--n-text-color);
  font-size: 16px;
}

.help-content h5 {
  margin: 12px 0 8px 0;
  color: var(--n-text-color);
  font-size: 14px;
}

.mode-description p {
  margin: 6px 0;
  font-size: 13px;
  line-height: 1.5;
  color: var(--n-text-color-2);
}

.tutorial-links {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--n-divider-color);
}

.tutorial-links :deep(.n-button) {
  width: 100%;
  justify-content: flex-start;
  padding: 8px 12px;
  margin: 2px 0;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.tutorial-links :deep(.n-button:hover) {
  background-color: var(--n-button-color-hover);
  transform: translateX(2px);
}
</style>