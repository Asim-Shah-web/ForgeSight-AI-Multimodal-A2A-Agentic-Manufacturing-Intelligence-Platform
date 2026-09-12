"""
Per-agent output contracts (Phase 6 Section 3 capability tables), used to
validate LLM/tool output before it's merged into InvestigationState.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CvFindingSummary(BaseModel):
    cv_finding_id: str
    defect_type: str
    component_designator: Optional[str] = None
    confidence: float
    bounding_box: list[int]


class VisionAnalysisOutput(BaseModel):
    board_id: str
    cv_findings: list[CvFindingSummary]
    gap: bool = False  # True if no inspection data was available at all


class TelemetryDeviation(BaseModel):
    parameter: str
    timestamp: datetime
    value: float
    note: str


class TelemetryAnalysisOutput(BaseModel):
    machine_id: str
    batch_id: str
    flagged_deviations: list[TelemetryDeviation]
    gap: bool = False


class MaintenanceAssessment(BaseModel):
    machine_id: str
    nozzle_id: Optional[str] = None
    days_since_cleaning: Optional[int] = None
    wear_measurement_mm: Optional[float] = None
    disposition: str
    recommendation: Optional[dict] = None  # PendingApprovalRequest-shaped, if generated
    gap: bool = False


class LotStatistics(BaseModel):
    lot_number: str
    part_number: str
    supplier_id: str
    historical_defect_rate_pct: Optional[float] = None
    correlation_statement: str  # mandated correlation-only wording, never fault attribution
    gap: bool = False


class RetrievedPassageSummary(BaseModel):
    passage_id: str
    document_id: str
    document_title: str
    section_reference: Optional[str] = None
    chunk_text: str
    retrieval_score: float


class DocumentRetrievalOutput(BaseModel):
    passages: list[RetrievedPassageSummary]
    gap: bool = False  # True on NO_RELEVANT_DOCUMENT_FOUND — never fabricated


class SimilarIncidentSummary(BaseModel):
    incident_id: str
    defect_type: str
    root_cause_confirmed: Optional[str] = None
    similarity_score: float


class HistoricalIncidentOutput(BaseModel):
    matches: list[SimilarIncidentSummary]
    gap: bool = False  # True on NO_SIMILAR_INCIDENTS_FOUND


class EvidenceGraphNode(BaseModel):
    node_id: str
    domain: str  # "vision" | "telemetry" | "maintenance" | "component_lot" | "documents" | "historical"
    summary: str


class EvidenceGraphEdge(BaseModel):
    from_node_id: str
    to_node_id: str
    relation: str


class EvidenceGraph(BaseModel):
    nodes: list[EvidenceGraphNode]
    edges: list[EvidenceGraphEdge]
    contradictions: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)


class RootCauseHypothesisOutput(BaseModel):
    conclusion: str
    supporting_evidence_refs: list[str]
    contradicting_evidence_refs: list[str] = Field(default_factory=list)
    confidence_level: float
    reasoning_summary: str  # the ONLY reasoning text ever persisted/traced
    rank: int


class CorrectiveActionOutput(BaseModel):
    proposed_action: str
    supporting_evidence_refs: list[str]
    requires_approval_by: str


class ReportOutput(BaseModel):
    narrative: str
    sections_included: list[str]