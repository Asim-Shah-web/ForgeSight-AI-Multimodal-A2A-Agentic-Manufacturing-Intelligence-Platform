"""User domain model and role enum (Phase 1 personas, docs/business/personas.md)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlmodel import Field, SQLModel


class UserRole(str, Enum):
    """The 7 human personas established in Phase 1. Do not add persona-named
    AI agents to this enum — this enum models human accountability roles only."""

    PRODUCTION_OPERATOR = "production_operator"
    QUALITY_ENGINEER = "quality_engineer"
    MANUFACTURING_ENGINEER = "manufacturing_engineer"
    MAINTENANCE_ENGINEER = "maintenance_engineer"
    QUALITY_MANAGER = "quality_manager"
    SUPPLIER_QUALITY_ENGINEER = "supplier_quality_engineer"
    SYSTEM_ADMINISTRATOR = "system_administrator"


class User(SQLModel, table=True):
    """A human user of the ForgeSight platform, bound to exactly one persona role."""

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