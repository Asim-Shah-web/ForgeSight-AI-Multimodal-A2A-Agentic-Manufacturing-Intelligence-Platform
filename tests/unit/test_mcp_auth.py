"""Unit tests for the shared MCP authentication/RBAC helper (Step 10.1)."""

from __future__ import annotations

import pytest

from forgesight.api.security import create_access_token
from forgesight.domain.models.users import UserRole
from mcp_servers.shared.auth import McpAuthenticationError, McpPermissionError, check_tool_permission, resolve_caller


@pytest.mark.asyncio
async def test_resolve_caller_with_valid_token_returns_correct_user(session, users_per_role) -> None:
    qe = users_per_role[UserRole.QUALITY_ENGINEER]
    token, _ = create_access_token(subject=qe.username, role=qe.role)

    resolved = await resolve_caller(token, session)
    assert resolved.username == qe.username
    assert resolved.role == UserRole.QUALITY_ENGINEER


@pytest.mark.asyncio
async def test_resolve_caller_with_malformed_token_raises(session) -> None:
    with pytest.raises(McpAuthenticationError):
        await resolve_caller("not-a-real-jwt", session)


@pytest.mark.asyncio
async def test_resolve_caller_with_empty_token_raises(session) -> None:
    with pytest.raises(McpAuthenticationError):
        await resolve_caller("", session)


def test_check_tool_permission_raises_for_lacking_role() -> None:
    with pytest.raises(McpPermissionError):
        check_tool_permission(UserRole.PRODUCTION_OPERATOR, "component_lot:read")


def test_check_tool_permission_passes_for_permitted_role() -> None:
    check_tool_permission(UserRole.SUPPLIER_QUALITY_ENGINEER, "component_lot:read")  # should not raise