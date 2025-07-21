import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../components/Layout/MainLayout.vue'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import TestView from '../views/TestView.vue'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/test',
      name: 'test',
      component: TestView,
      meta: { requiresAuth: false }
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      redirect: '/app'
    },
    {
      path: '/app',
      component: MainLayout,
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'home',
          component: HomeView,
        },
        {
          path: '/tools',
          name: 'tools',
          component: () => import('../views/ToolsView.vue'),
        },
        {
          path: '/proxy',
          name: 'proxy',
          redirect: '/proxy/sessions'
        },
        {
          path: '/proxy/sessions',
          name: 'proxy-sessions',
          component: () => import('../views/MCPAgentSessionView.vue'),
        },
        {
          path: '/proxy/status',
          name: 'proxy-status',
          component: () => import('../views/ProxyStatusView.vue'),
        },
        {
          path: '/tasks/monitor',
          name: 'task-monitor',
          component: () => import('../views/TaskMonitorView.vue'),
        },
        {
          path: '/proxy/auto-session',
          name: 'auto-session',
          component: () => import('../views/AutoSessionView.vue'),
        },
        {
          path: '/proxy/mcp-proxy',
          name: 'mcp-proxy',
          component: () => import('../views/FastMCPProxyView.vue'),
        },
        {
          path: '/logs',
          name: 'logs',
          component: () => import('../views/LogsView.vue'),
        },
        {
          path: '/settings',
          name: 'settings',
          component: () => import('../views/SystemSettingsView.vue'),
        },
        {
          path: '/system-settings',
          name: 'system-settings',
          component: () => import('../views/SystemSettingsView.vue'),
        },
        {
          path: '/help',
          name: 'help',
          component: () => import('../views/HelpView.vue'),
        },
        {
          path: '/tutorial/tools',
          name: 'tutorial-tools',
          component: () => import('../views/TutorialToolsView.vue'),
        },
        {
          path: '/tutorial/proxy-mode',
          name: 'tutorial-proxy-mode',
          component: () => import('../views/TutorialProxyModeView.vue'),
        },
        {
          path: '/tutorial/mcp-mode',
          name: 'tutorial-mcp-mode',
          component: () => import('../views/TutorialMcpModeView.vue'),
        },
      ],
    },
  ],
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  // 初始化认证状态
  if (authStore.token && !authStore.user) {
    try {
      await authStore.initAuth()
    } catch (error) {
      console.error('初始化认证状态失败:', error)
    }
  }
  
  const requiresAuth = to.meta.requiresAuth !== false
  const isAuthenticated = authStore.isAuthenticated
  
  if (requiresAuth && !isAuthenticated) {
    // 需要认证但未登录，跳转到登录页
    next({
      path: '/login',
      query: { redirect: to.fullPath }
    })
  } else if (to.path === '/login' && isAuthenticated) {
    // 已登录用户访问登录页，跳转到首页
    next('/')
  } else {
    next()
  }
})

export default router
