"""Investigation domain models: Incident, RootCauseHypothesis, CorrectiveAction, Report.

IncidentStatus and the trust-chain fields on RootCauseHypothesis directly
implement the Phase 1/2 human-in-the-loop and evidence-provenance rules.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class IncidentStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    AWAITING_APPROVAL = "awaiting_approval"
    CLOSED = "closed"
    ESCALATED = "escalated"


class Incident(SQLModel, table=True):
    """A quality incident investigation, anchored to a board/batch/defect."""

    __tablename__ = "incidents"

    incident_id: str = Field(primary_key=True)  # e.g. "INCIDENT-2026-00421"
    board_id: str = Field(foreign_key="boards.board_id", index=True)
    batch_id: str = Field(foreign_key="batches.batch_id", index=True)
    line_id: str = Field(foreign_key="lines.line_id", index=True)
    product_id: str = Field(foreign_key="products.product_id", index=True)

    defect_type: str
    component_designator: Optional[str] = None
    description: str

    status: IncidentStatus = Field(default=IncidentStatus.OPEN, index=True)
    current_stage: int = Field(default=1)

    created_by: uuid.UUID = Field(foreign_key="users.user_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    signed_off_by: Optional[uuid.UUID] = Field(default=None, foreign_key="users.user_id")
    signed_off_at: Optional[datetime] = None


class RootCauseHypothesis(SQLModel, table=True):
    """A ranked root-cause hypothesis generated for an incident.

    Every trust-chain field (Phase 2 Section 15) is mandatory: a hypothesis
    without supporting_evidence_refs or a reasoning_summary is not a valid
    row in this table.
    """

    __tablename__ = "root_cause_hypotheses"

    hypothesis_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    incident_id: str = Field(foreign_key="incidents.incident_id", index=True)

    conclusion: str
    supporting_evidence_refs: list[str] = Field(sa_column=Column(JSON))
    contradicting_evidence_refs: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    confidence_level: float
    reasoning_summary: str

    rank: int
    is_confirmed: bool = Field(default=False)
    confirmed_by: Optional[uuid.UUID] = Field(default=None, foreign_key="users.user_id")
    confirmed_at: Optional[datetime] = None

    model_version: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CorrectiveAction(SQLModel, table=True):
    """A recommended corrective action tied to a confirmed hypothesis.

    Always created in a pending state — this table has no field that lets a
    row represent an already-executed high-risk action without an
    `approved_by` value populated by a human.
    """

    __tablename__ = "corrective_actions"

    action_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    incident_id: str = Field(foreign_key="incidents.incident_id", index=True)
    hypothesis_id: uuid.UUID = Field(foreign_key="root_cause_hypotheses.hypothesis_id")

    proposed_action: str
    supporting_evidence_refs: list[str] = Field(sa_column=Column(JSON))
    requires_approval_by: str  # persona role name

    status: str = Field(default="pending")  # "pending" | "approved" | "rejected"
    approved_by: Optional[uuid.UUID] = Field(default=None, foreign_key="users.user_id")
    approved_at: Optional[datetime] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Report(SQLModel, table=True):
    """The final compiled investigation report (Stage 12)."""

    __tablename__ = "reports"

    report_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    incident_id: str = Field(foreign_key="incidents.incident_id", index=True, unique=True)

    narrative: str
    sections_included: list[str] = Field(sa_column=Column(JSON))
    evidence_appendix: dict[str, Any] = Field(sa_column=Column(JSON))

    generated_by: Optional[str] = None  # agent/model identifier
    model_version: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))