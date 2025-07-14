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
  SettingsSharp
} from '@vicons/ionicons5'

const router = useRouter()
const route = useRoute()

// 侧边栏折叠状态
const collapsed = ref(false)

// 当前激活的菜单项
const activeKey = computed(() => route.name as string)

// 当前页面标题
const currentPageTitle = computed(() => {
  const menuItem = menuOptions.value.find(item => item.key === activeKey.value)
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
    icon: () => h(NIcon, null, { default: () => h(ExtensionPuzzleOutline) }),
    children: [
      {
        label: '工具管理',
        key: 'tools-manage'
      },
      {
        label: '工具配置',
        key: 'tools-config'
      }
    ]
  },
  {
    label: 'MCP 代理',
    key: 'proxy',
    icon: () => h(NIcon, null, { default: () => h(ServerOutline) }),
    children: [
      {
        label: '代理管理',
        key: 'proxy-manage'
      },
      {
        label: '连接状态',
        key: 'proxy-status'
      }
    ]
  },
  {
    label: '系统监控',
    key: 'monitor',
    icon: () => h(NIcon, null, { default: () => h(BarChartOutline) })
  },
  {
    label: '日志管理',
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
    label: '个人设置',
    key: 'profile',
    icon: () => h(NIcon, null, { default: () => h(PersonOutline) })
  },
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
    case 'tools-manage':
      router.push('/tools')
      break
    case 'tools-config':
      router.push('/tools/config')
      break
    case 'proxy-manage':
      router.push('/proxy')
      break
    case 'proxy-status':
      router.push('/proxy/status')
      break
    case 'monitor':
      router.push('/monitor')
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
    case 'profile':
      // 跳转到个人设置页面
      router.push('/profile')
      break
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