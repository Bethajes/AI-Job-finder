import { NativeStackScreenProps } from '@react-navigation/native-stack';
import React, { useCallback } from 'react';
import {
  Alert,
  Image,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { RegisterForm } from '../../components/auth';
import { colors, fontFamily, fontSize, spacing } from '../../constants/theme';
import { useAuth } from '../../hooks/useAuth';
import { AuthStackParamList } from '../../navigation/types';
import { RegisterFormValues } from '../../utils/validators';

type RegisterScreenProps = NativeStackScreenProps<AuthStackParamList, 'Register'>;

export function RegisterScreen({ navigation }: RegisterScreenProps) {
  const { register, isLoading } = useAuth();

  const handleSubmit = useCallback(
    async (values: RegisterFormValues) => {
      try {
        await register({
          email: values.email.trim(),
          first_name: values.first_name.trim(),
          last_name: values.last_name.trim(),
          phone: values.phone ? values.phone.trim() : undefined,
          password: values.password,
          role: values.role,
        });
      } catch (error) {
        Alert.alert(
          'Registration Failed',
          error instanceof Error && error.message
            ? error.message
            : 'Could not create your account. Please try again.',
        );
      }
    },
    [register],
  );

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView
          style={styles.flex}
          contentContainerStyle={styles.content}
          keyboardShouldPersistTaps="handled"
          bounces={false}
        >
          <TouchableOpacity
            accessibilityRole="button"
            accessibilityLabel="Back to login"
            onPress={() => navigation.goBack()}
            style={styles.backButton}
          >
            <Text style={styles.backText}>‹ Back</Text>
          </TouchableOpacity>
          <View style={styles.header}>
            <Image
              source={require('../../../assets/images/icon.png')}
              style={styles.logo}
              resizeMode="contain"
            />
            <Text style={styles.title}>Create your account</Text>
            <Text style={styles.subtitle}>
              Join thousands of job seekers and employers
            </Text>
          </View>
          <RegisterForm onSubmit={handleSubmit} loading={isLoading} />
          <TouchableOpacity
            accessibilityRole="button"
            onPress={() => navigation.navigate('Login')}
            style={styles.linkButton}
          >
            <Text style={styles.linkText}>
              Already have an account?{' '}
              <Text style={styles.linkHighlight}>Login</Text>
            </Text>
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.surface,
  },
  flex: {
    flex: 1,
  },
  content: {
    flexGrow: 1,
    padding: spacing.lg,
    paddingBottom: spacing.xl,
  },
  backButton: {
    alignSelf: 'flex-start',
    paddingVertical: spacing.sm,
    paddingRight: spacing.md,
  },
  backText: {
    fontSize: fontSize.md,
    fontFamily: fontFamily.medium,
    color: colors.primary,
  },
  header: {
    alignItems: 'center',
    marginBottom: spacing.lg,
  },
  logo: {
    width: 60,
    height: 60,
    marginBottom: spacing.md,
  },
  title: {
    fontSize: fontSize.xl,
    fontFamily: fontFamily.bold,
    color: colors.text,
  },
  subtitle: {
    marginTop: spacing.xs + 2,
    fontSize: fontSize.sm + 1,
    fontFamily: fontFamily.regular,
    color: colors.textMuted,
    textAlign: 'center',
  },
  linkButton: {
    alignItems: 'center',
    marginTop: spacing.lg,
    paddingVertical: spacing.sm,
  },
  linkText: {
    fontSize: fontSize.sm + 1,
    fontFamily: fontFamily.regular,
    color: colors.textMuted,
  },
  linkHighlight: {
    fontFamily: fontFamily.bold,
    color: colors.primary,
  },
});
