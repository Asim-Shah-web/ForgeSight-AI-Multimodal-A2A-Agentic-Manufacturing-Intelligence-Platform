"""Centralizes shared FastAPI dependencies used across route modules."""

from __future__ import annotations

from forgesight.api.security import get_current_user, require_permission, require_roles
from forgesight.config.database import get_session
from forgesight.config.redis_client import get_redis

__all__ = [
    "get_current_user",
    "require_roles",
    "require_permission",
    "get_session",
    "get_redis",
]