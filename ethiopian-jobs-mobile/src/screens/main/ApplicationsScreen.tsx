import { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import React, { useMemo, useState } from 'react';
import {
  FlatList,
  Modal,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  ApplicationStatusBadge,
} from '../../components/jobs/ApplicationStatusBadge';
import {
  colors,
  fontFamily,
  fontSize,
  radius,
  spacing,
} from '../../constants/theme';
import { useMyApplications } from '../../hooks/useApplications';
import { MainTabParamList } from '../../navigation/types';
import {
  Application,
  ApplicationStatus,
} from '../../types';
import { formatDate } from '../../utils/format';

type ApplicationsScreenNavigationProp = BottomTabNavigationProp<
  MainTabParamList,
  'Applications'
>;

interface ApplicationsScreenProps {
  navigation: ApplicationsScreenNavigationProp;
}

const STATUS_TABS: (ApplicationStatus | 'all')[] = [
  'all',
  'applied',
  'viewed',
  'shortlisted',
  'interviewed',
  'offered',
  'hired',
  'rejected',
];

export function ApplicationsScreen({ navigation }: ApplicationsScreenProps) {
  const applicationsQuery = useMyApplications();
  const [activeTab, setActiveTab] = useState<ApplicationStatus | 'all'>('all');
  const [selectedApplication, setSelectedApplication] = useState<Application | null>(null);

  const applications = useMemo(
    () => applicationsQuery.data?.items ?? [],
    [applicationsQuery.data],
  );

  const filtered = useMemo(
    () =>
      activeTab === 'all'
        ? applications
        : applications.filter((application) => application.status === activeTab),
    [applications, activeTab],
  );

  const statusCounts = useMemo(() => {
    const counts: Partial<Record<ApplicationStatus | 'all', number>> = { all: applications.length };
    for (const application of applications) {
      const key = application.status as ApplicationStatus;
      counts[key] = (counts[key] ?? 0) + 1;
    }
    return counts;
  }, [applications]);

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.title}>My Applications</Text>
        {applications.length > 0 ? (
          <Text style={styles.subtitle}>
            {applications.length} application{applications.length > 1 ? 's' : ''} submitted
          </Text>
        ) : null}
        <View>
          <FlatList
            horizontal
            data={STATUS_TABS}
            keyExtractor={(item) => item}
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.tabsContent}
            renderItem={({ item }) => {
              const count = statusCounts[item] ?? 0;
              if (item !== 'all' && count === 0) return null;
              return (
                <TouchableOpacity
                  accessibilityRole="tab"
                  accessibilityState={{ selected: activeTab === item }}
                  style={[styles.tab, activeTab === item && styles.tabActive]}
                  onPress={() => setActiveTab(item)}
                >
                  <Text style={[styles.tabText, activeTab === item && styles.tabTextActive]}>
                    {item === 'all' ? 'All' : item}
                    {count > 0 ? ` (${count})` : ''}
                  </Text>
                </TouchableOpacity>
              );
            }}
          />
        </View>
      </View>

      {applicationsQuery.isLoading ? (
        <View style={styles.loadingWrap}>
          <Ionicons name="hourglass-outline" size={28} color={colors.textMuted} />
          <Text style={styles.loadingText}>Loading your applications…</Text>
        </View>
      ) : applicationsQuery.isError ? (
        <View style={styles.stateCard}>
          <Ionicons name="cloud-offline-outline" size={32} color={colors.textMuted} />
          <Text style={styles.stateTitle}>Something went wrong</Text>
          <TouchableOpacity
            accessibilityRole="button"
            style={styles.retryButton}
            onPress={() => void applicationsQuery.refetch()}
          >
            <Text style={styles.retryText}>Try Again</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <FlatList
          data={filtered}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listContent}
          ItemSeparatorComponent={Separator}
          refreshControl={
            <RefreshControl
              refreshing={applicationsQuery.isRefetching}
              onRefresh={() => void applicationsQuery.refetch()}
              tintColor={colors.primary}
            />
          }
          renderItem={({ item }) => (
            <ApplicationRow
              application={item}
              onPress={() => setSelectedApplication(item)}
            />
          )}
          ListEmptyComponent={
            <EmptyState
              filtered={activeTab !== 'all'}
              onBrowse={() => navigation.navigate('Jobs')}
            />
          }
        />
      )}

      <Modal
        visible={selectedApplication !== null}
        animationType="slide"
        transparent
        onRequestClose={() => setSelectedApplication(null)}
      >
        {selectedApplication ? (
          <Pressable style={styles.detailOverlay} onPress={() => setSelectedApplication(null)}>
            <Pressable style={styles.detailSheet}>
              <View style={styles.sheetHandle} />
              <ScrollView contentContainerStyle={styles.detailContent}>
                <View style={styles.detailHeaderRow}>
                  <View style={styles.detailTitleWrap}>
                    <Text style={styles.detailJobTitle}>{selectedApplication.job.title}</Text>
                    <Text style={styles.detailCompany}>{selectedApplication.job.company_name}</Text>
                  </View>
                  <ApplicationStatusBadge status={selectedApplication.status} />
                </View>

                <Text style={styles.timelineTitle}>Timeline</Text>
                <Timeline application={selectedApplication} />

                {selectedApplication.cover_letter ? (
                  <View style={styles.detailSection}>
                    <Text style={styles.sectionLabel}>Cover Letter</Text>
                    <Text style={styles.bodyText}>{selectedApplication.cover_letter}</Text>
                  </View>
                ) : null}

                <View style={styles.detailSection}>
                  <Text style={styles.sectionLabel}>Details</Text>
                  <DetailLine label="Applied on" value={formatDate(selectedApplication.applied_at)} />
                  <DetailLine label="Source" value={selectedApplication.source} />
                  <DetailLine label="Last update" value={formatDate(selectedApplication.updated_at)} />
                </View>

                <TouchableOpacity
                  accessibilityRole="button"
                  style={styles.viewJobButton}
                  onPress={() => {
                    const jobId = selectedApplication.job_id;
                    setSelectedApplication(null);
                    // Job detail lives on the root stack.
                    navigation.getParent()?.navigate('JobDetail', { jobId });
                  }}
                >
                  <Text style={styles.viewJobButtonText}>View Job</Text>
                </TouchableOpacity>
              </ScrollView>
            </Pressable>
          </Pressable>
        ) : null}
      </Modal>
    </SafeAreaView>
  );
}

