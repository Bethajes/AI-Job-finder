'use client';

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import type { GrowthPoint } from '@/types/admin';

interface UserGrowthChartProps {
  data?: GrowthPoint[];
  isLoading?: boolean;
}

export function UserGrowthChart({ data, isLoading }: UserGrowthChartProps) {
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
        <CardTitle className="text-base">New Users (last 30 days)</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-64 w-full" />
        ) : points.length === 0 ? (
          <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
            No sign-up data yet
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={256}>
            <AreaChart data={points} margin={{ top: 4, right: 8, bottom: 0, left: -16 }}>
              <defs>
                <linearGradient id="userGrowthFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                </linearGradient>
              </defs>
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
              <Area
                type="monotone"
                dataKey="count"
                name="Sign-ups"
                stroke="hsl(var(--primary))"
                strokeWidth={2}
                fill="url(#userGrowthFill)"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
