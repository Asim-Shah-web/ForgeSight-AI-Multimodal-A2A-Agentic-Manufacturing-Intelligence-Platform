"""Unit tests for JWT authentication and RBAC enforcement."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from jose import jwt

from forgesight.api.security import (
    ROLE_PERMISSIONS,
    create_access_token,
    require_roles,
)
from forgesight.config.settings import settings
from forgesight.domain.models.users import User, UserRole


def _make_user(role: UserRole, username: str = "testuser") -> User:
    return User(
        user_id=uuid.uuid4(),
        username=username,
        email=f"{username}@forgesight.example",
        full_name="Test User",
        hashed_password="irrelevant-for-this-test",
        role=role,
        is_active=True,
    )


@pytest.mark.asyncio
async def test_require_roles_raises_403_for_unauthorized_role() -> None:
    checker = require_roles(UserRole.QUALITY_ENGINEER, UserRole.QUALITY_MANAGER)
    unauthorized_user = _make_user(UserRole.PRODUCTION_OPERATOR)

    dependency_fn = checker.__wrapped__ if hasattr(checker, "__wrapped__") else checker
    inner = checker.__closure__  # not used directly; call through FastAPI's Depends contract instead

    # require_roles returns an async function; call it directly with the
    # already-resolved user, bypassing FastAPI's DI container.
    async def call_checker():
        # Reimplements the dependency's own resolution path by calling the
        # inner coroutine function directly with a pre-resolved user.
        from forgesight.api.security import get_current_user  # noqa: F401

        async def fake_current_user():
            return unauthorized_user

        # The checker closure expects `current_user` via Depends(get_current_user);
        # to unit test purely the role-check logic we invoke the checker's
        # underlying coroutine with the user injected directly.
        return await checker.__call__(current_user=unauthorized_user)  # type: ignore[misc]

    with pytest.raises(HTTPException) as exc_info:
        await call_checker()
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_require_roles_allows_authorized_role() -> None:
    checker = require_roles(UserRole.QUALITY_ENGINEER, UserRole.QUALITY_MANAGER)
    authorized_user = _make_user(UserRole.QUALITY_ENGINEER)

    result = await checker.__call__(current_user=authorized_user)  # type: ignore[misc]
    assert result is authorized_user


def test_expired_jwt_token_is_rejected() -> None:
    expired_payload = {
        "sub": "testuser",
        "role": UserRole.QUALITY_ENGINEER.value,
        "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
        "iat": datetime.now(timezone.utc) - timedelta(minutes=10),
    }
    expired_token = jwt.encode(expired_payload, settings.secret_key, algorithm=settings.algorithm)

    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(expired_token, settings.secret_key, algorithms=[settings.algorithm])


def test_valid_token_round_trips_role_and_subject() -> None:
    token, expires_in = create_access_token(subject="qe1", role=UserRole.QUALITY_ENGINEER)
    decoded = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    assert decoded["sub"] == "qe1"
    assert decoded["role"] == UserRole.QUALITY_ENGINEER.value
    assert expires_in == settings.access_token_expire_minutes * 60


def test_system_administrator_lacks_approve_permission() -> None:
    """SEC-003: SysAdmin permission set must never include any approval permission."""
    sysadmin_permissions = ROLE_PERMISSIONS[UserRole.SYSTEM_ADMINISTRATOR]
    approval_permissions = {p for p in sysadmin_permissions if "approve" in p}
    assert approval_permissions == set(), (
        f"SYSTEM_ADMINISTRATOR must not hold any approval permission, found: {approval_permissions}"
    )