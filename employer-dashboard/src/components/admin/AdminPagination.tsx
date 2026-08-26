'use client';

import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface PaginationProps {
  page: number;
  pages: number;
  total?: number;
  onPageChange: (page: number) => void;
}

export function AdminPagination({
  page,
  pages,
  total,
  onPageChange,
}: PaginationProps) {
  if (pages <= 1) {
    return total !== undefined ? (
      <p className="py-3 text-sm text-muted-foreground">
        {total} result{total === 1 ? '' : 's'}
      </p>
    ) : null;
  }

  return (
    <div className="flex items-center justify-between py-3">
      <p className="text-sm text-muted-foreground">
        Page {page} of {pages}
        {total !== undefined && ` · ${total} results`}
      </p>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          <ChevronLeft className="size-4" /> Previous
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={page >= pages}
          onClick={() => onPageChange(page + 1)}
        >
          Next <ChevronRight className="size-4" />
        </Button>
      </div>
    </div>
  );
}
