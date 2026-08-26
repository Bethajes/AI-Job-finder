'use client';

import { useState } from 'react';
import { format } from 'date-fns';
import toast from 'react-hot-toast';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { AdminPagination } from '@/components/admin/AdminPagination';
import { useAuditLogs } from '@/hooks/useAdmin';
import type {
  AdminLogEntry,
  AuditActionType,
  AuditLogChanges,
  AuditResourceType,
} from '@/types/admin';

const ACTION_VARIANT: Record<AuditActionType, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  user_update: 'secondary',
  user_delete: 'destructive',
  user_verify: 'outline',
  company_verify: 'default',
  company_delete: 'destructive',
  job_moderate: 'secondary',
  job_delete: 'destructive',
};

export default function AuditLogsPage() {
  const [filters, setFilters] = useState<{
    action_type: AuditActionType | '';
    resource_type: AuditResourceType | '';
    start_date?: string;
    end_date?: string;
    page: number;
  }>({ action_type: '', resource_type: '', page: 1 });

  const [selected, setSelected] = useState<AdminLogEntry | null>(null);
  const { data, isLoading, isFetching } = useAuditLogs(filters);

  const applyFilters = (changes: Partial<typeof filters>) =>
    setFilters((prev) => ({ ...prev, ...changes }));

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">Audit Logs</h1>

      <div className="mb-4 flex flex-wrap items-end gap-3">
        <div className="space-y-1">
          <Label className="text-xs text-muted-foreground">Action</Label>
          <Select
            value={filters.action_type || 'all'}
            onValueChange={(value) =>
              applyFilters({
                action_type: value === 'all' ? '' : (value as AuditActionType),
                page: 1,
              })
            }
          >
            <SelectTrigger className="w-44" aria-label="Filter by action">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All actions</SelectItem>
              <SelectItem value="user_update">User update</SelectItem>
              <SelectItem value="user_delete">User delete</SelectItem>
              <SelectItem value="user_verify">User verify</SelectItem>
              <SelectItem value="company_verify">Company verify</SelectItem>
              <SelectItem value="company_delete">Company suspend</SelectItem>
              <SelectItem value="job_moderate">Job moderate</SelectItem>
              <SelectItem value="job_delete">Job delete</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1">
          <Label className="text-xs text-muted-foreground">Resource</Label>
          <Select
            value={filters.resource_type || 'all'}
            onValueChange={(value) =>
              applyFilters({
                resource_type:
                  value === 'all' ? '' : (value as AuditResourceType),
                page: 1,
              })
            }
          >
            <SelectTrigger className="w-36" aria-label="Filter by resource type">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All resources</SelectItem>
              <SelectItem value="user">User</SelectItem>
              <SelectItem value="company">Company</SelectItem>
              <SelectItem value="job">Job</SelectItem>
              <SelectItem value="application">Application</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1">
          <Label htmlFor="audit-from" className="text-xs text-muted-foreground">
            From
          </Label>
          <Input
            id="audit-from"
            type="date"
            className="w-40"
            onChange={(e) =>
              applyFilters({ start_date: e.target.value || undefined, page: 1 })
            }
          />
        </div>

        <div className="space-y-1">
          <Label htmlFor="audit-to" className="text-xs text-muted-foreground">
            To
          </Label>
          <Input
            id="audit-to"
            type="date"
            className="w-40"
            onChange={(e) =>
              applyFilters({ end_date: e.target.value || undefined, page: 1 })
            }
          />
        </div>
      </div>

      <div className={isFetching && !isLoading ? 'opacity-70 transition-opacity' : ''}>
        <AuditLogTable logs={data?.items} isLoading={isLoading} onSelect={setSelected} />
        <AdminPagination
          page={filters.page}
          pages={data?.pages ?? 0}
          total={data?.total ?? 0}
          onPageChange={(page) => applyFilters({ page })}
        />
      </div>

      <AuditLogDetailDialog entry={selected} onClose={() => setSelected(null)} />
    </div>
  );
}

