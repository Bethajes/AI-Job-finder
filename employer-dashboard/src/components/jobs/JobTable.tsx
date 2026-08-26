'use client';

import Link from 'next/link';
import { useState } from 'react';
import { format } from 'date-fns';
import {
  Copy,
  MapPin,
  MoreHorizontal,
  Pencil,
  Send,
  Trash2,
  XCircle,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { JobStatusBadge } from '@/components/jobs/JobStatusBadge';
import {
  useCloseJob,
  useDeleteJob,
  usePublishJob,
} from '@/hooks/useJobs';
import { formatSalary, type Job } from '@/types';
import { getApiErrorMessage } from '@/lib/api';
import {
  Card,
  CardContent,
} from '@/components/ui/card';

export function JobTable({ jobs, isLoading }: { jobs?: Job[]; isLoading: boolean }) {
  const [jobToDelete, setJobToDelete] = useState<Job | null>(null);
  const publishJob = usePublishJob();
  const closeJob = useCloseJob();
  const deleteJob = useDeleteJob();

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-14 w-full" />
        ))}
      </div>
    );
  }

  if (!jobs?.length) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center gap-2 py-12 text-center">
          <p className="font-medium">No jobs posted yet</p>
          <p className="text-sm text-muted-foreground">
            Create your first job posting to start hiring.
          </p>
          <Button asChild className="mt-2">
            <Link href="/jobs/new">Post New Job</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  async function handleAction(
    action: Promise<unknown>,
    successMessage: string
  ) {
    try {
      await action;
      toast.success(successMessage);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Action failed'));
    }
  }

  return (
    <>
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Job</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Salary</TableHead>
                <TableHead className="text-right">Applicants</TableHead>
                <TableHead>Posted</TableHead>
                <TableHead className="w-10" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {jobs.map((job) => (
                <TableRow key={job.id}>
                  <TableCell>
                    <div className="max-w-xs">
                      <Link
                        href={`/jobs/${job.id}/edit`}
                        className="font-medium hover:underline"
                      >
                        {job.title}
                      </Link>
                      <p className="flex items-center gap-1 text-xs text-muted-foreground">
                        <MapPin className="size-3" />
                        {job.is_remote ? 'Remote' : job.location || '—'}
                      </p>
                    </div>
                  </TableCell>
                  <TableCell>
                    <JobStatusBadge status={job.status} />
                  </TableCell>
                  <TableCell className="capitalize">{job.employment_type}</TableCell>
                  <TableCell>{formatSalary(job)}</TableCell>
                  <TableCell className="text-right font-medium">
                    {job.applications_count}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {job.posted_date
                      ? format(new Date(job.posted_date), 'MMM d, yyyy')
                      : '—'}
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" aria-label="Actions">
                          <MoreHorizontal className="size-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem asChild>
                          <Link href={`/jobs/${job.id}/edit`}>
                            <Pencil className="size-4" /> Edit
                          </Link>
                        </DropdownMenuItem>
                        {job.status === 'draft' && (
                          <DropdownMenuItem
                            onClick={() =>
                              void handleAction(
                                publishJob.mutateAsync(job.id),
                                'Job published'
                              )
                            }
                          >
                            <Send className="size-4" /> Publish
                          </DropdownMenuItem>
                        )}
                        {job.status === 'published' && (
                          <DropdownMenuItem
                            onClick={() =>
                              void handleAction(
                                closeJob.mutateAsync(job.id),
                                'Job closed'
                              )
                            }
                          >
                            <XCircle className="size-4" /> Close
                          </DropdownMenuItem>
                        )}
                        <DropdownMenuItem
                          onClick={() => {
                            void navigator.clipboard.writeText(job.id);
                            toast.success('Job ID copied');
                          }}
                        >
                          <Copy className="size-4" /> Copy ID
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          variant="destructive"
                          onClick={() => setJobToDelete(job)}
                        >
                          <Trash2 className="size-4" /> Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <AlertDialog open={!!jobToDelete} onOpenChange={(open) => !open && setJobToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete job posting?</AlertDialogTitle>
            <AlertDialogDescription>
              &quot;{jobToDelete?.title}&quot; will be closed and kept for record
              keeping. This cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-red-600 hover:bg-red-700"
              disabled={deleteJob.isPending}
              onClick={async () => {
                if (!jobToDelete) return;
                await handleAction(deleteJob.mutateAsync(jobToDelete.id), 'Job deleted');
                setJobToDelete(null);
              }}
            >
              {deleteJob.isPending ? 'Deleting…' : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
