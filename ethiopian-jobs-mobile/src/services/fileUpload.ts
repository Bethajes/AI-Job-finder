import * as DocumentPicker from 'expo-document-picker';

import { PickedResumeFile } from '../types';

const MAX_RESUME_SIZE_BYTES = 5 * 1024 * 1024;

const ALLOWED_MIME_TYPES = [
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
] as const;

const ALLOWED_EXTENSIONS = ['.pdf', '.doc', '.docx'];

export const RESUME_PICKER_TYPES = [...ALLOWED_MIME_TYPES];

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function hasAllowedExtension(name: string): boolean {
  const lower = name.toLowerCase();
  return ALLOWED_EXTENSIONS.some((ext) => lower.endsWith(ext));
}

export function validateResumeFile(file: PickedResumeFile): string | null {
  const mime = file.mimeType ?? '';
  if (!ALLOWED_MIME_TYPES.includes(mime as (typeof ALLOWED_MIME_TYPES)[number]) && !hasAllowedExtension(file.name)) {
    return 'Only PDF, DOC, or DOCX files are allowed.';
  }
  if (file.size > MAX_RESUME_SIZE_BYTES) {
    return `File is too large (${formatFileSize(file.size)}). Maximum size is 5 MB.`;
  }
  if (file.size === 0) {
    return 'The selected file is empty.';
  }
  return null;
}

/**
 * Opens the system document picker and returns a validated resume file.
 * Throws an Error with a user-friendly message when validation fails.
 */
export async function pickResume(): Promise<PickedResumeFile> {
  const result = await DocumentPicker.getDocumentAsync({
    type: RESUME_PICKER_TYPES,
    copyToCacheDirectory: true,
    multiple: false,
  });

  if (result.canceled || !result.assets?.length) {
    throw new Error('cancelled');
  }

  const asset = result.assets[0];
  const file: PickedResumeFile = {
    uri: asset.uri,
    name: asset.name ?? 'resume.pdf',
    size: asset.size ?? 0,
    mimeType: asset.mimeType ?? null,
  };

  const validationError = validateResumeFile(file);
  if (validationError) {
    throw new Error(validationError);
  }
  return file;
}

export interface ApplicationFormInput {
  jobId: string;
  resume: PickedResumeFile;
  coverLetter?: string;
}

/** Builds the multipart/form-data body expected by POST /applications. */
export function buildApplicationForm(
  input: ApplicationFormInput,
): FormData {
  const formData = new FormData();
  formData.append('job_id', input.jobId);
  formData.append('source', 'mobile');
  if (input.coverLetter && input.coverLetter.trim().length > 0) {
    formData.append('cover_letter', input.coverLetter.trim());
  }
  formData.append('resume', {
    uri: input.resume.uri,
    name: input.resume.name,
    type: input.resume.mimeType ?? 'application/pdf',
  } as unknown as Blob);
  return formData;
}
