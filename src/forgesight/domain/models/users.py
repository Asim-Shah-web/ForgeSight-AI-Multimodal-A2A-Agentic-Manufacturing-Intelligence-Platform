"""User domain model and role enum (Phase 1 personas, docs/business/personas.md;
extended in Phase 11 Step 11.1 with a non-human system role)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlmodel import Field, SQLModel


class UserRole(str, Enum):
    """
    The 7 human personas established in Phase 1, plus one non-human system
    role added in Phase 11.

    Do NOT add persona-named AI agents to this enum — this enum models
    accountability roles (who a User record represents), not software
    capabilities. AGENT_ORCHESTRATOR is the sole, deliberate exception: it
    exists only so that MCP tool calls made by the LangGraph orchestrator
    on behalf of an investigation are attributable to "the system," rather
    than being misattributed to whichever Quality Engineer happened to
    trigger the investigation. It is NOT a human persona, must never be
    assignable via the normal POST /users flow, and must never hold any
    *:approve permission (enforced in security.py's ROLE_PERMISSIONS and
    tested explicitly in tests/unit/test_security.py).
    """

    PRODUCTION_OPERATOR = "production_operator"
    QUALITY_ENGINEER = "quality_engineer"
    MANUFACTURING_ENGINEER = "manufacturing_engineer"
    MAINTENANCE_ENGINEER = "maintenance_engineer"
    QUALITY_MANAGER = "quality_manager"
    SUPPLIER_QUALITY_ENGINEER = "supplier_quality_engineer"
    SYSTEM_ADMINISTRATOR = "system_administrator"
    AGENT_ORCHESTRATOR = "agent_orchestrator"


# Roles that represent a real human accountable for a business decision.
# Used by the users API (Step 11.1) to reject attempts to assign the
# non-human AGENT_ORCHESTRATOR role through the normal user-creation flow.
HUMAN_PERSONA_ROLES: frozenset[UserRole] = frozenset(
    {
        UserRole.PRODUCTION_OPERATOR,
        UserRole.QUALITY_ENGINEER,
        UserRole.MANUFACTURING_ENGINEER,
        UserRole.MAINTENANCE_ENGINEER,
        UserRole.QUALITY_MANAGER,
        UserRole.SUPPLIER_QUALITY_ENGINEER,
        UserRole.SYSTEM_ADMINISTRATOR,
    }
)


class User(SQLModel, table=True):
    """A user of the ForgeSight platform, bound to exactly one role.

    Almost always a human persona; the sole exception is the single seeded
    AGENT_ORCHESTRATOR system account (see scripts/seed_database.py), which
    exists only to mint tokens for agent-initiated MCP tool calls.
    """

    __tablename__ = "users"

    user_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False)
    email: str = Field(index=True, unique=True, nullable=False)
    full_name: str
    hashed_password: str
    role: UserRole = Field(index=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )