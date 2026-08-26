import axios, { AxiosError } from 'axios';

import { API_BASE_URL, API_TIMEOUT_MS } from '../config';
import {
  clearSession,
  getAccessToken,
  getRefreshToken,
  saveTokens,
} from '../utils/storage';
import { TokenResponse } from '../types';

type UnauthorizedCallback = () => void | Promise<void>;

let onUnauthorized: UnauthorizedCallback | null = null;

export function setOnUnauthorized(callback: UnauthorizedCallback): void {
  onUnauthorized = callback;
}

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT_MS,
  headers: { 'Content-Type': 'application/json' },
});

let refreshPromise: Promise<string> | null = null;

async function requestRefreshedAccessToken(refreshToken: string): Promise<string> {
  const response = await axios.post<TokenResponse>(
    `${API_BASE_URL}/auth/refresh`,
    { refresh_token: refreshToken },
    { timeout: API_TIMEOUT_MS },
  );
  await saveTokens(response.data);
  return response.data.access_token;
}

apiClient.interceptors.request.use(async (config) => {
  const token = await getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config;
    const url = originalRequest?.url ?? '';
    const isAuthRoute =
      url.includes('/auth/login') ||
      url.includes('/auth/register') ||
      url.includes('/auth/refresh');

    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !isAuthRoute
    ) {
      originalRequest._retry = true;
      const refreshToken = await getRefreshToken();

      if (refreshToken) {
        try {
          if (!refreshPromise) {
            refreshPromise = requestRefreshedAccessToken(refreshToken).finally(
              () => {
                refreshPromise = null;
              },
            );
          }
          const accessToken = await refreshPromise;
          originalRequest.headers.Authorization = `Bearer ${accessToken}`;
          return apiClient(originalRequest);
        } catch {
          await clearSession();
          await onUnauthorized?.();
        }
      } else {
        await clearSession();
        await onUnauthorized?.();
      }
    }

    return Promise.reject(error);
  },
);

export default apiClient;
