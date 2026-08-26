import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

import { STORAGE_KEYS } from '../config';
import { TokenResponse, User } from '../types';

const canUseSecureStore = Platform.OS !== 'web';

async function secureSet(key: string, value: string): Promise<void> {
  if (canUseSecureStore) {
    await SecureStore.setItemAsync(key, value);
    return;
  }
  await AsyncStorage.setItem(key, value);
}

async function secureGet(key: string): Promise<string | null> {
  if (canUseSecureStore) {
    return SecureStore.getItemAsync(key);
  }
  return AsyncStorage.getItem(key);
}

async function secureRemove(key: string): Promise<void> {
  if (canUseSecureStore) {
    await SecureStore.deleteItemAsync(key);
    return;
  }
  await AsyncStorage.removeItem(key);
}

export async function saveTokens(tokens: TokenResponse): Promise<void> {
  await Promise.all([
    secureSet(STORAGE_KEYS.accessToken, tokens.access_token),
    secureSet(STORAGE_KEYS.refreshToken, tokens.refresh_token),
  ]);
}

export async function getAccessToken(): Promise<string | null> {
  return secureGet(STORAGE_KEYS.accessToken);
}

export async function getRefreshToken(): Promise<string | null> {
  return secureGet(STORAGE_KEYS.refreshToken);
}

export async function clearSession(): Promise<void> {
  await Promise.all([
    secureRemove(STORAGE_KEYS.accessToken),
    secureRemove(STORAGE_KEYS.refreshToken),
    AsyncStorage.removeItem(STORAGE_KEYS.user),
  ]);
}

export async function saveUser(user: User): Promise<void> {
  await AsyncStorage.setItem(STORAGE_KEYS.user, JSON.stringify(user));
}

export async function getCachedUser(): Promise<User | null> {
  const raw = await AsyncStorage.getItem(STORAGE_KEYS.user);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}
