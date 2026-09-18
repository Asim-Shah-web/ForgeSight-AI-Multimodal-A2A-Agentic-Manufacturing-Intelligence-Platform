export interface EvidenceAttachRequest {
  evidence_type: string;
  reference_id: string;
  note?: string | null;
}

export interface EvidenceResponse {
  incident_id: string;
  evidence_type: string;
  reference_id: string;
  note: string | null;
  attached_by: string;
  attached_at: string;
}



