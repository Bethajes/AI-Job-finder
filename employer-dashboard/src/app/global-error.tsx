'use client';

/** Root-level fallback for errors thrown outside app/error.tsx boundaries. */
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body
        style={{
          fontFamily: 'system-ui, sans-serif',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          gap: '0.5rem',
        }}
      >
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700 }}>
          Something went wrong!
        </h2>
        <p style={{ color: '#555' }}>{error.message}</p>
        <button
          onClick={reset}
          style={{
            marginTop: '1rem',
            padding: '0.5rem 1rem',
            borderRadius: '0.5rem',
            background: '#111',
            color: '#fff',
            cursor: 'pointer',
          }}
        >
          Try again
        </button>
      </body>
    </html>
  );
}
