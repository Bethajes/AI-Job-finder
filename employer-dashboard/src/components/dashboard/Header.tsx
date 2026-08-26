'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Briefcase,
  ChevronDown,
  LayoutDashboard,
  LogOut,
  Settings,
  User,
  Users,
} from 'lucide-react';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useAuth } from '@/hooks/useAuth';

const pageTitles: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/jobs': 'Jobs',
  '/jobs/new': 'Post New Job',
  '/applicants': 'Applicants',
  '/profile': 'Company Profile',
  '/settings': 'Settings',
};

export function Header() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const title =
    pageTitles[pathname] ??
    (pathname.includes('/edit') ? 'Edit Job' : 'Dashboard');

  const initials = user
    ? `${user.first_name[0] ?? ''}${user.last_name[0] ?? ''}`.toUpperCase()
    : '?';

  return (
    <header className="flex h-16 items-center justify-between border-b bg-background px-6">
      <h2 className="text-lg font-semibold">{title}</h2>

      <div className="flex items-center gap-3">
        <nav className="hidden items-center gap-1 lg:flex xl:hidden">
          {[
            { href: '/dashboard', icon: LayoutDashboard },
            { href: '/jobs', icon: Briefcase },
            { href: '/applicants', icon: Users },
          ].map((item) => (
            <Button key={item.href} variant="ghost" size="icon" asChild>
              <Link href={item.href} aria-label={item.href}>
                <item.icon className="size-4" />
              </Link>
            </Button>
          ))}
        </nav>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-2 rounded-full focus-visible:outline-2">
              <Avatar className="size-8">
                <AvatarFallback className="text-xs">{initials}</AvatarFallback>
              </Avatar>
              <ChevronDown className="size-4 text-muted-foreground" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>
              <p>{user ? `${user.first_name} ${user.last_name}` : 'Account'}</p>
              <p className="text-xs font-normal text-muted-foreground">
                {user?.email}
              </p>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link href="/profile">
                <User className="size-4" /> Company Profile
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link href="/settings">
                <Settings className="size-4" /> Settings
              </Link>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => void logout()}>
              <LogOut className="size-4" /> Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
