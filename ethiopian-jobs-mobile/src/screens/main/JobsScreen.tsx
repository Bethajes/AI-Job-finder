import { Ionicons } from '@expo/vector-icons';
import React, { useCallback, useMemo, useState } from 'react';
import {
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Loading } from '../../components/common';
import { JobCard } from '../../components/jobs';
import {
  colors,
  fontFamily,
  fontSize,
  radius,
  spacing,
} from '../../constants/theme';
import { useInfiniteJobs } from '../../hooks/useApi';
import { Job } from '../../types';

export function JobsScreen() {
  const [searchInput, setSearchInput] = useState('');
  const [activeSearch, setActiveSearch] = useState('');

  const jobsQuery = useInfiniteJobs(
    useMemo(() => (activeSearch ? { search: activeSearch } : {}), [activeSearch]),
  );

  const jobs = useMemo(
    () => jobsQuery.data?.pages.flatMap((page) => page.items) ?? [],
    [jobsQuery.data],
  );

  const handleRefresh = useCallback(() => {
    void jobsQuery.refetch();
  }, [jobsQuery.refetch]);

  const loadMore = useCallback(() => {
    if (jobsQuery.hasNextPage && !jobsQuery.isFetchingNextPage) {
      void jobsQuery.fetchNextPage();
    }
  }, [
    jobsQuery.hasNextPage,
    jobsQuery.isFetchingNextPage,
    jobsQuery.fetchNextPage,
  ]);

  const submitSearch = useCallback(() => {
    setActiveSearch(searchInput.trim());
  }, [searchInput]);

  const clearSearch = useCallback(() => {
    setSearchInput('');
    setActiveSearch('');
  }, []);

  const renderItem = useCallback(({ item }: { item: Job }) => (
    <JobCard job={item} />
  ), []);

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.title}>Find Jobs</Text>
        <View style={styles.searchRow}>
          <Ionicons
            name="search"
            size={18}
            color={colors.textMuted}
            style={styles.searchIcon}
          />
          <TextInput
            style={styles.searchInput}
            placeholder="Job title or keyword"
            placeholderTextColor={colors.textMuted}
            value={searchInput}
            onChangeText={setSearchInput}
            onSubmitEditing={submitSearch}
            returnKeyType="search"
            autoCapitalize="none"
          />
          {searchInput.length > 0 ? (
            <TouchableOpacity
              accessibilityRole="button"
              accessibilityLabel="Clear search"
              onPress={clearSearch}
              hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
            >
              <Ionicons name="close-circle" size={18} color={colors.textMuted} />
            </TouchableOpacity>
          ) : null}
        </View>
      </View>

      {jobsQuery.isLoading ? (
        <Loading message="Searching jobs…" fullscreen={false} />
      ) : jobsQuery.isError ? (
        <View style={styles.stateCard}>
          <Ionicons name="cloud-offline-outline" size={32} color={colors.textMuted} />
          <Text style={styles.stateTitle}>Something went wrong</Text>
          <Text style={styles.stateSubtitle}>
            We couldn't reach the server. Check your connection.
          </Text>
          <TouchableOpacity
            accessibilityRole="button"
            style={styles.retryButton}
            onPress={() => void jobsQuery.refetch()}
          >
            <Text style={styles.retryText}>Try Again</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <FlatList
          data={jobs}
          keyExtractor={(item) => item.id}
          renderItem={renderItem}
          contentContainerStyle={styles.listContent}
          ItemSeparatorComponent={Separator}
          onEndReachedThreshold={0.4}
          onEndReached={loadMore}
          refreshControl={
            <RefreshControl
              refreshing={jobsQuery.isRefetching}
              onRefresh={handleRefresh}
              tintColor={colors.primary}
            />
          }
          ListEmptyComponent={
            <View style={styles.stateCard}>
              <Ionicons name="briefcase-outline" size={32} color={colors.textMuted} />
              <Text style={styles.stateTitle}>No jobs found</Text>
              <Text style={styles.stateSubtitle}>
                {activeSearch
                  ? `Nothing matches "${activeSearch}". Try a different keyword.`
                  : 'No jobs have been posted yet. Check back soon.'}
              </Text>
            </View>
          }
          ListFooterComponent={
            jobsQuery.isFetchingNextPage ? (
              <View style={styles.footerLoading}>
                <Loading message="Loading more…" fullscreen={false} />
              </View>
            ) : null
          }
        />
      )}
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
  searchRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: colors.background,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: spacing.md,
    marginBottom: spacing.sm,
  },
  searchIcon: {
    marginRight: -spacing.xs,
  },
  searchInput: {
    flex: 1,
    paddingVertical: spacing.sm + 3,
    fontSize: fontSize.md,
    fontFamily: fontFamily.regular,
    color: colors.text,
  },
  listContent: {
    padding: spacing.lg,
    paddingBottom: spacing.xl,
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
