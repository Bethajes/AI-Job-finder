export type UserRole = "job_seeker" | "employer" | "admin";

export type EmploymentType =
  | "full-time"
  | "part-time"
  | "contract"
  | "internship"
  | "remote";

export type ExperienceLevel = "entry" | "mid" | "senior" | "lead";

export type JobStatus = "draft" | "published" | "closed" | "expired";

export type ApplicationStatus =
  | "applied"
  | "viewed"
  | "shortlisted"
  | "interviewed"
  | "offered"
  | "hired"
  | "rejected"
  | "withdrawn";

export const EMPLOYMENT_TYPES: { value: EmploymentType; label: string }[] = [
  { value: "full-time", label: "Full Time" },
  { value: "part-time", label: "Part Time" },
  { value: "contract", label: "Contract" },
  { value: "internship", label: "Internship" },
  { value: "remote", label: "Remote" },
];

export const EXPERIENCE_LEVELS: { value: ExperienceLevel; label: string }[] = [
  { value: "entry", label: "Entry Level" },
  { value: "mid", label: "Mid Level" },
  { value: "senior", label: "Senior" },
  { value: "lead", label: "Lead" },
];

export const JOB_STATUSES: JobStatus[] = [
  "draft",
  "published",
  "closed",
  "expired",
];

export const APPLICATION_STATUSES: ApplicationStatus[] = [
  "applied",
  "viewed",
  "shortlisted",
  "interviewed",
  "offered",
  "hired",
  "rejected",
];

export interface User {
  id: string;
  email: string;
  phone?: string | null;
  first_name: string;
  last_name: string;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface CompanyBrief {
  id: string;
  name: string;
  slug: string;
  logo_url?: string | null;
  city?: string | null;
  is_verified: boolean;
}

export interface Job {
  id: string;
  title: string;
  description: string;
  requirements: string[];
  responsibilities: string[];
  employment_type: EmploymentType;
  experience_level: ExperienceLevel;
  salary_min?: number | null;
  salary_max?: number | null;
  currency: string;
  location?: string | null;
  is_remote: boolean;
  company_id: string;
  posted_by_id: string;
  company: CompanyBrief;
  status: JobStatus;
  application_deadline?: string | null;
  posted_date?: string | null;
  closing_date?: string | null;
  views_count: number;
  applications_count: number;
  is_featured: boolean;
  category?: string | null;
  tags: string[];
  created_at: string;
  updated_at: string;
}

/** GET /jobs pagination shape */
export interface JobListResponse {
  items: Job[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ApplicationJobBrief {
  id: string;
  title: string;
  employment_type: string;
  location?: string | null;
  is_remote: boolean;
  company_name: string;
}

export interface ApplicantSummary {
  id: string;
  full_name: string;
  email: string;
  headline?: string | null;
  location?: string | null;
  experience_years?: number | null;
}

export interface Application {
  id: string;
  job_id: string;
  applicant_id: string;
  status: ApplicationStatus;
  cover_letter?: string | null;
  resume_url: string;
  additional_documents: unknown[];
  source: "web" | "mobile" | "api" | "referral";
  applied_at: string;
  updated_at: string;
  viewed_at?: string | null;
  interview_date?: string | null;
  job: ApplicationJobBrief;
  applicant: ApplicantSummary;
  employer_notes?: string | null;
  ip_address?: string | null;
}

/** GET/PUT company profile + list responses */
export interface CompanyProfile {
  id: string;
  owner_id: string;
  name: string;
  slug: string;
  description?: string | null;
  logo_url?: string | null;
  city?: string | null;
  country?: string | null;
  address?: string | null;
  industry?: string | null;
  is_verified: boolean;
  is_active: boolean;
  profile_picture_url?: string | null;
  profile_completeness?: number | null;
  created_at: string;
  updated_at: string;
}

/** GET /applications/company pagination shape */
export interface CompanyApplicationsListResponse {
  items: Application[];
  total: number;
  page: number;
  limit: number;
  pages: number;
  has_next: boolean;
  has_previous: boolean;
  filters: Record<string, unknown>;
}

export function formatSalary(job: Pick<Job, "salary_min" | "salary_max" | "currency">): string {
  const fmt = (n: number) =>
    new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(n);
  if (job.salary_min && job.salary_max)
    return `${fmt(job.salary_min)} - ${fmt(job.salary_max)} ${job.currency}`;
  if (job.salary_min) return `From ${fmt(job.salary_min)} ${job.currency}`;
  if (job.salary_max) return `Up to ${fmt(job.salary_max)} ${job.currency}`;
  return "Negotiable";
}
