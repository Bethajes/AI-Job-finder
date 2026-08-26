import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { fontFamily, fontSize, radius, spacing } from '../../constants/theme';
import { ApplicationStatus } from '../../types';

const statusColors: Record<ApplicationStatus | string, string> = {
  applied: '#FFA500',
  viewed: '#1E90FF',
  shortlisted: '#9B59B6',
  interviewed: '#3498DB',
  offered: '#2ECC71',
  hired: '#27AE60',
  rejected: '#E74C3C',
  withdrawn: '#667085',
};

interface ApplicationStatusBadgeProps {
  status: string;
}

export const ApplicationStatusBadge = React.memo(
  function ApplicationStatusBadge({ status }: ApplicationStatusBadgeProps) {
    const background = statusColors[status] ?? '#667085';

    return (
      <View style={[styles.badge, { backgroundColor: background }]}>
        <Text style={styles.text}>{status}</Text>
      </View>
    );
  },
);

const styles = StyleSheet.create({
  badge: {
    borderRadius: radius.pill,
    paddingVertical: 3,
    paddingHorizontal: spacing.sm + 4,
  },
  text: {
    fontSize: fontSize.sm - 2,
    fontFamily: fontFamily.medium,
    color: '#FFFFFF',
    textTransform: 'capitalize',
  },
});