function AuditLogTable({
  logs,
  isLoading,
  onSelect,
}: {
  logs?: AdminLogEntry[];
  isLoading: boolean;
  onSelect: (entry: AdminLogEntry) => void;
}) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  return (
    <Card>
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Timestamp</TableHead>
              <TableHead>Admin</TableHead>
              <TableHead>Action</TableHead>
              <TableHead>Resource</TableHead>
              <TableHead>IP address</TableHead>
              <TableHead className="w-10" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {(logs ?? []).map((entry) => (
              <TableRow key={entry.id}>
                <TableCell className="whitespace-nowrap text-sm tabular-nums">
                  {format(new Date(entry.created_at), 'MMM d, yyyy HH:mm:ss')}
                </TableCell>
                <TableCell className="max-w-[220px] truncate text-sm">
                  {entry.admin_email ?? 'System'}
                </TableCell>
                <TableCell>
                  <Badge variant={ACTION_VARIANT[entry.action_type] ?? 'outline'}>
                    {entry.action_type.replace(/_/g, ' ')}
                  </Badge>
                </TableCell>
                <TableCell className="text-sm capitalize">
                  {entry.resource_type}
                  {entry.resource_id && (
                    <span
                      className="ml-1 cursor-pointer font-mono text-xs text-muted-foreground hover:underline"
                      title={entry.resource_id}
                      onClick={() => {
                        void navigator.clipboard.writeText(entry.resource_id!);
                        toast.success('Resource ID copied');
                      }}
                    >
                      {entry.resource_id.slice(0, 8)}…
                    </span>
                  )}
                </TableCell>
                <TableCell className="font-mono text-xs text-muted-foreground">
                  {entry.ip_address ?? '—'}
                </TableCell>
                <TableCell>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onSelect(entry)}
                  >
                    View
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {!isLoading && !logs?.length && (
              <TableRow>
                <TableCell
                  colSpan={6}
                  className="py-12 text-center text-sm text-muted-foreground"
                >
                  No audit entries match these filters.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function AuditLogDetailDialog({
  entry,
  onClose,
}: {
  entry: AdminLogEntry | null;
  onClose: () => void;
}) {
  const changes: AuditLogChanges | null | undefined = entry?.changes;

  return (
    <Dialog open={!!entry} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-lg max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Audit entry details</DialogTitle>
          <DialogDescription>
            {entry &&
              `${entry.action_type.replace(/_/g, ' ')} · ${format(
                new Date(entry.created_at),
                'MMM d, yyyy HH:mm:ss'
              )}`}
          </DialogDescription>
        </DialogHeader>

        {entry && (
          <dl className="space-y-2 text-sm">
            <div>
              <dt className="text-muted-foreground">Admin</dt>
              <dd>{entry.admin_email ?? 'System'}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Resource ID</dt>
              <dd className="break-all font-mono text-xs">
                {entry.resource_id ?? '—'}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">IP address</dt>
              <dd className="font-mono text-xs">{entry.ip_address ?? '—'}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">User agent</dt>
              <dd className="break-all text-xs">{entry.user_agent ?? '—'}</dd>
            </div>
            <div>
              <dt className="mb-1 text-muted-foreground">Changes (before → after)</dt>
              {changes && Object.keys(changes).length > 0 ? (
                <ul className="space-y-1 rounded-md border p-3 font-mono text-xs">
                  {Object.entries(changes).map(([field, change]) => (
                    <li key={field} className="break-all">
                      <span className="font-semibold">{field}</span>: [
                      {JSON.stringify(change[0])} → {JSON.stringify(change[1])}]
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="rounded-md border border-dashed p-3 text-xs text-muted-foreground">
                  No field-level diff recorded for this action.
                </p>
              )}
            </div>
          </dl>
        )}
      </DialogContent>
    </Dialog>
  );
}
