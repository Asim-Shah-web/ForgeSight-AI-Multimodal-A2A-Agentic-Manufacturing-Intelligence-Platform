import React from 'react';
import { Card } from '@/components/ui/Card';

export function CorrectiveActionCard({
  proposedAction,
  supportingEvidenceRefs,
}: {
  proposedAction: string;
  supportingEvidenceRefs: string[];
}) {
  return (
    <Card>
      <p className="font-medium">{proposedAction}</p>
      {supportingEvidenceRefs.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {supportingEvidenceRefs.map((ref) => (
            <span key={ref} className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-700">
              {ref}
            </span>
          ))}
        </div>
      )}
    </Card>
  );
}