'use client';

import Link from 'next/link';
import { useState } from 'react';
import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { JobTable } from '@/components/jobs/JobTable';
import { useJobs } from '@/hooks/useJobs';
import { JOB_STATUSES } from '@/types';

export default function JobsPage() {
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const { data, isLoading } = useJobs(statusFilter === 'all' ? undefined : statusFilter);

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
        <h1 className="text-2xl font-bold">My Jobs</h1>
        <div className="flex items-center gap-3">
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-36" aria-label="Filter by status">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All statuses</SelectItem>
              {JOB_STATUSES.map((status) => (
                <SelectItem key={status} value={status} className="capitalize">
                  {status.charAt(0).toUpperCase() + status.slice(1)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button asChild>
            <Link href="/jobs/new">
              <Plus className="size-4" /> Post New Job
            </Link>
          </Button>
        </div>
      </div>
      <JobTable jobs={data?.items} isLoading={isLoading} />
    </div>
  );
}
