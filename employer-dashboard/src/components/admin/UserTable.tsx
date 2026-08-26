'use client';

import { useState } from 'react';
import { format } from 'date-fns';
import {
  BadgeCheck,
  Ban,
  Eye,
  MoreHorizontal,
  ShieldCheck,
  Trash2,
  UserCog,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
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
import { Separator } from '@/components/ui/separator';
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
  useDeleteUser,
  useUpdateUser,
  useUserDetail,
  useVerifyUserEmail,
} from '@/hooks/useAdmin';
import { AdminPagination } from '@/components/admin/AdminPagination';
import type {
  AdminUserRole,
  AdminUserListItem,
} from '@/types/admin';

const ROLE_LABELS: Record<AdminUserRole, string> = {
  job_seeker: 'Job Seeker',
  employer: 'Employer',
  admin: 'Admin',
};

interface UserTableProps {
  users?: AdminUserListItem[];
  total: number;
  pages: number;
  isLoading: boolean;
  page: number;
  onPageChange: (page: number) => void;
}

export function UserTable({
  users,
  total,
  pages,
  isLoading,
  page,
  onPageChange,
}: UserTableProps) {
  const [detailUserId, setDetailUserId] = useState<string | null>(null);
  const [userToDelete, setUserToDelete] = useState<AdminUserListItem | null>(null);
  const updateUser = useUpdateUser();
  const verifyEmail = useVerifyUserEmail();
  const deleteUser = useDeleteUser();

  async function runAction(action: Promise<unknown>, successMessage: string) {
    try {
      await action;
      toast.success(successMessage);
    } catch {
      // error toast already shown by mutation onError
    }
  }

  if (isLoading && !users?.length) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 6 }).map((_, i) => (
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
                <TableHead>User</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Email verified</TableHead>
                <TableHead>Joined</TableHead>
                <TableHead>Last login</TableHead>
                <TableHead className="w-10" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {(users ?? []).map((user) => (
                <TableRow key={user.id}>
                  <TableCell>
                    <button
                      onClick={() => setDetailUserId(user.id)}
                      className="text-left"
                    >
                      <p className="font-medium hover:underline">
                        {user.first_name} {user.last_name}
                      </p>
                      <p className="text-xs text-muted-foreground">{user.email}</p>
                    </button>
                  </TableCell>
                  <TableCell>
                    <Badge variant={user.role === 'admin' ? 'default' : 'secondary'}>
                      {ROLE_LABELS[user.role]}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={user.is_active ? 'outline' : 'destructive'}>
                      {user.is_active ? 'Active' : 'Blocked'}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {user.is_verified ? (
                      <span className="flex items-center gap-1 text-sm text-emerald-600">
                        <BadgeCheck className="size-4" /> Yes
                      </span>
                    ) : (
                      <span className="text-sm text-muted-foreground">No</span>
                    )}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {format(new Date(user.created_at), 'MMM d, yyyy')}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {user.last_login
                      ? format(new Date(user.last_login), 'MMM d, yyyy')
                      : 'Never'}
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" aria-label="User actions">
                          <MoreHorizontal className="size-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" className="w-52">
                        <DropdownMenuItem onClick={() => setDetailUserId(user.id)}>
                          <Eye className="size-4" /> View details
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          disabled={updateUser.isPending}
                          onClick={() =>
                            void runAction(
                              updateUser.mutateAsync({
                                userId: user.id,
                                data: { is_active: !user.is_active },
                              }),
                              user.is_active ? 'User blocked' : 'User activated'
                            )
                          }
                        >
                          <Ban className="size-4" />
                          {user.is_active ? 'Block user' : 'Unblock user'}
                        </DropdownMenuItem>
                        {!user.is_verified && (
                          <DropdownMenuItem
                            disabled={verifyEmail.isPending}
                            onClick={() =>
                              void runAction(
                                verifyEmail.mutateAsync(user.id),
                                'Email marked as verified'
                              )
                            }
                          >
                            <BadgeCheck className="size-4" /> Verify email
                          </DropdownMenuItem>
                        )}
                        <DropdownMenuSeparator />
                        <DropdownMenuLabel className="flex items-center gap-2 text-xs text-muted-foreground">
                          <UserCog className="size-3.5" /> Change role
                        </DropdownMenuLabel>
                        {(['job_seeker', 'employer', 'admin'] as const)
                          .filter((role) => role !== user.role)
                          .map((role) => (
                            <DropdownMenuItem
                              key={role}
                              disabled={updateUser.isPending}
                              onClick={() =>
                                void runAction(
                                  updateUser.mutateAsync({
                                    userId: user.id,
                                    data: { role },
                                  }),
                                  `Role changed to ${ROLE_LABELS[role]}`
                                )
                              }
                            >
                              <ShieldCheck className="size-4" /> Make{' '}
                              {ROLE_LABELS[role]}
                            </DropdownMenuItem>
                          ))}
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          variant="destructive"
                          onClick={() => setUserToDelete(user)}
                        >
                          <Trash2 className="size-4" /> Delete user
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
              {!isLoading && !users?.length && (
                <TableRow>
                  <TableCell
                    colSpan={7}
                    className="py-12 text-center text-sm text-muted-foreground"
                  >
                    No users match these filters.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <AdminPagination page={page} pages={pages} total={total} onPageChange={onPageChange} />

      <UserDetailDialog
        userId={detailUserId}
        open={!!detailUserId}
        onClose={() => setDetailUserId(null)}
      />

      <AlertDialog
        open={!!userToDelete}
        onOpenChange={(open) => !open && setUserToDelete(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this user?</AlertDialogTitle>
            <AlertDialogDescription>
              &quot;{userToDelete?.first_name} {userToDelete?.last_name}&quot;
              ({userToDelete?.email}) will be deactivated and unable to sign in.
              Their data is retained for record keeping.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-red-600 hover:bg-red-700"
              disabled={deleteUser.isPending}
              onClick={async () => {
                if (!userToDelete) return;
                await runAction(
                  deleteUser.mutateAsync({ userId: userToDelete.id }),
                  'User deactivated'
                );
                setUserToDelete(null);
              }}
            >
              {deleteUser.isPending ? 'Deleting…' : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

function DetailRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 py-1.5">
      <dt className="shrink-0 text-sm text-muted-foreground">{label}</dt>
      <dd className="text-right text-sm font-medium">{value}</dd>
    </div>
  );
}

function UserDetailDialog({
  userId,
  open,
  onClose,
}: {
  userId: string | null;
  open: boolean;
  onClose: () => void;
}) {
  const { data: user, isLoading } = useUserDetail(open ? userId : null);

  return (
    <Dialog open={open} onOpenChange={(next) => !next && onClose()}>
      <DialogContent className="max-w-lg overflow-y-auto max-h-[85vh]">
        <DialogHeader>
          <DialogTitle>User details</DialogTitle>
          <DialogDescription>
            {user ? `${user.first_name} ${user.last_name}` : 'Loading…'}
          </DialogDescription>
        </DialogHeader>

        {isLoading || !user ? (
          <div className="space-y-2 py-2">
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-2/3" />
          </div>
        ) : (
          <div className="space-y-4">
            <dl>
              <DetailRow label="Email" value={user.email} />
              <DetailRow label="Phone" value={user.phone ?? '—'} />
              <DetailRow label="Role" value={ROLE_LABELS[user.role]} />
              <DetailRow
                label="Status"
                value={user.is_active ? 'Active' : 'Blocked'}
              />
              <DetailRow
                label="Verified"
                value={user.is_verified ? 'Yes' : 'No'}
              />
              <DetailRow
                label="Joined"
                value={format(new Date(user.created_at), 'MMM d, yyyy HH:mm')}
              />
              <DetailRow
                label="Last login"
                value={
                  user.last_login
                    ? format(new Date(user.last_login), 'MMM d, yyyy HH:mm')
                    : 'Never'
                }
              />
            </dl>

            {user.job_seeker_profile && (
              <>
                <Separator />
                <div>
                  <h4 className="mb-2 text-sm font-semibold">Job seeker profile</h4>
                  <dl>
                    <DetailRow
                      label="Title"
                      value={user.job_seeker_profile.title ?? '—'}
                    />
                    <DetailRow
                      label="Experience"
                      value={
                        user.job_seeker_profile.experience_years != null
                          ? `${user.job_seeker_profile.experience_years} years`
                          : '—'
                      }
                    />
                    <DetailRow
                      label="City"
                      value={user.job_seeker_profile.city ?? '—'}
                    />
                  </dl>
                </div>
              </>
            )}

            {user.companies.length > 0 && (
              <>
                <Separator />
                <div>
                  <h4 className="mb-2 text-sm font-semibold">Owned companies</h4>
                  <ul className="space-y-1">
                    {user.companies.map((company) => (
                      <li key={company.id} className="text-sm">
                        {company.name}
                        {company.is_verified && (
                          <BadgeCheck className="ml-1 inline size-3.5 text-emerald-600" />
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              </>
            )}

            {Object.keys(user.application_stats ?? {}).length > 0 && (
              <>
                <Separator />
                <div>
                  <h4 className="mb-2 text-sm font-semibold">Application stats</h4>
                  <p className="text-sm text-muted-foreground">
                    {Object.entries(user.application_stats)
                      .map(([key, value]) => `${key.replace(/_/g, ' ')}: ${value}`)
                      .join(' · ')}
                  </p>
                </div>
              </>
            )}

            {Object.keys(user.job_stats ?? {}).length > 0 && (
              <>
                <Separator />
                <div>
                  <h4 className="mb-2 text-sm font-semibold">Job stats</h4>
                  <p className="text-sm text-muted-foreground">
                    {Object.entries(user.job_stats)
                      .map(([key, value]) => `${key.replace(/_/g, ' ')}: ${value}`)
                      .join(' · ')}
                  </p>
                </div>
              </>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
