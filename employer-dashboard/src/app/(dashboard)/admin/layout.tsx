import { requireAdmin } from '@/lib/auth';
import { AdminSidebar } from '@/components/admin/AdminSidebar';

export const metadata = {
  title: 'Admin Console | Ethiopian Jobs',
};

export default async function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  await requireAdmin(); // Redirect if not admin
  return (
    <div className="flex h-screen">
      <AdminSidebar />
      <main className="flex-1 overflow-y-auto p-6 bg-slate-50">{children}</main>
    </div>
  );
}
