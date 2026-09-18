import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { listIncidents } from '@/api/endpoints/incidents';
import { IncidentStatus } from '@/types/incidents';
import { Card } from '@/components/ui/Card';
import { EmptyState } from '@/components/ui/EmptyState';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorBanner } from '@/components/ui/ErrorBanner';
import { IncidentStatusBadge } from '@/components/incidents/IncidentStatusBadge';
import { IncidentFilterBar } from '@/components/incidents/IncidentFilterBar';

export function IncidentListPage() {
  const [status, setStatus] = useState<IncidentStatus | ''>('');
  const [lineId, setLineId] = useState('');

  const { data, isLoading, error } = useQuery({
    queryKey: ['incidents', status, lineId],
    queryFn: () => listIncidents({ status: status || undefined, line_id: lineId || undefined }),
  });

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold">Incidents</h1>
      <IncidentFilterBar status={status} lineId={lineId} onStatusChange={setStatus} onLineIdChange={setLineId} />

      {isLoading && <LoadingSpinner label="Loading incidents…" />}
      {error && <ErrorBanner error={error} />}

      {data && data.items.length === 0 && (
        <EmptyState title="No incidents match these filters" description="Try clearing the status or line filter." />
      )}

      {data && data.items.length > 0 && (
        <div className="space-y-3">
          {data.items.map((incident) => (
            <Link key={incident.incident_id} to={`/incidents/${incident.incident_id}`}>
              <Card className="hover:border-blue-400 transition-colors">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold">{incident.incident_id}</p>
                    <p className="text-sm text-slate-600">
                      {incident.defect_type}
                      {incident.component_designator && ` · ${incident.component_designator}`}
                    </p>
                    <p className="mt-1 text-xs text-slate-400">
                      Stage {incident.current_stage} of 12 · Created {new Date(incident.created_at).toLocaleString()}
                    </p>
                  </div>
                  <IncidentStatusBadge status={incident.status} />
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}