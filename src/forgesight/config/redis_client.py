"""
Async Redis client management.

Redis is used per the Phase 2/6 data-boundary rules for ephemeral,
high-speed state (live investigation session cache, telemetry snapshot
cache) — it is never the durable system of record. PostgreSQL remains the
system of record for everything persisted here.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import redis.asyncio as redis

from forgesight.config.logging import get_logger
from forgesight.config.settings import settings

logger = get_logger(__name__)

redis_pool: redis.ConnectionPool = redis.ConnectionPool.from_url(
    settings.redis_url,
    decode_responses=True,
)


def get_redis_client() -> redis.Redis:
    """Return a Redis client bound to the shared connection pool."""
    return redis.Redis(connection_pool=redis_pool)


async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    """FastAPI dependency yielding a Redis client from the shared pool."""
    client = get_redis_client()
    try:
        yield client
    finally:
        await client.aclose()


async def check_redis_connection() -> bool:
    """Ping Redis to verify connectivity. Used by the /health endpoint."""
    client = get_redis_client()
    try:
        pong = await client.ping()
        return bool(pong)
    except Exception:  # noqa: BLE001 - health check must not raise
        logger.exception("redis_health_check_failed")
        return False
    finally:
        await client.aclose()


async def close_redis_pool() -> None:
    """Close the shared Redis connection pool on application shutdown."""
    await redis_pool.disconnect()
    logger.info("redis_pool_closed")