"""Authentication routes: POST /auth/token."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from forgesight.api.schemas.users import TokenResponse
from forgesight.api.security import create_access_token, verify_password
from forgesight.config.database import get_session
from forgesight.config.logging import get_logger
from forgesight.domain.models.audit import AuditEvent, AuditEventType
from forgesight.domain.models.users import User

logger = get_logger(__name__)

router = APIRouter()


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """
    Exchange a username/password for a JWT access token.

    On failure returns HTTP 401 with a WWW-Authenticate: Bearer header,
    without revealing whether the username or the password was incorrect.
    """
    result = await session.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active or not verify_password(form_data.password, user.hashed_password):
        logger.warning(
            "authentication_failed",
            extra={"username": form_data.username, "ip_address": request.client.host if request.client else None},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token, expires_in = create_access_token(subject=user.username, role=user.role)

    audit_event = AuditEvent(
        who=user.user_id,
        what=AuditEventType.USER_AUTHENTICATION,
        target_id=str(user.user_id),
        target_type="user",
        action="login",
        result="success",
        ip_address=request.client.host if request.client else None,
    )
    session.add(audit_event)
    await session.flush()

    logger.info("authentication_succeeded", extra={"user_id": str(user.user_id), "role": user.role.value})

    return TokenResponse(access_token=token, token_type="bearer", expires_in=expires_in)