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
          name: 'tools-manage',
          component: () => import('../views/ToolsView.vue'),
        },
        {
          path: '/tools/config',
          name: 'tools-config',
          component: () => import('../views/ToolConfigView.vue'),
        },
        {
          path: '/proxy',
          name: 'proxy-manage',
          component: () => import('../views/MCPAgentView.vue'),
        },
        {
          path: '/proxy/status',
          name: 'proxy-status',
          component: () => import('../views/ProxyStatusView.vue'),
        },
        {
          path: '/monitor',
          name: 'monitor',
          component: () => import('../views/MonitorView.vue'),
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
          path: '/profile',
          name: 'profile',
          component: () => import('../views/ProfileView.vue'),
        },
        {
          path: '/about',
          name: 'about',
          component: () => import('../views/AboutView.vue'),
        },
      ],
    },
  ],
})

export default router
