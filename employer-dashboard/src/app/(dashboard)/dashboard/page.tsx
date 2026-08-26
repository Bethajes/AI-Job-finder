'use client';

import Link from 'next/link';
import { format } from 'date-fns';
import {
  ArrowRight,
  Briefcase,
  FileText,
  Send,
  Users,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { StatusBadge } from '@/components/applicants/StatusBadge';
import { JobStatusBadge } from '@/components/jobs/JobStatusBadge';
import { useJobs } from '@/hooks/useJobs';
import { useApplications } from '@/hooks/useApplications';

export default function DashboardPage() {
  const { data: jobsData, isLoading: jobsLoading } = useJobs();
  const { data: appsData, isLoading: appsLoading } = useApplications({
    sort_by: 'applied_at',
    sort_order: 'desc',
  });
  const { data: newAppsData } = useApplications({ status: 'applied' });

  const jobs = jobsData?.items ?? [];
  const published = jobs.filter((job) => job.status === 'published').length;
  const drafts = jobs.filter((job) => job.status === 'draft').length;

  const stats = [
    { label: 'Total Jobs', value: jobsData?.total ?? 0, icon: Briefcase },
    { label: 'Published', value: published, icon: Send },
    { label: 'Drafts', value: drafts, icon: FileText },
    { label: 'New Applicants', value: newAppsData?.total ?? 0, icon: Users },
  ];

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) =>
          jobsLoading || appsLoading ? (
            <Skeleton key={stat.label} className="h-28" />
          ) : (
            <Card key={stat.label}>
              <CardHeader className="flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {stat.label}
                </CardTitle>
                <stat.icon className="size-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{stat.value}</p>
              </CardContent>
            </Card>
          )
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <div>
              <CardTitle>Recent Applicants</CardTitle>
              <CardDescription>Latest applications to your jobs</CardDescription>
            </div>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/applicants">
                View all <ArrowRight className="size-4" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent>
            {appsLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} className="h-12" />
                ))}
              </div>
            ) : appsData?.items.length ? (
              <ul className="divide-y">
                {appsData.items.slice(0, 5).map((application) => (
                  <li key={application.id} className="flex items-center justify-between py-3">
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">
                        {application.applicant.full_name}
                      </p>
                      <p className="truncate text-xs text-muted-foreground">
                        {application.job.title}
                      </p>
                    </div>
                    <StatusBadge status={application.status} />
                  </li>
                ))}
              </ul>
            ) : (
              <p className="py-8 text-center text-sm text-muted-foreground">
                No applications yet.
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <div>
              <CardTitle>Your Job Postings</CardTitle>
              <CardDescription>Status of your listings</CardDescription>
            </div>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/jobs">
                Manage <ArrowRight className="size-4" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent>
            {jobsLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} className="h-12" />
                ))}
              </div>
            ) : jobs.length ? (
              <ul className="divide-y">
                {jobs.slice(0, 5).map((job) => (
                  <li key={job.id} className="flex items-center justify-between py-3">
                    <div className="min-w-0">
                      <Link
                        href={`/jobs/${job.id}/edit`}
                        className="block truncate text-sm font-medium hover:underline"
                      >
                        {job.title}
                      </Link>
                      <p className="text-xs text-muted-foreground">
                        {job.applications_count} applicant
                        {job.applications_count === 1 ? '' : 's'} ·{' '}
                        {job.posted_date
                          ? format(new Date(job.posted_date), 'MMM d')
                          : 'draft'}
                      </p>
                    </div>
                    <JobStatusBadge status={job.status} />
                  </li>
                ))}
              </ul>
            ) : (
              <div className="py-8 text-center">
                <p className="text-sm text-muted-foreground">No jobs posted yet.</p>
                <Button size="sm" className="mt-3" asChild>
                  <Link href="/jobs/new">Post your first job</Link>
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
