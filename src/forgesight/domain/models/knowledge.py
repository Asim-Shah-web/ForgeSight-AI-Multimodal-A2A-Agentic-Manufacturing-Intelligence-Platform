"""Knowledge domain models: TechnicalDocument, DocumentChunk.

DocumentChunk.embedding uses pgvector's Vector(1024) type per Phase 4
ADR-005 (BAAI/bge-large-en-v1.5, 1024 dimensions).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column
from sqlmodel import Field, SQLModel


class TechnicalDocument(SQLModel, table=True):
    """A governed technical document (SOP, machine manual, engineering doc)."""

    __tablename__ = "technical_documents"

    document_id: str = Field(primary_key=True)  # e.g. "SOP-QUAL-042"
    title: str
    category: str  # "sop" | "machine_manual" | "engineering_doc" | "historical_report"
    version: str
    document_date: date
    author: str
    approved_by: str
    file_path: str
    status: str = Field(default="active")  # "active" | "retired"
    language: str = Field(default="en")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DocumentChunk(SQLModel, table=True):
    """A retrievable, embedded chunk of a TechnicalDocument (Phase 4)."""

    __tablename__ = "document_chunks"

    chunk_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    document_id: str = Field(foreign_key="technical_documents.document_id", index=True)
    document_title: str
    document_version: str
    section_title: Optional[str] = None
    section_reference: Optional[str] = None
    chunk_index: int
    chunk_text: str
    token_count: int
    embedding: Optional[list[float]] = Field(
        default=None,
        sa_column=Column(Vector(1024)),  # Phase 4 ADR-005: vector(1024)
    )
    embedding_model: Optional[str] = None
    status: str = Field(default="active")  # "active" | "retired"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class IncidentEmbedding(SQLModel, table=True):
    """Semantic embedding of a closed incident summary, for historical search."""

    __tablename__ = "incident_embeddings"

    embedding_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    incident_id: str = Field(foreign_key="incidents.incident_id", index=True, unique=True)
    summary_text: str
    embedding: Optional[list[float]] = Field(
        default=None,
        sa_column=Column(Vector(1024)),
    )
    embedding_model: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))