"use client";

import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import toast from "react-hot-toast";
import api, { getApiErrorMessage } from "@/lib/api";
import type {
  AdminCompanyDetail,
  AdminCompanyListItem,
  AdminJobDetail,
  AdminJobListItem,
  AdminListResponse,
  AdminLogEntry,
  AdminUserDetail,
  AdminUserListItem,
  CompanyFilters,
  DashboardStats,
  JobFilters,
  JobModerationAction,
  JobPerformanceReport,
  JobStats,
  AuditActionType,
  AuditLogFilters,
  AuditResourceType,
  UserActivityReport,
  UserAdminUpdatePayload,
  UserFilters,
  UserStats,
} from "@/types/admin";

/** Admin stats refresh periodically; lists refetch on demand. */
const STATS_REFETCH_MS = 60_000;

function buildParams<T extends object>(filters: T) {
  return Object.fromEntries(
    Object.entries(filters).filter(([, v]) => v !== "" && v !== undefined)
  );
}

// ── Overview stats ───────────────────────────────────────────────────

export function useAdminStats() {
  return useQuery({
    queryKey: ["admin", "stats"],
    queryFn: async (): Promise<DashboardStats> => {
      const res = await api.get<DashboardStats>("/admin/stats");
      return res.data;
    },
    refetchInterval: STATS_REFETCH_MS,
  });
}

export function useUserStats() {
  return useQuery({
    queryKey: ["admin", "stats", "users"],
    queryFn: async (): Promise<UserStats> => {
      const res = await api.get<UserStats>("/admin/stats/users");
      return res.data;
    },
    refetchInterval: STATS_REFETCH_MS,
  });
}

export function useJobStats() {
  return useQuery({
    queryKey: ["admin", "stats", "jobs"],
    queryFn: async (): Promise<JobStats> => {
      const res = await api.get<JobStats>("/admin/stats/jobs");
      return res.data;
    },
    refetchInterval: STATS_REFETCH_MS,
  });
}

// ── Reports ──────────────────────────────────────────────────────────

export function useActivityReport() {
  return useQuery({
    queryKey: ["admin", "reports", "user-activity"],
    queryFn: async (): Promise<UserActivityReport> => {
      const res = await api.get<UserActivityReport>(
        "/admin/reports/user-activity"
      );
      return res.data;
    },
    refetchInterval: STATS_REFETCH_MS,
  });
}

export function useJobPerformanceReport() {
  return useQuery({
    queryKey: ["admin", "reports", "job-performance"],
    queryFn: async (): Promise<JobPerformanceReport> => {
      const res = await api.get<JobPerformanceReport>(
        "/admin/reports/job-performance"
      );
      return res.data;
    },
    refetchInterval: STATS_REFETCH_MS,
  });
}

// ── Users ────────────────────────────────────────────────────────────

export const ADMIN_USERS_KEY = ["admin", "users"] as const;

export function useUsers(filters: UserFilters) {
  return useQuery({
    queryKey: [...ADMIN_USERS_KEY, filters],
    queryFn: async (): Promise<AdminListResponse<AdminUserListItem>> => {
      const res = await api.get("/admin/users", {
        params: buildParams(filters),
      });
      return res.data;
    },
    placeholderData: keepPreviousData,
  });
}

export function useUserDetail(userId?: string | null) {
  return useQuery({
    queryKey: [...ADMIN_USERS_KEY, "detail", userId],
    queryFn: async (): Promise<AdminUserDetail> => {
      const res = await api.get(`/admin/users/${userId}`);
      return res.data;
    },
    enabled: !!userId,
  });
}

function invalidateUsers(queryClient: ReturnType<typeof useQueryClient>) {
  queryClient.invalidateQueries({ queryKey: ADMIN_USERS_KEY });
  queryClient.invalidateQueries({ queryKey: ["admin", "stats"] });
}

