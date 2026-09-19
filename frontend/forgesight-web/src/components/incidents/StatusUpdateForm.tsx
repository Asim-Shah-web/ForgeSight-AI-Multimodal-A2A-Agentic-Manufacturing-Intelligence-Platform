import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { updateIncidentStatus } from '@/api/endpoints/incidents';
import { IncidentStatus } from '@/types/incidents';
import { Button } from '@/components/ui/Button';
import { ErrorBanner } from '@/components/ui/ErrorBanner';

const STATUSES: IncidentStatus[] = ['open', 'in_progress', 'awaiting_approval', 'closed', 'escalated'];

export function StatusUpdateForm({ incidentId, currentStatus }: { incidentId: string; currentStatus: IncidentStatus }) {
  const [status, setStatus] = useState<IncidentStatus>(currentStatus);
  const [reason, setReason] = useState('');
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => updateIncidentStatus(incidentId, { status, reason: reason || null }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['incident', incidentId] }),
  });

  return (
    <div className="flex flex-col gap-2">
      {mutation.isError && <ErrorBanner error={mutation.error} />}
      <div className="flex gap-2">
        <select
          aria-label="New status"
          className="rounded-md border border-slate-300 px-3 py-2 text-sm"
          value={status}
          onChange={(e) => setStatus(e.target.value as IncidentStatus)}
        >
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s.replace(/_/g, ' ')}
            </option>
          ))}
        </select>
        <input
          aria-label="Reason for status change"
          placeholder="Reason (optional)"
          className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
        />
        <Button onClick={() => mutation.mutate()} isLoading={mutation.isPending}>
          Update Status
        </Button>
      </div>
    </div>
  );
}