import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4 text-center">
      <p className="text-sm font-semibold text-primary">404</p>
      <h1 className="mt-2 text-2xl font-bold">Page not found</h1>
      <p className="mt-1 max-w-md text-gray-600">
        The page you are looking for doesn&apos;t exist or has been moved.
      </p>
      <Button asChild className="mt-6">
        <Link href="/dashboard">Back to dashboard</Link>
      </Button>
    </div>
  );
}
