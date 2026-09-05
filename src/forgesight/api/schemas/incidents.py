"""Request/response schemas for incident endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import ConfigDict, Field, field_validator
from sqlmodel import SQLModel

from forgesight.domain.models.investigation import IncidentStatus


class IncidentCreate(SQLModel):
    """Request body for POST /incidents."""

    board_id: str = Field(min_length=1)
    batch_id: str = Field(min_length=1)
    line_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    defect_type: str = Field(min_length=1)
    component_designator: Optional[str] = None
    description: str = Field(min_length=1, max_length=4000)

    model_config = ConfigDict(str_strip_whitespace=True)


class IncidentResponse(SQLModel):
    """Response body representing a full incident record."""

    incident_id: str
    board_id: str
    batch_id: str
    line_id: str
    product_id: str
    defect_type: str
    component_designator: Optional[str]
    description: str
    status: IncidentStatus
    current_stage: int
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    signed_off_by: Optional[uuid.UUID]
    signed_off_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class IncidentListResponse(SQLModel):
    """Paginated list response for GET /incidents."""

    items: list[IncidentResponse]
    total: int
    page: int
    page_size: int


class IncidentStatusUpdate(SQLModel):
    """Request body for PATCH /incidents/{incident_id}/status."""

    status: IncidentStatus
    reason: Optional[str] = Field(default=None, max_length=2000)


class IncidentApprovalRequest(SQLModel):
    """Request body for POST /incidents/{incident_id}/approve.

    This is the Stage 11 mandatory HITL sign-off gate. Approval always
    requires an explicit human statement — there is no default/blank
    approval path.
    """

    approval_statement: str = Field(
        min_length=1,
        max_length=4000,
        description="QE's explicit sign-off statement / justification",
    )
    confirmed_hypothesis_id: Optional[uuid.UUID] = Field(
        default=None,
        description="If Stage 9 produced hypotheses, the confirmed one being signed off on",
    )

    @field_validator("approval_statement")
    @classmethod
    def statement_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("approval_statement cannot be blank")
        return value