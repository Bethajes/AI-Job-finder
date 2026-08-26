"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { CompanyProfile } from "@/types";

export const COMPANY_QUERY_KEY = ["company"];

export function useMyCompanies() {
  return useQuery({
    queryKey: COMPANY_QUERY_KEY,
    queryFn: async () => {
      const res = await api.get<CompanyProfile[]>("/profiles/me/companies");
      return res.data;
    },
    retry: false,
  });
}

/** First (primary) company of the authenticated employer. */
export function useMyCompany() {
  const query = useMyCompanies();
  return {
    ...query,
    company: query.data?.[0] ?? null,
  };
}

export interface CompanyProfileUpdatePayload {
  name?: string;
  description?: string;
  industry?: string;
  city?: string;
  country?: string;
  address?: string;
}

export function useUpdateCompanyProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      companyId,
      data,
    }: {
      companyId: string;
      data: CompanyProfileUpdatePayload;
    }) => {
      const res = await api.put<CompanyProfile>(
        `/profiles/me/companies/${companyId}`,
        data
      );
      return res.data;
    },
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: COMPANY_QUERY_KEY }),
  });
}
