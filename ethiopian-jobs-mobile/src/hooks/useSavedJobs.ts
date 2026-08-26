import { useMemo } from 'react';
import {
  InfiniteData,
  useInfiniteQuery,
  useMutation,
  useQueryClient,
} from '@tanstack/react-query';
import { Alert } from 'react-native';

import { savedJobsApi } from '../api';
import { extractErrorMessage } from '../utils/errors';
import {
  Job,
  JobSearchItem,
  SavedJobJobBrief,
  SavedJobView,
  SavedJobsListResponse,
} from '../types';

export const savedJobsKeys = {
  all: ['saved-jobs'] as const,
  list: () => [...savedJobsKeys.all, 'list'] as const,
};

const SAVED_JOBS_PAGE_SIZE = 50;

export function useInfiniteSavedJobs() {
  return useInfiniteQuery({
    queryKey: savedJobsKeys.list(),
    queryFn: ({ pageParam }) =>
      savedJobsApi.listMine(pageParam, SAVED_JOBS_PAGE_SIZE),
    initialPageParam: 1,
    getNextPageParam: (lastPage) =>
      lastPage.has_next ? lastPage.page + 1 : undefined,
    staleTime: 60_000,
  });
}

/** Set of saved job ids derived from the cached saved-jobs list. */
export function useSavedJobIds(): Set<string> {
  const { data } = useInfiniteSavedJobs();
  return useMemo(() => {
    if (!data) return new Set<string>();
    return new Set(
      data.pages.flatMap((page) => page.items.map((item) => item.job_id)),
    );
  }, [data]);
}

function toBrief(
  job: Pick<
    Job | JobSearchItem,
    | 'id'
    | 'title'
    | 'employment_type'
    | 'location'
    | 'is_remote'
    | 'salary_min'
    | 'salary_max'
    | 'currency'
  > &
    Partial<Pick<Job, 'company'>>,
): SavedJobJobBrief {
  return {
    id: job.id,
    title: job.title,
    employment_type: String(job.employment_type),
    location: job.location,
    is_remote: job.is_remote,
    salary_min: job.salary_min,
    salary_max: job.salary_max,
    currency: job.currency,
    company_name: job.company?.name ?? 'Unknown company',
  };
}

interface ToggleVariables {
  jobId: string;
  save: boolean;
  /** Snapshot of the job so it can be inserted optimistically into the list. */
  job?: Parameters<typeof toBrief>[0];
}

interface ToggleContext {
  previous: InfiniteData<SavedJobsListResponse> | undefined;
}

/**
 * Save/unsave a job with an optimistic update on the saved-jobs cache.
 * Reverts and alerts when the request fails.
 */
export function useToggleSavedJob() {
  const queryClient = useQueryClient();

  return useMutation<
    SavedJobView['id'] | null,
    Error,
    ToggleVariables,
    ToggleContext
  >({
    mutationFn: async ({ jobId, save }) => {
      const response = save
        ? await savedJobsApi.save(jobId)
        : await savedJobsApi.unsave(jobId);
      return response.id;
    },
    onMutate: async ({ jobId, save, job }) => {
      await queryClient.cancelQueries({ queryKey: savedJobsKeys.list() });
      const previous = queryClient.getQueryData<InfiniteData<SavedJobsListResponse>>(
        savedJobsKeys.list(),
      );

      queryClient.setQueryData<InfiniteData<SavedJobsListResponse>>(
        savedJobsKeys.list(),
        (old) => {
          if (!old) return old;
          if (save) {
            if (!job) return old;
            const optimisticItem: SavedJobView = {
              id: `optimistic-${jobId}`,
              job_id: jobId,
              is_active: true,
              created_at: new Date().toISOString(),
              job: toBrief(job),
            };
            const [firstPage, ...restPages] = old.pages;
            return {
              ...old,
              pages: [
                {
                  ...firstPage,
                  total: firstPage.total + 1,
                  items: [optimisticItem, ...firstPage.items],
                },
                ...restPages,
              ],
            };
          }
          return {
            ...old,
            pages: old.pages.map((page) => ({
              ...page,
              total: Math.max(0, page.total - 1),
              items: page.items.filter((item) => item.job_id !== jobId),
            })),
          };
        },
      );

      return { previous };
    },
    onError: (error, _variables, context) => {
      if (context?.previous) {
        queryClient.setQueryData(savedJobsKeys.list(), context.previous);
      }
      Alert.alert('Error', extractErrorMessage(error, 'Failed to update saved job.'));
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: savedJobsKeys.list() });
    },
  });
}
