import React from 'react';
import { Card } from '@/components/ui/Card';
import { RootCauseHypothesis } from '@/types/incidents';

/** Renders ONLY reasoning_summary/conclusion — the already-summarized,
 * backend-produced fields. No code path here can render a raw agent/LLM
 * response object (Mandatory Rule 3). */
export function HypothesisCard({ hypothesis }: { hypothesis: RootCauseHypothesis }) {
  return (
    <Card>
      <div className="flex items-center justify-between">
        <p className="font-semibold">Rank {hypothesis.rank}</p>
        <span className="text-sm text-slate-500">{Math.round(hypothesis.confidence_level * 100)}% confidence</span>
      </div>
      <p className="mt-2 font-medium">{hypothesis.conclusion}</p>
      <p className="mt-2 text-sm text-slate-600">{hypothesis.reasoning_summary}</p>
      {hypothesis.supporting_evidence_refs.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {hypothesis.supporting_evidence_refs.map((ref) => (
            <span key={ref} className="rounded bg-green-100 px-2 py-0.5 text-xs text-green-800">
              supports: {ref}
            </span>
          ))}
        </div>
      )}
      {hypothesis.contradicting_evidence_refs.length > 0 && (
        <div className="mt-1 flex flex-wrap gap-1">
          {hypothesis.contradicting_evidence_refs.map((ref) => (
            <span key={ref} className="rounded bg-red-100 px-2 py-0.5 text-xs text-red-800">
              contradicts: {ref}
            </span>
          ))}
        </div>
      )}
    </Card>
  );
}