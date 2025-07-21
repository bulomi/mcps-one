import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/api/user'
import { authApi } from '@/api/auth'

export interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  isAuthenticated: boolean
}

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))

  // 计算属性
  const isAuthenticated = computed(() => {
    return !!token.value && !!user.value
  })

  // 登录
  const login = async (username: string, password: string) => {
    try {
      const response = await authApi.login({ username, password })
      
      // 保存令牌
      token.value = response.access_token
      refreshToken.value = response.refresh_token
      user.value = response.user
      
      // 保存到本地存储
      localStorage.setItem('access_token', response.access_token)
      localStorage.setItem('refresh_token', response.refresh_token)
      
      return response
    } catch (error) {
      console.error('登录失败:', error)
      throw error
    }
  }

  // 登出
  const logout = async () => {
    try {
      if (token.value) {
        await authApi.logout()
      }
    } catch (error) {
      console.error('登出失败:', error)
    } finally {
      // 清除状态
      user.value = null
      token.value = null
      refreshToken.value = null
      
      // 清除本地存储
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    }
  }

  // 刷新令牌
  const refreshAccessToken = async () => {
    try {
      if (!refreshToken.value) {
        throw new Error('没有刷新令牌')
      }
      
      const response = await authApi.refreshToken({ refresh_token: refreshToken.value })
      
      // 更新访问令牌
      token.value = response.access_token
      localStorage.setItem('access_token', response.access_token)
      
      return response.access_token
    } catch (error) {
      console.error('刷新令牌失败:', error)
      // 刷新失败，清除所有认证信息
      await logout()
      throw error
    }
  }

  // 获取当前用户信息
  const fetchCurrentUser = async () => {
    try {
      if (!token.value) {
        throw new Error('未登录')
      }
      
      const currentUser = await authApi.getCurrentUser()
      user.value = currentUser
      
      return currentUser
    } catch (error) {
      console.error('获取用户信息失败:', error)
      throw error
    }
  }

  // 初始化认证状态
  const initAuth = async () => {
    if (token.value) {
      try {
        await fetchCurrentUser()
      } catch (error) {
        // 如果获取用户信息失败，尝试刷新令牌
        try {
          await refreshAccessToken()
          await fetchCurrentUser()
        } catch (refreshError) {
          // 刷新也失败，清除认证信息
          await logout()
        }
      }
    }
  }

  // 修改密码
  const changePassword = async (oldPassword: string, newPassword: string) => {
    try {
      await authApi.changePassword({
        old_password: oldPassword,
        new_password: newPassword
      })
    } catch (error) {
      console.error('修改密码失败:', error)
      throw error
    }
  }

  return {
    // 状态
    user,
    token,
    refreshToken,
    isAuthenticated,
    
    // 方法
    login,
    logout,
    refreshAccessToken,
    fetchCurrentUser,
    initAuth,
    changePassword
  }
})