function Separator() {
  return <View style={styles.separator} />;
}

function ApplicationRow({
  application,
  onPress,
}: {
  application: Application;
  onPress: () => void;
}) {
  return (
    <TouchableOpacity
      accessibilityRole="button"
      accessibilityLabel={`Application for ${application.job.title}`}
      style={styles.rowCard}
      onPress={onPress}
      activeOpacity={0.85}
    >
      <View style={styles.rowLogo}>
        <Text style={styles.rowLogoText}>
          {application.job.company_name.charAt(0).toUpperCase()}
        </Text>
      </View>
      <View style={styles.rowBody}>
        <Text style={styles.rowTitle} numberOfLines={1}>
          {application.job.title}
        </Text>
        <Text style={styles.rowCompany} numberOfLines={1}>
          {application.job.company_name}
        </Text>
        <Text style={styles.rowDate}>
          Applied {formatDate(application.applied_at)}
        </Text>
      </View>
      <ApplicationStatusBadge status={application.status} />
    </TouchableOpacity>
  );
}

function EmptyState({
  filtered,
  onBrowse,
}: {
  filtered: boolean;
  onBrowse: () => void;
}) {
  return (
    <View style={styles.stateCard}>
      <View style={styles.iconCircle}>
        <Ionicons name="document-text-outline" size={34} color={colors.primary} />
      </View>
      <Text style={styles.emptyTitle}>
        {filtered ? 'No applications with this status' : 'No applications yet'}
      </Text>
      <Text style={styles.emptySubtitle}>
        {filtered
          ? 'Try a different status filter to see more of your applications.'
          : 'Track every job you apply for in one place. Apply to your first job to get started.'}
      </Text>
      {!filtered ? (
        <TouchableOpacity
          accessibilityRole="button"
          style={styles.browseButton}
          onPress={onBrowse}
        >
          <Text style={styles.browseButtonText}>Browse Jobs</Text>
        </TouchableOpacity>
      ) : null}
    </View>
  );
}

