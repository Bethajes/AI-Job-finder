'use client';

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { APPLICATION_STATUSES, type ApplicationStatus } from '@/types';

const statusOptions = APPLICATION_STATUSES;

export function StatusDropdown({
  applicationId,
  currentStatus,
  onUpdate,
  disabled,
}: {
  applicationId: string;
  currentStatus: ApplicationStatus;
  onUpdate: (applicationId: string, newStatus: ApplicationStatus) => void;
  disabled?: boolean;
}) {
  return (
    <Select
      value={currentStatus}
      disabled={disabled}
      onValueChange={(newStatus) =>
        onUpdate(applicationId, newStatus as ApplicationStatus)
      }
    >
      <SelectTrigger className="w-36 capitalize" size="sm" aria-label="Update status">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {statusOptions.map((status) => (
          <SelectItem key={status} value={status} className="capitalize">
            {status.charAt(0).toUpperCase() + status.slice(1)}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
