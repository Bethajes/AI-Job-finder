import apiClient from './client';
import {
  LoginPayload,
  MessageResponse,
  RefreshTokenPayload,
  RegisterPayload,
  TokenResponse,
  User,
} from '../types';

export const authApi = {
  async register(payload: RegisterPayload): Promise<TokenResponse> {
    const { data } = await apiClient.post<TokenResponse>(
      '/auth/register',
      payload,
    );
    return data;
  },

  async login(payload: LoginPayload): Promise<TokenResponse> {
    const { data } = await apiClient.post<TokenResponse>('/auth/login', payload);
    return data;
  },

  async refresh(payload: RefreshTokenPayload): Promise<TokenResponse> {
    const { data } = await apiClient.post<TokenResponse>(
      '/auth/refresh',
      payload,
    );
    return data;
  },

  async me(): Promise<User> {
    const { data } = await apiClient.get<User>('/auth/me');
    return data;
  },

  async logout(): Promise<MessageResponse> {
    const { data } = await apiClient.post<MessageResponse>('/auth/logout');
    return data;
  },
};
