"""
Alembic environment configuration for ForgeSight AI.

- Uses the async engine pattern (run_sync inside an async connection) since
  the application itself is fully async (psycopg async driver).
- Imports every SQLModel table model so SQLModel.metadata is complete before
  autogenerate runs a diff.
- Ensures the pgvector extension exists before any table DDL is compared/run,
  so pgvector column types (Vector(1024)) are detected correctly.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool, text
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlmodel import SQLModel

# Import every domain model module so SQLModel.metadata is fully populated.
# This import is required even though the names aren't used directly below.
from forgesight.domain.models import (  # noqa: F401
    AuditEvent,
    Batch,
    Board,
    Component,
    ComponentLot,
    CorrectiveAction,
    CvFinding,
    DocumentChunk,
    Feeder,
    Incident,
    IncidentEmbedding,
    InspectionImage,
    Line,
    Machine,
    MaintenanceRecord,
    Nozzle,
    Product,
    ProductionTelemetry,
    ReflowProfile,
    Report,
    RootCauseHypothesis,
    Supplier,
    TechnicalDocument,
    User,
    WorkOrder,
)
from forgesight.config.settings import settings

# Alembic Config object, provides access to values in alembic.ini
config = context.config

# Override the sqlalchemy.url from alembic.ini with the application's
# settings-derived database URL — never hardcode or duplicate it here.
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# SQLModel.metadata is the single source of truth for autogenerate diffing.
target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generates SQL without a live DB)."""
    url = settings.database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        # Ensures pgvector's Vector column type is compared correctly rather
        # than triggering spurious diffs on every autogenerate run.
        render_item=_render_item,
    )

    with context.begin_transaction():
        # Guarantee the extension exists before any DDL comparison/execution.
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        context.run_migrations()


def _render_item(type_, obj, autogen_context):
    """Let pgvector's Vector type render naturally; return False to fall back
    to Alembic's default rendering for every other type."""
    return False


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode using an async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()