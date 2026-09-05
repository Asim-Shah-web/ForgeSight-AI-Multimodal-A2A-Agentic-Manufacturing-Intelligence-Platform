"""Unit tests for domain model definitions (no live DB required for these assertions)."""

from __future__ import annotations

import pytest
from pgvector.sqlalchemy import Vector

from forgesight.domain.models.audit import AuditEvent
from forgesight.domain.models.investigation import IncidentStatus
from forgesight.domain.models.knowledge import DocumentChunk
from forgesight.domain.models.users import UserRole


def test_user_role_enum_contains_all_seven_personas() -> None:
    expected = {
        "production_operator",
        "quality_engineer",
        "manufacturing_engineer",
        "maintenance_engineer",
        "quality_manager",
        "supplier_quality_engineer",
        "system_administrator",
    }
    actual = {role.value for role in UserRole}
    assert actual == expected
    assert len(UserRole) == 7


def test_audit_event_has_all_ar002_required_fields() -> None:
    required_fields = {
        "audit_id",
        "who",
        "what",
        "when",
        "target_id",
        "target_type",
        "action",
        "result",
        "prior_state",
        "new_state",
        "approval_by",
        "ai_version",
        "evidence_version",
        "ip_address",
    }
    model_fields = set(AuditEvent.model_fields.keys())
    missing = required_fields - model_fields
    assert not missing, f"AuditEvent is missing required AR-002 fields: {missing}"


def test_document_chunk_embedding_is_vector_1024() -> None:
    embedding_field = DocumentChunk.model_fields["embedding"]
    sa_column = embedding_field.sa_column
    assert sa_column is not None
    assert isinstance(sa_column.type, Vector)
    assert sa_column.type.dim == 1024


def test_incident_status_only_contains_legal_values() -> None:
    expected = {"open", "in_progress", "awaiting_approval", "closed", "escalated"}
    actual = {status.value for status in IncidentStatus}
    assert actual == expected