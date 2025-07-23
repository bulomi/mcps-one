import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../components/Layout/MainLayout.vue'
import LoginView from '../views/LoginView.vue'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [

    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      redirect: '/tools'
    },
    {
      path: '/app',
      redirect: '/tools'
    },
    {
      path: '/tools',
      name: 'tools',
      component: MainLayout,
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          component: () => import('../views/ToolsView.vue'),
        },
      ],
    },
    {
      path: '/tutorial',
      name: 'Tutorial',
      component: MainLayout,
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          component: () => import('../views/TutorialView.vue'),
        },
        {
          path: 'mcp-server',
          name: 'McpServerTutorial',
          component: () => import('../views/DocsView.vue'),
          beforeEnter: (to, from, next) => {
            to.query.doc = 'configuration.md'
            next()
          }
        },
        {
          path: 'tool-management',
          name: 'ToolManagementTutorial',
          component: () => import('../views/DocsView.vue'),
          beforeEnter: (to, from, next) => {
            to.query.doc = 'getting-started.md'
            next()
          }
        },
        {
          path: 'api-documentation',
          name: 'ApiDocumentation',
          component: () => import('../views/DocsView.vue'),
          beforeEnter: (to, from, next) => {
            to.query.doc = 'api-guide.md'
            next()
          }
        },
      ],
    },
    {
      path: '/docs',
      name: 'docs',
      component: MainLayout,
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          component: () => import('../views/DocsView.vue'),
        },
      ],
    },
    {
      path: '/settings',
      name: 'settings',
      component: MainLayout,
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          component: () => import('../views/SystemSettingsView.vue'),
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
