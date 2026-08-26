import { Ionicons } from '@expo/vector-icons';
import React from 'react';
import { Pressable, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import {
  colors,
  fontFamily,
  fontSize,
  radius,
  spacing,
} from '../../constants/theme';
import { JobSearchItem } from '../../types';
import {
  formatDate,
  formatEmploymentType,
  formatSalaryRange,
} from '../../utils/format';

interface JobCardProps {
  job: JobSearchItem;
  onPress?: () => void;
  isSaved?: boolean;
  onToggleSave?: () => void;
}

export const JobCard = React.memo(function JobCard({
  job,
  onPress,
  isSaved = false,
  onToggleSave,
}: JobCardProps) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={`View ${job.title} at ${job.company.name}`}
      onPress={onPress}
      style={({ pressed }) => [styles.card, pressed && styles.pressed]}
    >
      <View style={styles.headerRow}>
        <View style={styles.logoPlaceholder}>
          <Text style={styles.logoText}>
            {job.company.name.charAt(0).toUpperCase()}
          </Text>
        </View>
        <View style={styles.headerText}>
          <Text style={styles.title} numberOfLines={2}>
            {job.title}
          </Text>
          <Text style={styles.company} numberOfLines={1}>
            {job.company.name}
            {job.company.is_verified ? ' ✓' : ''}
          </Text>
        </View>
        {onToggleSave ? (
          <TouchableOpacity
            accessibilityRole="button"
            accessibilityLabel={isSaved ? 'Remove from saved jobs' : 'Save job'}
            accessibilityState={{ selected: isSaved }}
            onPress={onToggleSave}
            hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
            style={styles.saveButton}
          >
            <Ionicons
              name={isSaved ? 'bookmark' : 'bookmark-outline'}
              size={22}
              color={isSaved ? colors.primary : colors.textMuted}
            />
          </TouchableOpacity>
        ) : null}
      </View>
      <View style={styles.metaRow}>
        <View style={styles.metaItem}>
          <Ionicons
            name="location-outline"
            size={14}
            color={colors.textMuted}
          />
          <Text style={styles.metaText} numberOfLines={1}>
            {job.is_remote ? 'Remote' : (job.location ?? job.company.city ?? 'Ethiopia')}
          </Text>
        </View>
        <View style={styles.metaItem}>
          <Ionicons name="time-outline" size={14} color={colors.textMuted} />
          <Text style={styles.metaText}>
            {formatEmploymentType(job.employment_type)}
          </Text>
        </View>
      </View>
      <View style={styles.footerRow}>
        <Text style={styles.salary}>
          {formatSalaryRange(job.salary_min, job.salary_max, job.currency)}
        </Text>
        <View style={[styles.levelBadge, levelBadgeStyles[job.experience_level] ?? null]}>
          <Text style={styles.levelText}>{job.experience_level}</Text>
        </View>
      </View>
      {job.posted_date ? (
        <Text style={styles.postedDate}>Posted {formatDate(job.posted_date)}</Text>
      ) : null}
    </Pressable>
  );
});

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
    gap: spacing.sm + 2,
  },
  pressed: {
    opacity: 0.9,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md - 2,
  },
  logoPlaceholder: {
    width: 44,
    height: 44,
    borderRadius: radius.sm,
    backgroundColor: colors.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoText: {
    fontSize: fontSize.lg,
    fontFamily: fontFamily.bold,
    color: colors.primaryDark,
  },
  headerText: {
    flex: 1,
  },
  title: {
    fontSize: fontSize.md,
    fontFamily: fontFamily.bold,
    color: colors.text,
  },
  company: {
    marginTop: 2,
    fontSize: fontSize.sm,
    fontFamily: fontFamily.regular,
    color: colors.textMuted,
  },
  saveButton: {
    marginLeft: spacing.xs,
  },
  metaRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.md,
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  metaText: {
    fontSize: fontSize.sm,
    color: colors.textMuted,
    maxWidth: 150,
  },
  footerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  salary: {
    fontSize: fontSize.sm,
    fontFamily: fontFamily.bold,
    color: colors.primaryDark,
  },
  levelBadge: {
    backgroundColor: colors.background,
    borderRadius: radius.pill,
    paddingVertical: 3,
    paddingHorizontal: spacing.sm + 4,
  },
  entryBadge: {
    backgroundColor: '#E8F5E9',
  },
  midBadge: {
    backgroundColor: '#FFF8E1',
  },
  seniorBadge: {
    backgroundColor: '#E3F2FD',
  },
  leadBadge: {
    backgroundColor: '#F3E5F5',
  },
  levelText: {
    fontSize: fontSize.sm - 1,
    fontFamily: fontFamily.medium,
    color: colors.textMuted,
    textTransform: 'capitalize',
  },
  postedDate: {
    fontSize: fontSize.sm - 2,
    color: colors.textMuted,
  },
});

const levelBadgeStyles: Record<string, object> = {
  entry: styles.entryBadge,
  mid: styles.midBadge,
  senior: styles.seniorBadge,
  lead: styles.leadBadge,
};
