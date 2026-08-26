'use client';

import { useState } from 'react';
import { Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useCompanies } from '@/hooks/useAdmin';
import { CompanyApprovalList } from '@/components/admin/CompanyApprovalList';
import type { CompanyFilters, VerificationStatus } from '@/types/admin';

export default function CompaniesPage() {
  const [filters, setFilters] = useState<CompanyFilters>({
    search: undefined,
    verification_status: '',
    page: 1,
  });
  const { data, isLoading, isFetching } = useCompanies(filters);

  const applyFilters = (changes: Partial<CompanyFilters>) =>
    setFilters((prev) => ({ ...prev, ...changes }));

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">Company Approvals</h1>

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search company name…"
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
          value={filters.verification_status || 'all'}
          onValueChange={(value) =>
            applyFilters({
              verification_status:
                value === 'all' ? '' : (value as VerificationStatus),
              page: 1,
            })
          }
        >
          <SelectTrigger className="w-44" aria-label="Filter by verification status">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="pending">Pending review</SelectItem>
            <SelectItem value="approved">Verified</SelectItem>
            <SelectItem value="rejected">Rejected</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className={isFetching && !isLoading ? 'opacity-70 transition-opacity' : ''}>
        <CompanyApprovalList
          companies={data?.items}
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
