'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import type { UserActivityReport } from '@/types/admin';

interface ActivityReportProps {
  data?: UserActivityReport;
  isLoading: boolean;
}

export function ActivityReport({ data, isLoading }: ActivityReportProps) {
  if (isLoading || !data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">User activity</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-2/3" />
        </CardContent>
      </Card>
    );
  }

  const metrics = [
    { label: 'Daily active users', value: data.active_users_daily },
    { label: 'Weekly active users', value: data.active_users_weekly },
    { label: 'Monthly active users', value: data.active_users_monthly },
    { label: 'Applications (24h)', value: data.applications_last_24h },
    { label: 'Applications (7d)', value: data.applications_last_7d },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">User activity</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <dl className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {metrics.map((metric) => (
            <div
              key={metric.label}
              className="flex items-center justify-between rounded-lg border px-3 py-2"
            >
              <dt className="text-sm text-muted-foreground">{metric.label}</dt>
              <dd className="font-semibold tabular-nums">
                {metric.value.toLocaleString()}
              </dd>
            </div>
          ))}
        </dl>

        {data.most_active_users.length > 0 && (
          <div>
            <h4 className="mb-2 text-sm font-semibold">Most active applicants</h4>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.most_active_users.slice(0, 5).map((user) => (
                  <TableRow key={user.user_id}>
                    <TableCell className="font-medium">{user.full_name}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {user.email}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {user.activity_count}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}

        <p className="text-xs text-muted-foreground">{data.note}</p>
      </CardContent>
    </Card>
  );
}
