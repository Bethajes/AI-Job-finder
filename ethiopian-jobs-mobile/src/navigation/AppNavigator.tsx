import {
  DarkTheme,
  DefaultTheme,
  NavigationContainer,
  Theme,
} from '@react-navigation/native';
import * as ExpoSplashScreen from 'expo-splash-screen';
import {
  Inter_400Regular,
  Inter_500Medium,
  Inter_700Bold,
  useFonts,
} from '@expo-google-fonts/inter';
import React, { useEffect, useState } from 'react';

import { SplashScreen } from '../screens/SplashScreen';
import { colors } from '../constants/theme';
import { useAuthStore } from '../store';
import { AuthStack } from './AuthStack';
import { MainTabs } from './MainTabs';

const navigationTheme: Theme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    ...DarkTheme.colors,
    primary: colors.primary,
    background: colors.background,
    card: colors.surface,
    text: colors.text,
    border: colors.border,
  },
};

export function AppNavigator() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const isBootstrapping = useAuthStore((state) => state.isBootstrapping);
  const restoreSession = useAuthStore((state) => state.restoreSession);

  const [fontsLoaded, fontError] = useFonts({
    Inter_400Regular,
    Inter_500Medium,
    Inter_700Bold,
  });
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    ExpoSplashScreen.preventAutoHideAsync().catch(() => undefined);
  }, []);

  useEffect(() => {
    restoreSession();
  }, [restoreSession]);

  useEffect(() => {
    if ((fontsLoaded || fontError) && !isBootstrapping) {
      setIsReady(true);
      ExpoSplashScreen.hideAsync().catch(() => undefined);
    }
  }, [fontsLoaded, fontError, isBootstrapping]);

  if (!isReady || isBootstrapping) {
    return <SplashScreen />;
  }

  return (
    <NavigationContainer theme={navigationTheme}>
      {isAuthenticated ? <MainTabs /> : <AuthStack />}
    </NavigationContainer>
  );
}
