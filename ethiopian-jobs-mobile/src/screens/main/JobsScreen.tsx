import { Ionicons } from '@expo/vector-icons';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import React, { useCallback, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  JobCard,
  JobCardSkeleton,
  JobFiltersModal,
  JobSearchBar,
} from '../../components/jobs';
import {
  colors,
  fontFamily,
  fontSize,
  radius,
  spacing,
} from '../../constants/theme';
import { useInfiniteJobs } from '../../hooks/useJobs';
import {
  useSavedJobIds,
  useToggleSavedJob,
} from '../../hooks/useSavedJobs';
import { RootStackParamList } from '../../navigation/types';
import { JobFilters, JobSearchItem } from '../../types';

type JobsScreenNavigationProp = NativeStackNavigationProp<
  RootStackParamList,
  'JobDetail'
>;

interface JobsScreenProps {
  navigation: JobsScreenNavigationProp;
}

export function JobsScreen({ navigation }: JobsScreenProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<JobFilters>({});
  const [isFilterModalVisible, setIsFilterModalVisible] = useState(false);

  const effectiveFilters = useMemo<JobFilters>(
    () => ({ ...filters, q: searchQuery || undefined }),
    [filters, searchQuery],
  );

  const jobsQuery = useInfiniteJobs(effectiveFilters);
  const savedJobIds = useSavedJobIds();
  const toggleSavedJob = useToggleSavedJob();
  const { hasNextPage, isFetchingNextPage, fetchNextPage, refetch, isError, isLoading, isRefetching } =
    jobsQuery;

  const jobs = useMemo(
    () => jobsQuery.data?.pages.flatMap((page) => page.items) ?? [],
    [jobsQuery.data],
  );

  const activeFilterCount = useMemo(
    () =>
      Object.values(filters).filter((value) => value !== undefined && value !== false)
        .length,
    [filters],
  );

  const openJobDetail = useCallback(
    (jobId: string) => {
      navigation.navigate('JobDetail', { jobId });
    },
    [navigation],
  );

  const handleToggleSave = useCallback(
    (job: JobSearchItem) => {
      toggleSavedJob.mutate({
        jobId: job.id,
        save: !savedJobIds.has(job.id),
        job,
      });
    },
    [toggleSavedJob, savedJobIds],
  );

  const loadMore = useCallback(() => {
    if (hasNextPage && !isFetchingNextPage) {
      void fetchNextPage();
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  const renderJob = useCallback(
    ({ item }: { item: JobSearchItem }) => (
      <JobCard
        job={item}
        onPress={() => openJobDetail(item.id)}
        isSaved={savedJobIds.has(item.id)}
        onToggleSave={() => handleToggleSave(item)}
      />
    ),
    [openJobDetail, savedJobIds, handleToggleSave],
  );

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.title}>Find Jobs</Text>
        <View style={styles.controlsRow}>
          <JobSearchBar onSearch={setSearchQuery} />
          <TouchableOpacity
            accessibilityRole="button"
            accessibilityLabel="Open filters"
            style={styles.filterButton}
            onPress={() => setIsFilterModalVisible(true)}
          >
            <Ionicons name="options-outline" size={20} color={colors.primaryDark} />
            {activeFilterCount > 0 ? (
              <View style={styles.filterBadge}>
                <Text style={styles.filterBadgeText}>{activeFilterCount}</Text>
              </View>
            ) : null}
          </TouchableOpacity>
        </View>
        {activeFilterCount > 0 ? (
          <TouchableOpacity
            accessibilityRole="button"
            onPress={() => setFilters({})}
            style={styles.clearFilters}
          >
            <Ionicons name="close-circle" size={14} color={colors.textMuted} />
            <Text style={styles.clearFiltersText}>
              {activeFilterCount} filter{activeFilterCount > 1 ? 's' : ''} active — clear
            </Text>
          </TouchableOpacity>
        ) : null}
      </View>

      {isLoading ? (
        <View style={styles.skeletonList}>
          {[1, 2, 3, 4].map((index) => (
            <JobCardSkeleton key={index} />
          ))}
        </View>
      ) : isError ? (
        <View style={styles.stateCard}>
          <Ionicons name="cloud-offline-outline" size={32} color={colors.textMuted} />
          <Text style={styles.stateTitle}>Something went wrong</Text>
          <Text style={styles.stateSubtitle}>
            We could not reach the server. Check your connection.
          </Text>
          <TouchableOpacity
            accessibilityRole="button"
            style={styles.retryButton}
            onPress={() => void refetch()}
          >
            <Text style={styles.retryText}>Try Again</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <FlatList
          data={jobs}
          keyExtractor={(item) => item.id}
          renderItem={renderJob}
          contentContainerStyle={styles.listContent}
          ItemSeparatorComponent={Separator}
          onEndReachedThreshold={0.5}
          onEndReached={loadMore}
          refreshControl={
            <RefreshControl
              refreshing={isRefetching && !isFetchingNextPage}
              onRefresh={() => void refetch()}
              tintColor={colors.primary}
            />
          }
          ListEmptyComponent={
            <View style={styles.stateCard}>
              <Ionicons name="briefcase-outline" size={32} color={colors.textMuted} />
              <Text style={styles.stateTitle}>No jobs found</Text>
              <Text style={styles.stateSubtitle}>
                {searchQuery || activeFilterCount > 0
                  ? 'Nothing matches your search or filters. Try adjusting them.'
                  : 'No jobs have been posted yet. Check back soon.'}
              </Text>
            </View>
          }
          ListFooterComponent={
            isFetchingNextPage ? (
              <View style={styles.footerLoading}>
                <ActivityIndicator size="large" color={colors.primary} />
              </View>
            ) : null
          }
        />
      )}

      <JobFiltersModal
        visible={isFilterModalVisible}
        filters={filters}
        onClose={() => setIsFilterModalVisible(false)}
        onApply={setFilters}
      />
    </SafeAreaView>
  );
}

function Separator() {
  return <View style={styles.separator} />;
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.md,
    paddingBottom: spacing.sm + 2,
    gap: spacing.md - 2,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  title: {
    fontSize: fontSize.xl,
    fontFamily: fontFamily.bold,
    color: colors.text,
  },
  controlsRow: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  filterButton: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.background,
  },
  filterBadge: {
    position: 'absolute',
    top: -5,
    right: -5,
    minWidth: 18,
    height: 18,
    borderRadius: radius.pill,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 4,
  },
  filterBadgeText: {
    fontSize: fontSize.sm - 3,
    fontFamily: fontFamily.bold,
    color: colors.white,
  },
  clearFilters: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    gap: 4,
  },
  clearFiltersText: {
    fontSize: fontSize.sm - 1,
    color: colors.textMuted,
  },
  listContent: {
    padding: spacing.lg,
    paddingBottom: spacing.xl,
  },
  skeletonList: {
    padding: spacing.lg,
    gap: spacing.md - 2,
  },
  separator: {
    height: spacing.md - 2,
  },
  footerLoading: {
    paddingTop: spacing.md,
  },
  stateCard: {
    marginTop: spacing.lg,
    marginHorizontal: spacing.lg,
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    paddingVertical: spacing.xl,
    paddingHorizontal: spacing.lg,
  },
  stateTitle: {
    fontSize: fontSize.md,
    fontFamily: fontFamily.bold,
    color: colors.text,
  },
  stateSubtitle: {
    fontSize: fontSize.sm,
    fontFamily: fontFamily.regular,
    color: colors.textMuted,
    textAlign: 'center',
  },
  retryButton: {
    marginTop: spacing.xs,
    backgroundColor: colors.primary,
    borderRadius: radius.md,
    paddingVertical: spacing.sm + 2,
    paddingHorizontal: spacing.lg,
  },
  retryText: {
    fontSize: fontSize.sm,
    fontFamily: fontFamily.bold,
    color: colors.white,
  },
});