function Timeline({ application }: { application: Application }) {
  const steps = buildTimeline(application);
  return (
    <View style={styles.timeline}>
      {steps.map((step, index) => {
        const isLast = index === steps.length - 1;
        return (
          <View key={step.label} style={styles.timelineRow}>
            <View style={styles.timelineMarkerColumn}>
              <View
                style={[
                  styles.timelineDot,
                  step.done && styles.timelineDotDone,
                ]}
              >
                {step.done ? (
                  <Ionicons name="checkmark" size={12} color="#FFFFFF" />
                ) : null}
              </View>
              {!isLast ? (
                <View
                  style={[
                    styles.timelineLine,
                    step.done && steps[index + 1]?.done && styles.timelineLineDone,
                  ]}
                />
              ) : null}
            </View>
            <View style={styles.timelineBody}>
              <Text style={[styles.timelineStep, step.done && styles.timelineStepDone]}>
                {step.label}
              </Text>
              <Text style={styles.timelineDate}>{step.date}</Text>
            </View>
          </View>
        );
      })}
    </View>
  );
}

interface TimelineStep {
  label: string;
  date: string;
  done: boolean;
}

function buildTimeline(application: Application): TimelineStep[] {
  const isDecision = ['offered', 'hired', 'rejected'].includes(application.status);

  const steps: TimelineStep[] = [
    {
      label: 'Application submitted',
      date: formatDate(application.applied_at),
      done: true,
    },
    {
      label: 'Viewed by employer',
      date: application.viewed_at ? formatDate(application.viewed_at) : 'Pending',
      done: Boolean(application.viewed_at) || application.status !== 'applied',
    },
    {
      label: 'Interview',
      date: application.interview_date ? formatDate(application.interview_date) : 'Not scheduled yet',
      done:
        Boolean(application.interview_date) ||
        ['interviewed', 'offered', 'hired'].includes(application.status),
    },
    {
      label:
        application.status === 'rejected'
          ? 'Application rejected'
          : isDecision
            ? `Offer ${application.status}`
            : 'Final decision',
      date: isDecision ? formatDate(application.updated_at) : 'In review',
      done: isDecision || application.status === 'offered',
    },
  ];
  return steps;
}

