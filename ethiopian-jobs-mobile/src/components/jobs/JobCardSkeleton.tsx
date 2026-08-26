import React from 'react';
import { StyleSheet, View } from 'react-native';

import { radius, spacing } from '../../constants/theme';

export function JobCardSkeleton() {
  return (
    <View style={styles.card}>
      <View style={styles.headerRow}>
        <View style={[styles.skeleton, styles.logo]} />
        <View style={styles.headerText}>
          <View style={[styles.skeleton, styles.titleLine]} />
          <View style={[styles.skeleton, styles.companyLine]} />
        </View>
      </View>
      <View style={styles.metaRow}>
        <View style={[styles.skeleton, styles.metaChip]} />
        <View style={[styles.skeleton, styles.metaChip]} />
      </View>
      <View style={styles.footerRow}>
        <View style={[styles.skeleton, styles.salaryLine]} />
        <View style={[styles.skeleton, styles.levelChip]} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: radius.lg,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: '#E4E7EC',
    gap: spacing.sm + 2,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md - 2,
  },
  headerText: {
    flex: 1,
    gap: spacing.sm - 2,
  },
  skeleton: {
    backgroundColor: '#EDF0F2',
    borderRadius: radius.sm,
  },
  logo: {
    width: 44,
    height: 44,
    borderRadius: radius.sm,
  },
  titleLine: {
    height: 14,
    width: '80%',
  },
  companyLine: {
    height: 11,
    width: '50%',
  },
  metaRow: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  metaChip: {
    height: 12,
    width: 110,
  },
  footerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  salaryLine: {
    height: 12,
    width: 130,
  },
  levelChip: {
    height: 20,
    width: 56,
    borderRadius: radius.pill,
  },
});
