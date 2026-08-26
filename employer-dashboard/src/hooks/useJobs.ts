"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import api from "@/lib/api";
import { useMyCompany } from "@/hooks/useCompany";
import { JOB_STATUSES, type Job, type JobListResponse } from "@/types";

export const JOBS_QUERY_KEY = ["jobs"];

const EMPTY_LIST: JobListResponse = {
  items: [],
  total: 0,
  page: 1,
  page_size: 100,
  total_pages: 1,
};

/**
 * List the company's jobs.
 *
 * The public listing endpoint (`GET /jobs`) filters by exactly one status
 * (defaults to `published` when omitted), so an "all statuses" view merges
 * one request per status. Owners may filter private statuses such as drafts.
 */
export function useJobs(status?: string) {
  const { company } = useMyCompany();
  const companyId = company?.id;

  return useQuery({
    queryKey: [...JOBS_QUERY_KEY, "company", companyId, status ?? "all"],
    queryFn: async (): Promise<JobListResponse> => {
      if (!companyId) return EMPTY_LIST;
      const statuses = status ? [status] : [...JOB_STATUSES];
      const responses = await Promise.all(
        statuses.map((jobStatus) =>
          api.get<JobListResponse>("/jobs", {
            params: { company_id: companyId, page_size: 100, status: jobStatus },
          })
        )
      );
      const items = responses
        .flatMap((res) => res.data.items)
        .sort(
          (a, b) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
      return { ...EMPTY_LIST, items, total: items.length };
    },
    enabled: !!companyId,
  });
}

export function useJob(jobId?: string) {
  return useQuery({
    queryKey: [...JOBS_QUERY_KEY, "detail", jobId],
    queryFn: async () => {
      const res = await api.get<Job>(`/jobs/${jobId}`);
      return res.data;
    },
    enabled: !!jobId,
  });
}

export interface JobPayload {
  title: string;
  description: string;
  requirements: string[];
  responsibilities: string[];
  employment_type: Job["employment_type"];
  experience_level: Job["experience_level"];
  salary_min?: number;
  salary_max?: number;
  currency: string;
  location?: string;
  is_remote: boolean;
  application_deadline?: string;
  category?: string;
  tags: string[];
}

export function useCreateJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ companyId, data }: { companyId: string; data: JobPayload }) => {
      const res = await api.post<Job>("/jobs", { ...data, company_id: companyId });
      return res.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: JOBS_QUERY_KEY }),
  });
}

export function useUpdateJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ jobId, data }: { jobId: string; data: Partial<JobPayload> }) => {
      const res = await api.put<Job>(`/jobs/${jobId}`, data);
      return res.data;
    },
    onSuccess: (job) => {
      queryClient.invalidateQueries({ queryKey: JOBS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: ["jobs", "detail", job.id] });
    },
  });
}

function invalidateJobsAndApplications(queryClient: ReturnType<typeof useQueryClient>) {
  queryClient.invalidateQueries({ queryKey: JOBS_QUERY_KEY });
  queryClient.invalidateQueries({ queryKey: ["applications"] });
}

/** Soft delete: backend sets status to closed. */
export function useDeleteJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) => api.delete(`/jobs/${jobId}`),
    onSuccess: (_data, jobId) => {
      queryClient.removeQueries({ queryKey: ["jobs", "detail", jobId] });
      invalidateJobsAndApplications(queryClient);
    },
  });
}

export function usePublishJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) =>
      api.patch<Job>(`/jobs/${jobId}/publish`).then((res) => res.data),
    onSuccess: () => invalidateJobsAndApplications(queryClient),
  });
}

export function useCloseJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) =>
      api.patch<Job>(`/jobs/${jobId}/close`).then((res) => res.data),
    onSuccess: () => invalidateJobsAndApplications(queryClient),
  });
}
