'use client';

import { useState } from 'react';
import toast from 'react-hot-toast';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ApplicantTable } from '@/components/applicants/ApplicantTable';
import {
  useApplications,
  useUpdateApplicationStatus,
} from '@/hooks/useApplications';
import { useJobs } from '@/hooks/useJobs';
import { APPLICATION_STATUSES, type ApplicationStatus } from '@/types';
import { getApiErrorMessage } from '@/lib/api';

export default function ApplicantsPage() {
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [jobFilter, setJobFilter] = useState<string>('all');
  const [page, setPage] = useState(1);

  const { data, isLoading, isFetching } = useApplications({
    status: statusFilter === 'all' ? undefined : statusFilter,
    job_id: jobFilter === 'all' ? undefined : jobFilter,
    sort_by: 'applied_at',
    sort_order: 'desc',
    page,
  });

  const { data: jobsData } = useJobs();
  const updateStatus = useUpdateApplicationStatus();

  async function handleStatusChange(applicationId: string, newStatus: ApplicationStatus) {
    try {
      await updateStatus.mutateAsync({ applicationId, status: newStatus });
      toast.success(`Candidate moved to ${newStatus}`);
    } catch (error) {
      // Optimistic state is rolled back inside the hook.
      toast.error(getApiErrorMessage(error, 'Could not update status'));
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Applicants</h1>

      <div className="flex flex-wrap gap-3 mb-4">
        <Select
          value={statusFilter}
          onValueChange={(value) => {
            setStatusFilter(value);
            setPage(1);
          }}
        >
          <SelectTrigger className="w-44" aria-label="Filter by status">
            <SelectValue placeholder="All statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            {APPLICATION_STATUSES.map((status) => (
              <SelectItem key={status} value={status} className="capitalize">
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={jobFilter}
          onValueChange={(value) => {
            setJobFilter(value);
            setPage(1);
          }}
        >
          <SelectTrigger className="w-56" aria-label="Filter by job">
            <SelectValue placeholder="All jobs" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All jobs</SelectItem>
            {(jobsData?.items ?? []).map((job) => (
              <SelectItem key={job.id} value={job.id}>
                {job.title}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {(statusFilter !== 'all' || jobFilter !== 'all') && (
          <Button
            variant="ghost"
            onClick={() => {
              setStatusFilter('all');
              setJobFilter('all');
              setPage(1);
            }}
          >
            Clear filters
          </Button>
        )}

        <p className="ml-auto self-center text-sm text-muted-foreground">
          {data ? `${data.total} total` : ''}
        </p>
      </div>

      <ApplicantTable
        applications={data?.items}
        isLoading={isLoading}
        onStatusChange={(id, next) => void handleStatusChange(id, next)}
        pendingId={
          updateStatus.isPending ? updateStatus.variables?.applicationId : null
        }
      />

      {data && data.pages > 1 && (
        <div className="flex items-center justify-end gap-3 mt-4">
          <Button
            variant="outline"
            size="sm"
            disabled={!data.has_previous || isFetching}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {data.page} of {data.pages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={!data.has_next || isFetching}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
