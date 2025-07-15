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
        <n-icon size="32" color="#18a058">
          <SettingsOutline />
        </n-icon>
        <span v-if="!collapsed" class="logo-text">MCPS.ONE</span>
      </div>
      
      <n-menu
        :collapsed="collapsed"
        :collapsed-width="64"
        :collapsed-icon-size="22"
        :options="menuOptions"
        :value="activeKey"
        @update:value="handleMenuSelect"
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
              <n-badge :value="12" :max="99">
                <n-button quaternary circle>
                  <template #icon>
                    <n-icon><NotificationsOutline /></n-icon>
                  </template>
                </n-button>
              </n-badge>
              <n-button quaternary circle @click="feedbackRef?.openFeedback()">
                <template #icon>
                  <n-icon><ChatbubbleEllipsesOutline /></n-icon>
                </template>
              </n-button>
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
  
  <!-- 用户反馈组件 -->
  <UserFeedback ref="feedbackRef" hide-button />
</template>

<script setup lang="ts">
import { ref, computed, h } from 'vue'
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
  NBadge,
  NDropdown,
  type MenuOption
} from 'naive-ui'
import {
  SettingsOutline,
  HomeOutline,
  ExtensionPuzzleOutline,
  ServerOutline,
  BarChartOutline,
  DocumentTextOutline,
  NotificationsOutline,
  PersonOutline,
  LogOutOutline,
  SettingsSharp,
  WarningOutline,
  ChatbubbleEllipsesOutline
} from '@vicons/ionicons5'
import UserFeedback from '@/components/UserFeedback.vue'

const router = useRouter()
const route = useRoute()

// 侧边栏折叠状态
const collapsed = ref(false)
const feedbackRef = ref()

// 当前激活的菜单项
const activeKey = computed(() => route.name as string)

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
    label: '首页',
    key: 'home',
    icon: () => h(NIcon, null, { default: () => h(HomeOutline) })
  },
  {
    label: 'MCP 工具',
    key: 'tools',
    icon: () => h(NIcon, null, { default: () => h(ExtensionPuzzleOutline) })
  },
  {
    label: 'MCP 统一管理',
    key: 'mcp-unified',
    icon: () => h(NIcon, null, { default: () => h(SettingsOutline) })
  },
  {
    label: '代理状态',
    key: 'proxy',
    icon: () => h(NIcon, null, { default: () => h(ServerOutline) }),
    children: [
      {
        label: '当前会话',
        key: 'proxy-sessions'
      },
      {
        label: '工具状态',
        key: 'proxy-status'
      }
    ]
  },
  {
    label: '日志查看',
    key: 'logs',
    icon: () => h(NIcon, null, { default: () => h(DocumentTextOutline) })
  },
  {
    label: '系统设置',
    key: 'settings',
    icon: () => h(NIcon, null, { default: () => h(SettingsSharp) })
  }
])

// 用户下拉菜单选项
const userOptions = [
  {
    label: '系统设置',
    key: 'system-settings',
    icon: () => h(NIcon, null, { default: () => h(SettingsOutline) })
  },
  {
    type: 'divider',
    key: 'd1'
  },
  {
    label: '退出登录',
    key: 'logout',
    icon: () => h(NIcon, null, { default: () => h(LogOutOutline) })
  }
]

// 处理菜单选择
const handleMenuSelect = (key: string) => {
  // 根据菜单项导航到对应页面
  switch (key) {
    case 'home':
      router.push('/')
      break
    case 'tools':
      router.push('/tools')
      break
    case 'mcp-unified':
      router.push('/mcp-unified')
      break
    case 'proxy-sessions':
      router.push('/proxy/sessions')
      break
    case 'proxy-status':
      router.push('/proxy/status')
      break
    case 'logs':
      router.push('/logs')
      break
    case 'settings':
      router.push('/settings')
      break
  }
}

// 处理用户操作
const handleUserAction = (key: string) => {
  switch (key) {
    case 'system-settings':
      router.push('/settings')
      break
    case 'logout':
      // 处理退出登录
      console.log('用户退出登录')
      // TODO: 实现退出登录逻辑
      break
  }
}
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.logo-text {
  font-size: 20px;
  font-weight: bold;
  color: white;
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
</style>