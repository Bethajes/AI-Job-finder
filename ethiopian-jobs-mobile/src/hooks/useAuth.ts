import { useCallback } from 'react';

import { User } from '../types';
import { useAuthStore } from '../store';

export function useAuth() {
  const user = useAuthStore((state) => state.user);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const isLoading = useAuthStore((state) => state.isLoading);
  const error = useAuthStore((state) => state.error);
  const login = useAuthStore((state) => state.login);
  const register = useAuthStore((state) => state.register);
  const logoutAction = useAuthStore((state) => state.logout);
  const refreshUserProfile = useAuthStore((state) => state.refreshUserProfile);

  const logout = useCallback(() => logoutAction(), [logoutAction]);

  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    register,
    logout,
    refreshUserProfile,
  };
}

export function useRequireAuth(): {
  user: User;
  logout: () => Promise<void>;
  refreshUserProfile: () => Promise<void>;
} {
  const { user, isAuthenticated, logout, refreshUserProfile } = useAuth();

  if (!isAuthenticated || !user) {
    throw new Error(
      'useRequireAuth was used outside an authenticated session. Render this screen behind MainTabs only.',
    );
  }

  return { user, logout, refreshUserProfile };
}
