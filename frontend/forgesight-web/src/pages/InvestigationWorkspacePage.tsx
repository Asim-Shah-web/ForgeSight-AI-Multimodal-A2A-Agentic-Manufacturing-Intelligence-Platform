import React from 'react';
import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getInvestigationStatus } from '@/api/endpoints/incidents';
import { Card } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorBanner } from '@/components/ui/ErrorBanner';
import { Badge } from '@/components/ui/Badge';
import { StageProgressBar } from '@/components/investigation/StageProgressBar';
import { EvidenceSummaryPanel } from '@/components/investigation/EvidenceSummaryPanel';
import { ApprovalGatePanel } from '@/components/investigation/ApprovalGatePanel';

const ACTIVE_STATUSES = new Set(['in_progress']);

export function InvestigationWorkspacePage() {
  const { incidentId } = useParams<{ incidentId: string }>();

  const { data, isLoading, error } = useQuery({
    queryKey: ['investigation-status', incidentId],
    queryFn: () => getInvestigationStatus(incidentId!),
    enabled: !!incidentId,
    refetchInterval: (query) => (ACTIVE_STATUSES.has(query.state.data?.status ?? '') ? 4000 : false),
    refetchIntervalInBackground: false,
  });

  if (isLoading) return <LoadingSpinner label="Loading investigation status…" />;
  if (error) return <ErrorBanner error={error} />;
  if (!data) return null;

  const pendingApproval = data.pending_approvals.find((a) => a.status === 'pending');

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Investigation: {data.incident_id}</h1>
        <Badge
          label={data.status.replace(/_/g, ' ')}
          colorClass={
            data.status === 'complete'
              ? 'bg-green-600 text-white'
              : data.status === 'failed'
                ? 'bg-red-600 text-white'
                : data.status === 'awaiting_approval'
                  ? 'bg-amber-600 text-white'
                  : 'bg-blue-600 text-white'
          }
        />
      </div>

      {data.status === 'in_progress' && (
        <Card>
          <LoadingSpinner label={`Investigation running — currently at Stage ${data.current_stage}…`} />
        </Card>
      )}

      {data.status === 'complete' && (
        <Card className="border-green-300 bg-green-50">
          <p className="font-medium text-green-800">Investigation complete.</p>
          <p className="mt-1 text-sm text-green-700">
            Report details are included in this investigation's final evidence and hypothesis records above.
          </p>
        </Card>
      )}

      {data.status === 'failed' && (
        <Card className="border-red-300 bg-red-50">
          <p className="font-medium text-red-800">Investigation halted — a gate was rejected.</p>
          <Link to={`/incidents/${data.incident_id}`} className="mt-2 inline-block text-sm text-red-700 underline">
            Return to incident to re-gather evidence
          </Link>
        </Card>
      )}

      <Card>
        <h2 className="mb-3 font-semibold">Workflow Progress</h2>
        <StageProgressBar currentStage={data.current_stage} completedStages={data.completed_stages} />
      </Card>

      <div>
        <h2 className="mb-3 font-semibold">Evidence Gathered</h2>
        <EvidenceSummaryPanel summary={data.evidence_graph_summary} />
      </div>

      {pendingApproval && <ApprovalGatePanel incidentId={data.incident_id} approval={pendingApproval} />}
    </div>
  );
}