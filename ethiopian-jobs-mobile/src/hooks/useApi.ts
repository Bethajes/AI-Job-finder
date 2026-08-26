import {
  useInfiniteQuery,
  useQuery,
} from '@tanstack/react-query';

import { jobsApi } from '../api';
import { JobQueryParams } from '../types';

export const queryKeys = {
  jobs: (filters: Omit<JobQueryParams, 'page' | 'page_size'> = {}) =>
    ['jobs', filters] as const,
};

const JOBS_PAGE_SIZE = 10;

export function useJobs(
  filters: Omit<JobQueryParams, 'page' | 'page_size'> = {},
  page = 1,
  pageSize = JOBS_PAGE_SIZE,
) {
  return useQuery({
    queryKey: [...queryKeys.jobs(filters), { page, pageSize }],
    queryFn: () => jobsApi.list({ ...filters, page, page_size: pageSize }),
    staleTime: 60_000,
  });
}

export function useInfiniteJobs(
  filters: Omit<JobQueryParams, 'page' | 'page_size'> = {},
  pageSize = JOBS_PAGE_SIZE,
) {
  return useInfiniteQuery({
    queryKey: queryKeys.jobs(filters),
    queryFn: ({ pageParam }) =>
      jobsApi.list({ ...filters, page: pageParam, page_size: pageSize }),
    initialPageParam: 1 as number,
    getNextPageParam: (lastPage) =>
      lastPage.page < lastPage.total_pages ? lastPage.page + 1 : undefined,
    staleTime: 60_000,
  });
}
