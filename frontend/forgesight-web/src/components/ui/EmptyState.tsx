import React from 'react';

export function EmptyState({ title, description }: { title: string; description?: string }) {
  return (
    <div className="rounded-md border border-dashed border-slate-300 p-6 text-center text-slate-500">
      <p className="font-medium">{title}</p>
      {description && <p className="mt-1 text-sm">{description}</p>}
    </div>
  );
}