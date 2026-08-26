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

export interface Application {
  id: string;
  job_id: string;
  status: string;
  created_at: string;
}
