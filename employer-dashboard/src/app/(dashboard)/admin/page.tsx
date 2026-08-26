'use client';
import { useAdminStats, useJobStats, useUserStats } from '@/hooks/useAdmin';
import { StatsCards } from '@/components/admin/StatsCards';
import { UserGrowthChart } from '@/components/admin/charts/UserGrowthChart';
import { JobTrendsChart } from '@/components/admin/charts/JobTrendsChart';

export default function AdminDashboard() {
  const { data: stats, isLoading } = useAdminStats();
  const { data: userStats, isLoading: userStatsLoading } = useUserStats();
  const { data: jobStats, isLoading: jobStatsLoading } = useJobStats();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Admin Dashboard</h1>
        {stats && (
          <p className="text-sm text-muted-foreground">
            Last refreshed{' '}
            {new Date(stats.generated_at).toLocaleTimeString('en-US', {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </p>
        )}
      </div>
      <StatsCards stats={stats} isLoading={isLoading} />
      <div className="grid gap-6 lg:grid-cols-2">
        <UserGrowthChart
          data={userStats?.growth_daily}
          isLoading={userStatsLoading}
        />
        <JobTrendsChart
          data={jobStats?.posting_trend_daily}
          isLoading={jobStatsLoading}
        />
      </div>
    </div>
  );
}
