'use client';

import { useState } from 'react';
import { useUsers } from '@/hooks/useAdmin';
import { UserFilters } from '@/components/admin/UserFilters';
import { UserTable } from '@/components/admin/UserTable';
import type { UserFilters as UserFiltersState } from '@/types/admin';

const DEFAULT_FILTERS: UserFiltersState = {
  search: undefined,
  role: '',
  is_active: '',
  is_verified: '',
  sort_by: 'created_at',
  sort_order: 'desc',
  page: 1,
};

export default function UsersPage() {
  const [filters, setFilters] = useState<UserFiltersState>(DEFAULT_FILTERS);
  const { data, isLoading, isFetching } = useUsers(filters);

  const applyFilters = (changes: Partial<UserFiltersState>) =>
    setFilters((prev) => ({ ...prev, ...changes }));

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">User Management</h1>
      <UserFilters filters={filters} onFilterChange={applyFilters} />
      <div className={isFetching && !isLoading ? 'opacity-70 transition-opacity' : ''}>
        <UserTable
          users={data?.items}
          total={data?.total ?? 0}
          pages={data?.pages ?? 0}
          page={filters.page}
          onPageChange={(page) => applyFilters({ page })}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}
