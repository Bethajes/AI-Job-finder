import { Job, User } from '../types';

const numberFormatter = new Intl.NumberFormat('en-US');

export function formatNumber(value: number): string {
  return numberFormatter.format(value);
}

export function formatSalaryRange(
  salaryMin: number | null,
  salaryMax: number | null,
  currency: string,
): string {
  if (salaryMin == null && salaryMax == null) return 'Negotiable';
  if (salaryMin != null && salaryMax != null && salaryMin !== salaryMax) {
    return `${currency} ${formatNumber(salaryMin)} - ${formatNumber(salaryMax)}`;
  }
  const amount = salaryMin ?? salaryMax ?? 0;
  return `${currency} ${formatNumber(amount)}`;
}

export function formatEmploymentType(value: string): string {
  return value
    .split('-')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

export function formatDate(isoDate: string | null): string {
  if (!isoDate) return '';
  const date = new Date(isoDate);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

export function fullName(
  user: Pick<User, 'first_name' | 'last_name'> | null,
): string {
  if (!user) return '';
  return `${user.first_name} ${user.last_name}`.trim();
}

export function initials(
  user: Pick<User, 'first_name' | 'last_name'> | null,
): string {
  if (!user) return '?';
  const first = user.first_name.charAt(0);
  const last = user.last_name.charAt(0);
  return `${first}${last}`.toUpperCase() || '?';
}
