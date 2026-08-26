import apiClient from './client';
import { Application, MyApplicationsResponse } from '../types';

export interface MyApplicationsParams {
  page?: number;
  limit?: number;
  status?: string;
  job_title?: string;
}

export const applicationsApi = {
  /** POST /applications expects multipart/form-data built by buildApplicationForm(). */
  async apply(formData: FormData): Promise<Application> {
    const { data } = await apiClient.post<Application>(
      '/applications',
      formData,
    );
    return data;
  },

  async listMine(
    params: MyApplicationsParams = {},
  ): Promise<MyApplicationsResponse> {
    const { data } = await apiClient.get<MyApplicationsResponse>(
      '/applications/me',
      { params },
    );
    return data;
  },
};
