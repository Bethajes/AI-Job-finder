import { Ionicons } from '@expo/vector-icons';
import React, { useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import {
  colors,
  fontFamily,
  fontSize,
  radius,
  spacing,
} from '../../constants/theme';
import { formatFileSize, pickResume } from '../../services/fileUpload';
import { PickedResumeFile } from '../../types';

interface ResumeUploaderProps {
  file: PickedResumeFile | null;
  onChange: (file: PickedResumeFile | null) => void;
}

export function ResumeUploader({ file, onChange }: ResumeUploaderProps) {
  const [error, setError] = useState<string | null>(null);

  const handlePick = async () => {
    setError(null);
    try {
      const picked = await pickResume();
      onChange(picked);
    } catch (pickError) {
      if (pickError instanceof Error && pickError.message !== 'cancelled') {
        setError(pickError.message);
      }
    }
  };

  return (
    <View style={styles.container}>
      {file ? (
        <View style={styles.previewCard}>
          <View style={styles.fileIcon}>
            <Ionicons name="document-text" size={20} color={colors.primaryDark} />
          </View>
          <View style={styles.fileMeta}>
            <Text style={styles.fileName} numberOfLines={1}>
              {file.name}
            </Text>
            <Text style={styles.fileSize}>{formatFileSize(file.size)}</Text>
          </View>
          <TouchableOpacity
            accessibilityRole="button"
            accessibilityLabel="Remove selected resume"
            onPress={() => onChange(null)}
            hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
          >
            <Ionicons name="trash-outline" size={20} color={colors.error} />
          </TouchableOpacity>
        </View>
      ) : (
        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel="Choose resume file"
          style={styles.uploadArea}
          onPress={() => void handlePick()}
        >
          <Ionicons name="cloud-upload-outline" size={26} color={colors.primary} />
          <Text style={styles.uploadTitle}>Upload Resume</Text>
          <Text style={styles.uploadHint}>PDF or DOCX · max 5 MB</Text>
        </TouchableOpacity>
      )}

      {file ? (
        <TouchableOpacity
          accessibilityRole="button"
          onPress={() => void handlePick()}
        >
          <Text style={styles.replaceLink}>Choose a different file</Text>
        </TouchableOpacity>
      ) : null}

      {error ? <Text style={styles.error}>{error}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: spacing.sm,
  },
  uploadArea: {
    alignItems: 'center',
    gap: spacing.xs,
    borderWidth: 1.5,
    borderStyle: 'dashed',
    borderColor: colors.border,
    borderRadius: radius.md,
    backgroundColor: colors.background,
    paddingVertical: spacing.lg - 4,
    paddingHorizontal: spacing.md,
  },
  uploadTitle: {
    fontSize: fontSize.sm + 1,
    fontFamily: fontFamily.medium,
    color: colors.text,
  },
  uploadHint: {
    fontSize: fontSize.sm - 1,
    color: colors.textMuted,
  },
  previewCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md - 2,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
    padding: spacing.sm + 4,
  },
  fileIcon: {
    width: 40,
    height: 40,
    borderRadius: radius.sm,
    backgroundColor: colors.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  fileMeta: {
    flex: 1,
  },
  fileName: {
    fontSize: fontSize.sm + 1,
    fontFamily: fontFamily.medium,
    color: colors.text,
  },
  fileSize: {
    marginTop: 1,
    fontSize: fontSize.sm - 2,
    color: colors.textMuted,
  },
  replaceLink: {
    fontSize: fontSize.sm,
    fontFamily: fontFamily.medium,
    color: colors.primary,
    textAlign: 'center',
  },
  error: {
    fontSize: fontSize.sm,
    color: colors.error,
  },
});
