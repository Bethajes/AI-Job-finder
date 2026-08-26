import apiClient from './client';
import { JobListResponse, JobQueryParams } from '../types';

export const jobsApi = {
  async list(params: JobQueryParams = {}): Promise<JobListResponse> {
    const { data } = await apiClient.get<JobListResponse>('/jobs', { params });
    return data;
  },
};
