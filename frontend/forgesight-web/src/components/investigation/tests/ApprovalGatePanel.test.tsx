import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ApprovalGatePanel } from '../ApprovalGatePanel';
import { AuthProvider } from '@/contexts/AuthContext';
import * as incidentsApi from '@/api/endpoints/incidents';
import { PendingApproval } from '@/types/incidents';

vi.mock('@/contexts/AuthContext', async () => {
  const actual = await vi.importActual('@/contexts/AuthContext');
  return {
    ...actual,
    useAuth: () => ({
      user: { role: 'quality_engineer', user_id: '1', username: 'qe1', email: '', full_name: 'QE One', is_active: true, created_at: '' },
    }),
  };
});

const approval: PendingApproval = {
  gate: 'hypothesis_confirmation',
  status: 'pending',
  requires_approval_by: 'Quality Engineer',
  hypotheses: [
    {
      conclusion: 'Nozzle wear caused the misalignment.',
      supporting_evidence_refs: ['maintenance'],
      contradicting_evidence_refs: [],
      confidence_level: 0.8,
      reasoning_summary: 'Maintenance gap overlapped with defect timing.',
      rank: 1,
    },
  ],
};

function renderPanel() {
  const client = new QueryClient();
  return render(
    <QueryClientProvider client={client}>
      <ApprovalGatePanel incidentId="INCIDENT-TEST-001" approval={approval} />
    </QueryClientProvider>
  );
}

describe('ApprovalGatePanel', () => {
  it('renders only reasoning_summary/conclusion — no raw object leaks into the DOM', () => {
    renderPanel();
    expect(screen.getByText('Nozzle wear caused the misalignment.')).toBeInTheDocument();
    expect(screen.getByText('Maintenance gap overlapped with defect timing.')).toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/\{"conclusion":/);
  });

  it('requires passing through a confirmation modal before the mutation fires (Mandatory Rule 4)', async () => {
    const resumeSpy = vi.spyOn(incidentsApi, 'resumeInvestigation').mockResolvedValue({} as any);
    renderPanel();

    await userEvent.click(screen.getByText('Confirm'));
    expect(resumeSpy).not.toHaveBeenCalled();
    expect(screen.getByRole('dialog')).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText('Notes (required)'), 'Confirmed after reviewing evidence.');
    const confirmButtons = screen.getAllByText('Confirm');
    await userEvent.click(confirmButtons[confirmButtons.length - 1]);

    expect(resumeSpy).toHaveBeenCalledWith('INCIDENT-TEST-001', {
      approved: true,
      notes: 'Confirmed after reviewing evidence.',
    });
  });
});