import React from 'react';
import { yupResolver } from '@hookform/resolvers/yup';
import { Controller, useForm } from 'react-hook-form';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Button, Input } from '../common';
import { colors, fontFamily, fontSize, radius, spacing } from '../../constants/theme';
import { RegisterFormValues, registerSchema } from '../../utils/validators';

interface RegisterFormProps {
  onSubmit: (values: RegisterFormValues) => Promise<void>;
  loading?: boolean;
}

const roleOptions: Array<{
  value: RegisterFormValues['role'];
  label: string;
  description: string;
}> = [
  { value: 'job_seeker', label: 'Job Seeker', description: 'Find and apply for jobs' },
  { value: 'employer', label: 'Employer', description: 'Post jobs and hire talent' },
];

export function RegisterForm({ onSubmit, loading = false }: RegisterFormProps) {
  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: yupResolver(registerSchema),
    defaultValues: {
      first_name: '',
      last_name: '',
      email: '',
      phone: '',
      password: '',
      confirmPassword: '',
      role: 'job_seeker',
    },
    mode: 'onTouched',
  });

  return (
    <View>
      <View style={styles.nameRow}>
        <Controller
          control={control}
          name="first_name"
          render={({ field: { onChange, onBlur, value } }) => (
            <Input
              label="First name"
              placeholder="Abebe"
              autoCapitalize="words"
              autoComplete="given-name"
              value={value}
              onChangeText={onChange}
              onBlur={onBlur}
              error={errors.first_name?.message}
              containerStyle={styles.nameField}
            />
          )}
        />
        <Controller
          control={control}
          name="last_name"
          render={({ field: { onChange, onBlur, value } }) => (
            <Input
              label="Last name"
              placeholder="Kebede"
              autoCapitalize="words"
              autoComplete="family-name"
              value={value}
              onChangeText={onChange}
              onBlur={onBlur}
              error={errors.last_name?.message}
              containerStyle={styles.nameField}
            />
          )}
        />
      </View>
      <Controller
        control={control}
        name="email"
        render={({ field: { onChange, onBlur, value } }) => (
          <Input
            label="Email"
            placeholder="you@example.com"
            keyboardType="email-address"
            autoCapitalize="none"
            autoComplete="email"
            textContentType="emailAddress"
            value={value}
            onChangeText={onChange}
            onBlur={onBlur}
            error={errors.email?.message}
          />
        )}
      />
      <Controller
        control={control}
        name="phone"
        render={({ field: { onChange, onBlur, value } }) => (
          <Input
            label="Phone (optional)"
            placeholder="+251912345678"
            keyboardType="phone-pad"
            autoComplete="tel"
            textContentType="telephoneNumber"
            value={value ?? ''}
            onChangeText={onChange}
            onBlur={onBlur}
            error={errors.phone?.message}
          />
        )}
      />
      <Controller
        control={control}
        name="role"
        render={({ field: { onChange, value } }) => (
          <View style={styles.roleGroup}>
            <Text style={styles.roleLabel}>I am joining as</Text>
            <View style={styles.roleRow}>
              {roleOptions.map((option) => {
                const isSelected = value === option.value;
                return (
                  <Pressable
                    key={option.value}
                    accessibilityRole="radio"
                    accessibilityState={{ selected: isSelected }}
                    onPress={() => onChange(option.value)}
                    style={[styles.roleCard, isSelected && styles.roleCardSelected]}
                  >
                    <Text style={[styles.roleTitle, isSelected && styles.roleTitleSelected]}>
                      {option.label}
                    </Text>
                    <Text style={styles.roleDescription}>{option.description}</Text>
                  </Pressable>
                );
              })}
            </View>
            {errors.role ? (
              <Text style={styles.roleError}>{errors.role.message}</Text>
            ) : null}
          </View>
        )}
      />
      <Controller
        control={control}
        name="password"
        render={({ field: { onChange, onBlur, value } }) => (
          <Input
            label="Password"
            placeholder="At least 8 characters"
            secureTextEntry
            autoComplete="new-password"
            textContentType="newPassword"
            value={value}
            onChangeText={onChange}
            onBlur={onBlur}
            error={errors.password?.message}
          />
        )}
      />
      <Controller
        control={control}
        name="confirmPassword"
        render={({ field: { onChange, onBlur, value } }) => (
          <Input
            label="Confirm password"
            placeholder="Re-enter your password"
            secureTextEntry
            autoComplete="new-password"
            textContentType="newPassword"
            value={value}
            onChangeText={onChange}
            onBlur={onBlur}
            error={errors.confirmPassword?.message}
          />
        )}
      />
      <Button title="Create Account" onPress={() => handleSubmit(onSubmit)()} loading={loading} style={{ marginTop: spacing.sm }} />
    </View>
  );
}

const styles = StyleSheet.create({
  nameRow: {
    flexDirection: 'row',
    gap: spacing.md - 4,
  },
  nameField: {
    flex: 1,
  },
  roleGroup: {
    marginBottom: spacing.md,
  },
  roleLabel: {
    fontSize: fontSize.sm,
    fontFamily: fontFamily.medium,
    color: colors.text,
    marginBottom: spacing.sm + 2,
  },
  roleRow: {
    flexDirection: 'row',
    gap: spacing.sm + 2,
  },
  roleCard: {
    flex: 1,
    borderWidth: 1.5,
    borderColor: colors.border,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
    paddingVertical: spacing.sm + 2,
    paddingHorizontal: spacing.md,
  },
  roleCardSelected: {
    borderColor: colors.primary,
    backgroundColor: colors.primaryLight,
  },
  roleTitle: {
    fontSize: fontSize.sm,
    fontFamily: fontFamily.bold,
    color: colors.text,
  },
  roleTitleSelected: {
    color: colors.primaryDark,
  },
  roleDescription: {
    marginTop: 2,
    fontSize: fontSize.sm - 1,
    color: colors.textMuted,
  },
  roleError: {
    marginTop: spacing.xs,
    fontSize: fontSize.sm,
    color: colors.error,
  },
});
