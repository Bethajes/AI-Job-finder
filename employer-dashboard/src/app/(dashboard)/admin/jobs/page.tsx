'use client';

import { useState } from 'react';
import { Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useAdminJobs } from '@/hooks/useAdmin';
import { JobModerationList } from '@/components/admin/JobModerationList';
import type { JobFilters, JobStatusType } from '@/types/admin';

export default function JobsPage() {
  const [filters, setFilters] = useState<JobFilters>({
    search: undefined,
    status: '',
    flagged_only: false,
    hidden_only: false,
    page: 1,
  });
  const { data, isLoading, isFetching } = useAdminJobs(filters);

  const applyFilters = (changes: Partial<JobFilters>) =>
    setFilters((prev) => ({ ...prev, ...changes }));

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">Job Moderation</h1>

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search job title…"
            className="w-64 pl-8"
            defaultValue={filters.search}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                applyFilters({
                  search: (e.target as HTMLInputElement).value || undefined,
                  page: 1,
                });
              }
            }}
            onBlur={(e) => {
              const value = e.target.value || undefined;
              if (value !== filters.search) applyFilters({ search: value, page: 1 });
            }}
          />
        </div>

        <Select
          value={filters.status || 'all'}
          onValueChange={(value) =>
            applyFilters({ status: value === 'all' ? '' : (value as JobStatusType), page: 1 })
          }
        >
          <SelectTrigger className="w-36" aria-label="Filter by status">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="published">Published</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="closed">Closed</SelectItem>
            <SelectItem value="expired">Expired</SelectItem>
          </SelectContent>
        </Select>

        <Button
          variant={filters.flagged_only ? 'default' : 'outline'}
          size="sm"
          onClick={() => applyFilters({ flagged_only: !filters.flagged_only, page: 1 })}
        >
          Flagged only
        </Button>
        <Button
          variant={filters.hidden_only ? 'default' : 'outline'}
          size="sm"
          onClick={() => applyFilters({ hidden_only: !filters.hidden_only, page: 1 })}
        >
          Hidden only
        </Button>
      </div>

      <div className={isFetching && !isLoading ? 'opacity-70 transition-opacity' : ''}>
        <JobModerationList
          jobs={data?.items}
          total={data?.total ?? 0}
          pages={data?.pages ?? 0}
          page={filters.page}
          isLoading={isLoading}
          onPageChange={(page) => applyFilters({ page })}
        />
      </div>
    </div>
  );
}
