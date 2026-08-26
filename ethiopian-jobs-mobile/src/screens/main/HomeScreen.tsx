import { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import React, { useCallback } from 'react';
import {
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { JobCard } from '../../components/jobs';
import { Loading } from '../../components/common';
import { colors, fontFamily, fontSize, radius, spacing } from '../../constants/theme';
import { useAuth } from '../../hooks/useAuth';
import { useJobs } from '../../hooks/useApi';
import { MainTabParamList } from '../../navigation/types';

type HomeScreenNavigationProp = BottomTabNavigationProp<MainTabParamList, 'Home'>;

interface HomeScreenProps {
  navigation: HomeScreenNavigationProp;
}

export function HomeScreen({ navigation }: HomeScreenProps) {
  const { user } = useAuth();
  const jobsQuery = useJobs({}, 1, 5);
  const recentJobs = jobsQuery.data?.items ?? [];

  const handleRefresh = useCallback(() => {
    void jobsQuery.refetch();
  }, [jobsQuery.refetch]);

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl
            refreshing={jobsQuery.isRefetching}
            onRefresh={handleRefresh}
            tintColor={colors.primary}
          />
        }
      >
        <View style={styles.greetingRow}>
          <View>
            <Text style={styles.greeting}>Hello 👋</Text>
            <Text style={styles.userName}>{user?.first_name ?? 'there'}!</Text>
          </View>
          <TouchableOpacity
            accessibilityRole="button"
            onPress={() => navigation.navigate('Profile')}
            style={styles.avatar}
          >
            <Text style={styles.avatarText}>
              {(user?.first_name?.charAt(0) ?? '') + (user?.last_name?.charAt(0) ?? '')}
            </Text>
          </TouchableOpacity>
        </View>

        <View style={styles.statsCard}>
          <Ionicons name="briefcase" size={22} color={colors.primaryDark} />
          <View style={styles.statsText}>
            <Text style={styles.statsNumber}>
              {jobsQuery.data ? String(jobsQuery.data.total) : '—'}
            </Text>
            <Text style={styles.statsLabel}>open jobs on the platform</Text>
          </View>
        </View>

        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Latest Jobs</Text>
          <TouchableOpacity
            accessibilityRole="button"
            onPress={() => navigation.navigate('Jobs')}
          >
            <Text style={styles.seeAll}>See all</Text>
          </TouchableOpacity>
        </View>

        {jobsQuery.isLoading ? (
          <Loading message="Fetching latest jobs…" fullscreen={false} />
        ) : jobsQuery.isError ? (
          <View style={styles.placeholder}>
            <Ionicons name="cloud-offline-outline" size={28} color={colors.textMuted} />
            <Text style={styles.placeholderTitle}>Could not load jobs</Text>
            <TouchableOpacity accessibilityRole="button" onPress={() => jobsQuery.refetch()}>
              <Text style={styles.seeAll}>Tap to retry</Text>
            </TouchableOpacity>
          </View>
        ) : recentJobs.length === 0 ? (
          <View style={styles.placeholder}>
            <Ionicons name="search-outline" size={28} color={colors.textMuted} />
            <Text style={styles.placeholderTitle}>No jobs posted yet</Text>
            <Text style={styles.placeholderSubtitle}>Check back soon.</Text>
          </View>
        ) : (
          <View style={styles.jobList}>
            {recentJobs.map((job) => (
              <JobCard key={job.id} job={job} />
            ))}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    padding: spacing.lg,
    paddingBottom: spacing.xl,
    gap: spacing.lg - 4,
  },
  greetingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  greeting: {
    fontSize: fontSize.sm + 1,
    fontFamily: fontFamily.regular,
    color: colors.textMuted,
  },
  userName: {
    fontSize: fontSize.xl,
    fontFamily: fontFamily.bold,
    color: colors.text,
  },
  avatar: {
    width: 44,
    height: 44,
    borderRadius: radius.pill,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    fontSize: fontSize.md,
    fontFamily: fontFamily.bold,
    color: colors.white,
  },
  statsCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    backgroundColor: colors.primaryLight,
    borderRadius: radius.lg,
    padding: spacing.md,
  },
  statsText: {
    flex: 1,
  },
  statsNumber: {
    fontSize: fontSize.xl,
    fontFamily: fontFamily.bold,
    color: colors.primaryDark,
  },
  statsLabel: {
    fontSize: fontSize.sm + 1,
    color: colors.textMuted,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  sectionTitle: {
    fontSize: fontSize.lg,
    fontFamily: fontFamily.bold,
    color: colors.text,
  },
  seeAll: {
    fontSize: fontSize.sm + 1,
    fontFamily: fontFamily.medium,
    color: colors.primary,
  },
  jobList: {
    gap: spacing.md - 2,
  },
  placeholder: {
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    paddingVertical: spacing.xl,
    paddingHorizontal: spacing.lg,
  },
  placeholderTitle: {
    fontSize: fontSize.md,
    fontFamily: fontFamily.medium,
    color: colors.text,
  },
  placeholderSubtitle: {
    fontSize: fontSize.sm,
    color: colors.textMuted,
  },
});
