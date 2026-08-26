'use client';

import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { JobForm } from '@/components/jobs/JobForm';
import {
  Card,
  CardContent,
} from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useMyCompany } from '@/hooks/useCompany';
import { useCreateJob, type JobPayload } from '@/hooks/useJobs';
import type { JobFormOutput } from '@/lib/validations';
import { splitLines } from '@/lib/validations';
import { getApiErrorMessage } from '@/lib/api';

function toIsoDeadline(value?: string): string | undefined {
  if (!value) return undefined;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? undefined : date.toISOString();
}

export default function NewJobPage() {
  const router = useRouter();
  const { company, isLoading } = useMyCompany();
  const createJob = useCreateJob();

  async function onSubmit(values: JobFormOutput) {
    if (!company) return;
    const payload: JobPayload = {
      title: values.title,
      description: values.description,
      requirements: splitLines(values.requirements),
      responsibilities: splitLines(values.responsibilities),
      employment_type: values.employment_type,
      experience_level: values.experience_level,
      salary_min: values.salary_min,
      salary_max: values.salary_max,
      currency: values.currency,
      location: values.location || undefined,
      is_remote: values.is_remote,
      application_deadline: toIsoDeadline(values.application_deadline),
      category: values.category || undefined,
      tags: splitLines(values.tags),
    };
    try {
      await createJob.mutateAsync({ companyId: company.id, data: payload });
      toast.success('Job created as draft. Publish it when ready.');
      router.push('/jobs');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Could not create job'));
    }
  }

  if (isLoading) {
    return <Skeleton className="h-96 w-full" />;
  }

  if (!company) {
    return (
      <Card>
        <CardContent className="py-12 text-center text-sm text-muted-foreground">
          You need a company profile before posting jobs. Set up your{' '}
          <a href="/profile" className="font-medium text-primary hover:underline">
            company profile
          </a>{' '}
          first.
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-2xl font-bold mb-6">Post New Job</h1>
      <p className="text-sm text-muted-foreground mb-4">
        New jobs are saved as <strong>drafts</strong>. Publish from the jobs list
        when you are ready to receive applications.
      </p>
      <JobForm
        isSubmitting={createJob.isPending}
        submitLabel="Save Draft"
        onSubmit={onSubmit}
      />
    </div>
  );
}
