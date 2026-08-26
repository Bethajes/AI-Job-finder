'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { CompanyProfileFormValues } from '@/lib/validations';
import { companyProfileSchema } from '@/lib/validations';
import type { CompanyProfile } from '@/types';

interface CompanyProfileFormProps {
  initialData?: CompanyProfile | null;
  isSubmitting?: boolean;
  onSubmit: (values: CompanyProfileFormValues) => void | Promise<void>;
}

export function CompanyProfileForm({
  initialData,
  isSubmitting,
  onSubmit,
}: CompanyProfileFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<CompanyProfileFormValues>({
    resolver: zodResolver(companyProfileSchema),
    defaultValues: {
      name: initialData?.name ?? '',
      description: initialData?.description ?? '',
      industry: initialData?.industry ?? '',
      city: initialData?.city ?? '',
      country: initialData?.country ?? 'Ethiopia',
      address: initialData?.address ?? '',
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6" noValidate>
      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle>Company Information</CardTitle>
          {initialData?.is_verified && (
            <Badge className="bg-green-100 text-green-800 hover:bg-green-100">
              Verified
            </Badge>
          )}
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Company Name</Label>
            <Input id="name" placeholder="e.g. Addis Software PLC" {...register('name')} />
            {errors.name && <p className="text-sm text-red-500">{errors.name.message}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              rows={5}
              placeholder="Tell candidates about your company, mission and culture…"
              {...register('description')}
            />
            {errors.description && (
              <p className="text-sm text-red-500">{errors.description.message}</p>
            )}
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="industry">Industry</Label>
              <Input id="industry" placeholder="e.g. Fintech" {...register('industry')} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="city">City</Label>
              <Input id="city" placeholder="e.g. Addis Ababa" {...register('city')} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="country">Country</Label>
              <Input id="country" placeholder="Ethiopia" {...register('country')} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="address">Address</Label>
              <Input id="address" placeholder="Bole Road, …" {...register('address')} />
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end gap-3">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Saving…' : 'Save Changes'}
        </Button>
      </div>
    </form>
  );
}
