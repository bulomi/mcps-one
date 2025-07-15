import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../components/Layout/MainLayout.vue'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: MainLayout,
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
          path: '/mcp-unified',
          name: 'mcp-unified',
          component: () => import('../components/MCPUnifiedManager.vue'),
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
      ],
    },
  ],
})

export default router
