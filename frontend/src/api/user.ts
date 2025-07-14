import api from './index'

// 用户信息类型
export interface UserProfile {
  id: number
  username: string
  email: string
  full_name?: string
  phone?: string
  bio?: string
  avatar_url?: string
  theme: string
  language: string
  timezone: string
  email_notifications: boolean
  created_at?: string
  updated_at?: string
}

// 更新用户信息类型
export interface UserUpdateData {
  username?: string
  email?: string
  full_name?: string
  phone?: string
  bio?: string
  avatar_url?: string
}

// 修改密码类型
export interface PasswordUpdateData {
  current_password: string
  new_password: string
  confirm_password: string
}

// 用户偏好设置类型
export interface UserPreferences {
  theme?: string
  language?: string
  timezone?: string
  email_notifications?: boolean
}

// 用户统计信息类型
export interface UserStats {
  total_users: number
  active_users: number
  inactive_users: number
}

// 用户API接口
export const userApi = {
  // 获取用户资料
  getProfile: async (): Promise<UserProfile> => {
    const response = await api.get('/user/profile')
    return response.data
  },

  // 更新用户资料
  updateProfile: async (data: UserUpdateData): Promise<UserProfile> => {
    const response = await api.put('/user/profile', data)
    return response.data
  },

  // 修改密码
  updatePassword: async (data: PasswordUpdateData): Promise<{ success: boolean; message: string }> => {
    const response = await api.put('/user/password', data)
    return response.data
  },

  // 更新用户偏好设置
  updatePreferences: async (data: UserPreferences): Promise<UserProfile> => {
    const response = await api.put('/user/preferences', data)
    return response.data
  },

  // 获取用户统计信息
  getStats: async (): Promise<UserStats> => {
    const response = await api.get('/user/stats')
    return response.data.data
  }
}

export default userApi