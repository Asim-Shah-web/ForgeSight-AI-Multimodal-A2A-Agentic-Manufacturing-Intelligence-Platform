import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { resumeInvestigation } from '@/api/endpoints/incidents';
import { PendingApproval } from '@/types/incidents';
import { useAuth } from '@/contexts/AuthContext';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { ErrorBanner } from '@/components/ui/ErrorBanner';
import { HypothesisCard } from './HypothesisCard';
import { CorrectiveActionCard } from './CorrectiveActionCard';

const ROLE_LABEL_MAP: Record<string, string> = {
  'Quality Engineer': 'quality_engineer',
  'Maintenance Engineer': 'maintenance_engineer',
  'Quality Manager': 'quality_manager',
};

export function ApprovalGatePanel({ incidentId, approval }: { incidentId: string; approval: PendingApproval }) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [pendingDecision, setPendingDecision] = useState<'approve' | 'reject' | null>(null);
  const [notes, setNotes] = useState('');

  const mutation = useMutation({
    mutationFn: (approved: boolean) => resumeInvestigation(incidentId, { approved, notes }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['investigation-status', incidentId] });
      setPendingDecision(null);
      setNotes('');
    },
  });

  const requiredRoleValue = ROLE_LABEL_MAP[approval.requires_approval_by];
  const userCanAct = user && requiredRoleValue && user.role === requiredRoleValue;

  const gateTitle =
    approval.gate === 'hypothesis_confirmation' ? 'Confirm Root-Cause Hypothesis' : 'Approve Corrective Action';

  return (
    <Card className="border-amber-300">
      <h3 className="mb-1 font-semibold">{gateTitle}</h3>
      <p className="mb-3 text-xs text-slate-500">Requires approval by: {approval.requires_approval_by}</p>

      {approval.gate === 'hypothesis_confirmation' &&
        approval.hypotheses?.map((h) => <HypothesisCard key={h.rank} hypothesis={h} />)}

      {approval.gate === 'corrective_action_approval' && approval.proposed_action && (
        <CorrectiveActionCard
          proposedAction={approval.proposed_action}
          supportingEvidenceRefs={approval.supporting_evidence_refs ?? []}
        />
      )}

      {!userCanAct && (
        <p className="mt-3 text-sm text-slate-500">
          Only a {approval.requires_approval_by} can act on this gate. You are viewing it read-only.
        </p>
      )}

      {userCanAct && (
        <div className="mt-4 flex gap-2">
          <Button variant="primary" onClick={() => setPendingDecision('approve')}>
            Confirm
          </Button>
          <Button variant="danger" onClick={() => setPendingDecision('reject')}>
            Reject
          </Button>
        </div>
      )}

      <Modal
        isOpen={pendingDecision !== null}
        title={pendingDecision === 'approve' ? 'Confirm this decision?' : 'Reject this decision?'}
        onClose={() => setPendingDecision(null)}
      >
        <p className="mb-3 text-sm text-slate-600">
          {pendingDecision === 'approve'
            ? 'This will advance the investigation to the next stage.'
            : 'This will route the investigation back for re-evaluation.'}
        </p>
        {mutation.isError && <div className="mb-3"><ErrorBanner error={mutation.error} /></div>}
        <label htmlFor="resume-notes" className="mb-1 block text-sm font-medium">
          Notes (required)
        </label>
        <textarea
          id="resume-notes"
          required
          rows={3}
          className="mb-3 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Explain the basis for this decision…"
        />
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setPendingDecision(null)}>
            Cancel
          </Button>
          <Button
            variant={pendingDecision === 'approve' ? 'primary' : 'danger'}
            disabled={notes.trim().length === 0}
            isLoading={mutation.isPending}
            onClick={() => mutation.mutate(pendingDecision === 'approve')}
          >
            {pendingDecision === 'approve' ? 'Confirm' : 'Reject'}
          </Button>
        </div>
      </Modal>
    </Card>
  );
}