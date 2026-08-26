import { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button } from '../../components/common';
import {
  colors,
  fontFamily,
  fontSize,
  radius,
  spacing,
} from '../../constants/theme';
import { MainTabParamList } from '../../navigation/types';

type ApplicationsScreenNavigationProp = BottomTabNavigationProp<
  MainTabParamList,
  'Applications'
>;

interface ApplicationsScreenProps {
  navigation: ApplicationsScreenNavigationProp;
}

export function ApplicationsScreen({ navigation }: ApplicationsScreenProps) {
  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.title}>My Applications</Text>
      </View>
      <View style={styles.emptyState}>
        <View style={styles.iconCircle}>
          <Ionicons name="document-text-outline" size={34} color={colors.primary} />
        </View>
        <Text style={styles.emptyTitle}>No applications yet</Text>
        <Text style={styles.emptySubtitle}>
          Track every job you apply for in one place. Apply to your first job to
          get started.
        </Text>
        <Button
          title="Browse Jobs"
          onPress={() => navigation.navigate('Jobs')}
          style={styles.cta}
        />
        <Text style={styles.comingSoon}>
          Application tracking arrives in Week 10 of the MVP build.
        </Text>
      </View>
    </SafeAreaView>
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
  emptyState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.xl,
    gap: spacing.sm + 2,
  },
  iconCircle: {
    width: 76,
    height: 76,
    borderRadius: radius.pill,
    backgroundColor: colors.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.xs,
  },
  emptyTitle: {
    fontSize: fontSize.lg,
    fontFamily: fontFamily.bold,
    color: colors.text,
  },
  emptySubtitle: {
    fontSize: fontSize.sm + 1,
    fontFamily: fontFamily.regular,
    color: colors.textMuted,
    textAlign: 'center',
    lineHeight: 22,
  },
  cta: {
    marginTop: spacing.md,
  },
  comingSoon: {
    marginTop: spacing.sm,
    fontSize: fontSize.sm,
    color: colors.textMuted,
    fontStyle: 'italic',
  },
});