function DetailLine({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.detailLine}>
      <Text style={styles.detailLineLabel}>{label}</Text>
      <Text style={styles.detailLineValue}>{value}</Text>
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
    paddingBottom: 0,
    gap: spacing.sm - 2,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  title: {
    fontSize: fontSize.xl,
    fontFamily: fontFamily.bold,
    color: colors.text,
  },
  subtitle: {
    fontSize: fontSize.sm,
    color: colors.textMuted,
  },
  tabsContent: {
    gap: spacing.sm,
    paddingVertical: spacing.sm + 2,
    paddingRight: spacing.lg,
  },
  tab: {
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.background,
    paddingHorizontal: spacing.md - 2,
    paddingVertical: spacing.sm - 2,
  },
  tabActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  tabText: {
    fontSize: fontSize.sm - 1,
    fontFamily: fontFamily.medium,
    color: colors.textMuted,
    textTransform: 'capitalize',
  },
  tabTextActive: {
    color: colors.white,
  },
  listContent: {
    padding: spacing.lg,
    paddingBottom: spacing.xl,
  },
  separator: {
    height: spacing.md - 2,
  },
  rowCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md - 2,
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
  },
  rowLogo: {
    width: 44,
    height: 44,
    borderRadius: radius.sm,
    backgroundColor: colors.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  rowLogoText: {
    fontSize: fontSize.lg,
    fontFamily: fontFamily.bold,
    color: colors.primaryDark,
  },
  rowBody: {
    flex: 1,
  },
  rowTitle: {
    fontSize: fontSize.md,
    fontFamily: fontFamily.bold,
    color: colors.text,
  },
  rowCompany: {
    marginTop: 1,
    fontSize: fontSize.sm,
    color: colors.textMuted,
  },
  rowDate: {
    marginTop: 3,
    fontSize: fontSize.sm - 2,
    color: colors.textMuted,
  },
  loadingWrap: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm + 2,
  },
  loadingText: {
    fontSize: fontSize.sm + 1,
    color: colors.textMuted,
  },
  stateCard: {
    marginTop: spacing.xl,
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
  iconCircle: {
    width: 76,
    height: 76,
    borderRadius: radius.pill,
    backgroundColor: colors.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyTitle: {
    fontSize: fontSize.lg,
    fontFamily: fontFamily.bold,
    color: colors.text,
    textAlign: 'center',
  },
  emptySubtitle: {
    fontSize: fontSize.sm + 1,
    fontFamily: fontFamily.regular,
    color: colors.textMuted,
    textAlign: 'center',
    lineHeight: 22,
  },
  browseButton: {
    marginTop: spacing.xs,
    backgroundColor: colors.primary,
    borderRadius: radius.md,
    paddingVertical: spacing.sm + 4,
    paddingHorizontal: spacing.xl,
  },
  browseButtonText: {
    fontSize: fontSize.sm + 1,
    fontFamily: fontFamily.bold,
    color: colors.white,
  },
  stateTitle: {
    fontSize: fontSize.md,
    fontFamily: fontFamily.bold,
    color: colors.text,
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
  detailOverlay: {
    flex: 1,
    justifyContent: 'flex-end',
    backgroundColor: 'rgba(16, 24, 40, 0.5)',
  },
  detailSheet: {
    backgroundColor: colors.surface,
    borderTopLeftRadius: radius.lg + 4,
    borderTopRightRadius: radius.lg + 4,
    maxHeight: '88%',
  },
  sheetHandle: {
    alignSelf: 'center',
    width: 44,
    height: 5,
    borderRadius: radius.pill,
    backgroundColor: colors.border,
    marginTop: spacing.sm + 2,
  },
  detailContent: {
    padding: spacing.lg,
    paddingBottom: spacing.xl,
    gap: spacing.md,
  },
  detailHeaderRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: spacing.sm + 2,
  },
  detailTitleWrap: {
    flex: 1,
  },
  detailJobTitle: {
    fontSize: fontSize.lg,
    fontFamily: fontFamily.bold,
    color: colors.text,
  },
  detailCompany: {
    marginTop: 2,
    fontSize: fontSize.sm + 1,
    color: colors.textMuted,
  },
  timelineTitle: {
    fontSize: fontSize.sm,
    fontFamily: fontFamily.medium,
    color: colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 0.4,
  },
  timeline: {
    gap: 0,
  },
  timelineRow: {
    flexDirection: 'row',
    gap: spacing.md - 2,
  },
  timelineMarkerColumn: {
    alignItems: 'center',
  },
  timelineDot: {
    width: 20,
    height: 20,
    borderRadius: radius.pill,
    borderWidth: 2,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  timelineDotDone: {
    borderColor: colors.primary,
    backgroundColor: colors.primary,
  },
  timelineLine: {
    width: 2,
    flex: 1,
    minHeight: 28,
    backgroundColor: colors.border,
  },
  timelineLineDone: {
    backgroundColor: colors.primary,
  },
  timelineBody: {
    flex: 1,
    paddingBottom: spacing.sm + 4,
  },
  timelineStep: {
    fontSize: fontSize.sm + 1,
    fontFamily: fontFamily.regular,
    color: colors.textMuted,
  },
  timelineStepDone: {
    fontFamily: fontFamily.medium,
    color: colors.text,
  },
  timelineDate: {
    marginTop: 1,
    fontSize: fontSize.sm - 1,
    color: colors.textMuted,
  },
  detailSection: {
    gap: spacing.sm,
  },
  sectionLabel: {
    fontSize: fontSize.sm,
    fontFamily: fontFamily.medium,
    color: colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 0.4,
  },
  bodyText: {
    fontSize: fontSize.sm + 1,
    lineHeight: 21,
    fontFamily: fontFamily.regular,
    color: colors.text,
  },
  detailLine: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: spacing.xs + 2,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  detailLineLabel: {
    fontSize: fontSize.sm + 1,
    color: colors.textMuted,
  },
  detailLineValue: {
    fontSize: fontSize.sm + 1,
    fontFamily: fontFamily.medium,
    color: colors.text,
  },
  viewJobButton: {
    alignItems: 'center',
    backgroundColor: colors.primaryLight,
    borderRadius: radius.md,
    paddingVertical: spacing.md - 2,
  },
  viewJobButtonText: {
    fontSize: fontSize.sm + 1,
    fontFamily: fontFamily.bold,
    color: colors.primaryDark,
  },
});
