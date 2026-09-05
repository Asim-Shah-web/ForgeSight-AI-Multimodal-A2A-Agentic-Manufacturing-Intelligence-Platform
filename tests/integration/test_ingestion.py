"""Integration tests for document ingestion, against a real Postgres+pgvector DB."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlmodel import select

from forgesight.domain.models.knowledge import DocumentChunk, TechnicalDocument
from forgesight.rag.ingestion import ingest_document

SYNTHETIC_DOCS_DIR = Path("data/documents/synthetic")


@pytest.mark.asyncio
@pytest.mark.skipif(not SYNTHETIC_DOCS_DIR.exists(), reason="synthetic SOP fixtures not present")
async def test_ingest_document_creates_document_and_chunks(session) -> None:
    file_path = SYNTHETIC_DOCS_DIR / "SOP-QUAL-042.md"
    document = await ingest_document(session, str(file_path))
    await session.commit()

    assert document.document_id == "SOP-QUAL-042"

    result = await session.execute(
        select(DocumentChunk).where(
            DocumentChunk.document_id == "SOP-QUAL-042",
            DocumentChunk.status == "active",
        )
    )
    chunks = result.scalars().all()
    assert len(chunks) > 0
    assert all(chunk.embedding is not None for chunk in chunks)
    assert all(len(chunk.embedding) == 1024 for chunk in chunks)


@pytest.mark.asyncio
@pytest.mark.skipif(not SYNTHETIC_DOCS_DIR.exists(), reason="synthetic SOP fixtures not present")
async def test_reingesting_same_version_is_idempotent(session) -> None:
    file_path = SYNTHETIC_DOCS_DIR / "SOP-MAINT-017.md"
    await ingest_document(session, str(file_path))
    await session.commit()

    result_before = await session.execute(
        select(DocumentChunk).where(
            DocumentChunk.document_id == "SOP-MAINT-017", DocumentChunk.status == "active"
        )
    )
    count_before = len(result_before.scalars().all())

    await ingest_document(session, str(file_path))
    await session.commit()

    result_after = await session.execute(
        select(DocumentChunk).where(
            DocumentChunk.document_id == "SOP-MAINT-017", DocumentChunk.status == "active"
        )
    )
    assert len(result_after.scalars().all()) == count_before


@pytest.mark.asyncio
@pytest.mark.skipif(not SYNTHETIC_DOCS_DIR.exists(), reason="synthetic SOP fixtures not present")
async def test_new_version_retires_prior_chunks(session, tmp_path) -> None:
    original_path = SYNTHETIC_DOCS_DIR / "SOP-PROC-031.md"
    await ingest_document(session, str(original_path))
    await session.commit()

    raw_text = original_path.read_text(encoding="utf-8")
    bumped_text = raw_text.replace("version: v1.0", "version: v1.1", 1)
    bumped_path = tmp_path / "SOP-PROC-031-v1.1.md"
    bumped_path.write_text(bumped_text, encoding="utf-8")

    await ingest_document(session, str(bumped_path))
    await session.commit()

    retired_result = await session.execute(
        select(DocumentChunk).where(
            DocumentChunk.document_id == "SOP-PROC-031", DocumentChunk.status == "retired"
        )
    )
    active_result = await session.execute(
        select(DocumentChunk).where(
            DocumentChunk.document_id == "SOP-PROC-031", DocumentChunk.status == "active"
        )
    )
    assert len(retired_result.scalars().all()) > 0
    assert len(active_result.scalars().all()) > 0

    document_result = await session.execute(
        select(TechnicalDocument).where(TechnicalDocument.document_id == "SOP-PROC-031")
    )
    assert document_result.scalar_one().version == "v1.1"