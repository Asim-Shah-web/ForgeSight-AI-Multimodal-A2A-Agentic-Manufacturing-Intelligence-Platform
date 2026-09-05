"""AuditEvent domain model — implements Phase 1 requirement AR-002.

Every write operation in the API layer must emit one of these rows. Audit
records are treated as append-only: no route in this codebase updates or
deletes an existing AuditEvent row.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class AuditEventType(str, Enum):
    """Canonical event types, drawn from the Phase 1/Phase 2 audit principle."""

    USER_AUTHENTICATION = "user_authentication"
    INCIDENT_CREATED = "incident_created"
    INCIDENT_MODIFIED = "incident_modified"
    INCIDENT_STATUS_CHANGED = "incident_status_changed"
    EVIDENCE_SUBMITTED = "evidence_submitted"
    CV_EXECUTION = "cv_execution"
    MCP_TOOL_INVOCATION = "mcp_tool_invocation"
    RAG_RETRIEVAL = "rag_retrieval"
    AI_RECOMMENDATION_GENERATED = "ai_recommendation_generated"
    HUMAN_MODIFICATION_OF_AI_RECOMMENDATION = "human_modification_of_ai_recommendation"
    HUMAN_APPROVAL = "human_approval"
    HUMAN_REJECTION = "human_rejection"
    HIGH_RISK_ACTION_EXECUTION = "high_risk_action_execution"
    REPORT_GENERATION = "report_generation"
    SYSTEM_CONFIGURATION_CHANGE = "system_configuration_change"
    USER_CREATED = "user_created"
    USER_ROLE_CHANGED = "user_role_changed"


class AuditEvent(SQLModel, table=True):
    """Immutable audit trail record. Timestamps are always UTC."""

    __tablename__ = "audit_events"

    audit_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    who: uuid.UUID = Field(foreign_key="users.user_id", index=True)
    what: AuditEventType = Field(index=True)
    when: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), index=True, nullable=False
    )

    target_id: Optional[str] = Field(default=None, index=True)
    target_type: Optional[str] = Field(default=None, index=True)
    action: str
    result: str  # e.g. "success", "error:PERMISSION_DENIED", "pending_approval"

    prior_state: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    new_state: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON))

    approval_by: Optional[uuid.UUID] = Field(default=None, foreign_key="users.user_id")
    ai_version: Optional[str] = Field(default=None)
    evidence_version: Optional[str] = Field(default=None)
    ip_address: Optional[str] = Field(default=None)