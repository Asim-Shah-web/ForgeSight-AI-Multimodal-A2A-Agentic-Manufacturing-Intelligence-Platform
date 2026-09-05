"""
JWT authentication and RBAC enforcement.

RBAC permission mapping is derived directly from the Phase 1 persona
permission matrix (docs/business/personas.md Section 5.3). No endpoint in
this codebase is reachable without either being explicitly listed as public
(/health, /auth/token) or protected by `require_roles(...)`.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from forgesight.config.database import get_session
from forgesight.config.logging import get_logger
from forgesight.config.settings import settings
from forgesight.domain.models.users import User, UserRole

logger = get_logger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# JWT token creation / verification
# ---------------------------------------------------------------------------

def create_access_token(*, subject: str, role: UserRole) -> tuple[str, int]:
    """
    Create a signed JWT access token.

    Returns a tuple of (token, expires_in_seconds) so callers can populate
    the OAuth2 token response body without recomputing expiry.
    """
    expire_delta = timedelta(minutes=settings.access_token_expire_minutes)
    expire_at = datetime.now(timezone.utc) + expire_delta
    payload = {
        "sub": subject,
        "role": role.value,
        "exp": expire_at,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return token, int(expire_delta.total_seconds())


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token. Raises JWTError if invalid/expired."""
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])


# ---------------------------------------------------------------------------
# FastAPI dependency: resolve the current authenticated user
# ---------------------------------------------------------------------------

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """
    Resolve the JWT bearer token to an active User row.

    Raises HTTP 401 for any invalid, expired, or unresolvable token, and for
    a token that resolves to a deactivated user.
    """
    try:
        payload = decode_access_token(token)
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise CREDENTIALS_EXCEPTION
    except JWTError as exc:
        logger.warning("jwt_decode_failed", extra={"error": str(exc)})
        raise CREDENTIALS_EXCEPTION from exc

    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise CREDENTIALS_EXCEPTION
    return user


# ---------------------------------------------------------------------------
# RBAC permission matrix (Phase 1 personas.md Section 5.3)
# ---------------------------------------------------------------------------

ROLE_PERMISSIONS: dict[UserRole, set[str]] = {
    UserRole.PRODUCTION_OPERATOR: {
        "incident:create",
        "incident:read_own",
        "evidence:submit",
    },
    UserRole.QUALITY_ENGINEER: {
        "incident:read",
        "incident:modify",
        "incident:approve",
        "evidence:read",
        "evidence:submit",
        "hypothesis:read",
        "hypothesis:modify",
        "hypothesis:approve",
        "corrective_action:read",
        "corrective_action:approve",
        "report:read",
        "report:generate",
    },
    UserRole.MANUFACTURING_ENGINEER: {
        "incident:read",
        "evidence:read",
        "hypothesis:read",
        "process_change:recommend",
        "report:read",
    },
    UserRole.MAINTENANCE_ENGINEER: {
        "incident:read",
        "evidence:read",
        "maintenance:read",
        "maintenance:recommend",
        "work_order:approve",
        "report:read",
    },
    UserRole.QUALITY_MANAGER: {
        "incident:read",
        "incident:modify",
        "incident:approve",
        "incident:escalate",
        "evidence:read",
        "hypothesis:read",
        "hypothesis:approve",
        "corrective_action:read",
        "corrective_action:approve",
        "high_risk_hold:approve",
        "audit:request",
        "report:read",
        "report:generate",
    },
    UserRole.SUPPLIER_QUALITY_ENGINEER: {
        "incident:read",
        "evidence:read",
        "component_lot:read",
        "supplier:read",
        "scar:approve",
        "report:read",
    },
    UserRole.SYSTEM_ADMINISTRATOR: {
        "user:create",
        "user:read",
        "user:modify_role",
        "system_config:modify",
        "audit:read",
        # Deliberately excludes every quality-approval permission
        # (incident:approve, hypothesis:approve, corrective_action:approve,
        # high_risk_hold:approve, scar:approve) — technical administration
        # never unlocks manufacturing/quality approval authority (SEC-003).
    },
}


def role_has_permission(role: UserRole, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())


def require_roles(*allowed_roles: UserRole):
    """
    Returns a FastAPI dependency that checks the current user's role against
    `allowed_roles`. Raises HTTP 403 if the current user's role is not in
    the allowed set.

    Usage:
        @router.get(
            "/incidents",
            dependencies=[Depends(require_roles(UserRole.QUALITY_ENGINEER, UserRole.QUALITY_MANAGER))],
        )
    """

    async def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            logger.warning(
                "rbac_denied",
                extra={
                    "user_id": str(current_user.user_id),
                    "role": current_user.role.value,
                    "allowed_roles": [r.value for r in allowed_roles],
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return current_user

    return _checker


def require_permission(permission: str):
    """
    Returns a FastAPI dependency that checks whether the current user's role
    grants the given fine-grained permission string (per ROLE_PERMISSIONS).
    """

    async def _checker(current_user: User = Depends(get_current_user)) -> User:
        if not role_has_permission(current_user.role, permission):
            logger.warning(
                "rbac_permission_denied",
                extra={
                    "user_id": str(current_user.user_id),
                    "role": current_user.role.value,
                    "permission": permission,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role.value}' lacks permission '{permission}'.",
            )
        return current_user

    return _checker