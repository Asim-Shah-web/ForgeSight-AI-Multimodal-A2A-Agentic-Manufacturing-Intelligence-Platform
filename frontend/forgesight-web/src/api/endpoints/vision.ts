import { apiClient } from '../client';
import { CvFindingResponse, InspectionResultResponse } from '@/types/vision';

export async function inspectBoard(boardId: string, file: File): Promise<InspectionResultResponse> {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post<InspectionResultResponse>(
    `/vision/boards/${boardId}/inspect`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  );
  return response.data;
}

export async function getBoardFindings(boardId: string): Promise<CvFindingResponse[]> {
  const response = await apiClient.get<CvFindingResponse[]>(`/vision/boards/${boardId}/findings`);
  return response.data;
}