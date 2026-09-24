"""
Session-scoped infrastructure fixtures for the E2E suite.

Reuses the existing docker-compose.yml's db/redis services directly (Option
A from the Phase 13 plan) rather than introducing a second container
orchestration mechanism. MCP servers are NOT containerized here — they run
as real stdio subprocesses via the same mechanism
forgesight.agents.mcp_client already uses in production.

CRITICAL: this fixture set NEVER trains a model. It requires the fixture CV
checkpoint to already exist on disk (produced by you, manually, via
notebooks/finetune_yolov8_forgesight.ipynb) and fails fast with a clear,
actionable message if it's missing.
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

import pytest

from forgesight.config.database import session_scope
from forgesight.config.settings import settings
from forgesight.rag.ingestion import ingest_document

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILE = REPO_ROOT / "docker-compose.yml"
INFRA_STARTUP_TIMEOUT_SECONDS = 60
SYNTHETIC_DOCS_DIR = REPO_ROOT / "data" / "documents" / "synthetic"


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, **kwargs)


def _wait_for_healthy(service: str, check_cmd: list[str], timeout: int) -> None:
    deadline = time.monotonic() + timeout
    last_error = ""
    while time.monotonic() < deadline:
        result = _run(check_cmd)
        if result.returncode == 0:
            return
        last_error = result.stderr or result.stdout
        time.sleep(2)
    raise RuntimeError(
        f"Service '{service}' did not become healthy within {timeout}s. "
        f"Last check output: {last_error}"
    )


@pytest.fixture(scope="session")
def e2e_infrastructure():
    """Starts db+redis via the existing docker-compose.yml, waits for their
    own healthchecks, tears down at session end regardless of outcome."""
    up_result = _run(["docker", "compose", "-f", str(COMPOSE_FILE), "up", "-d", "db", "redis"])
    if up_result.returncode != 0:
        pytest.fail(
            f"Failed to start db/redis via docker compose. "
            f"stdout: {up_result.stdout}\nstderr: {up_result.stderr}"
        )

    try:
        _wait_for_healthy(
            "db",
            ["docker", "compose", "-f", str(COMPOSE_FILE), "exec", "-T", "db", "pg_isready", "-U", "forgesight"],
            INFRA_STARTUP_TIMEOUT_SECONDS,
        )
        _wait_for_healthy(
            "redis",
            ["docker", "compose", "-f", str(COMPOSE_FILE), "exec", "-T", "redis", "redis-cli", "ping"],
            INFRA_STARTUP_TIMEOUT_SECONDS,
        )
        yield
    finally:
        _run(["docker", "compose", "-f", str(COMPOSE_FILE), "down"])


@pytest.fixture(scope="session")
def e2e_migrated_database(e2e_infrastructure):
    """Runs Alembic migrations against the real started Postgres instance."""
    result = _run(["alembic", "upgrade", "head"])
    if result.returncode != 0:
        pytest.fail(f"Alembic migration failed.\nstdout: {result.stdout}\nstderr: {result.stderr}")
    yield


@pytest.fixture(scope="session")
def e2e_ingested_corpus(e2e_migrated_database):
    """Ingests the real synthetic SOPs with real embeddings into the real
    pgvector-backed document_chunks table."""
    if not SYNTHETIC_DOCS_DIR.exists():
        pytest.fail(
            f"Synthetic SOP corpus not found at {SYNTHETIC_DOCS_DIR}. "
            f"This should already be committed from Phase 4 — check the repo state."
        )

    import asyncio

    async def _ingest_all():
        async with session_scope() as session:
            for file_path in sorted(SYNTHETIC_DOCS_DIR.glob("*.md")):
                await ingest_document(session, str(file_path))

    asyncio.run(_ingest_all())
    yield


@pytest.fixture(scope="session")
def e2e_vision_checkpoint(e2e_infrastructure):
    """
    Asserts the fixture CV checkpoint already exists on disk. NEVER trains
    a model here — per the Phase 13 decision, model training happens only
    via the notebook, run manually by a human, with the resulting checkpoint
    either committed to the repo or fetched from external storage before
    this test suite runs. This fixture fails fast and explains exactly what
    is missing rather than silently falling back to training.
    """
    checkpoint_path = Path(settings.cv_model_path)
    if not checkpoint_path.exists():
        pytest.fail(
            f"CV checkpoint not found at '{checkpoint_path}'.\n\n"
            f"This test suite does NOT train models. Produce the checkpoint by running "
            f"notebooks/finetune_yolov8_forgesight.ipynb locally, then either:\n"
            f"  (a) commit it to the repo at this exact path, or\n"
            f"  (b) fetch it from external storage as a setup step before running this suite.\n"
        )
    yield checkpoint_path


@pytest.fixture
def e2e_seeded_data(e2e_migrated_database, e2e_ingested_corpus, e2e_vision_checkpoint):
    """Runs the real seeder against the real DB. Idempotent — safe to call
    once per test function without accumulating duplicate data."""
    import asyncio

    from scripts.seed_database import main as seed_main

    asyncio.run(seed_main())
    yield {"incident_id": "INCIDENT-2026-00421", "board_id": "BRD-24017-00432"}