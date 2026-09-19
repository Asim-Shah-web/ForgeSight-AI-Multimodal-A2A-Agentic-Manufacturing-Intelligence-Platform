import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { inspectBoard } from '@/api/endpoints/vision';
import { Button } from '@/components/ui/Button';
import { ErrorBanner } from '@/components/ui/ErrorBanner';
import { EmptyState } from '@/components/ui/EmptyState';
import { CvFindingCard } from './CvFindingCard';

export function InspectionUploadForm({ boardId }: { boardId: string }) {
  const [file, setFile] = useState<File | null>(null);
  const mutation = useMutation({
    mutationFn: () => {
      if (!file) throw new Error('No file selected.');
      return inspectBoard(boardId, file);
    },
  });

  return (
    <div>
      <div className="flex items-center gap-3">
        <input
          type="file"
          accept="image/jpeg,image/png"
          aria-label="Upload AOI inspection image"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
        <Button onClick={() => mutation.mutate()} disabled={!file} isLoading={mutation.isPending}>
          Run Inspection
        </Button>
      </div>

      {mutation.isError && (
        <div className="mt-3">
          <ErrorBanner error={mutation.error} />
        </div>
      )}

      {mutation.isSuccess && (
        <div className="mt-4">
          <p className="mb-2 text-sm font-medium">
            {mutation.data.findings_count} finding(s) above the configured confidence threshold.
          </p>
          {mutation.data.findings_count === 0 ? (
            <EmptyState title="No defects detected above the confidence threshold." />
          ) : (
            <div className="space-y-2">
              {mutation.data.cv_findings.map((finding) => (
                <CvFindingCard
                  key={finding.cv_finding_id}
                  defectType={finding.defect_type}
                  componentDesignator={finding.component_designator}
                  confidence={finding.confidence}
                  modelVersion={finding.model_version}
                  datasetUsedForTraining={finding.dataset_used_for_training ?? 'Not disclosed'}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}