"""Request/response schemas for the document/RAG search endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import ConfigDict
from sqlmodel import SQLModel


class RetrievedPassageResponse(SQLModel):
    passage_id: uuid.UUID
    document_id: str
    document_title: str
    document_version: str
    document_date: Optional[str] = None
    section_title: Optional[str] = None
    section_reference: Optional[str] = None
    chunk_text: str
    retrieval_score: float
    rerank_score: Optional[float] = None
    retrieval_query: str
    retrieval_timestamp: datetime
    embedding_model: str
    retrieved_by: str

    model_config = ConfigDict(from_attributes=True)


class DocumentSearchResponse(SQLModel):
    passages: list[RetrievedPassageResponse]
    no_relevant_document_found: bool
    result_count: int


class DocumentDetailResponse(SQLModel):
    document_id: str
    title: str
    category: str
    version: str
    document_date: str
    author: str
    approved_by: str
    status: str
    language: str
    full_text: Optional[str] = None


class HistoricalIncidentMatchResponse(SQLModel):
    incident_id: str
    title: str
    defect_type: str
    root_cause_confirmed: Optional[str] = None
    corrective_action_taken: Optional[str] = None
    similarity_score: float
    retrieval_timestamp: datetime


class HistoricalIncidentSearchResponse(SQLModel):
    matches: list[HistoricalIncidentMatchResponse]
    result_count: int