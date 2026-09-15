export interface CvFindingResponse {
  cv_finding_id: string;
  image_id: string;
  board_id: string;
  defect_type: string;
  component_designator: string | null;
  confidence: number;
  bounding_box: [number, number, number, number]; // [x, y, w, h]
  raw_image_reference: string;
  model_name: string;
  model_version: string;
  inference_timestamp: string;
  dataset_used_for_training: string | null;
}

export interface InspectionImageResponse {
  image_id: string;
  board_id: string;
  image_reference: string;
  station_id: string | null;
  captured_at: string;
}

export interface InspectionResultResponse {
  inspection_image: InspectionImageResponse;
  cv_findings: CvFindingResponse[];
  findings_count: number;
}