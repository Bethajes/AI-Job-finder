"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import api from "@/lib/api";
import type { Application, ApplicationStatus, CompanyApplicationsListResponse } from "@/types";

export const APPLICATIONS_QUERY_KEY = ["applications"];

export interface ApplicationFilters {
  status?: string;
  job_id?: string;
  sort_by?: "applied_at" | "status";
  sort_order?: "asc" | "desc";
  page?: number;
}

export function useApplications(filters: ApplicationFilters = {}) {
  return useQuery({
    queryKey: [...APPLICATIONS_QUERY_KEY, "company", filters],
    queryFn: async () => {
      const res = await api.get<CompanyApplicationsListResponse>(
        "/applications/company",
        { params: { page_size: undefined, ...cleanParams(filters), limit: 20 } }
      );
      return res.data;
    },
    placeholderData: (previous) => previous,
  });
}

function cleanParams(filters: ApplicationFilters) {
  return Object.fromEntries(
    Object.entries(filters).filter(([, value]) => value !== undefined && value !== "")
  );
}

export function useUpdateApplicationStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      applicationId,
      status,
    }: {
      applicationId: string;
      status: ApplicationStatus;
    }) => {
      const res = await api.patch<Application>(
        `/applications/${applicationId}/status`,
        { status }
      );
      return res.data;
    },
    onMutate: async ({ applicationId, status }) => {
      // Optimistic update so the dropdown reflects the change instantly.
      await queryClient.cancelQueries({ queryKey: APPLICATIONS_QUERY_KEY });
      const previousLists = queryClient.getQueriesData<CompanyApplicationsListResponse>({
        queryKey: [...APPLICATIONS_QUERY_KEY, "company"],
      });
      for (const [key, data] of previousLists) {
        if (!data) continue;
        queryClient.setQueryData<CompanyApplicationsListResponse>(key, {
          ...data,
          items: data.items.map((item) =>
            item.id === applicationId ? { ...item, status } : item
          ),
        });
      }
      return { previousLists };
    },
    onError: (_error, _vars, context) => {
      context?.previousLists.forEach(([key, data]) => queryClient.setQueryData(key, data));
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: APPLICATIONS_QUERY_KEY });
    },
  });
}
