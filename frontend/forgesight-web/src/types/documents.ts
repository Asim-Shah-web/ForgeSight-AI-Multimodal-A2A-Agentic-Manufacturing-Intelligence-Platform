export interface RetrievedPassageResponse {
  passage_id: string;
  document_id: string;
  document_title: string;
  document_version: string;
  document_date: string | null;
  section_title: string | null;
  section_reference: string | null;
  chunk_text: string;
  retrieval_score: number;
  rerank_score: number | null;
  retrieval_query: string;
  retrieval_timestamp: string;
  embedding_model: string;
  retrieved_by: string;
}

export interface DocumentSearchResponse {
  passages: RetrievedPassageResponse[];
  no_relevant_document_found: boolean;
  result_count: number;
}

export interface DocumentDetailResponse {
  document_id: string;
  title: string;
  category: string;
  version: string;
  document_date: string;
  author: string;
  approved_by: string;
  status: string;
  language: string;
  full_text: string | null;
}

export interface HistoricalIncidentMatchResponse {
  incident_id: string;
  title: string;
  defect_type: string;
  root_cause_confirmed: string | null;
  corrective_action_taken: string | null;
  similarity_score: number;
  retrieval_timestamp: string;
}