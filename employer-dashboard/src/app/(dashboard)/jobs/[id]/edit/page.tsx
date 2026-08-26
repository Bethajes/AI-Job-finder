'use client';

import { useParams, useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { JobForm, type JobFormDefaultValues } from '@/components/jobs/JobForm';
import { Skeleton } from '@/components/ui/skeleton';
import { useJob, useUpdateJob, type JobPayload } from '@/hooks/useJobs';
import { splitLines, type JobFormOutput } from '@/lib/validations';
import { getApiErrorMessage } from '@/lib/api';

function toDatetimeLocal(value?: string | null): string {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(
    date.getHours()
  )}:${pad(date.getMinutes())}`;
}

export default function EditJobPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const jobId = params?.id;
  const { data: job, isLoading } = useJob(jobId);
  const updateJob = useUpdateJob();

  async function onSubmit(values: JobFormOutput) {
    if (!job) return;
    // Only send a future deadline; the API rejects past dates.
    const deadline = toDatetimeLocal(values.application_deadline);
    const payload: Partial<JobPayload> = {
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
      application_deadline:
        deadline && new Date(deadline).getTime() > Date.now()
          ? new Date(deadline).toISOString()
          : undefined,
      category: values.category || undefined,
      tags: splitLines(values.tags),
    };
    try {
      await updateJob.mutateAsync({ jobId: job.id, data: payload });
      toast.success('Job updated');
      router.push('/jobs');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Could not update job'));
    }
  }

  if (isLoading || !job) {
    return <Skeleton className="h-96 w-full" />;
  }

  const defaultValues: JobFormDefaultValues = {
    title: job.title,
    description: job.description,
    requirements: job.requirements.join('\n'),
    responsibilities: job.responsibilities.join('\n'),
    employment_type: job.employment_type,
    experience_level: job.experience_level,
    salary_min: job.salary_min ?? '',
    salary_max: job.salary_max ?? '',
    currency: job.currency,
    location: job.location ?? '',
    is_remote: job.is_remote,
    // Only prefill a still-future deadline; past ones cannot be re-saved.
    application_deadline:
      job.application_deadline &&
      // eslint-disable-next-line react-hooks/purity -- mount-time default only; "now" comparison for prefill
      new Date(job.application_deadline).getTime() > Date.now()
        ? toDatetimeLocal(job.application_deadline)
        : '',
    category: job.category ?? '',
    tags: job.tags.join(', '),
  };

  return (
    <div className="mx-auto max-w-3xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Edit Job</h1>
      </div>
      <JobForm
        defaultValues={defaultValues}
        isSubmitting={updateJob.isPending}
        submitLabel="Save Changes"
        onSubmit={onSubmit}
      />
    </div>
  );
}
