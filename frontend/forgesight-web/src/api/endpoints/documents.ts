import { apiClient } from '../client';
import { DocumentDetailResponse, DocumentSearchResponse } from '@/types/documents';

export async function searchDocuments(
  query: string,
  category?: string,
  machineId?: string
): Promise<DocumentSearchResponse> {
  const response = await apiClient.get<DocumentSearchResponse>('/documents/search', {
    params: { query, category, machine_id: machineId },
  });
  return response.data;
}

export async function getDocument(documentId: string, version?: string): Promise<DocumentDetailResponse> {
  const response = await apiClient.get<DocumentDetailResponse>(`/documents/${documentId}`, {
    params: { version },
  });
  return response.data;
}