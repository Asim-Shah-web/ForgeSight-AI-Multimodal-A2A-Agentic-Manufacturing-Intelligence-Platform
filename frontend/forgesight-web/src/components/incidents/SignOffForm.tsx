import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { approveIncident } from '@/api/endpoints/incidents';
import { Button } from '@/components/ui/Button';
import { ErrorBanner } from '@/components/ui/ErrorBanner';
import { Card } from '@/components/ui/Card';

export function SignOffForm({ incidentId }: { incidentId: string }) {
  const [statement, setStatement] = useState('');
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => approveIncident(incidentId, { approval_statement: statement }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['incident', incidentId] }),
  });

  const isBlank = statement.trim().length === 0;

  return (
    <Card>
      <h3 className="mb-2 font-semibold">Stage 11 — Sign Off & Close</h3>
      {mutation.isError && <ErrorBanner error={mutation.error} />}
      <textarea
        aria-label="Approval statement"
        placeholder="Explain the basis for sign-off (required)…"
        rows={3}
        className="mb-3 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
        value={statement}
        onChange={(e) => setStatement(e.target.value)}
      />
      <Button onClick={() => mutation.mutate()} disabled={isBlank} isLoading={mutation.isPending} variant="primary">
        Sign Off & Close
      </Button>
    </Card>
  );
}