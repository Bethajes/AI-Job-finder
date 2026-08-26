import { Badge } from '@/components/ui/badge';
import type { ApplicationStatus } from '@/types';

const statusStyles: Record<ApplicationStatus, string> = {
  applied: 'bg-blue-100 text-blue-800 hover:bg-blue-100',
  viewed: 'bg-indigo-100 text-indigo-800 hover:bg-indigo-100',
  shortlisted: 'bg-purple-100 text-purple-800 hover:bg-purple-100',
  interviewed: 'bg-amber-100 text-amber-800 hover:bg-amber-100',
  offered: 'bg-teal-100 text-teal-800 hover:bg-teal-100',
  hired: 'bg-green-100 text-green-800 hover:bg-green-100',
  rejected: 'bg-red-100 text-red-800 hover:bg-red-100',
  withdrawn: 'bg-slate-200 text-slate-600 hover:bg-slate-200',
};

export function StatusBadge({ status }: { status: ApplicationStatus }) {
  return (
    <Badge variant="secondary" className={`capitalize ${statusStyles[status]}`}>
      {status}
    </Badge>
  );
}
