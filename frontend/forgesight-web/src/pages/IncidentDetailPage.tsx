import React from 'react';
import { Link, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getIncident, startInvestigation } from '@/api/endpoints/incidents';
import { useAuth } from '@/contexts/AuthContext';
import { Card } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorBanner } from '@/components/ui/ErrorBanner';
import { Button } from '@/components/ui/Button';
import { IncidentStatusBadge } from '@/components/incidents/IncidentStatusBadge';
import { StatusUpdateForm } from '@/components/incidents/StatusUpdateForm';
import { SignOffForm } from '@/components/incidents/SignOffForm';
import { InspectionUploadForm } from '@/components/vision/InspectionUploadForm';
import { DocumentSearchPanel } from '@/components/documents/DocumentSearchPanel';

const STATUS_UPDATE_ROLES = ['quality_engineer', 'quality_manager'];
const SIGN_OFF_ROLES = ['quality_engineer'];
const EVIDENCE_SUBMIT_ROLES = ['production_operator', 'quality_engineer'];

export function IncidentDetailPage() {
  const { incidentId } = useParams<{ incidentId: string }>();
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const { data: incident, isLoading, error } = useQuery({
    queryKey: ['incident', incidentId],
    queryFn: () => getIncident(incidentId!),
    enabled: !!incidentId,
  });

  const startInvestigationMutation = useMutation({
    mutationFn: () => startInvestigation(incidentId!),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['incident', incidentId] }),
  });

  if (isLoading) return <LoadingSpinner label="Loading incident…" />;
  if (error) return <ErrorBanner error={error} />;
  if (!incident) return null;

  const canStartInvestigation = incident.current_stage < 9 && user?.role === 'quality_engineer';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{incident.incident_id}</h1>
          <p className="text-slate-600">
            {incident.defect_type}
            {incident.component_designator && ` · ${incident.component_designator}`}
          </p>
        </div>
        <IncidentStatusBadge status={incident.status} />
      </div>

      <Card>
        <p className="mb-2 text-sm text-slate-700">{incident.description}</p>
        <dl className="grid grid-cols-2 gap-2 text-sm text-slate-500">
          <div><dt className="inline font-medium">Board:</dt> <dd className="inline">{incident.board_id}</dd></div>
          <div><dt className="inline font-medium">Batch:</dt> <dd className="inline">{incident.batch_id}</dd></div>
          <div><dt className="inline font-medium">Line:</dt> <dd className="inline">{incident.line_id}</dd></div>
          <div><dt className="inline font-medium">Stage:</dt> <dd className="inline">{incident.current_stage} of 12</dd></div>
        </dl>
        <div className="mt-4 flex gap-2">
          {canStartInvestigation && (
            <Button onClick={() => startInvestigationMutation.mutate()} isLoading={startInvestigationMutation.isPending}>
              Start Investigation
            </Button>
          )}
          <Link to={`/incidents/${incident.incident_id}/investigation`}>
            <Button variant="secondary">View Investigation Workspace</Button>
          </Link>
        </div>
        {startInvestigationMutation.isError && <div className="mt-2"><ErrorBanner error={startInvestigationMutation.error} /></div>}
      </Card>

      {user && EVIDENCE_SUBMIT_ROLES.includes(user.role) && (
        <Card>
          <h2 className="mb-3 font-semibold">Upload AOI Inspection Image</h2>
          <InspectionUploadForm boardId={incident.board_id} />
        </Card>
      )}

      <Card>
        <h2 className="mb-3 font-semibold">Search Technical SOPs</h2>
        <DocumentSearchPanel />
      </Card>

      {user && STATUS_UPDATE_ROLES.includes(user.role) && (
        <Card>
          <h2 className="mb-3 font-semibold">Update Status</h2>
          <StatusUpdateForm incidentId={incident.incident_id} currentStatus={incident.status} />
        </Card>
      )}

      {user && SIGN_OFF_ROLES.includes(user.role) && incident.status !== 'closed' && (
        <SignOffForm incidentId={incident.incident_id} />
      )}
    </div>
  );
}