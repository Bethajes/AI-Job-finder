import apiClient from './client';
import {
  JobDetailResponse,
  JobFilters,
  JobSearchResponse,
} from '../types';

export interface JobSearchParams extends JobFilters {
  page?: number;
  limit?: number;
  sort_by?: 'relevance' | 'posted_date' | 'salary_max' | 'salary_min';
  sort_order?: 'asc' | 'desc';
}

function toQueryParams(params: JobSearchParams): Record<string, unknown> {
  const query: Record<string, unknown> = {};
  if (params.q) query.q = params.q;
  if (params.page != null) query.page = params.page;
  if (params.limit != null) query.limit = params.limit;
  if (params.employment_type) query.employment_type = params.employment_type;
  if (params.experience_level) query.experience_level = params.experience_level;
  if (params.salary_min != null) query.salary_min = params.salary_min;
  if (params.salary_max != null) query.salary_max = params.salary_max;
  if (params.is_remote === true) query.is_remote = true;
  return query;
}

export const jobsApi = {
  async search(params: JobSearchParams = {}): Promise<JobSearchResponse> {
    const { data } = await apiClient.get<JobSearchResponse>('/jobs/search', {
      params: toQueryParams(params),
    });
    return data;
  },

  async getById(jobId: string, includeRelated = true): Promise<JobDetailResponse> {
    const { data } = await apiClient.get<JobDetailResponse>(`/jobs/${jobId}`, {
      params: includeRelated ? undefined : { include_related: false },
    });
    return data;
  },
};