export function useUpdateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      userId,
      data,
    }: {
      userId: string;
      data: UserAdminUpdatePayload;
    }) => {
      const res = await api.patch<AdminUserDetail>(
        `/admin/users/${userId}`,
        data
      );
      return res.data;
    },
    onSuccess: (user) => {
      invalidateUsers(queryClient);
      queryClient.setQueryData(
        [...ADMIN_USERS_KEY, "detail", user.id],
        user
      );
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useVerifyUserEmail() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (userId: string) =>
      api
        .post<AdminUserDetail>(`/admin/users/${userId}/verify`)
        .then((res) => res.data),
    onSuccess: (user) => {
      invalidateUsers(queryClient);
      queryClient.setQueryData([...ADMIN_USERS_KEY, "detail", user.id], user);
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useDeleteUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ userId, hard }: { userId: string; hard?: boolean }) =>
      api.delete(`/admin/users/${userId}`, { params: { hard: hard ?? false } }),
    onSuccess: (_data, variables) => {
      queryClient.removeQueries({
        queryKey: [...ADMIN_USERS_KEY, "detail", variables.userId],
      });
      invalidateUsers(queryClient);
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

// ── Companies ────────────────────────────────────────────────────────

export const ADMIN_COMPANIES_KEY = ["admin", "companies"] as const;

export function useCompanies(filters: CompanyFilters) {
  return useQuery({
    queryKey: [...ADMIN_COMPANIES_KEY, filters],
    queryFn: async (): Promise<AdminListResponse<AdminCompanyListItem>> => {
      const res = await api.get("/admin/companies", {
        params: buildParams(filters),
      });
      return res.data;
    },
    placeholderData: keepPreviousData,
  });
}

export function useCompanyDetail(companyId?: string | null) {
  return useQuery({
    queryKey: [...ADMIN_COMPANIES_KEY, "detail", companyId],
    queryFn: async (): Promise<AdminCompanyDetail> => {
      const res = await api.get(`/admin/companies/${companyId}`);
      return res.data;
    },
    enabled: !!companyId,
  });
}

function invalidateCompanies(queryClient: ReturnType<typeof useQueryClient>) {
  queryClient.invalidateQueries({ queryKey: ADMIN_COMPANIES_KEY });
  queryClient.invalidateQueries({ queryKey: ["admin", "stats"] });
}

export function useVerifyCompany() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      companyId,
      status,
      adminNotes,
    }: {
      companyId: string;
      status: "approved" | "rejected" | "pending";
      adminNotes?: string;
    }) => {
      const res = await api.patch<AdminCompanyDetail>(
        `/admin/companies/${companyId}/verify`,
        { status, admin_notes: adminNotes || undefined }
      );
      return res.data;
    },
    onSuccess: (company) => {
      invalidateCompanies(queryClient);
      queryClient.setQueryData(
        [...ADMIN_COMPANIES_KEY, "detail", company.id],
        company
      );
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

/** Suspend a company (soft delete). */
export function useSuspendCompany() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (companyId: string) =>
      api.delete(`/admin/companies/${companyId}`),
    onSuccess: () => invalidateCompanies(queryClient),
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

// ── Jobs moderation ──────────────────────────────────────────────────

export const ADMIN_JOBS_KEY = ["admin", "jobs"] as const;

export function useAdminJobs(filters: JobFilters) {
  return useQuery({
    queryKey: [...ADMIN_JOBS_KEY, filters],
    queryFn: async (): Promise<AdminListResponse<AdminJobListItem>> => {
      const res = await api.get("/admin/jobs", {
        params: buildParams(filters),
      });
      return res.data;
    },
    placeholderData: keepPreviousData,
  });
}

export function useAdminJobDetail(jobId?: string | null) {
  return useQuery({
    queryKey: [...ADMIN_JOBS_KEY, "detail", jobId],
    queryFn: async (): Promise<AdminJobDetail> => {
      const res = await api.get(`/admin/jobs/${jobId}`);
      return res.data;
    },
    enabled: !!jobId,
  });
}

function invalidateJobsAndAudit(queryClient: ReturnType<typeof useQueryClient>) {
  queryClient.invalidateQueries({ queryKey: ADMIN_JOBS_KEY });
  queryClient.invalidateQueries({ queryKey: ["admin", "stats"] });
  queryClient.invalidateQueries({ queryKey: ["admin", "audit-logs"] });
}

export function useModerateJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      jobId,
      action,
      adminNotes,
    }: {
      jobId: string;
      action: JobModerationAction;
      adminNotes?: string;
    }) => {
      const res = await api.patch<AdminJobDetail>(
        `/admin/jobs/${jobId}/moderate`,
        { action, admin_notes: adminNotes || undefined }
      );
      return res.data;
    },
    onSuccess: (job) => {
      invalidateJobsAndAudit(queryClient);
      queryClient.setQueryData([...ADMIN_JOBS_KEY, "detail", job.id], job);
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

// ── Audit logs ───────────────────────────────────────────────────────

export function useAuditLogs(
  filters: Omit<AuditLogFilters, "page"> & { page: number }
) {
  return useQuery({
    queryKey: ["admin", "audit-logs", filters],
    queryFn: async (): Promise<AdminListResponse<AdminLogEntry>> => {
      const res = await api.get("/admin/audit-logs", {
        params: buildParams(filters),
      });
      return res.data;
    },
    placeholderData: keepPreviousData,
  });
}

export type { AuditActionType, AuditResourceType };
