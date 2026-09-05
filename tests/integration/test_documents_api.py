"""Integration tests for the /api/v1/documents routes."""

from __future__ import annotations

from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlmodel import select

from forgesight.config import database as db_module
from forgesight.domain.models.audit import AuditEvent, AuditEventType
from forgesight.domain.models.users import UserRole
from forgesight.rag.ingestion import ingest_document

SYNTHETIC_DOCS_DIR = Path("data/documents/synthetic")


@pytest.fixture(scope="module", autouse=True)
def _skip_if_no_fixtures():
    if not SYNTHETIC_DOCS_DIR.exists():
        pytest.skip("synthetic SOP fixtures not present")


@pytest.mark.asyncio
async def test_search_returns_relevant_passage_for_qe(
    client: AsyncClient, users_per_role, make_auth_headers
) -> None:
    async with db_module.AsyncSessionFactory() as session:
        await ingest_document(session, str(SYNTHETIC_DOCS_DIR / "SOP-QUAL-042.md"))
        await session.commit()

    qe = users_per_role[UserRole.QUALITY_ENGINEER]
    response = await client.get(
        "/api/v1/documents/search",
        params={"query": "placement tolerance for a 10uF capacitor C17"},
        headers=make_auth_headers(qe),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["no_relevant_document_found"] is False
    assert body["result_count"] > 0
    assert any(p["document_id"] == "SOP-QUAL-042" for p in body["passages"])


@pytest.mark.asyncio
async def test_search_returns_no_relevant_document_for_unrelated_query(
    client: AsyncClient, users_per_role, make_auth_headers
) -> None:
    qe = users_per_role[UserRole.QUALITY_ENGINEER]
    response = await client.get(
        "/api/v1/documents/search",
        params={"query": "unrelated nonsense xyz123 quantum flux capacitor banana"},
        headers=make_auth_headers(qe),
    )
    assert response.status_code == 200
    body = response.json()
    if body["result_count"] == 0:
        assert body["no_relevant_document_found"] is True


@pytest.mark.asyncio
async def test_search_unauthenticated_returns_401(client: AsyncClient) -> None:
    response = await client.get("/api/v1/documents/search", params={"query": "anything"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_nonexistent_document_returns_404(
    client: AsyncClient, users_per_role, make_auth_headers
) -> None:
    qe = users_per_role[UserRole.QUALITY_ENGINEER]
    response = await client.get(
        "/api/v1/documents/SOP-DOES-NOT-EXIST-9999", headers=make_auth_headers(qe)
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_search_creates_rag_retrieval_audit_event(
    client: AsyncClient, users_per_role, make_auth_headers
) -> None:
    async with db_module.AsyncSessionFactory() as session:
        await ingest_document(session, str(SYNTHETIC_DOCS_DIR / "SOP-SUPP-008.md"))
        await session.commit()

    qe = users_per_role[UserRole.QUALITY_ENGINEER]
    await client.get(
        "/api/v1/documents/search",
        params={"query": "incoming lot sampling plan"},
        headers=make_auth_headers(qe),
    )

    async with db_module.AsyncSessionFactory() as session:
        result = await session.execute(
            select(AuditEvent).where(
                AuditEvent.who == qe.user_id,
                AuditEvent.what == AuditEventType.RAG_RETRIEVAL,
            )
        )
        assert len(result.scalars().all()) >= 1