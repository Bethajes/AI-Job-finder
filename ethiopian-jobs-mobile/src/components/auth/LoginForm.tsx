import React from 'react';
import { yupResolver } from '@hookform/resolvers/yup';
import { Controller, useForm } from 'react-hook-form';
import { View } from 'react-native';

import { Button, Input } from '../common';
import { LoginFormValues, loginSchema } from '../../utils/validators';

interface LoginFormProps {
  onSubmit: (values: LoginFormValues) => Promise<void>;
  loading?: boolean;
}

export function LoginForm({ onSubmit, loading = false }: LoginFormProps) {
  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: yupResolver(loginSchema),
    defaultValues: { email: '', password: '' },
    mode: 'onTouched',
  });

  return (
    <View>
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
        name="password"
        render={({ field: { onChange, onBlur, value } }) => (
          <Input
            label="Password"
            placeholder="Enter your password"
            secureTextEntry
            autoComplete="password"
            textContentType="password"
            value={value}
            onChangeText={onChange}
            onBlur={onBlur}
            error={errors.password?.message}
          />
        )}
      />
      <Button
        title="Login"
        onPress={() => handleSubmit(onSubmit)()}
        loading={loading}
        style={{ marginTop: 8 }}
      />
    </View>
  );
}
