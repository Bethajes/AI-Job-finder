import AsyncStorage from '@react-native-async-storage/async-storage';
import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';

import { authApi, setOnUnauthorized } from '../api';
import { LoginPayload, RegisterPayload, User } from '../types';
import {
  clearSession,
  getAccessToken,
  getCachedUser,
  saveTokens,
  saveUser,
} from '../utils/storage';
import { extractErrorMessage, isSessionInvalidError } from '../utils/errors';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isBootstrapping: boolean;
  isLoading: boolean;
  error: string | null;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
  restoreSession: () => Promise<void>;
  refreshUserProfile: () => Promise<void>;
}

const unauthenticatedState = {
  user: null,
  isAuthenticated: false,
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      isBootstrapping: true,
      isLoading: false,
      error: null,

      login: async (payload) => {
        set({ isLoading: true, error: null });
        try {
          const tokens = await authApi.login(payload);
          await saveTokens(tokens);
          const user = await authApi.me();
          await saveUser(user);
          set({ user, isAuthenticated: true });
        } catch (error) {
          await clearSession();
          set({ error: extractErrorMessage(error, 'Invalid email or password.') });
          throw error;
        } finally {
          set({ isLoading: false });
        }
      },

      register: async (payload) => {
        set({ isLoading: true, error: null });
        try {
          const tokens = await authApi.register(payload);
          await saveTokens(tokens);
          const user = await authApi.me();
          await saveUser(user);
          set({ user, isAuthenticated: true });
        } catch (error) {
          await clearSession();
          set({ error: extractErrorMessage(error, 'Registration failed. Please try again.') });
          throw error;
        } finally {
          set({ isLoading: false });
        }
      },

      logout: async () => {
        await authApi.logout().catch(() => undefined);
        await clearSession();
        set({ ...unauthenticatedState, isLoading: false, error: null });
      },

      restoreSession: async () => {
        const [accessToken, cachedUser] = await Promise.all([
          getAccessToken(),
          getCachedUser(),
        ]);

        if (!accessToken) {
          if (cachedUser) await clearSession();
          set({ ...unauthenticatedState, isBootstrapping: false });
          return;
        }

        try {
          const user = await authApi.me();
          await saveUser(user);
          set({ user, isAuthenticated: true, isBootstrapping: false });
        } catch (error) {
          if (isSessionInvalidError(error)) {
            await clearSession();
            set({ ...unauthenticatedState, isBootstrapping: false });
            return;
          }
          if (cachedUser) {
            set({ user: cachedUser, isAuthenticated: true, isBootstrapping: false });
            return;
          }
          await clearSession();
          set({ ...unauthenticatedState, isBootstrapping: false });
        }
      },

      refreshUserProfile: async () => {
        const user = await authApi.me();
        await saveUser(user);
        set({ user });
      },
    }),
    {
      name: 'auth-storage',
      version: 1,
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({ user: state.user }),
    },
  ),
);

setOnUnauthorized(() => {
  useAuthStore.setState(unauthenticatedState);
});
