import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { applicationsApi } from '../api';
import { Application, MyApplicationsResponse } from '../types';

export const applicationsKeys = {
  all: ['applications'] as const,
  mine: ['applications', 'mine'] as const,
};

const APPLICATIONS_PAGE_SIZE = 100;

/**
 * The seeker's applications (most recent first). Filtered client-side by
 * status tabs; also powers the "already applied" state on job screens.
 */
export function useMyApplications() {
  return useQuery<MyApplicationsResponse, Error>({
    queryKey: applicationsKeys.mine,
    queryFn: () =>
      applicationsApi.listMine({ page: 1, limit: APPLICATIONS_PAGE_SIZE }),
    staleTime: 60_000,
  });
}

export function useAppliedJobIds(): Set<string> {
  const { data } = useMyApplications();
  return useAppliedJobIdsFrom(data);
}

export function useApplyToJob() {
  const queryClient = useQueryClient();

  return useMutation<Application, Error, FormData>({
    mutationFn: (formData) => applicationsApi.apply(formData),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: applicationsKeys.all,
      });
    },
  });
}

function useAppliedJobIdsFrom(data: MyApplicationsResponse | undefined): Set<string> {
  if (!data) return new Set();
  return new Set(data.items.map((application) => application.job_id));
}
