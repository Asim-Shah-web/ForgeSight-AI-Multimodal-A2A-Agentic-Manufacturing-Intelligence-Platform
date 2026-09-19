import React from 'react';
import { Badge } from '@/components/ui/Badge';

interface CvFindingCardProps {
  defectType: string;
  componentDesignator: string | null;
  confidence: number;
  modelVersion: string;
  /** Mandatory Rule 7: required, not optional — omitting this disclosure
   * is a TypeScript compile error, not a possible runtime oversight. */
  datasetUsedForTraining: string;
}

export function CvFindingCard({
  defectType,
  componentDesignator,
  confidence,
  modelVersion,
  datasetUsedForTraining,
}: CvFindingCardProps) {
  return (
    <div className="rounded-md border border-slate-200 p-3">
      <div className="flex items-center justify-between">
        <p className="font-medium">
          {defectType.replace(/_/g, ' ')}
          {componentDesignator && <span className="text-slate-500"> · {componentDesignator}</span>}
        </p>
        <Badge label={`${Math.round(confidence * 100)}% confidence`} colorClass="bg-blue-100 text-blue-800" />
      </div>
      <p className="mt-1 text-xs text-slate-500">Model: {modelVersion}</p>
      <p data-testid="dataset-disclosure" className="mt-1 text-xs font-medium text-amber-700">
        Model trained on: {datasetUsedForTraining}
      </p>
    </div>
  );
}