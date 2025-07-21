import { api, withRetry, handleApiError } from './utils';
import type { ApiResponse } from './utils';
import { AUTH_PATHS } from './constants';
import type { User } from './user';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  user: {
    id: number;
    username: string;
    email: string;
    role: string;
  };
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface ChangePasswordRequest {
  currentPassword: string;
  newPassword: string;
}

export const authApi = {
  /**
   * 用户登录
   */
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    try {
      const response = await withRetry(() => api.post<LoginResponse>(AUTH_PATHS.LOGIN, data));
      return response.data!;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },
  
  /**
   * 用户登出
   */
  logout: async (): Promise<ApiResponse<void>> => {
    try {
      return await api.post<void>(AUTH_PATHS.LOGOUT);
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },
  
  /**
   * 刷新访问令牌
   */
  refreshToken: async (data: RefreshTokenRequest): Promise<LoginResponse> => {
    try {
      const response = await api.post<LoginResponse>(AUTH_PATHS.REFRESH, data);
      return response.data!;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },
  
  /**
   * 获取当前用户信息
   */
  getCurrentUser: async (): Promise<User> => {
    try {
      const response = await api.get<User>(AUTH_PATHS.ME);
      return response.data!;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },
  
  /**
   * 修改密码
   */
  changePassword: async (data: ChangePasswordRequest): Promise<ApiResponse<void>> => {
    try {
      return await api.post<void>(AUTH_PATHS.CHANGE_PASSWORD, data);
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },
};