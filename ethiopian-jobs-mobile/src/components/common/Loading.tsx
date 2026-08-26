import React from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import { colors, fontFamily, fontSize, spacing } from '../../constants/theme';

interface LoadingProps {
  message?: string;
  fullscreen?: boolean;
}

export const Loading = React.memo(function Loading({
  message = 'Loading…',
  fullscreen = false,
}: LoadingProps) {
  return (
    <View style={[styles.container, fullscreen ? styles.fullscreen : styles.inline]}>
      <ActivityIndicator size="large" color={colors.primary} />
      <Text style={styles.message}>{message}</Text>
    </View>
  );
});

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm + 2,
  },
  fullscreen: {
    flex: 1,
    backgroundColor: colors.background,
  },
  inline: {
    paddingVertical: spacing.xl,
  },
  message: {
    fontSize: fontSize.sm,
    fontFamily: fontFamily.regular,
    color: colors.textMuted,
  },
});
