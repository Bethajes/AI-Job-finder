'use client';

import { Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { AdminUserRole, UserFilters } from '@/types/admin';

interface UserFiltersBarProps {
  filters: UserFilters;
  onFilterChange: (filters: Partial<UserFilters>) => void;
}

export function UserFilters({ filters, onFilterChange }: UserFiltersBarProps) {
  return (
    <div className="mb-4 flex flex-wrap items-center gap-3">
      <div className="relative">
        <Search className="absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search email or name…"
          className="w-64 pl-8"
          defaultValue={filters.search}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              onFilterChange({
                search: (e.target as HTMLInputElement).value || undefined,
                page: 1,
              });
            }
          }}
          onBlur={(e) => {
            const value = e.target.value || undefined;
            if (value !== filters.search) {
              onFilterChange({ search: value, page: 1 });
            }
          }}
        />
      </div>

      <Select
        value={filters.role || 'all'}
        onValueChange={(role) =>
          onFilterChange({ role: role === 'all' ? '' : (role as AdminUserRole), page: 1 })
        }
      >
        <SelectTrigger className="w-40" aria-label="Filter by role">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All roles</SelectItem>
          <SelectItem value="job_seeker">Job Seekers</SelectItem>
          <SelectItem value="employer">Employers</SelectItem>
          <SelectItem value="admin">Admins</SelectItem>
        </SelectContent>
      </Select>

      <Select
        value={String(filters.is_active)}
        onValueChange={(value) =>
          onFilterChange({
            is_active: value === 'all' ? '' : value === 'true',
            page: 1,
          })
        }
      >
        <SelectTrigger className="w-36" aria-label="Filter by status">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All statuses</SelectItem>
          <SelectItem value="true">Active</SelectItem>
          <SelectItem value="false">Blocked</SelectItem>
        </SelectContent>
      </Select>

      <Select
        value={String(filters.is_verified)}
        onValueChange={(value) =>
          onFilterChange({
            is_verified: value === 'all' ? '' : value === 'true',
            page: 1,
          })
        }
      >
        <SelectTrigger className="w-40" aria-label="Filter by verification">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Verified &amp; unverified</SelectItem>
          <SelectItem value="true">Email verified</SelectItem>
          <SelectItem value="false">Not verified</SelectItem>
        </SelectContent>
      </Select>

      <Select
        value={`${filters.sort_by}:${filters.sort_order}`}
        onValueChange={(value) => {
          const [sort_by, sort_order] = value.split(':');
          onFilterChange({
            sort_by: sort_by as UserFilters['sort_by'],
            sort_order: sort_order as UserFilters['sort_order'],
            page: 1,
          });
        }}
      >
        <SelectTrigger className="w-44" aria-label="Sort users">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="created_at:desc">Newest first</SelectItem>
          <SelectItem value="created_at:asc">Oldest first</SelectItem>
          <SelectItem value="last_login:desc">Recent login</SelectItem>
          <SelectItem value="email:asc">Email A–Z</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}
