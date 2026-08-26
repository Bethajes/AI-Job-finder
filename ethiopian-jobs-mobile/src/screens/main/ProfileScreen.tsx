import Constants from 'expo-constants';
import { Ionicons } from '@expo/vector-icons';
import React, { useCallback, useState } from 'react';
import { Alert, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button } from '../../components/common';
import {
  colors,
  fontFamily,
  fontSize,
  radius,
  spacing,
} from '../../constants/theme';
import { useRequireAuth } from '../../hooks/useAuth';
import {
  formatDate,
  formatEmploymentType,
} from '../../utils/format';

const roleLabels: Record<string, string> = {
  job_seeker: 'Job Seeker',
  employer: 'Employer',
  admin: 'Admin',
};

export function ProfileScreen() {
  const { user, logout, refreshUserProfile } = useRequireAuth();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const handleRefreshProfile = useCallback(async () => {
    setIsRefreshing(true);
    await refreshUserProfile().catch(() => undefined);
    setIsRefreshing(false);
  }, [refreshUserProfile]);

  const performLogout = useCallback(async () => {
    setIsLoggingOut(true);
    await logout();
    setIsLoggingOut(false);
  }, [logout]);

  const confirmLogout = useCallback(() => {
    Alert.alert('Log Out', 'Are you sure you want to log out?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Log Out', style: 'destructive', onPress: () => void performLogout() },
    ]);
  }, [performLogout]);

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.title}>Profile</Text>
      </View>
      <View style={styles.content}>
        <View style={styles.profileCard}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>
              {(user.first_name.charAt(0) + user.last_name.charAt(0)).toUpperCase()}
            </Text>
          </View>
          <View style={styles.identity}>
            <Text style={styles.name}>
              {user.first_name} {user.last_name}
            </Text>
            <Text style={styles.email}>{user.email}</Text>
            <View style={styles.badgeRow}>
              <View style={[styles.badge, styles.roleBadge]}>
                <Text style={styles.roleBadgeText}>
                  {roleLabels[user.role] ?? user.role}
                </Text>
              </View>
              <View
                style={[
                  styles.badge,
                  user.is_verified ? styles.verifiedBadge : styles.pendingBadge,
                ]}
              >
                <Ionicons
                  name={user.is_verified ? 'checkmark-circle' : 'time'}
                  size={12}
                  color={user.is_verified ? colors.primaryDark : colors.textMuted}
                />
                <Text
                  style={
                    user.is_verified ? styles.verifiedText : styles.pendingText
                  }
                >
                  {user.is_verified ? 'Verified' : 'Unverified email'}
                </Text>
              </View>
            </View>
          </View>
        </View>

        <View style={styles.detailsCard}>
          <DetailRow icon="call-outline" label="Phone" value={user.phone ?? 'Not provided'} />
          <DetailRow icon="briefcase-outline" label="Role" value={formatEmploymentType(user.role)} />
          <DetailRow
            icon="calendar-outline"
            label="Member since"
            value={formatDate(user.created_at) || '—'}
          />
        </View>

        <Button
          title="Refresh Profile"
          variant="outline"
          onPress={() => void handleRefreshProfile()}
          loading={isRefreshing}
          style={styles.actionSpacing}
        />
        <Button
          title="Log Out"
          variant="danger"
          onPress={confirmLogout}
          loading={isLoggingOut}
        />

        <Text style={styles.version}>
          Ethiopian Jobs v{Constants.expoConfig?.version ?? '1.0.0'}
        </Text>
      </View>
    </SafeAreaView>
  );
}

function DetailRow({
  icon,
  label,
  value,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  label: string;
  value: string;
}) {
  return (
    <View style={styles.detailRow}>
      <View style={styles.detailIcon}>
        <Ionicons name={icon} size={18} color={colors.primaryDark} />
      </View>
      <View style={styles.detailTextWrap}>
        <Text style={styles.detailLabel}>{label}</Text>
        <Text style={styles.detailValue}>{value}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.md,
    paddingBottom: spacing.sm,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  title: {
    fontSize: fontSize.xl,
    fontFamily: fontFamily.bold,
    color: colors.text,
  },
  content: {
    padding: spacing.lg,
    gap: spacing.md,
  },
  profileCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
  },
  avatar: {
    width: 64,
    height: 64,
    borderRadius: radius.pill,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    fontSize: fontSize.xl - 2,
    fontFamily: fontFamily.bold,
    color: colors.white,
  },
  identity: {
    flex: 1,
  },
  name: {
    fontSize: fontSize.lg,
    fontFamily: fontFamily.bold,
    color: colors.text,
  },
  email: {
    marginTop: 2,
    fontSize: fontSize.sm,
    color: colors.textMuted,
  },
  badgeRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.xs + 2,
    marginTop: spacing.sm,
  },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    borderRadius: radius.pill,
    paddingVertical: 3,
    paddingHorizontal: spacing.sm + 2,
  },
  roleBadge: {
    backgroundColor: colors.primaryLight,
  },
  roleBadgeText: {
    fontSize: fontSize.sm - 1,
    fontFamily: fontFamily.medium,
    color: colors.primaryDark,
  },
  verifiedBadge: {
    backgroundColor: '#E8F5E9',
  },
  verifiedText: {
    fontSize: fontSize.sm - 1,
    color: colors.primaryDark,
  },
  pendingBadge: {
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.border,
  },
  pendingText: {
    fontSize: fontSize.sm - 1,
    color: colors.textMuted,
  },
  detailsCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.sm + 4,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md - 2,
    paddingVertical: spacing.sm + 3,
    paddingHorizontal: spacing.sm,
  },
  detailIcon: {
    width: 36,
    height: 36,
    borderRadius: radius.sm,
    backgroundColor: colors.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  detailTextWrap: {
    flex: 1,
  },
  detailLabel: {
    fontSize: fontSize.sm - 1,
    color: colors.textMuted,
  },
  detailValue: {
    marginTop: 1,
    fontSize: fontSize.sm + 1,
    fontFamily: fontFamily.medium,
    color: colors.text,
  },
  actionSpacing: {
    marginTop: spacing.sm,
  },
  version: {
    textAlign: 'center',
    fontSize: fontSize.sm - 1,
    color: colors.textMuted,
    marginTop: spacing.sm,
  },
});
