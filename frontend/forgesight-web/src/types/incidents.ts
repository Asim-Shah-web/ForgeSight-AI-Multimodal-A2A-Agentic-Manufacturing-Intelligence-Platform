export type IncidentStatus = 'open' | 'in_progress' | 'awaiting_approval' | 'closed' | 'escalated';

export interface IncidentCreate {
  board_id: string;
  batch_id: string;
  line_id: string;
  product_id: string;
  defect_type: string;
  component_designator?: string | null;
  description: string;
}

export interface IncidentResponse {
  incident_id: string;
  board_id: string;
  batch_id: string;
  line_id: string;
  product_id: string;
  defect_type: string;
  component_designator: string | null;
  description: string;
  status: IncidentStatus;
  current_stage: number;
  created_by: string;
  created_at: string;
  updated_at: string;
  signed_off_by: string | null;
  signed_off_at: string | null;
}

export interface IncidentListResponse {
  items: IncidentResponse[];
  total: number;
  page: number;
  page_size: number;
}

export interface IncidentStatusUpdate {
  status: IncidentStatus;
  reason?: string | null;
}

export interface IncidentApprovalRequest {
  approval_statement: string;
  confirmed_hypothesis_id?: string | null;
}

export interface PendingApproval {
  gate: 'hypothesis_confirmation' | 'corrective_action_approval';
  status: 'pending' | 'approved' | 'rejected';
  requires_approval_by: string;
  hypotheses?: RootCauseHypothesis[];
  proposed_action?: string;
  supporting_evidence_refs?: string[];
  notes?: string;
}

export interface RootCauseHypothesis {
  conclusion: string;
  supporting_evidence_refs: string[];
  contradicting_evidence_refs: string[];
  confidence_level: number;
  reasoning_summary: string;
  rank: number;
}

export interface InvestigationStatusResponse {
  incident_id: string;
  current_stage: number;
  status: 'in_progress' | 'awaiting_approval' | 'complete' | 'failed';
  evidence_graph_summary: Record<string, boolean>;
  pending_approvals: PendingApproval[];
  completed_stages: number[];
}

export interface InvestigationResumeRequest {
  approved: boolean;
  notes?: string | null;
}