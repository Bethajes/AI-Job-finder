import { useInfiniteQuery, useQuery } from '@tanstack/react-query';

import { jobsApi, JobSearchParams } from '../api';
import { JobDetailResponse, JobFilters, JobSearchResponse } from '../types';

export const jobsKeys = {
  all: ['jobs'] as const,
  list: (filters: JobFilters) => ['jobs', 'list', filters] as const,
  detail: (jobId: string) => ['jobs', 'detail', jobId] as const,
};

const JOBS_PAGE_SIZE = 10;

/** Infinite scroll over GET /jobs/search. */
export function useInfiniteJobs(filters: JobFilters = {}, pageSize = JOBS_PAGE_SIZE) {
  return useInfiniteQuery({
    queryKey: jobsKeys.list(filters),
    queryFn: ({ pageParam }) =>
      jobsApi.search({ ...filters, page: pageParam, limit: pageSize }),
    initialPageParam: 1,
    getNextPageParam: (lastPage) =>
      lastPage.has_next ? lastPage.page + 1 : undefined,
    staleTime: 60_000,
  });
}

/** First page only — used by the Home screen highlights. */
export function useLatestJobs(limit = 5) {
  return useQuery<JobSearchResponse, Error>({
    queryKey: [...jobsKeys.all, 'latest', { limit }],
    queryFn: () =>
      jobsApi.search({ page: 1, limit, sort_by: 'posted_date', sort_order: 'desc' }),
    staleTime: 60_000,
  });
}

export function useJob(jobId: string | undefined) {
  return useQuery<JobDetailResponse, Error>({
    queryKey: jobsKeys.detail(jobId ?? ''),
    queryFn: () => jobsApi.getById(jobId as string),
    enabled: Boolean(jobId),
    staleTime: 60_000,
  });
}

export type { JobSearchParams };
