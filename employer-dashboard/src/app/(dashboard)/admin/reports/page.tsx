'use client';

import { useState } from 'react';
import {
  Activity,
  BarChart3,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  useActivityReport,
  useJobPerformanceReport,
  useJobStats,
  useUserStats,
} from '@/hooks/useAdmin';
import { ActivityReport } from '@/components/admin/ActivityReport';
import { JobPerformanceReport } from '@/components/admin/JobPerformanceReport';
import { UserGrowthChart } from '@/components/admin/charts/UserGrowthChart';
import { JobTrendsChart } from '@/components/admin/charts/JobTrendsChart';

type RangeKey = '30d' | '7d';

export default function ReportsPage() {
  // The API currently exposes fixed reporting windows (30d growth series);
  // the selector narrows the charts client-side until range params exist.
  const [range, setRange] = useState<RangeKey>('30d');

  const { data: userStats, isLoading: userStatsLoading } = useUserStats();
  const { data: jobStats, isLoading: jobStatsLoading } = useJobStats();
  const activityQuery = useActivityReport();
  const performanceQuery = useJobPerformanceReport();

  const sliceForRange = <T extends { date: string }>(points?: T[]): T[] | undefined =>
    points ? (range === '7d' ? points.slice(-7) : points) : undefined;

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold">Reports &amp; Analytics</h1>
        <Select value={range} onValueChange={(value) => setRange(value as RangeKey)}>
          <SelectTrigger className="w-40" aria-label="Report range">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="30d">Last 30 days</SelectItem>
            <SelectItem value="7d">Last 7 days</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-6">
        <div className="grid gap-6 lg:grid-cols-2">
          <UserGrowthChart
            data={sliceForRange(userStats?.growth_daily)}
            isLoading={userStatsLoading}
          />
          <JobTrendsChart
            data={sliceForRange(jobStats?.posting_trend_daily)}
            isLoading={jobStatsLoading}
          />
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <div className="space-y-3">
            <h2 className="flex items-center gap-2 text-lg font-semibold">
              <Activity className="size-4" /> Engagement
            </h2>
            <ActivityReport
              data={activityQuery.data}
              isLoading={activityQuery.isLoading}
            />
          </div>
          <div className="space-y-3">
            <h2 className="flex items-center gap-2 text-lg font-semibold">
              <BarChart3 className="size-4" /> Job performance
            </h2>
            <JobPerformanceReport
              data={performanceQuery.data}
              isLoading={performanceQuery.isLoading}
            />
          </div>
        </div>

        {/* Application trends */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Application trends</CardTitle>
          </CardHeader>
          <CardContent>
            {activityQuery.isLoading || jobStatsLoading ? (
              <Skeleton className="h-24 w-full" />
            ) : (
              <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <div className="rounded-lg border px-3 py-2">
                  <dt className="text-sm text-muted-foreground">Applications (24h)</dt>
                  <dd className="text-xl font-bold tabular-nums">
                    {activityQuery.data?.applications_last_24h ?? 0}
                  </dd>
                </div>
                <div className="rounded-lg border px-3 py-2">
                  <dt className="text-sm text-muted-foreground">Applications (7d)</dt>
                  <dd className="text-xl font-bold tabular-nums">
                    {activityQuery.data?.applications_last_7d ?? 0}
                  </dd>
                </div>
                <div className="rounded-lg border px-3 py-2">
                  <dt className="text-sm text-muted-foreground">Avg / job</dt>
                  <dd className="text-xl font-bold tabular-nums">
                    {(jobStats?.average_applications_per_job ?? 0).toFixed(1)}
                  </dd>
                </div>
                <div className="rounded-lg border px-3 py-2">
                  <dt className="text-sm text-muted-foreground">Top category</dt>
                  <dd className="truncate text-sm font-semibold">
                    {jobStats?.popular_categories?.[0]?.category ?? '—'}
                  </dd>
                </div>
              </dl>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
