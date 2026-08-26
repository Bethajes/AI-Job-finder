import { Ionicons } from '@expo/vector-icons';
import React, { useEffect, useState } from 'react';
import { StyleSheet, TextInput, TouchableOpacity, View } from 'react-native';

import {
  colors,
  fontFamily,
  fontSize,
  radius,
  spacing,
} from '../../constants/theme';
import { useDebouncedValue } from '../../hooks/useDebouncedValue';

interface JobSearchBarProps {
  onSearch: (query: string) => void;
  placeholder?: string;
}

export function JobSearchBar({
  onSearch,
  placeholder = 'Job title or keyword',
}: JobSearchBarProps) {
  const [text, setText] = useState('');
  const debouncedText = useDebouncedValue(text.trim(), 500);

  useEffect(() => {
    onSearch(debouncedText);
  }, [debouncedText, onSearch]);

  const clear = () => {
    setText('');
    onSearch('');
  };

  return (
    <View style={styles.container}>
      <Ionicons
        name="search"
        size={18}
        color={colors.textMuted}
        style={styles.icon}
      />
      <TextInput
        style={styles.input}
        placeholder={placeholder}
        placeholderTextColor={colors.textMuted}
        value={text}
        onChangeText={setText}
        returnKeyType="search"
        autoCapitalize="none"
        autoCorrect={false}
        accessibilityLabel="Search jobs"
      />
      {text.length > 0 ? (
        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel="Clear search"
          onPress={clear}
          hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
        >
          <Ionicons name="close-circle" size={18} color={colors.textMuted} />
        </TouchableOpacity>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: colors.background,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: spacing.md,
  },
  icon: {
    marginRight: -spacing.xs,
  },
  input: {
    flex: 1,
    paddingVertical: spacing.sm + 3,
    fontSize: fontSize.md,
    fontFamily: fontFamily.regular,
    color: colors.text,
  },
});
