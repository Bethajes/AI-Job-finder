import React from 'react';
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  TextStyle,
  ViewStyle,
} from 'react-native';

import { colors, fontSize, fontFamily, radius, spacing } from '../../constants/theme';

type ButtonVariant = 'primary' | 'outline' | 'ghost' | 'danger';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: ButtonVariant;
  loading?: boolean;
  disabled?: boolean;
  fullWidth?: boolean;
  style?: ViewStyle;
}

interface VariantStyle {
  container: ViewStyle;
  text: TextStyle;
  spinnerColor: string;
}

const variantStyles: Record<ButtonVariant, VariantStyle> = {
  primary: {
    container: { backgroundColor: colors.primary },
    text: { color: colors.white },
    spinnerColor: colors.white,
  },
  outline: {
    container: {
      backgroundColor: 'transparent',
      borderWidth: 1.5,
      borderColor: colors.primary,
    },
    text: { color: colors.primary },
    spinnerColor: colors.primary,
  },
  ghost: {
    container: { backgroundColor: 'transparent' },
    text: { color: colors.primary },
    spinnerColor: colors.primary,
  },
  danger: {
    container: { backgroundColor: colors.errorLight },
    text: { color: colors.error },
    spinnerColor: colors.error,
  },
};

export const Button = React.memo(function Button({
  title,
  onPress,
  variant = 'primary',
  loading = false,
  disabled = false,
  fullWidth = true,
  style,
}: ButtonProps) {
  const isDisabled = disabled || loading;
  const variantStyle = variantStyles[variant];

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ disabled: isDisabled, busy: loading }}
      accessibilityLabel={title}
      onPress={onPress}
      disabled={isDisabled}
      style={({ pressed }) => [
        styles.container,
        !fullWidth && styles.hugContent,
        variantStyle.container,
        pressed && styles.pressed,
        isDisabled && styles.disabled,
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator size="small" color={variantStyle.spinnerColor} />
      ) : (
        <Text style={[styles.text, variantStyle.text]}>{title}</Text>
      )}
    </Pressable>
  );
});

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radius.md,
    paddingVertical: spacing.md - 2,
    paddingHorizontal: spacing.lg,
    minHeight: 48,
  },
  hugContent: {
    alignSelf: 'flex-start',
  },
  pressed: {
    opacity: 0.85,
  },
  disabled: {
    opacity: 0.55,
  },
  text: {
    fontSize: fontSize.md,
    fontFamily: fontFamily.bold,
  },
});
