'use client';

import { usePathname } from 'next/navigation';
import { Sidebar } from '@/components/dashboard/Sidebar';
import { Header } from '@/components/dashboard/Header';

/**
 * Employer dashboard chrome. Admin routes (/admin/*) render their own
 * layout (see app/(dashboard)/admin/layout.tsx), so they bypass this shell.
 */
export function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  if (pathname.startsWith('/admin')) {
    return <>{children}</>;
  }

  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto p-6 bg-slate-50">{children}</main>
      </div>
    </div>
  );
}
