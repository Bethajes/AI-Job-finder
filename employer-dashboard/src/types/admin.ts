/** Types mirroring backend Week 8 admin endpoints (app/schemas/admin.py, app/schemas/stats.py). */

export type AdminUserRole = "job_seeker" | "employer" | "admin";

export type VerificationStatus = "pending" | "approved" | "rejected";

export type JobModerationAction =
  | "approve"
  | "reject"
  | "flag"
  | "unflag"
  | "hide"
  | "unhide";

export type AuditActionType =
  | "user_update"
  | "user_delete"
  | "user_verify"
  | "company_verify"
  | "company_delete"
  | "job_moderate"
  | "job_delete";

export type AuditResourceType = "user" | "company" | "job" | "application";

/** Shared pagination envelope for all admin list endpoints. */
export interface AdminListResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  pages: number;
  has_next: boolean;
  has_previous: boolean;
  filters: Record<string, unknown>;
}

// ── Stats ────────────────────────────────────────────────────────────

export interface DashboardStats {
  total_users: number;
  users_by_role: Record<string, number>;
  total_jobs: number;
  jobs_by_status: Record<string, number>;
  total_applications: number;
  applications_by_status: Record<string, number>;
  total_companies: number;
  companies_by_verification: Record<string, number>;
  new_users_7d: number;
  new_users_30d: number;
  new_jobs_7d: number;
  new_jobs_30d: number;
  active_users_24h: number;
  active_users_7d: number;
  generated_at: string;
}

export interface GrowthPoint {
  date: string;
  count: number;
}

export interface UserStats {
  growth_daily: GrowthPoint[];
  distribution_by_role: Record<string, number>;
  distribution_by_verification: Record<string, number>;
}

export interface JobStats {
  posting_trend_daily: GrowthPoint[];
  popular_categories: { category: string; job_count: number; application_count: number }[];
  jobs_by_employment_type: Record<string, number>;
  average_applications_per_job: number;
}

export interface MostActiveUser {
  user_id: string;
  full_name: string;
  email: string;
  activity_count: number;
}

export interface UserActivityReport {
  active_users_daily: number;
  active_users_weekly: number;
  active_users_monthly: number;
  applications_last_24h: number;
  applications_last_7d: number;
  most_active_users: MostActiveUser[];
  note: string;
}

export interface TopJob {
  job_id: string;
  title: string;
  company_name?: string | null;
  applications_count: number;
}

export interface JobPerformanceReport {
  top_jobs_by_applications: TopJob[];
  average_applications_per_job: number;
  average_days_to_fill?: number | null;
  jobs_by_industry: Record<string, number>;
  jobs_by_employment_type: Record<string, number>;
}

// ── Users ────────────────────────────────────────────────────────────

export interface AdminUserListItem {
  id: string;
  email: string;
  phone?: string | null;
  first_name: string;
  last_name: string;
  role: AdminUserRole;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  last_login?: string | null;
}

export interface SeekerProfileBrief {
  title?: string | null;
  skills: unknown[];
  experience_years?: number | null;
  city?: string | null;
}

export interface OwnedCompanyBrief {
  id: string;
  name: string;
  slug: string;
  is_verified: boolean;
}

export interface AdminUserDetail extends AdminUserListItem {
  job_seeker_profile?: SeekerProfileBrief | null;
  companies: OwnedCompanyBrief[];
  application_stats: Record<string, unknown>;
  job_stats: Record<string, unknown>;
}

export interface UserAdminUpdatePayload {
  role?: AdminUserRole;
  is_active?: boolean;
  is_verified?: boolean;
}

export interface UserFilters {
  search?: string;
  role?: AdminUserRole | "";
  is_active?: boolean | "";
  is_verified?: boolean | "";
  sort_by: "created_at" | "last_login" | "email";
  sort_order: "asc" | "desc";
  page: number;
}

// ── Companies ────────────────────────────────────────────────────────

export interface CompanyOwnerBrief {
  id: string;
  email: string;
  full_name: string;
}

export interface AdminCompanyListItem {
  id: string;
  name: string;
  slug: string;
  industry?: string | null;
  city?: string | null;
  is_active: boolean;
  verification_status?: VerificationStatus | null;
  is_verified: boolean;
  admin_notes?: string | null;
  created_at: string;
}

export interface AdminCompanyDetail extends AdminCompanyListItem {
  owner: CompanyOwnerBrief;
  description?: string | null;
  job_count: number;
  total_applications: number;
  verified_at?: string | null;
}

export interface CompanyFilters {
  search?: string;
  verification_status?: VerificationStatus | "";
  page: number;
}

// ── Jobs moderation ──────────────────────────────────────────────────

export interface AdminJobCompanyBrief {
  id: string;
  name: string;
}

export type JobStatusType = "draft" | "published" | "closed" | "expired";

export interface AdminJobListItem {
  id: string;
  title: string;
  status: JobStatusType;
  employment_type: string;
  location?: string | null;
  category?: string | null;
  company_id: string;
  company: AdminJobCompanyBrief;
  views_count: number;
  applications_count: number;
  is_hidden: boolean;
  is_flagged: boolean;
  flagged_at?: string | null;
  posted_date?: string | null;
  created_at: string;
}

export interface AdminJobDetail extends AdminJobListItem {
  description: string;
  admin_notes?: string | null;
  application_stats: Record<string, unknown>;
}

export interface JobFilters {
  search?: string;
  status?: JobStatusType | "";
  flagged_only?: boolean;
  hidden_only?: boolean;
  page: number;
}

// ── Audit logs ───────────────────────────────────────────────────────

export interface AuditLogChanges {
  [field: string]: [unknown, unknown];
}

export interface AdminLogEntry {
  id: string;
  admin_id?: string | null;
  admin_email?: string | null;
  action_type: AuditActionType;
  resource_type: AuditResourceType;
  resource_id?: string | null;
  changes?: AuditLogChanges | null;
  ip_address?: string | null;
  user_agent?: string | null;
  created_at: string;
}

export interface AuditLogFilters {
  action_type?: AuditActionType | "";
  resource_type?: AuditResourceType | "";
  start_date?: string;
  end_date?: string;
  page: number;
}
