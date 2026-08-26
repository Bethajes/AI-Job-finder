'use client';

import Link from 'next/link';
import toast from 'react-hot-toast';
import { Building2 } from 'lucide-react';
import { CompanyProfileForm } from '@/components/company/CompanyProfileForm';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import {
  useMyCompanies,
  useUpdateCompanyProfile,
} from '@/hooks/useCompany';
import type { CompanyProfileFormValues } from '@/lib/validations';
import { getApiErrorMessage } from '@/lib/api';

export default function CompanyProfilePage() {
  const { data: companies, isLoading } = useMyCompanies();
  const company = companies?.[0];
  const updateProfile = useUpdateCompanyProfile();

  async function onSubmit(values: CompanyProfileFormValues) {
    if (!company) return;
    // Send only non-empty fields (PATCH-style update on the backend).
    const payload = Object.fromEntries(
      Object.entries(values).filter(([, value]) => value !== '')
    );
    try {
      await updateProfile.mutateAsync({ companyId: company.id, data: payload });
      toast.success('Company profile updated');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Could not update profile'));
    }
  }

  if (isLoading) {
    return <Skeleton className="h-96 w-full" />;
  }

  return (
    <div className="mx-auto max-w-3xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Company Profile</h1>
        {company && (
          <p className="text-sm text-muted-foreground">
            Completeness:{' '}
            <span className="font-medium text-foreground">
              {company.profile_completeness ?? '—'}%
            </span>
          </p>
        )}
      </div>

      {company ? (
        <CompanyProfileForm
          initialData={company}
          isSubmitting={updateProfile.isPending}
          onSubmit={onSubmit}
        />
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
            <Building2 className="size-10 text-muted-foreground" />
            <p className="font-medium">No company profile yet</p>
            <p className="max-w-sm text-sm text-muted-foreground">
              A company profile is created when your employer account is set up.
              If you just registered, contact support or try again shortly.
            </p>
            <Link href="/dashboard" className="text-sm font-medium text-primary hover:underline">
              Back to dashboard
            </Link>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
