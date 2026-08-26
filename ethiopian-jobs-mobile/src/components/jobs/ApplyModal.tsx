import React, { useState } from 'react';
import {
  Alert,
  KeyboardAvoidingView,
  Modal,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
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
import { useApplyToJob } from '../../hooks/useApplications';
import { buildApplicationForm } from '../../services/fileUpload';
import { extractErrorMessage } from '../../utils/errors';
import { formatEmploymentType, formatSalaryRange } from '../../utils/format';
import { ApplicationJobBrief, PickedResumeFile } from '../../types';
import { ResumeUploader } from './ResumeUploader';

const MAX_COVER_LETTER_LENGTH = 5000;

interface ApplyModalProps {
  visible: boolean;
  jobId: string;
  job: Pick<ApplicationJobBrief, 'title' | 'company_name' | 'employment_type'> & {
    salary_min?: number | null;
    salary_max?: number | null;
    currency?: string;
  };
  onClose: () => void;
  onApplied: () => void;
}

export function ApplyModal(props: ApplyModalProps) {
  return (
    <Modal
      visible={props.visible}
      animationType="slide"
      transparent
      onRequestClose={props.onClose}
    >
      {props.visible ? <ApplyForm {...props} /> : null}
    </Modal>
  );
}

function ApplyForm({ jobId, job, onClose, onApplied }: ApplyModalProps) {
  const [coverLetter, setCoverLetter] = useState('');
  const [resume, setResume] = useState<PickedResumeFile | null>(null);
  const applyMutation = useApplyToJob();

  const canSubmit =
    resume !== null && coverLetter.length <= MAX_COVER_LETTER_LENGTH && !applyMutation.isPending;

  const submit = () => {
    if (!resume) return;
    const formData = buildApplicationForm({
      jobId,
      resume,
      coverLetter,
    });
    applyMutation.mutate(formData, {
      onSuccess: () => {
        Alert.alert(
          'Application Sent',
          `Your application for ${job.title} was submitted successfully.`,
        );
        onApplied();
        onClose();
      },
      onError: (error) => {
        Alert.alert(
          'Application Failed',
          extractErrorMessage(error, 'Could not submit your application. Please try again.'),
        );
      },
    });
  };

  return (
    <KeyboardAvoidingView
      style={styles.overlay}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <View style={styles.sheet}>
          <View style={styles.sheetHeader}>
            <Text style={styles.sheetTitle}>Apply</Text>
            <Button title="Cancel" variant="ghost" onPress={onClose} fullWidth={false} />
          </View>

          <ScrollView keyboardShouldPersistTaps="handled">
            <View style={styles.jobSummary}>
              <Text style={styles.jobTitle}>{job.title}</Text>
              <Text style={styles.jobMeta}>
                {job.company_name} · {formatEmploymentType(job.employment_type)}
              </Text>
              {job.currency ? (
                <Text style={styles.jobSalary}>
                  {formatSalaryRange(
                    job.salary_min ?? null,
                    job.salary_max ?? null,
                    job.currency,
                  )}
                </Text>
              ) : null}
            </View>

            <Text style={styles.sectionLabel}>Cover Letter (optional)</Text>
            <TextInput
              style={styles.coverLetterInput}
              placeholder="Tell the employer why you are a great fit…"
              placeholderTextColor={colors.textMuted}
              value={coverLetter}
              onChangeText={setCoverLetter}
              multiline
              textAlignVertical="top"
              maxLength={MAX_COVER_LETTER_LENGTH}
            />
            <Text style={styles.charCount}>
              {coverLetter.length}/{MAX_COVER_LETTER_LENGTH}
            </Text>

            <Text style={[styles.sectionLabel, styles.sectionSpacing]}>Resume *</Text>
            <ResumeUploader file={resume} onChange={setResume} />
          </ScrollView>

          <View style={styles.footer}>
            <Button
              title="Submit Application"
              onPress={submit}
              loading={applyMutation.isPending}
              disabled={!canSubmit}
            />
          </View>
        </View>
      </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    justifyContent: 'flex-end',
    backgroundColor: 'rgba(16, 24, 40, 0.5)',
  },
  sheet: {
    backgroundColor: colors.surface,
    borderTopLeftRadius: radius.lg + 4,
    borderTopRightRadius: radius.lg + 4,
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.md,
    maxHeight: '92%',
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
  jobSummary: {
    marginTop: spacing.md,
    gap: 2,
    backgroundColor: colors.background,
    borderRadius: radius.md,
    padding: spacing.md - 2,
  },
  jobTitle: {
    fontSize: fontSize.md,
    fontFamily: fontFamily.bold,
    color: colors.text,
  },
  jobMeta: {
    fontSize: fontSize.sm,
    color: colors.textMuted,
  },
  jobSalary: {
    fontSize: fontSize.sm,
    fontFamily: fontFamily.medium,
    color: colors.primaryDark,
  },
  sectionLabel: {
    marginTop: spacing.md + 2,
    marginBottom: spacing.sm,
    fontSize: fontSize.sm,
    fontFamily: fontFamily.medium,
    color: colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 0.4,
  },
  sectionSpacing: {
    marginTop: spacing.md,
  },
  coverLetterInput: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    backgroundColor: colors.background,
    padding: spacing.md - 2,
    minHeight: 110,
    fontSize: fontSize.sm + 1,
    fontFamily: fontFamily.regular,
    color: colors.text,
  },
  charCount: {
    alignSelf: 'flex-end',
    marginTop: spacing.xs,
    fontSize: fontSize.sm - 2,
    color: colors.textMuted,
  },
  footer: {
    paddingTop: spacing.sm + 2,
    paddingBottom: spacing.lg,
  },
});
