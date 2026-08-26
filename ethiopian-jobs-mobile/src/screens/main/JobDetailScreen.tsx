import { Ionicons } from '@expo/vector-icons';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import React, { useCallback, useMemo, useState } from 'react';
import {
  Image,
  ScrollView,
  Share,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button, Loading } from '../../components/common';
import { ApplyModal } from '../../components/jobs/ApplyModal';
import { JobCard } from '../../components/jobs/JobCard';
import {
  colors,
  fontFamily,
  fontSize,
  radius,
  spacing,
} from '../../constants/theme';
import {
  useAppliedJobIds,
} from '../../hooks/useApplications';
import { useJob } from '../../hooks/useJobs';
import {
  useSavedJobIds,
  useToggleSavedJob,
} from '../../hooks/useSavedJobs';
import { RootStackParamList } from '../../navigation/types';
import {
  formatEmploymentType,
  formatDate,
  formatSalaryRange,
} from '../../utils/format';

type JobDetailScreenProps = NativeStackScreenProps<RootStackParamList, 'JobDetail'>;

export function JobDetailScreen({ route, navigation }: JobDetailScreenProps) {
  const { jobId } = route.params;
  const jobQuery = useJob(jobId);
  const savedJobIds = useSavedJobIds();
  const toggleSavedJob = useToggleSavedJob();
  const appliedJobIds = useAppliedJobIds();

  const [isApplyModalVisible, setIsApplyModalVisible] = useState(false);

  const job = jobQuery.data;

  const isSaved = savedJobIds.has(jobId);
  const hasApplied = appliedJobIds.has(jobId);

  const handleToggleSave = useCallback(() => {
    if (!job) return;
    toggleSavedJob.mutate({ jobId: job.id, save: !isSaved, job });
  }, [job, isSaved, toggleSavedJob]);

  const handleShare = useCallback(async () => {
    if (!job) return;
    try {
      await Share.share({
        message: `${job.title} at ${job.company.name}\n` +
          `${job.is_remote ? 'Remote' : job.location ?? 'Ethiopia'}\n` +
          `${formatSalaryRange(job.salary_min, job.salary_max, job.currency)}\n` +
          `Found on Ethiopian Jobs`,
      });
    } catch {
      // User dismissed the share sheet — nothing to do.
    }
  }, [job]);

  const relatedJobs = useMemo(() => job?.related_jobs.slice(0, 5) ?? [], [job]);

  if (jobQuery.isLoading) {
    return (
      <SafeAreaView style={styles.safe}>
        <DetailHeader title="" onBack={() => navigation.goBack()} />
        <Loading message="Loading job…" fullscreen={false} />
      </SafeAreaView>
    );
  }

  if (jobQuery.isError || !job) {
    return (
      <SafeAreaView style={styles.safe}>
        <DetailHeader title="Job Details" onBack={() => navigation.goBack()} />
        <View style={styles.errorState}>
          <Ionicons name="alert-circle-outline" size={32} color={colors.textMuted} />
          <Text style={styles.errorTitle}>Could not load this job</Text>
          <TouchableOpacity
            accessibilityRole="button"
            style={styles.retryButton}
            onPress={() => void jobQuery.refetch()}
          >
            <Text style={styles.retryText}>Try Again</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.headerCard}>
          <View style={styles.headerTopRow}>
            <View style={styles.logoPlaceholder}>
              {job.company.logo_url ? (
                <Image
                  source={{ uri: job.company.logo_url }}
                  style={styles.logoImage}
                  resizeMode="cover"
                />
              ) : (
                <Text style={styles.logoText}>
                  {job.company.name.charAt(0).toUpperCase()}
                </Text>
              )}
            </View>
            <View style={styles.titleWrap}>
              <Text style={styles.jobTitle}>{job.title}</Text>
              <Text style={styles.companyName}>
                {job.company.name}
                {job.company.is_verified ? ' ✓' : ''}
              </Text>
            </View>
          </View>

          <View style={styles.metaGrid}>
            <MetaItem icon="location-outline" label="Location">
              {job.is_remote ? 'Remote' : job.location ?? 'Ethiopia'}
            </MetaItem>
            <MetaItem icon="time-outline" label="Employment Type">
              {formatEmploymentType(job.employment_type)}
            </MetaItem>
            <MetaItem icon="trending-up-outline" label="Experience">
              {String(job.experience_level)}
            </MetaItem>
            <MetaItem icon="cash-outline" label="Salary">
              {formatSalaryRange(job.salary_min, job.salary_max, job.currency)}
            </MetaItem>
          </View>

          <View style={styles.tagRow}>
            {job.posted_date ? (
              <TagChip label={`Posted ${formatDate(job.posted_date)}`} />
            ) : null}
            {job.application_deadline ? (
              <TagChip label={`Deadline ${formatDate(job.application_deadline)}`} />
            ) : null}
            {job.category ? <TagChip label={job.category} /> : null}
          </View>
        </View>

        <Section title="Job Description">
          <Text style={styles.bodyText}>{job.description}</Text>
        </Section>

        {job.responsibilities.length > 0 ? (
          <Section title="Responsibilities">
            {job.responsibilities.map((item, index) => (
              <BulletPoint key={index} text={item} />
            ))}
          </Section>
        ) : null}

        {job.requirements.length > 0 ? (
          <Section title="Requirements">
            {job.requirements.map((item, index) => (
              <BulletPoint key={index} text={item} />
            ))}
          </Section>
        ) : null}

        <Section title="About the Company">
          <View style={styles.companyCard}>
            <Text style={styles.companyNameLarge}>{job.company.name}</Text>
            {job.company.city ? (
              <MetaItem icon="business-outline" label="City">
                {job.company.city}
              </MetaItem>
            ) : null}
            {job.company.is_verified ? (
              <View style={styles.verifiedBadge}>
                <Ionicons name="checkmark-circle" size={14} color={colors.primaryDark} />
                <Text style={styles.verifiedText}>Verified employer</Text>
              </View>
            ) : null}
          </View>
        </Section>

        {relatedJobs.length > 0 ? (
          <Section title="Related Jobs">
            {relatedJobs.map((related) => (
              <JobCard
                key={related.id}
                job={related}
                isSaved={savedJobIds.has(related.id)}
                onPress={() => navigation.push('JobDetail', { jobId: related.id })}
                onToggleSave={() =>
                  toggleSavedJob.mutate({
                    jobId: related.id,
                    save: !savedJobIds.has(related.id),
                    job: related,
                  })
                }
              />
            ))}
          </Section>
        ) : null}
      </ScrollView>

      <View style={styles.actionBar}>
        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel={isSaved ? 'Remove from saved jobs' : 'Save job'}
          style={[styles.iconAction, isSaved && styles.iconActionActive]}
          onPress={handleToggleSave}
        >
          <Ionicons
            name={isSaved ? 'bookmark' : 'bookmark-outline'}
            size={22}
            color={isSaved ? colors.primaryDark : colors.textMuted}
          />
          <Text style={[styles.iconActionText, isSaved && styles.iconActionTextActive]}>
            {isSaved ? 'Saved' : 'Save'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel="Share job"
          style={styles.iconAction}
          onPress={() => void handleShare()}
        >
          <Ionicons name="share-social-outline" size={22} color={colors.textMuted} />
          <Text style={styles.iconActionText}>Share</Text>
        </TouchableOpacity>

        <View style={styles.applyButtonWrap}>
          <Button
            title={hasApplied ? 'Application Sent ✓' : 'Apply Now'}
            onPress={() => setIsApplyModalVisible(true)}
            disabled={hasApplied || job.status !== 'published'}
            loading={false}
          />
        </View>
      </View>

      <ApplyModal
        visible={isApplyModalVisible}
        jobId={job.id}
        job={{
          title: job.title,
          company_name: job.company.name,
          employment_type: String(job.employment_type),
          salary_min: job.salary_min,
          salary_max: job.salary_max,
          currency: job.currency,
        }}
        onClose={() => setIsApplyModalVisible(false)}
        onApplied={() => undefined}
      />
    </SafeAreaView>
  );
}

function DetailHeader({ title, onBack }: { title: string; onBack: () => void }) {
  return (
    <View style={styles.detailHeader}>
      <TouchableOpacity
        accessibilityRole="button"
        accessibilityLabel="Go back"
        onPress={onBack}
        hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
      >
        <Ionicons name="arrow-back" size={24} color={colors.text} />
      </TouchableOpacity>
      {title ? <Text style={styles.detailHeaderTitle}>{title}</Text> : null}
    </View>
  );
}

function MetaItem({
  icon,
  label,
  children,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <View style={styles.metaItem}>
      <Ionicons name={icon} size={16} color={colors.primaryDark} />
      <View style={styles.metaTextWrap}>
        <Text style={styles.metaLabel}>{label}</Text>
        <Text style={styles.metaValue}>{children}</Text>
      </View>
    </View>
  );
}

function TagChip({ label }: { label: string }) {
  return (
    <View style={styles.tagChip}>
      <Text style={styles.tagChipText}>{label}</Text>
    </View>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      {children}
    </View>
  );
}

function BulletPoint({ text }: { text: string }) {
  return (
    <View style={styles.bulletRow}>
      <View style={styles.bulletDot} />
      <Text style={styles.bulletText}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.background,
  },
  detailHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md - 2,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm + 2,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  detailHeaderTitle: {
    fontSize: fontSize.lg,
    fontFamily: fontFamily.bold,
    color: colors.text,
  },
  content: {
    padding: spacing.lg,
    paddingBottom: spacing.xl + 40,
    gap: spacing.md,
  },
  headerCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    gap: spacing.md,
  },
  headerTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md - 2,
  },
  logoPlaceholder: {
    width: 56,
    height: 56,
    borderRadius: radius.md,
    backgroundColor: colors.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  logoImage: {
    width: '100%',
    height: '100%',
  },
  logoText: {
    fontSize: fontSize.xl - 4,
    fontFamily: fontFamily.bold,
    color: colors.primaryDark,
  },
  titleWrap: {
    flex: 1,
  },
  jobTitle: {
    fontSize: fontSize.lg + 1,
    fontFamily: fontFamily.bold,
    color: colors.text,
  },
  companyName: {
    marginTop: 2,
    fontSize: fontSize.sm + 1,
    fontFamily: fontFamily.medium,
    color: colors.primary,
  },
  metaGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.md - 2,
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: spacing.sm,
    minWidth: '45%',
    flexGrow: 1,
  },
  metaTextWrap: {
    flex: 1,
  },
  metaLabel: {
    fontSize: fontSize.sm - 2,
    color: colors.textMuted,
    textTransform: 'uppercase',
  },
  metaValue: {
    marginTop: 1,
    fontSize: fontSize.sm + 1,
    fontFamily: fontFamily.medium,
    color: colors.text,
  },
  tagRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  tagChip: {
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.pill,
    paddingVertical: 3,
    paddingHorizontal: spacing.sm + 2,
  },
  tagChipText: {
    fontSize: fontSize.sm - 2,
    color: colors.textMuted,
  },
  section: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    gap: spacing.sm + 2,
  },
  sectionTitle: {
    fontSize: fontSize.md,
    fontFamily: fontFamily.bold,
    color: colors.text,
  },
  bodyText: {
    fontSize: fontSize.sm + 1,
    lineHeight: 22,
    fontFamily: fontFamily.regular,
    color: colors.text,
  },
  bulletRow: {
    flexDirection: 'row',
    gap: spacing.sm + 2,
    paddingRight: spacing.sm,
  },
  bulletDot: {
    width: 6,
    height: 6,
    borderRadius: radius.pill,
    backgroundColor: colors.primary,
    marginTop: 8,
  },
  bulletText: {
    flex: 1,
    fontSize: fontSize.sm + 1,
    lineHeight: 21,
    fontFamily: fontFamily.regular,
    color: colors.text,
  },
  companyCard: {
    gap: spacing.sm + 2,
  },
  companyNameLarge: {
    fontSize: fontSize.md,
    fontFamily: fontFamily.bold,
    color: colors.text,
  },
  verifiedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    alignSelf: 'flex-start',
    backgroundColor: colors.primaryLight,
    borderRadius: radius.pill,
    paddingHorizontal: spacing.sm + 2,
    paddingVertical: 3,
  },
  verifiedText: {
    fontSize: fontSize.sm - 2,
    fontFamily: fontFamily.medium,
    color: colors.primaryDark,
  },
  actionBar: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm + 2,
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.md - 2,
    paddingBottom: spacing.md,
    backgroundColor: colors.surface,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  iconAction: {
    alignItems: 'center',
    justifyContent: 'center',
    gap: 2,
    width: 58,
    height: 52,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.background,
  },
  iconActionActive: {
    backgroundColor: colors.primaryLight,
    borderColor: colors.primary,
  },
  iconActionText: {
    fontSize: fontSize.sm - 3,
    color: colors.textMuted,
  },
  iconActionTextActive: {
    color: colors.primaryDark,
    fontFamily: fontFamily.medium,
  },
  applyButtonWrap: {
    flex: 1,
  },
  errorState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    padding: spacing.xl,
  },
  errorTitle: {
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
});
