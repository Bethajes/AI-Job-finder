'use client';

import { ApplicantRow } from '@/components/applicants/ApplicantRow';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import type { Application, ApplicationStatus } from '@/types';

export function ApplicantTable({
  applications,
  isLoading,
  onStatusChange,
  pendingId,
}: {
  applications?: Application[];
  isLoading: boolean;
  onStatusChange: (applicationId: string, newStatus: ApplicationStatus) => void;
  pendingId?: string | null;
}) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-14 w-full" />
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
              <TableHead>Applicant</TableHead>
              <TableHead>Applied For</TableHead>
              <TableHead>Applied</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {applications?.length ? (
              applications.map((application) => (
                <ApplicantRow
                  key={application.id}
                  application={application}
                  onStatusChange={onStatusChange}
                  isUpdating={pendingId === application.id}
                />
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={5} className="py-10 text-center text-sm text-muted-foreground">
                  No applications found.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
