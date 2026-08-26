'use client';

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
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
import type { JobPerformanceReport as JobPerformanceReportData } from '@/types/admin';

interface JobPerformanceReportProps {
  data?: JobPerformanceReportData;
  isLoading: boolean;
}

export function JobPerformanceReport({ data, isLoading }: JobPerformanceReportProps) {
  if (isLoading || !data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Job performance</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-2/3" />
        </CardContent>
      </Card>
    );
  }

  const categoryData = (data.jobs_by_industry ?? {})
    ? Object.entries(data.jobs_by_industry)
        .map(([industry, count]) => ({ industry, count }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 8)
    : [];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Job performance</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-2">
          <div className="rounded-lg border px-3 py-2">
            <p className="text-sm text-muted-foreground">Avg. applications / job</p>
            <p className="text-xl font-bold tabular-nums">
              {data.average_applications_per_job.toFixed(1)}
            </p>
          </div>
          <div className="rounded-lg border px-3 py-2">
            <p className="text-sm text-muted-foreground">Avg. days to fill</p>
            <p className="text-xl font-bold tabular-nums">
              {data.average_days_to_fill != null
                ? `${data.average_days_to_fill.toFixed(0)} days`
                : '—'}
            </p>
          </div>
        </div>

        <div>
          <h4 className="mb-2 text-sm font-semibold">Top jobs by applications</h4>
          {data.top_jobs_by_applications.length === 0 ? (
            <p className="py-4 text-center text-sm text-muted-foreground">
              No application data yet
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Job</TableHead>
                  <TableHead>Company</TableHead>
                  <TableHead className="text-right">Applications</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.top_jobs_by_applications.slice(0, 5).map((job) => (
                  <TableRow key={job.job_id}>
                    <TableCell className="max-w-[200px] truncate font-medium">
                      {job.title}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {job.company_name ?? '—'}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {job.applications_count}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </div>

        <div>
          <h4 className="mb-2 text-sm font-semibold">Jobs by industry</h4>
          {categoryData.length === 0 ? (
            <p className="py-4 text-center text-sm text-muted-foreground">
              No industry data yet
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart
                data={categoryData}
                layout="vertical"
                margin={{ top: 0, right: 16, bottom: 0, left: 8 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11 }} />
                <YAxis
                  type="category"
                  dataKey="industry"
                  width={110}
                  tick={{ fontSize: 11 }}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip />
                <Bar
                  dataKey="count"
                  name="Jobs"
                  fill="hsl(var(--primary))"
                  radius={[0, 4, 4, 0]}
                  barSize={16}
                />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
