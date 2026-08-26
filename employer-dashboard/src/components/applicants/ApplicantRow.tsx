'use client';

import { useState } from 'react';
import { format } from 'date-fns';
import { ExternalLink, Eye, Mail } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Separator } from '@/components/ui/separator';
import { StatusBadge } from '@/components/applicants/StatusBadge';
import { StatusDropdown } from '@/components/applicants/StatusDropdown';
import { resolveFileUrl } from '@/lib/api';
import type { Application, ApplicationStatus } from '@/types';

export function ApplicantRow({
  application,
  onStatusChange,
  isUpdating,
}: {
  application: Application;
  onStatusChange: (applicationId: string, newStatus: ApplicationStatus) => void;
  isUpdating?: boolean;
}) {
  const [detailsOpen, setDetailsOpen] = useState(false);
  const { applicant, job } = application;

  return (
    <>
      <tr className="border-b transition-colors hover:bg-muted/50">
        <td>
          <p className="font-medium">{applicant.full_name}</p>
          <p className="flex items-center gap-1 text-xs text-muted-foreground">
            <Mail className="size-3" /> {applicant.email}
          </p>
        </td>
        <td>
          <p>{job.title}</p>
          {applicant.headline && (
            <p className="text-xs text-muted-foreground">{applicant.headline}</p>
          )}
        </td>
        <td className="text-sm text-muted-foreground">
          {format(new Date(application.applied_at), 'MMM d, yyyy')}
        </td>
        <td>
          <StatusBadge status={application.status} />
        </td>
        <td>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setDetailsOpen(true)}
            >
              <Eye className="size-4" /> View
            </Button>
            <StatusDropdown
              applicationId={application.id}
              currentStatus={application.status}
              onUpdate={onStatusChange}
              disabled={isUpdating}
            />
          </div>
        </td>
      </tr>

      <Dialog open={detailsOpen} onOpenChange={setDetailsOpen}>
        <DialogContent className="max-w-lg overflow-y-auto max-h-[85vh]">
          <DialogHeader>
            <DialogTitle>{applicant.full_name}</DialogTitle>
            <DialogDescription>
              Applied for {job.title} on{' '}
              {format(new Date(application.applied_at), 'MMMM d, yyyy')}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 text-sm">
            <div className="grid grid-cols-2 gap-2">
              <div>
                <p className="text-xs uppercase text-muted-foreground">Email</p>
                <p>{applicant.email}</p>
              </div>
              <div>
                <p className="text-xs uppercase text-muted-foreground">Location</p>
                <p>{applicant.location || '—'}</p>
              </div>
              <div>
                <p className="text-xs uppercase text-muted-foreground">Experience</p>
                <p>
                  {applicant.experience_years != null
                    ? `${applicant.experience_years} years`
                    : '—'}
                </p>
              </div>
              <div>
                <p className="text-xs uppercase text-muted-foreground">Source</p>
                <p className="capitalize">{application.source}</p>
              </div>
            </div>
            <Separator />
            <div>
              <p className="mb-1 text-xs uppercase text-muted-foreground">
                Cover Letter
              </p>
              <p className="whitespace-pre-wrap">
                {application.cover_letter || 'No cover letter provided.'}
              </p>
            </div>
            <Separator />
            <Button variant="outline" asChild>
              <a href={resolveFileUrl(application.resume_url)} target="_blank" rel="noreferrer">
                <ExternalLink className="size-4" /> Open Resume
              </a>
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
