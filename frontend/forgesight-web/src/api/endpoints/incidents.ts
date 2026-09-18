import { apiClient } from '../client';
import {
  IncidentApprovalRequest,
  IncidentCreate,
  IncidentListResponse,
  IncidentResponse,
  IncidentStatusUpdate,
  InvestigationResumeRequest,
  InvestigationStatusResponse,
} from '@/types/incidents';
import { EvidenceAttachRequest, EvidenceResponse } from '@/types/evidence';

export async function listIncidents(params: {
  status?: string;
  line_id?: string;
  page?: number;
  page_size?: number;
}): Promise<IncidentListResponse> {
  const response = await apiClient.get<IncidentListResponse>('/incidents', { params });
  return response.data;
}

export async function getIncident(incidentId: string): Promise<IncidentResponse> {
  const response = await apiClient.get<IncidentResponse>(`/incidents/${incidentId}`);
  return response.data;
}

export async function createIncident(payload: IncidentCreate): Promise<IncidentResponse> {
  const response = await apiClient.post<IncidentResponse>('/incidents', payload);
  return response.data;
}

export async function updateIncidentStatus(
  incidentId: string,
  payload: IncidentStatusUpdate
): Promise<IncidentResponse> {
  const response = await apiClient.patch<IncidentResponse>(`/incidents/${incidentId}/status`, payload);
  return response.data;
}

export async function approveIncident(
  incidentId: string,
  payload: IncidentApprovalRequest
): Promise<IncidentResponse> {
  const response = await apiClient.post<IncidentResponse>(`/incidents/${incidentId}/approve`, payload);
  return response.data;
}

export async function attachEvidence(
  incidentId: string,
  payload: EvidenceAttachRequest
): Promise<EvidenceResponse> {
  const response = await apiClient.post<EvidenceResponse>(`/incidents/${incidentId}/evidence`, payload);
  return response.data;
}

export async function startInvestigation(incidentId: string): Promise<{ status: string; current_stage: number }> {
  const response = await apiClient.post(`/incidents/${incidentId}/investigate`);
  return response.data;
}

export async function getInvestigationStatus(incidentId: string): Promise<InvestigationStatusResponse> {
  const response = await apiClient.get<InvestigationStatusResponse>(
    `/incidents/${incidentId}/investigation-status`
  );
  return response.data;
}

export async function resumeInvestigation(
  incidentId: string,
  payload: InvestigationResumeRequest
): Promise<InvestigationStatusResponse> {
  const response = await apiClient.post<InvestigationStatusResponse>(
    `/incidents/${incidentId}/investigation/resume`,
    payload
  );
  return response.data;
}