'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  ArrowLeft,
  BarChart3,
  Briefcase,
  Building2,
  ClipboardList,
  LayoutDashboard,
  LogOut,
  Users,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/hooks/useAuth';

const navItems = [
  { href: '/admin', label: 'Overview', icon: LayoutDashboard, exact: true },
  { href: '/admin/users', label: 'Users Management', icon: Users },
  { href: '/admin/companies', label: 'Companies', icon: Building2 },
  { href: '/admin/jobs', label: 'Jobs Moderation', icon: Briefcase },
  { href: '/admin/reports', label: 'Reports & Analytics', icon: BarChart3 },
  { href: '/admin/audit-logs', label: 'Audit Logs', icon: ClipboardList },
];

export function AdminSidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="hidden w-64 flex-col border-r bg-slate-950 text-slate-100 md:flex">
      <div className="flex h-16 items-center gap-2 border-b border-slate-800 px-6">
        <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <BarChart3 className="size-4" />
        </span>
        <div>
          <p className="text-sm font-semibold leading-tight">Ethiopian Jobs</p>
          <p className="text-xs text-slate-400">Admin Console</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 p-3">
        {navItems.map((item) => {
          const isActive = item.exact
            ? pathname === item.href
            : pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              )}
            >
              <item.icon className="size-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-slate-800 p-3">
        <Link
          href="/dashboard"
          className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-slate-300 transition-colors hover:bg-slate-800 hover:text-white"
        >
          <ArrowLeft className="size-4" />
          Employer view
        </Link>
        <p className="truncate px-3 pb-1 pt-2 text-sm font-medium">
          {user ? `${user.first_name} ${user.last_name}` : '…'}
        </p>
        <p className="truncate px-3 pb-2 text-xs text-slate-400">
          {user?.email}
        </p>
        <button
          onClick={() => void logout()}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-slate-300 transition-colors hover:bg-slate-800 hover:text-white"
        >
          <LogOut className="size-4" />
          Sign out
        </button>
      </div>
    </aside>
  );
}
