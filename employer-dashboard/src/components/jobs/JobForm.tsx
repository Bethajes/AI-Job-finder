'use client';

import { Controller, useForm } from 'react-hook-form';
import { useState } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  EMPLOYMENT_TYPES,
  EXPERIENCE_LEVELS,
} from '@/types';
import {
  jobSchema,
  type JobFormOutput,
  type JobFormValues,
} from '@/lib/validations';

export interface JobFormDefaultValues {
  title?: string;
  description?: string;
  requirements?: string;
  responsibilities?: string;
  employment_type?: JobFormValues['employment_type'];
  experience_level?: JobFormValues['experience_level'];
  salary_min?: number | '';
  salary_max?: number | '';
  currency?: string;
  location?: string;
  is_remote?: boolean;
  application_deadline?: string;
  category?: string;
  tags?: string;
}

interface JobFormProps {
  defaultValues?: JobFormDefaultValues;
  isSubmitting?: boolean;
  submitLabel?: string;
  onSubmit: (values: JobFormOutput) => void | Promise<void>;
}

export function JobForm({
  defaultValues,
  isSubmitting,
  submitLabel = 'Publish Job',
  onSubmit,
}: JobFormProps) {
  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<JobFormValues, unknown, JobFormOutput>({
    resolver: zodResolver(jobSchema),
    defaultValues: {
      title: '',
      description: '',
      requirements: '',
      responsibilities: '',
      employment_type: 'full-time',
      experience_level: 'entry',
      salary_min: '',
      salary_max: '',
      currency: 'ETB',
      location: '',
      is_remote: false,
      application_deadline: '',
      category: '',
      tags: '',
      ...defaultValues,
    },
  });

  const [isRemote, setIsRemote] = useState(defaultValues?.is_remote ?? false);

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6" noValidate>
      <Card>
        <CardHeader>
          <CardTitle>Job Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="title">Job Title</Label>
            <Input id="title" placeholder="e.g. Senior Backend Engineer" {...register('title')} />
            {errors.title && <p className="text-sm text-red-500">{errors.title.message}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              rows={6}
              placeholder="Describe the role, team and what the candidate will do…"
              {...register('description')}
            />
            {errors.description && (
              <p className="text-sm text-red-500">{errors.description.message}</p>
            )}
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="requirements">Requirements</Label>
              <Textarea
                id="requirements"
                rows={5}
                placeholder={'One per line, e.g.\n3+ years with Python\nBS in Computer Science'}
                {...register('requirements')}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="responsibilities">Responsibilities</Label>
              <Textarea
                id="responsibilities"
                rows={5}
                placeholder={'One per line, e.g.\nDesign REST APIs\nMentor junior engineers'}
                {...register('responsibilities')}
              />
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label>Employment Type</Label>
              <Controller
                control={control}
                name="employment_type"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select type" />
                    </SelectTrigger>
                    <SelectContent>
                      {EMPLOYMENT_TYPES.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
              {errors.employment_type && (
                <p className="text-sm text-red-500">{errors.employment_type.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label>Experience Level</Label>
              <Controller
                control={control}
                name="experience_level"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select level" />
                    </SelectTrigger>
                    <SelectContent>
                      {EXPERIENCE_LEVELS.map((level) => (
                        <SelectItem key={level.value} value={level.value}>
                          {level.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Compensation &amp; Location</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="salary_min">Min Salary</Label>
              <Input id="salary_min" type="number" min={0} {...register('salary_min')} />
              {errors.salary_min && (
                <p className="text-sm text-red-500">{errors.salary_min.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="salary_max">Max Salary</Label>
              <Input id="salary_max" type="number" min={0} {...register('salary_max')} />
              {errors.salary_max && (
                <p className="text-sm text-red-500">{errors.salary_max.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="currency">Currency</Label>
              <Input id="currency" maxLength={3} placeholder="ETB" {...register('currency')} />
              {errors.currency && (
                <p className="text-sm text-red-500">{errors.currency.message}</p>
              )}
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="location">Location</Label>
              <Input
                id="location"
                placeholder="Addis Ababa"
                disabled={isRemote}
                {...register('location')}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="category">Category</Label>
              <Input id="category" placeholder="e.g. Software Development" {...register('category')} />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Controller
              control={control}
              name="is_remote"
              render={({ field }) => (
                <Checkbox
                  id="is_remote"
                  checked={field.value}
                  onCheckedChange={(checked) => {
                    const next = checked === true;
                    setIsRemote(next);
                    field.onChange(next);
                  }}
                />
              )}
            />
            <Label htmlFor="is_remote" className="cursor-pointer">
              This job can be done remotely
            </Label>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Application Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="application_deadline">Application Deadline</Label>
              <Input
                id="application_deadline"
                type="datetime-local"
                {...register('application_deadline')}
              />
              {errors.application_deadline && (
                <p className="text-sm text-red-500">
                  {errors.application_deadline.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="tags">Tags</Label>
              <Input id="tags" placeholder="python, fastapi, sql" {...register('tags')} />
              <p className="text-xs text-muted-foreground">Comma separated</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end gap-3">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Saving…' : submitLabel}
        </Button>
      </div>
    </form>
  );
}
