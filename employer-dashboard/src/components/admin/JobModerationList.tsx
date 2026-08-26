'use client';

import { useState } from 'react';
import { format } from 'date-fns';
import {
  CheckCircle2,
  Eye,
  Flag,
  EyeOff,
  MoreHorizontal,
  XCircle,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Textarea } from '@/components/ui/textarea';
import { AdminPagination } from '@/components/admin/AdminPagination';
import { useAdminJobDetail, useModerateJob } from '@/hooks/useAdmin';
import type { AdminJobListItem, JobModerationAction } from '@/types/admin';

const STATUS_VARIANT: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  published: 'default',
  draft: 'secondary',
  closed: 'outline',
  expired: 'destructive',
};

interface JobModerationListProps {
  jobs?: AdminJobListItem[];
  total: number;
  pages: number;
  page: number;
  isLoading: boolean;
  onPageChange: (page: number) => void;
}

export function JobModerationList({
  jobs,
  total,
  pages,
  page,
  isLoading,
  onPageChange,
}: JobModerationListProps) {
  const [detailId, setDetailId] = useState<string | null>(null);
  const [rejecting, setRejecting] = useState<AdminJobListItem | null>(null);
  const [notes, setNotes] = useState('');

  const moderateJob = useModerateJob();

  async function runAction(action: Promise<unknown>, successMessage: string) {
    try {
      await action;
      toast.success(successMessage);
    } catch {
      // error toast already shown by mutation onError
    }
  }

  const MODERATION_LABELS: Record<JobModerationAction, string> = {
    approve: 'Job approved',
    reject: 'Job rejected',
    flag: 'Job flagged for review',
    unflag: 'Flag removed',
    hide: 'Job hidden',
    unhide: 'Job is visible again',
  };

  function moderate(
    job: AdminJobListItem,
    action: JobModerationAction,
    adminNotes?: string
  ) {
    return runAction(
      moderateJob.mutateAsync({ jobId: job.id, action, adminNotes }),
      MODERATION_LABELS[action]
    );
  }

  if (isLoading && !jobs?.length) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-14 w-full" />
        ))}
      </div>
    );
  }

  return (
    <>
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Job</TableHead>
                <TableHead>Company</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Flags</TableHead>
                <TableHead className="text-right">Views</TableHead>
                <TableHead className="text-right">Applicants</TableHead>
                <TableHead>Posted</TableHead>
                <TableHead className="w-10" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {(jobs ?? []).map((job) => (
                <TableRow key={job.id}>
                  <TableCell>
                    <button onClick={() => setDetailId(job.id)} className="text-left">
                      <p className="max-w-xs truncate font-medium hover:underline">
                        {job.title}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {job.category ?? job.employment_type}
                        {job.location ? ` · ${job.location}` : ''}
                      </p>
                    </button>
                  </TableCell>
                  <TableCell className="text-sm">
                    {job.company.name}
                  </TableCell>
                  <TableCell>
                    <Badge variant={STATUS_VARIANT[job.status] ?? 'outline'}>
                      {job.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      {job.is_flagged && (
                        <Badge variant="destructive">
                          <Flag className="mr-1 size-3" /> flagged
                        </Badge>
                      )}
                      {job.is_hidden && (
                        <Badge variant="secondary">
                          <EyeOff className="mr-1 size-3" /> hidden
                        </Badge>
                      )}
                      {!job.is_flagged && !job.is_hidden && (
                        <span className="text-sm text-muted-foreground">—</span>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {job.views_count}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {job.applications_count}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {job.posted_date
                      ? format(new Date(job.posted_date), 'MMM d, yyyy')
                      : format(new Date(job.created_at), 'MMM d, yyyy')}
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" aria-label="Moderation actions">
                          <MoreHorizontal className="size-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" className="w-52">
                        <DropdownMenuItem onClick={() => setDetailId(job.id)}>
                          <Eye className="size-4" /> View details
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        {job.status !== 'published' && (
                          <DropdownMenuItem
                            disabled={moderateJob.isPending}
                            onClick={() => void moderate(job, 'approve')}
                          >
                            <CheckCircle2 className="size-4" /> Approve (publish)
                          </DropdownMenuItem>
                        )}
                        {job.status !== 'closed' && (
                          <DropdownMenuItem
                            variant="destructive"
                            disabled={moderateJob.isPending}
                            onClick={() => {
                              setNotes('');
                              setRejecting(job);
                            }}
                          >
                            <XCircle className="size-4" /> Reject…
                          </DropdownMenuItem>
                        )}
                        {!job.is_flagged && (
                          <DropdownMenuItem
                            disabled={moderateJob.isPending}
                            onClick={() =>
                              void runAction(
                                moderateJob.mutateAsync({
                                  jobId: job.id,
                                  action: 'flag',
                                  adminNotes: notes.trim() || undefined,
                                }),
                                'Job flagged for review'
                              )
                            }
                          >
                            <Flag className="size-4" /> Flag for review
                          </DropdownMenuItem>
                        )}
                        {job.is_flagged && (
                          <DropdownMenuItem
                            disabled={moderateJob.isPending}
                            onClick={() => void moderate(job, 'unflag')}
                          >
                            <Flag className="size-4" /> Remove flag
                          </DropdownMenuItem>
                        )}
                        {!job.is_hidden && (
                          <DropdownMenuItem
                            disabled={moderateJob.isPending}
                            onClick={() => void moderate(job, 'hide')}
                          >
                            <EyeOff className="size-4" /> Hide from public
                          </DropdownMenuItem>
                        )}
                        {job.is_hidden && (
                          <DropdownMenuItem
                            disabled={moderateJob.isPending}
                            onClick={() => void moderate(job, 'unhide')}
                          >
                            <EyeOff className="size-4" /> Unhide
                          </DropdownMenuItem>
                        )}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
              {!isLoading && !jobs?.length && (
                <TableRow>
                  <TableCell
                    colSpan={8}
                    className="py-12 text-center text-sm text-muted-foreground"
                  >
                    No jobs match these filters.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <AdminPagination page={page} pages={pages} total={total} onPageChange={onPageChange} />

      {/* Reject with reason */}
      <Dialog open={!!rejecting} onOpenChange={(open) => !open && setRejecting(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Reject &quot;{rejecting?.title}&quot;</DialogTitle>
            <DialogDescription>
              The posting will be closed and the employer can read your reason.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label htmlFor="rejection-reason">Reason (required)</Label>
            <Textarea
              id="rejection-reason"
              rows={4}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Misleading salary information…"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRejecting(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              disabled={moderateJob.isPending || !notes.trim()}
              onClick={() => {
                if (!rejecting) return;
                void moderate(rejecting, 'reject', notes.trim());
                setRejecting(null);
              }}
            >
              Reject job
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <JobDetailDialog
        jobId={detailId}
        open={!!detailId}
        onClose={() => setDetailId(null)}
      />
    </>
  );
}

function JobDetailDialog({
  jobId,
  open,
  onClose,
}: {
  jobId: string | null;
  open: boolean;
  onClose: () => void;
}) {
  const { data: job, isLoading } = useAdminJobDetail(open ? jobId : null);

  const row = (label: string, value: React.ReactNode) => (
    <div className="flex items-start justify-between gap-4 py-1.5">
      <dt className="shrink-0 text-sm text-muted-foreground">{label}</dt>
      <dd className="text-right text-sm font-medium">{value}</dd>
    </div>
  );

  return (
    <Dialog open={open} onOpenChange={(next) => !next && onClose()}>
      <DialogContent className="max-w-lg max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{job?.title ?? 'Job details'}</DialogTitle>
          <DialogDescription>Moderation record and activity.</DialogDescription>
        </DialogHeader>

        {isLoading || !job ? (
          <div className="space-y-2 py-2">
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-2/3" />
          </div>
        ) : (
          <dl>
            {row('Company', job.company.name)}
            {row('Status', job.status)}
            {row('Flagged', job.is_flagged ? 'Yes' : 'No')}
            {row('Hidden', job.is_hidden ? 'Yes' : 'No')}
            {row(
              'Posted',
              job.posted_date
                ? format(new Date(job.posted_date), 'MMM d, yyyy')
                : 'Not yet published'
            )}
            {row('Views', job.views_count)}
            {Object.keys(job.application_stats).length > 0 &&
              row(
                'Applications',
                Object.entries(job.application_stats)
                  .map(([key, value]) => `${key.replace(/_/g, ' ')}: ${value}`)
                  .join(' · ')
              )}
            {job.admin_notes && row('Previous admin notes', job.admin_notes)}
          </dl>
        )}
      </DialogContent>
    </Dialog>
  );
}
