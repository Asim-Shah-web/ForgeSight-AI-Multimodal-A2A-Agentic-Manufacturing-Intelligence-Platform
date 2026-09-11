"""User management routes: POST/GET /users, GET /users/me, PATCH /users/{id}/role."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from forgesight.api.schemas.users import UserCreate, UserResponse, UserRoleUpdate
from forgesight.api.security import get_current_user, hash_password, require_roles
from forgesight.config.database import get_session
from forgesight.config.logging import get_logger
from forgesight.domain.models.audit import AuditEvent, AuditEventType
from forgesight.domain.models.users import HUMAN_PERSONA_ROLES, User, UserRole

logger = get_logger(__name__)

router = APIRouter()


def _reject_non_human_role(role: UserRole) -> None:
    """
    Phase 11 Step 11.1: AGENT_ORCHESTRATOR is a non-human system role and
    must never be assignable through the normal user-creation/role-update
    flow, even by a System Administrator. The single AGENT_ORCHESTRATOR
    account is seeded directly (scripts/seed_database.py), not created or
    modified through this API.
    """
    if role not in HUMAN_PERSONA_ROLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Role '{role.value}' is a non-human system role and cannot be assigned "
                f"through this endpoint."
            ),
        )


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.SYSTEM_ADMINISTRATOR))],
)
async def create_user(
    payload: UserCreate,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Create a new user. Restricted to System Administrator.

    The System Administrator configures accounts and assigns a persona role,
    but this action alone never grants that user (or the administrator)
    quality approval authority in the investigation workflow — role
    assignment and permission enforcement remain governed by
    ROLE_PERMISSIONS regardless of who created the account (SEC-003). The
    non-human AGENT_ORCHESTRATOR role is also explicitly rejected here.
    """
    _reject_non_human_role(payload.role)

    existing = await session.execute(
        select(User).where((User.username == payload.username) | (User.email == payload.email))
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this username or email already exists.",
        )

    user = User(
        username=payload.username,
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)

    audit_event = AuditEvent(
        who=current_user.user_id,
        what=AuditEventType.USER_CREATED,
        target_id=str(user.user_id),
        target_type="user",
        action="create_user",
        result="success",
        new_state={"username": user.username, "role": user.role.value},
        ip_address=request.client.host if request.client else None,
    )
    session.add(audit_event)
    await session.flush()

    logger.info("user_created", extra={"created_user_id": str(user.user_id), "by": str(current_user.user_id)})
    return UserResponse.model_validate(user)


@router.get(
    "",
    response_model=list[UserResponse],
    dependencies=[Depends(require_roles(UserRole.SYSTEM_ADMINISTRATOR))],
)
async def list_users(session: AsyncSession = Depends(get_session)) -> list[UserResponse]:
    """List all users. Restricted to System Administrator."""
    result = await session.execute(select(User))
    users = result.scalars().all()
    return [UserResponse.model_validate(u) for u in users]


@router.get("/me", response_model=UserResponse)
async def get_own_profile(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Return the authenticated caller's own profile. Any authenticated user."""
    return UserResponse.model_validate(current_user)


@router.patch(
    "/{user_id}/role",
    response_model=UserResponse,
    dependencies=[Depends(require_roles(UserRole.SYSTEM_ADMINISTRATOR))],
)
async def update_user_role(
    user_id: uuid.UUID,
    payload: UserRoleUpdate,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Update a user's role. Restricted to System Administrator. Always emits
    an AuditEvent with both prior and new role recorded (AR-002). The
    non-human AGENT_ORCHESTRATOR role is explicitly rejected here as well —
    no existing human account can be converted into the system role, and
    vice versa, through this endpoint.
    """
    _reject_non_human_role(payload.role)

    result = await session.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    prior_role = user.role
    user.role = payload.role
    session.add(user)
    await session.flush()
    await session.refresh(user)

    audit_event = AuditEvent(
        who=current_user.user_id,
        what=AuditEventType.USER_ROLE_CHANGED,
        target_id=str(user.user_id),
        target_type="user",
        action="update_role",
        result="success",
        prior_state={"role": prior_role.value},
        new_state={"role": user.role.value},
        ip_address=request.client.host if request.client else None,
    )
    session.add(audit_event)
    await session.flush()

    logger.info(
        "user_role_changed",
        extra={"target_user_id": str(user.user_id), "prior_role": prior_role.value, "new_role": user.role.value},
    )
    return UserResponse.model_validate(user)