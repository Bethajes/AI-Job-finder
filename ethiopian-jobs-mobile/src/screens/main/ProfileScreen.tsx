import Constants from 'expo-constants';
import { Ionicons } from '@expo/vector-icons';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import React, { useCallback, useMemo, useState } from 'react';
import {
  Alert,
  FlatList,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
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
  useInfiniteSavedJobs,
  useToggleSavedJob,
} from '../../hooks/useSavedJobs';
import { RootStackParamList } from '../../navigation/types';
import {
  formatEmploymentType,
  formatDate,
  formatSalaryRange,
} from '../../utils/format';
import { SavedJobView } from '../../types';

const roleLabels: Record<string, string> = {
  job_seeker: 'Job Seeker',
  employer: 'Employer',
  admin: 'Admin',
};

type ProfileScreenNavigationProp = NativeStackNavigationProp<
  RootStackParamList,
  'JobDetail'
>;

interface ProfileScreenProps {
  navigation: ProfileScreenNavigationProp;
}

export function ProfileScreen({ navigation }: ProfileScreenProps) {
  const { user, logout, refreshUserProfile } = useRequireAuth();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const savedJobsQuery = useInfiniteSavedJobs();
  const toggleSavedJob = useToggleSavedJob();
  const refetchSavedJobs = savedJobsQuery.refetch;

  const savedJobs = useMemo(
    () => savedJobsQuery.data?.pages.flatMap((page) => page.items) ?? [],
    [savedJobsQuery.data],
  );

  const savedTotal = savedJobsQuery.data?.pages[0]?.total ?? 0;

  const handleRefreshProfile = useCallback(async () => {
    setIsRefreshing(true);
    await Promise.all([
      refreshUserProfile().catch(() => undefined),
      refetchSavedJobs(),
    ]);
    setIsRefreshing(false);
  }, [refreshUserProfile, refetchSavedJobs]);

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
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing || (savedJobsQuery.isRefetching && !savedJobsQuery.isFetchingNextPage)}
            onRefresh={() => void handleRefreshProfile()}
            tintColor={colors.primary}
          />
        }
      >
        <View style={styles.header}>
          <Text style={styles.title}>Profile</Text>
        </View>
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

        <View style={styles.savedSectionHeader}>
          <Text style={styles.savedSectionTitle}>Saved Jobs</Text>
          {savedTotal > 0 ? (
            <Text style={styles.savedSectionCount}>
              {savedTotal} saved
            </Text>
          ) : null}
        </View>

        {savedJobs.length === 0 ? (
          <View style={styles.savedEmpty}>
            <Ionicons name="bookmark-outline" size={26} color={colors.textMuted} />
            <Text style={styles.savedEmptyText}>
              Jobs you save will appear here for quick access.
            </Text>
          </View>
        ) : (
          <FlatList
            data={savedJobs}
            keyExtractor={(item) => item.id}
            scrollEnabled={false}
            ItemSeparatorComponent={() => <View style={styles.savedSeparator} />}
            renderItem={({ item }) => (
              <SavedJobRow
                item={item}
                onPress={() => navigation.navigate('JobDetail', { jobId: item.job_id })}
                onUnsave={() =>
                  toggleSavedJob.mutate({ jobId: item.job_id, save: false })
                }
              />
            )}
            onEndReached={() => {
              if (savedJobsQuery.hasNextPage && !savedJobsQuery.isFetchingNextPage) {
                void savedJobsQuery.fetchNextPage();
              }
            }}
            onEndReachedThreshold={0.5}
            ListFooterComponent={
              savedJobsQuery.isFetchingNextPage ? (
                <Text style={styles.loadingMore}>Loading more…</Text>
              ) : null
            }
          />
        )}

        <Button
          title="Log Out"
          variant="danger"
          onPress={confirmLogout}
          loading={isLoggingOut}
        />

        <Text style={styles.version}>
          Ethiopian Jobs v{Constants.expoConfig?.version ?? '1.0.0'}
        </Text>
      </ScrollView>
    </SafeAreaView>
  );
}

function SavedJobRow({
  item,
  onPress,
  onUnsave,
}: {
  item: SavedJobView;
  onPress: () => void;
  onUnsave: () => void;
}) {
  return (
    <TouchableOpacity
      accessibilityRole="button"
      accessibilityLabel={`Open saved job ${item.job.title}`}
      style={styles.savedCard}
      onPress={onPress}
      activeOpacity={0.85}
    >
      <View style={styles.savedBody}>
        <Text style={styles.savedTitle} numberOfLines={1}>
          {item.job.title}
        </Text>
        <Text style={styles.savedCompany} numberOfLines={1}>
          {item.job.company_name}
        </Text>
        <Text style={styles.savedMeta} numberOfLines={1}>
          {item.job.is_remote
            ? 'Remote'
            : item.job.location ?? 'Ethiopia'}
          {' · '}
          {formatSalaryRange(item.job.salary_min, item.job.salary_max, item.job.currency)}
        </Text>
      </View>
      <TouchableOpacity
        accessibilityRole="button"
        accessibilityLabel="Remove from saved jobs"
        onPress={onUnsave}
        hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
        style={styles.savedAction}
      >
        <Ionicons name="bookmark" size={20} color={colors.primary} />
      </TouchableOpacity>
    </TouchableOpacity>
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
  },
  title: {
    fontSize: fontSize.xl,
    fontFamily: fontFamily.bold,
    color: colors.text,
  },
  content: {
    paddingBottom: spacing.xl,
  },
  profileCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    marginHorizontal: spacing.lg,
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
    marginHorizontal: spacing.lg,
    marginTop: spacing.md,
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
    marginHorizontal: spacing.lg,
    marginTop: spacing.md,
  },
  savedSectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: spacing.lg,
    marginBottom: spacing.sm,
    marginHorizontal: spacing.lg,
  },
  savedSectionTitle: {
    fontSize: fontSize.lg,
    fontFamily: fontFamily.bold,
    color: colors.text,
  },
  savedSectionCount: {
    fontSize: fontSize.sm,
    color: colors.textMuted,
  },
  savedEmpty: {
    alignItems: 'center',
    gap: spacing.sm,
    marginHorizontal: spacing.lg,
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    paddingVertical: spacing.lg,
    paddingHorizontal: spacing.md,
  },
  savedEmptyText: {
    fontSize: fontSize.sm,
    color: colors.textMuted,
    textAlign: 'center',
  },
  savedSeparator: {
    height: spacing.sm + 2,
  },
  savedCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm + 2,
    marginHorizontal: spacing.lg,
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md - 2,
  },
  savedBody: {
    flex: 1,
  },
  savedTitle: {
    fontSize: fontSize.sm + 2,
    fontFamily: fontFamily.bold,
    color: colors.text,
  },
  savedCompany: {
    marginTop: 1,
    fontSize: fontSize.sm,
    color: colors.textMuted,
  },
  savedMeta: {
    marginTop: 3,
    fontSize: fontSize.sm - 2,
    color: colors.primaryDark,
  },
  savedAction: {
    padding: spacing.xs,
  },
  loadingMore: {
    textAlign: 'center',
    marginTop: spacing.sm,
    fontSize: fontSize.sm,
    color: colors.textMuted,
  },
  version: {
    textAlign: 'center',
    fontSize: fontSize.sm - 1,
    color: colors.textMuted,
    marginTop: spacing.lg,
  },
});
