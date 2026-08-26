import { AxiosError } from 'axios';

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null;

export function isSessionInvalidError(error: unknown): boolean {
  return error instanceof AxiosError && error.response?.status === 401;
}

export function extractErrorMessage(
  error: unknown,
  fallback = 'Something went wrong. Please try again.',
): string {
  if (error instanceof AxiosError) {
    const data: unknown = error.response?.data;
    if (isRecord(data)) {
      const detail = data.detail;
      if (typeof detail === 'string') return detail;
      if (Array.isArray(detail)) {
        const first = detail.find(isRecord);
        if (first && typeof first.msg === 'string') return first.msg;
      }
    }
    if (error.code === 'ECONNABORTED') {
      return 'The request timed out. Please check your connection.';
    }
    if (!error.response) {
      return 'Cannot reach the server. Please check your connection.';
    }
  }
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}
