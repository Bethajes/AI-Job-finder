'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const router = useRouter();

  useEffect(() => {
    // Surface to console / Sentry in production.
    console.error(error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-4 text-center">
      <h2 className="text-2xl font-bold mb-2">Something went wrong!</h2>
      <p className="text-gray-600 mb-1 max-w-md">
        {error.message || 'An unexpected error occurred while loading this page.'}
      </p>
      {error.digest && (
        <p className="mb-4 text-xs text-muted-foreground">Ref: {error.digest}</p>
      )}
      <div className="flex gap-3">
        <Button onClick={reset}>Try again</Button>
        <Button variant="outline" onClick={() => router.push('/')}>
          Go home
        </Button>
      </div>
    </div>
  );
}
