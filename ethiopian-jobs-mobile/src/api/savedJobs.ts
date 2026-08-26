import apiClient from './client';
import {
  SavedJobActionResponse,
  SavedJobsListResponse,
} from '../types';

export const savedJobsApi = {
  async save(jobId: string): Promise<SavedJobActionResponse> {
    const { data } = await apiClient.post<SavedJobActionResponse>(
      `/saved-jobs/${jobId}`,
    );
    return data;
  },

  async unsave(jobId: string): Promise<SavedJobActionResponse> {
    const { data } = await apiClient.delete<SavedJobActionResponse>(
      `/saved-jobs/${jobId}`,
    );
    return data;
  },

  async listMine(page = 1, limit = 50): Promise<SavedJobsListResponse> {
    const { data } = await apiClient.get<SavedJobsListResponse>(
      '/saved-jobs/me',
      { params: { page, limit } },
    );
    return data;
  },
};
