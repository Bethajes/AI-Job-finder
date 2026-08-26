'use client';

import {
  Activity,
  Briefcase,
  Building2,
  FileText,
  TrendingUp,
  UserCheck,
  Users,
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import type { DashboardStats } from '@/types/admin';

interface StatsCardsProps {
  stats?: DashboardStats;
  isLoading: boolean;
}

function StatCard({
  title,
  value,
  icon: Icon,
  sub,
}: {
  title: string;
  value: number | string;
  icon: React.ElementType;
  sub?: string;
}) {
  return (
    <Card>
      <CardContent className="flex items-start justify-between gap-2 p-4">
        <div className="min-w-0">
          <p className="truncate text-sm text-muted-foreground">{title}</p>
          <p className="text-2xl font-bold tabular-nums">{value}</p>
          {sub && (
            <p className="mt-1 truncate text-xs text-muted-foreground">{sub}</p>
          )}
        </div>
        <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary/10">
          <Icon className="size-4 text-primary" />
        </span>
      </CardContent>
    </Card>
  );
}

function formatBreakdown(map: Record<string, number>): string {
  return Object.entries(map)
    .map(([key, value]) => `${key.replace(/_/g, ' ')}: ${value}`)
    .join(' · ');
}

export function StatsCards({ stats, isLoading }: StatsCardsProps) {
  if (isLoading || !stats) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-24 w-full rounded-xl" />
        ))}
      </div>
    );
  }

  const jobsByStatus = stats.jobs_by_status ?? {};
  const companies = stats.companies_by_verification ?? {};

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <StatCard
        title="Total Users"
        value={stats.total_users.toLocaleString()}
        icon={Users}
        sub={formatBreakdown(stats.users_by_role)}
      />
      <StatCard
        title="Total Jobs"
        value={stats.total_jobs.toLocaleString()}
        icon={Briefcase}
        sub={`${jobsByStatus.published ?? 0} published · ${jobsByStatus.draft ?? 0} draft · ${jobsByStatus.closed ?? 0} closed`}
      />
      <StatCard
        title="Applications"
        value={stats.total_applications.toLocaleString()}
        icon={FileText}
        sub={formatBreakdown(stats.applications_by_status)}
      />
      <StatCard
        title="Companies"
        value={stats.total_companies.toLocaleString()}
        icon={Building2}
        sub={`${companies.approved ?? 0} verified · ${companies.pending ?? 0} pending verification`}
      />
      <StatCard
        title="New Users (Today)"
        value={(stats.active_users_24h ?? 0).toLocaleString()}
        icon={UserCheck}
        sub={`active in last 24h`}
      />
      <StatCard
        title="New Users (7 days)"
        value={stats.new_users_7d.toLocaleString()}
        icon={TrendingUp}
        sub={`${stats.new_users_30d} in the last 30 days`}
      />
      <StatCard
        title="Active Jobs"
        value={(jobsByStatus.published ?? 0).toLocaleString()}
        icon={Activity}
        sub={`${stats.new_jobs_7d} posted this week`}
      />
      <StatCard
        title="Active Users (7d)"
        value={stats.active_users_7d.toLocaleString()}
        icon={Users}
        sub="logged in within 7 days"
      />
    </div>
  );
}
