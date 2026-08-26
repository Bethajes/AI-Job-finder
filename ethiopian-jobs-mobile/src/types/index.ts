import type { InternalAxiosRequestConfig } from 'axios';

declare module 'axios' {
  export interface InternalAxiosRequestConfig {
    _retry?: boolean;
  }
}

export type UserRole = 'job_seeker' | 'employer' | 'admin';

export interface User {
  id: string;
  email: string;
  phone: string | null;
  first_name: string;
  last_name: string;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  first_name: string;
  last_name: string;
  phone?: string | null;
  password: string;
  role?: Exclude<UserRole, 'admin'>;
}

export interface RefreshTokenPayload {
  refresh_token: string;
}

export interface MessageResponse {
  message: string;
}

export interface CompanyBrief {
  id: string;
  name: string;
  slug: string;
  logo_url: string | null;
  city: string | null;
  is_verified: boolean;
}

export type EmploymentType =
  | 'full-time'
  | 'part-time'
  | 'contract'
  | 'internship'
  | 'remote';

export type ExperienceLevel = 'entry' | 'mid' | 'senior' | 'lead';

export interface JobSearchItem {
  id: string;
  title: string;
  employment_type: EmploymentType | string;
  experience_level: ExperienceLevel | string;
  salary_min: number | null;
  salary_max: number | null;
  currency: string;
  location: string | null;
  is_remote: boolean;
  company_id: string;
  company: CompanyBrief;
  posted_date: string | null;
  application_deadline: string | null;
  category: string | null;
  tags: string[];
  views_count: number;
}

export interface JobSearchResponse {
  items: JobSearchItem[];
  total: number;
  page: number;
  limit: number;
  pages: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface RelatedJob extends Omit<JobSearchItem, 'relevance_score'> {
  relevance_score?: number | null;
}

export interface JobDetailResponse extends Job {
  related_jobs: RelatedJob[];
}

export interface JobFilters {
  q?: string;
  employment_type?: EmploymentType | string;
  experience_level?: ExperienceLevel | string;
  salary_min?: number;
  salary_max?: number;
  is_remote?: boolean;
}

export interface Job {
  id: string;
  title: string;
  description: string;
  requirements: string[];
  responsibilities: string[];
  employment_type: EmploymentType | string;
  experience_level: ExperienceLevel | string;
  salary_min: number | null;
  salary_max: number | null;
  currency: string;
  location: string | null;
  is_remote: boolean;
  company_id: string;
  posted_by_id: string;
  company: CompanyBrief;
  status: string;
  application_deadline: string | null;
  posted_date: string | null;
  closing_date: string | null;
  views_count: number;
  applications_count: number;
  is_featured: boolean;
  category?: string | null;
  tags?: string[];
}

export interface JobListResponse {
  items: Job[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface JobQueryParams {
  page?: number;
  page_size?: number;
  search?: string;
  location?: string;
  employment_type?: string;
  experience_level?: string;
  is_remote?: boolean;
}

export type ApplicationStatus =
  | 'applied'
  | 'viewed'
  | 'shortlisted'
  | 'interviewed'
  | 'offered'
  | 'hired'
  | 'rejected'
  | 'withdrawn';

export const APPLICATION_STATUSES: ApplicationStatus[] = [
  'applied',
  'viewed',
  'shortlisted',
  'interviewed',
  'offered',
  'hired',
  'rejected',
  'withdrawn',
];

export interface ApplicationJobBrief {
  id: string;
  title: string;
  employment_type: string;
  location: string | null;
  is_remote: boolean;
  company_name: string;
}

export interface Application {
  id: string;
  job_id: string;
  applicant_id: string;
  status: ApplicationStatus | string;
  cover_letter: string | null;
  resume_url: string;
  additional_documents: unknown[];
  source: string;
  applied_at: string;
  updated_at: string;
  viewed_at: string | null;
  interview_date: string | null;
  job: ApplicationJobBrief;
}

export interface MyApplicationsResponse {
  items: Application[];
  total: number;
  page: number;
  limit: number;
  pages: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface SavedJobJobBrief {
  id: string;
  title: string;
  employment_type: string;
  location: string | null;
  is_remote: boolean;
  salary_min: number | null;
  salary_max: number | null;
  currency: string;
  company_name: string;
}

export interface SavedJobView {
  id: string;
  job_id: string;
  is_active: boolean;
  created_at: string;
  job: SavedJobJobBrief;
}

export interface SavedJobsListResponse {
  items: SavedJobView[];
  total: number;
  page: number;
  limit: number;
  pages: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface SavedJobActionResponse {
  id: string | null;
  job_id: string;
  message: string;
}

export interface PickedResumeFile {
  uri: string;
  name: string;
  size: number;
  mimeType: string | null;
}
