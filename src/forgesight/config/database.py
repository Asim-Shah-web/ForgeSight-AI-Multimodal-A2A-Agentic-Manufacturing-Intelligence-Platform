"""
Async database engine and session management.

Uses psycopg (v3) as the async PostgreSQL driver, SQLModel/SQLAlchemy 2.0
async sessions, and registers the pgvector extension's SQLAlchemy type
adapter by importing pgvector.sqlalchemy at module import time.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from pgvector.sqlalchemy import Vector  # noqa: F401  (registers pgvector type)
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import SQLModel

from forgesight.config.logging import get_logger
from forgesight.config.settings import settings

logger = get_logger(__name__)

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    echo=settings.debug,
    pool_pre_ping=True,
)

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency yielding an AsyncSession.

    Commits on successful completion of the request, rolls back on any
    exception raised while the session is in use.
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def session_scope() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for use outside of FastAPI request handling
    (e.g. in the seeder script or background jobs).
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def create_db_and_tables() -> None:
    """
    Ensure the pgvector extension exists and create all tables that don't
    already exist. Used at application startup; Alembic remains the source
    of truth for schema evolution in production, but this makes local/dev
    startup self-sufficient.
    """
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(SQLModel.metadata.create_all)
    logger.info("database_initialized", extra={"event": "create_db_and_tables"})


async def dispose_engine() -> None:
    """Dispose of the async engine's connection pool on shutdown."""
    await engine.dispose()
    logger.info("database_engine_disposed")