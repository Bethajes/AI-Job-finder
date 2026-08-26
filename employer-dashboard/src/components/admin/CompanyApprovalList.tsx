'use client';

import { useState } from 'react';
import { format } from 'date-fns';
import {
  BadgeCheck,
  Building2,
  CheckCircle2,
  Eye,
  MoreHorizontal,
  PauseCircle,
  XCircle,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
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
import {
  useCompanyDetail,
  useSuspendCompany,
  useVerifyCompany,
} from '@/hooks/useAdmin';
import type { AdminCompanyListItem } from '@/types/admin';

const STATUS_BADGE: Record<string, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' }> = {
  approved: { label: 'Verified', variant: 'default' },
  pending: { label: 'Pending review', variant: 'outline' },
  rejected: { label: 'Rejected', variant: 'destructive' },
};

interface CompanyApprovalListProps {
  companies?: AdminCompanyListItem[];
  total: number;
  pages: number;
  page: number;
  isLoading: boolean;
  onPageChange: (page: number) => void;
}

export function CompanyApprovalList({
  companies,
  total,
  pages,
  page,
  isLoading,
  onPageChange,
}: CompanyApprovalListProps) {
  const [detailId, setDetailId] = useState<string | null>(null);
  const [decision, setDecision] = useState<{
    company: AdminCompanyListItem;
    status: 'approved' | 'rejected';
  } | null>(null);
  const [toSuspend, setToSuspend] = useState<AdminCompanyListItem | null>(null);
  const [notes, setNotes] = useState('');

  const verifyCompany = useVerifyCompany();
  const suspendCompany = useSuspendCompany();

  async function runAction(action: Promise<unknown>, successMessage: string) {
    try {
      await action;
      toast.success(successMessage);
    } catch {
      // error toast already shown by mutation onError
    }
  }

  if (isLoading && !companies?.length) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
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
                <TableHead>Company</TableHead>
                <TableHead>Industry</TableHead>
                <TableHead>City</TableHead>
                <TableHead>Verification</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Registered</TableHead>
                <TableHead className="w-10" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {(companies ?? []).map((company) => {
                const badge =
                  STATUS_BADGE[company.verification_status ?? 'pending'] ??
                  STATUS_BADGE.pending;
                return (
                  <TableRow key={company.id}>
                    <TableCell>
                      <button
                        onClick={() => setDetailId(company.id)}
                        className="text-left"
                      >
                        <p className="flex items-center gap-1 font-medium hover:underline">
                          <Building2 className="size-4 text-muted-foreground" />
                          {company.name}
                          {company.is_verified && (
                            <BadgeCheck className="size-4 text-emerald-600" />
                          )}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          /{company.slug}
                        </p>
                      </button>
                    </TableCell>
                    <TableCell className="text-sm">
                      {company.industry ?? '—'}
                    </TableCell>
                    <TableCell className="text-sm">
                      {company.city ?? '—'}
                    </TableCell>
                    <TableCell>
                      <Badge variant={badge.variant}>{badge.label}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={company.is_active ? 'outline' : 'destructive'}>
                        {company.is_active ? 'Active' : 'Suspended'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {format(new Date(company.created_at), 'MMM d, yyyy')}
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            variant="ghost"
                            size="icon"
                            aria-label="Company actions"
                          >
                            <MoreHorizontal className="size-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="w-52">
                          <DropdownMenuItem onClick={() => setDetailId(company.id)}>
                            <Eye className="size-4" /> View details
                          </DropdownMenuItem>
                          {company.verification_status !== 'approved' && (
                            <>
                              <DropdownMenuItem
                                disabled={verifyCompany.isPending}
                                onClick={() =>
                                  void runAction(
                                    verifyCompany.mutateAsync({
                                      companyId: company.id,
                                      status: 'approved',
                                    }),
                                    `${company.name} approved`
                                  )
                                }
                              >
                                <CheckCircle2 className="size-4" /> Approve
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                variant="destructive"
                                disabled={verifyCompany.isPending}
                                onClick={() => {
                                  setNotes('');
                                  setDecision({ company, status: 'rejected' });
                                }}
                              >
                                <XCircle className="size-4" /> Reject…
                              </DropdownMenuItem>
                            </>
                          )}
                          {company.verification_status !== 'pending' && (
                            <DropdownMenuItem
                              disabled={verifyCompany.isPending}
                              onClick={() =>
                                void runAction(
                                  verifyCompany.mutateAsync({
                                    companyId: company.id,
                                    status: 'pending',
                                  }),
                                  `${company.name} moved back to pending`
                                )
                              }
                            >
                              <PauseCircle className="size-4" /> Reset to pending
                            </DropdownMenuItem>
                          )}
                          {company.is_active && (
                            <>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                variant="destructive"
                                onClick={() => setToSuspend(company)}
                              >
                                <PauseCircle className="size-4" /> Suspend
                              </DropdownMenuItem>
                            </>
                          )}
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                );
              })}
              {!isLoading && !companies?.length && (
                <TableRow>
                  <TableCell
                    colSpan={7}
                    className="py-12 text-center text-sm text-muted-foreground"
                  >
                    No companies match these filters.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <AdminPagination page={page} pages={pages} total={total} onPageChange={onPageChange} />

      {/* Approve / reject with notes */}
      <Dialog
        open={!!decision}
        onOpenChange={(open) => !open && setDecision(null)}
      >
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              {decision?.status === 'approved' ? 'Approve' : 'Reject'}{' '}
              {decision?.company.name}
            </DialogTitle>
            <DialogDescription>
              {decision?.status === 'approved'
                ? 'The company will be marked verified and may post jobs freely.'
                : 'Explain why the company is rejected — the owner receives your note by email.'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label htmlFor="company-notes">
              Notes to the owner {decision?.status === 'rejected' && '(required)'}
            </Label>
            <Textarea
              id="company-notes"
              rows={4}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder={
                decision?.status === 'rejected'
                  ? 'e.g. Trade license could not be verified…'
                  : 'Optional message…'
              }
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDecision(null)}>
              Cancel
            </Button>
            <Button
              disabled={
                verifyCompany.isPending ||
                (decision?.status === 'rejected' && !notes.trim())
              }
              onClick={() => {
                if (!decision) return;
                void runAction(
                  verifyCompany.mutateAsync({
                    companyId: decision.company.id,
                    status: decision.status,
                    adminNotes: notes.trim() || undefined,
                  }),
                  decision.status === 'approved'
                    ? 'Company approved'
                    : 'Company rejected'
                );
                setDecision(null);
              }}
            >
              Confirm {decision?.status === 'approved' ? 'approval' : 'rejection'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Suspend confirm */}
      <AlertDialog
        open={!!toSuspend}
        onOpenChange={(open) => !open && setToSuspend(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Suspend this company?</AlertDialogTitle>
            <AlertDialogDescription>
              &quot;{toSuspend?.name}&quot; will be deactivated along with its
              job listings. This cannot be undone from this screen.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-red-600 hover:bg-red-700"
              disabled={suspendCompany.isPending}
              onClick={async () => {
                if (!toSuspend) return;
                await runAction(
                  suspendCompany.mutateAsync(toSuspend.id),
                  'Company suspended'
                );
                setToSuspend(null);
              }}
            >
              {suspendCompany.isPending ? 'Suspending…' : 'Suspend'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Detail dialog */}
      <CompanyDetailDialog
        companyId={detailId}
        open={!!detailId}
        onClose={() => setDetailId(null)}
      />
    </>
  );
}

function CompanyDetailDialog({
  companyId,
  open,
  onClose,
}: {
  companyId: string | null;
  open: boolean;
  onClose: () => void;
}) {
  const { data: company, isLoading } = useCompanyDetail(open ? companyId : null);

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
          <DialogTitle>{company?.name ?? 'Company details'}</DialogTitle>
          <DialogDescription>
            Verification record, owner and activity overview.
          </DialogDescription>
        </DialogHeader>

        {isLoading || !company ? (
          <div className="space-y-2 py-2">
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-2/3" />
          </div>
        ) : (
          <dl>
            {row('Verification', company.verification_status ?? 'pending')}
            {row('Owner', `${company.owner.full_name} (${company.owner.email})`)}
            {row('Industry', company.industry ?? '—')}
            {row('City', company.city ?? '—')}
            {row('Registered', format(new Date(company.created_at), 'MMM d, yyyy'))}
            {row(
              'Verified at',
              company.verified_at
                ? format(new Date(company.verified_at), 'MMM d, yyyy')
                : '—'
            )}
            {row('Jobs posted', company.job_count)}
            {row('Total applications', company.total_applications)}
            {company.admin_notes &&
              row('Previous admin notes', company.admin_notes)}
          </dl>
        )}
      </DialogContent>
    </Dialog>
  );
}
