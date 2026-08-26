import { Badge } from '@/components/ui/badge';
import type { JobStatus } from '@/types';

const statusStyles: Record<JobStatus, string> = {
  draft: 'bg-yellow-100 text-yellow-800 hover:bg-yellow-100',
  published: 'bg-green-100 text-green-800 hover:bg-green-100',
  closed: 'bg-slate-200 text-slate-700 hover:bg-slate-200',
  expired: 'bg-red-100 text-red-800 hover:bg-red-100',
};

export function JobStatusBadge({ status }: { status: JobStatus }) {
  return (
    <Badge variant="secondary" className={`capitalize ${statusStyles[status]}`}>
      {status}
    </Badge>
  );
}
