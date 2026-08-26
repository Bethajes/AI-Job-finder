import { Ionicons } from '@expo/vector-icons';
import React, { useState } from 'react';
import {
  Modal,
  Pressable,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import { Button } from '../common/Button';
import {
  colors,
  fontFamily,
  fontSize,
  radius,
  spacing,
} from '../../constants/theme';
import {
  EmploymentType,
  ExperienceLevel,
  JobFilters,
} from '../../types';

const EMPLOYMENT_TYPES: EmploymentType[] = [
  'full-time',
  'part-time',
  'contract',
  'internship',
];

const EXPERIENCE_LEVELS: ExperienceLevel[] = ['entry', 'mid', 'senior', 'lead'];

interface JobFiltersModalProps {
  visible: boolean;
  filters: JobFilters;
  onClose: () => void;
  onApply: (filters: JobFilters) => void;
}

export function JobFiltersModal(props: JobFiltersModalProps) {
  return (
    <Modal
      visible={props.visible}
      animationType="slide"
      transparent
      onRequestClose={props.onClose}
    >
      {props.visible ? <FilterForm {...props} /> : null}
    </Modal>
  );
}

function FilterForm({ filters, onClose, onApply }: JobFiltersModalProps) {
  const [draft, setDraft] = useState<JobFilters>(filters);
  const [salaryMinText, setSalaryMinText] = useState(
    filters.salary_min != null ? String(filters.salary_min) : '',
  );
  const [salaryMaxText, setSalaryMaxText] = useState(
    filters.salary_max != null ? String(filters.salary_max) : '',
  );

  const selectEmploymentType = (value: EmploymentType) => {
    setDraft((prev) => ({
      ...prev,
      employment_type: prev.employment_type === value ? undefined : value,
    }));
  };

  const selectExperienceLevel = (value: ExperienceLevel) => {
    setDraft((prev) => ({
      ...prev,
      experience_level: prev.experience_level === value ? undefined : value,
    }));
  };

  const reset = () => {
    setDraft({});
    setSalaryMinText('');
    setSalaryMaxText('');
  };

  const apply = () => {
    const salary_min = parseAmount(salaryMinText);
    const salary_max = parseAmount(salaryMaxText);
    onApply({
      ...draft,
      salary_min,
      salary_max:
        salary_max != null
          ? Math.max(salary_max, salary_min ?? 0)
          : undefined,
    });
    onClose();
  };

  return (
    <View style={styles.overlay}>
        <Pressable style={styles.backdrop} onPress={onClose} />
        <View style={styles.sheet}>
          <View style={styles.sheetHeader}>
            <Text style={styles.sheetTitle}>Filter Jobs</Text>
            <TouchableOpacity
              accessibilityRole="button"
              accessibilityLabel="Close filters"
              onPress={onClose}
              hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
            >
              <Ionicons name="close" size={22} color={colors.textMuted} />
            </TouchableOpacity>
          </View>

          <OptionGroup label="Employment Type">
            {EMPLOYMENT_TYPES.map((value) => (
              <RadioRow
                key={value}
                label={formatLabel(value)}
                selected={draft.employment_type === value}
                onPress={() => selectEmploymentType(value)}
              />
            ))}
          </OptionGroup>

          <OptionGroup label="Experience Level">
            {EXPERIENCE_LEVELS.map((value) => (
              <RadioRow
                key={value}
                label={formatLabel(value)}
                selected={draft.experience_level === value}
                onPress={() => selectExperienceLevel(value)}
              />
            ))}
          </OptionGroup>

          <OptionGroup label="Salary Range (ETB)">
            <View style={styles.salaryRow}>
              <TextInput
                style={styles.salaryInput}
                placeholder="Min"
                placeholderTextColor={colors.textMuted}
                keyboardType="number-pad"
                value={salaryMinText}
                onChangeText={setSalaryMinText}
              />
              <Text style={styles.salaryDash}>–</Text>
              <TextInput
                style={styles.salaryInput}
                placeholder="Max"
                placeholderTextColor={colors.textMuted}
                keyboardType="number-pad"
                value={salaryMaxText}
                onChangeText={setSalaryMaxText}
              />
            </View>
          </OptionGroup>

          <View style={styles.switchRow}>
            <Text style={styles.switchLabel}>Remote only</Text>
            <Switch
              value={draft.is_remote === true}
              onValueChange={(value) =>
                setDraft((prev) => ({ ...prev, is_remote: value || undefined }))
              }
              trackColor={{ true: colors.primary, false: colors.border }}
              thumbColor="#FFFFFF"
            />
          </View>

          <View style={styles.actions}>
            <Button title="Reset" variant="outline" onPress={reset} style={styles.resetButton} fullWidth={false} />
            <Button title="Apply Filters" onPress={apply} style={styles.applyButton} />
          </View>
        </View>
      </View>
  );
}

function OptionGroup({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <View style={styles.group}>
      <Text style={styles.groupLabel}>{label}</Text>
      {children}
    </View>
  );
}

function RadioRow({
  label,
  selected,
  onPress,
}: {
  label: string;
  selected: boolean;
  onPress: () => void;
}) {
  return (
    <TouchableOpacity
      accessibilityRole="radio"
      accessibilityState={{ selected }}
      style={styles.radioRow}
      onPress={onPress}
    >
      <Ionicons
        name={selected ? 'radio-button-on' : 'radio-button-off'}
        size={20}
        color={selected ? colors.primary : colors.textMuted}
      />
      <Text style={[styles.radioLabel, selected && styles.radioLabelSelected]}>
        {label}
      </Text>
    </TouchableOpacity>
  );
}

function formatLabel(value: string): string {
  return value
    .split('-')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function parseAmount(text: string): number | undefined {
  if (!text.trim()) return undefined;
  const value = Number(text.trim());
  return Number.isFinite(value) && value >= 0 ? value : undefined;
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    justifyContent: 'flex-end',
  },
  backdrop: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(16, 24, 40, 0.5)',
  },
  sheet: {
    backgroundColor: colors.surface,
    borderTopLeftRadius: radius.lg + 4,
    borderTopRightRadius: radius.lg + 4,
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.md,
    paddingBottom: spacing.xl,
    gap: spacing.lg - 4,
  },
  sheetHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  sheetTitle: {
    fontSize: fontSize.lg,
    fontFamily: fontFamily.bold,
    color: colors.text,
  },
  group: {
    gap: spacing.sm + 2,
  },
  groupLabel: {
    fontSize: fontSize.sm,
    fontFamily: fontFamily.medium,
    color: colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 0.4,
  },
  radioRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm + 2,
    paddingVertical: spacing.xs + 2,
  },
  radioLabel: {
    fontSize: fontSize.md,
    fontFamily: fontFamily.regular,
    color: colors.text,
  },
  radioLabelSelected: {
    fontFamily: fontFamily.medium,
    color: colors.primaryDark,
  },
  salaryRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm + 2,
  },
  salaryInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    backgroundColor: colors.background,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm + 2,
    fontSize: fontSize.md,
    fontFamily: fontFamily.regular,
    color: colors.text,
  },
  salaryDash: {
    fontSize: fontSize.md,
    color: colors.textMuted,
  },
  switchRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  switchLabel: {
    fontSize: fontSize.md,
    fontFamily: fontFamily.medium,
    color: colors.text,
  },
  actions: {
    flexDirection: 'row',
    gap: spacing.sm + 2,
  },
  resetButton: {
    flexGrow: 1,
  },
  applyButton: {
    flexGrow: 2,
  },
});
