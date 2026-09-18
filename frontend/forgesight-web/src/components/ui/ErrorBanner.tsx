import React from 'react';
import { ApiError, isApiError } from '@/api/client';

export function ErrorBanner({ error }: { error: unknown }) {
  if (!error) return null;
  const message: string = isApiError(error) ? (error as ApiError).detail : 'An unexpected error occurred.';

  return (
    <div role="alert" className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800">
      {message}
    </div>
  );
}