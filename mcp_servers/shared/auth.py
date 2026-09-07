"""
MCP-layer authentication and RBAC enforcement.

MCP tool calls carry no HTTP Authorization header — per Phase 5 Section 4.2,
every call must carry a caller_token (a JWT issued by the existing
POST /api/v1/auth/token endpoint) as an explicit tool argument. This module
resolves that token to a User using the exact same decode_access_token logic
already implemented in forgesight.api.security (Phase 7) — it does not
reimplement JWT verification.
"""

from __future__ import annotations

from jose import JWTError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from forgesight.api.security import decode_access_token, role_has_permission
from forgesight.config.logging import get_logger
from forgesight.domain.models.users import User, UserRole

logger = get_logger(__name__)


class McpAuthenticationError(Exception):
    """Raised when a caller_token is missing, invalid, expired, or resolves
    to an inactive/nonexistent user."""


class McpPermissionError(Exception):
    """Raised when an authenticated caller's role lacks the required permission."""

    def __init__(self, role: UserRole, permission: str) -> None:
        self.role = role
        self.permission = permission
        super().__init__(f"Role '{role.value}' lacks permission '{permission}'.")


async def resolve_caller(caller_token: str, session: AsyncSession) -> User:
    """
    Resolve a caller_token to an active User row.

    Mirrors forgesight.api.security.get_current_user's resolution logic,
    but as a plain function usable outside a FastAPI request context.
    """
    if not caller_token:
        raise McpAuthenticationError("No caller_token provided.")

    try:
        payload = decode_access_token(caller_token)
    except JWTError as exc:
        logger.warning("mcp_jwt_decode_failed", extra={"error": str(exc)})
        raise McpAuthenticationError("Invalid or expired caller_token.") from exc

    username = payload.get("sub")
    if username is None:
        raise McpAuthenticationError("caller_token missing 'sub' claim.")

    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise McpAuthenticationError(f"No active user found for token subject '{username}'.")

    return user


def check_tool_permission(role: UserRole, permission: str) -> None:
    """Raise McpPermissionError if `role` does not hold `permission`."""
    if not role_has_permission(role, permission):
        logger.warning(
            "mcp_permission_denied",
            extra={"role": role.value, "permission": permission},
        )
        raise McpPermissionError(role, permission)