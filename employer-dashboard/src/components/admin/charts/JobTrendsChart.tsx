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
import type { GrowthPoint } from '@/types/admin';

interface JobTrendsChartProps {
  data?: GrowthPoint[];
  isLoading?: boolean;
}

export function JobTrendsChart({ data, isLoading }: JobTrendsChartProps) {
  const points = (data ?? []).map((p) => ({
    date: new Date(p.date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    }),
    count: p.count,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Job Postings (last 30 days)</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-64 w-full" />
        ) : points.length === 0 ? (
          <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
            No job posting data yet
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={256}>
            <BarChart data={points} margin={{ top: 4, right: 8, bottom: 0, left: -16 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11 }}
                interval="preserveStartEnd"
                minTickGap={24}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                allowDecimals={false}
                tick={{ fontSize: 11 }}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip />
              <Bar
                dataKey="count"
                name="New jobs"
                fill="hsl(var(--primary))"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
