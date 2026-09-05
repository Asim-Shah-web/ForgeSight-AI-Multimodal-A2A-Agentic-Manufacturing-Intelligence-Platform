"""Health check route: GET /health. Publicly accessible, no auth required."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlmodel.ext.asyncio.session import AsyncSession

from forgesight.config.database import get_session
from forgesight.config.logging import get_logger
from forgesight.config.redis_client import check_redis_connection
from forgesight.config.settings import settings

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check(session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    """
    Returns overall service health, including real connectivity checks
    against PostgreSQL and Redis (not just process liveness).
    """
    db_status = "ok"
    try:
        await session.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001 - health check must not raise
        logger.exception("health_check_db_failed")
        db_status = "error"

    redis_status = "ok" if await check_redis_connection() else "error"

    overall_status = "ok" if db_status == "ok" and redis_status == "ok" else "degraded"

    return {
        "status": overall_status,
        "version": settings.app_version,
        "db": db_status,
        "redis": redis_status,
    }