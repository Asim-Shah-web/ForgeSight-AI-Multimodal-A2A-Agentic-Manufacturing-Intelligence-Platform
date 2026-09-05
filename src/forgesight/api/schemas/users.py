"""Request/response schemas for user and auth endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import ConfigDict, EmailStr, Field
from sqlmodel import SQLModel

from forgesight.domain.models.users import UserRole


class UserCreate(SQLModel):
    """Request body for POST /users."""

    username: str = Field(min_length=3, max_length=64)
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole

    model_config = ConfigDict(str_strip_whitespace=True)


class UserResponse(SQLModel):
    """Response body representing a user. Never includes hashed_password."""

    user_id: uuid.UUID
    username: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserRoleUpdate(SQLModel):
    """Request body for PATCH /users/{user_id}/role."""

    role: UserRole


class TokenResponse(SQLModel):
    """Response body for POST /auth/token."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int