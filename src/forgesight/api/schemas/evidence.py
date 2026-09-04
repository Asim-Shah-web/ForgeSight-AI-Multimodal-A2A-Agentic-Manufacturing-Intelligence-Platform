"""Request/response schemas for evidence attachment endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import ConfigDict, Field
from sqlmodel import SQLModel


class EvidenceAttachRequest(SQLModel):
    """Request body for POST /incidents/{incident_id}/evidence.

    Represents a manually attached evidence item (e.g. a QE attaching a
    reference to an inspection image, a maintenance record, or a retrieved
    SOP passage) rather than evidence gathered automatically by an agent.
    """

    evidence_type: str = Field(
        description="e.g. 'cv_finding', 'maintenance_record', 'document_passage', 'telemetry'"
    )
    reference_id: str = Field(description="ID of the referenced evidence row")
    note: Optional[str] = Field(default=None, max_length=2000)

    model_config = ConfigDict(str_strip_whitespace=True)


class EvidenceResponse(SQLModel):
    """Response body confirming an evidence attachment."""

    incident_id: str
    evidence_type: str
    reference_id: str
    note: Optional[str]
    attached_by: uuid.UUID
    attached_at: datetime

    model_config = ConfigDict(from_attributes=True)