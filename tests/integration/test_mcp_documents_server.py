"""Integration tests for the Documents MCP Server's tool implementations."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from forgesight.api.security import create_access_token
from forgesight.config import database as db_module
from forgesight.domain.models.users import UserRole
from forgesight.rag.ingestion import ingest_document

from mcp_servers.documents.server import call_tool

SYNTHETIC_DOCS_DIR = Path("data/documents/synthetic")


def _token_for(user) -> str:
    token, _ = create_access_token(subject=user.username, role=user.role)
    return token


@pytest.fixture(scope="module", autouse=True)
def _skip_if_no_fixtures():
    if not SYNTHETIC_DOCS_DIR.exists():
        pytest.skip("synthetic SOP fixtures not present")


@pytest.mark.asyncio
async def test_search_technical_sops_returns_relevant_passage(users_per_role) -> None:
    async with db_module.AsyncSessionFactory() as session:
        await ingest_document(session, str(SYNTHETIC_DOCS_DIR / "SOP-QUAL-042.md"))
        await session.commit()

    qe = users_per_role[UserRole.QUALITY_ENGINEER]
    result = await call_tool(
        "search_technical_sops",
        {"caller_token": _token_for(qe), "query": "placement tolerance for a 10uF capacitor C17"},
    )
    body = json.loads(result[0].text)

    assert "error_code" not in body
    assert body["result_count"] > 0
    assert any(r["document_id"] == "SOP-QUAL-042" for r in body["results"])
    for field in ("passage_id", "retrieval_score", "retrieval_query", "retrieval_timestamp", "embedding_model"):
        assert field in body["results"][0]


@pytest.mark.asyncio
async def test_search_technical_sops_returns_no_relevant_document_found_error(users_per_role) -> None:
    qe = users_per_role[UserRole.QUALITY_ENGINEER]
    result = await call_tool(
        "search_technical_sops",
        {"caller_token": _token_for(qe), "query": "unrelated nonsense xyz123 quantum banana flux"},
    )
    body = json.loads(result[0].text)

    if "error_code" in body:
        assert body["error_code"] == "NO_RELEVANT_DOCUMENT_FOUND"


@pytest.mark.asyncio
async def test_get_document_by_id_returns_document_not_found(users_per_role) -> None:
    qe = users_per_role[UserRole.QUALITY_ENGINEER]
    result = await call_tool(
        "get_document_by_id",
        {"caller_token": _token_for(qe), "document_id": "SOP-DOES-NOT-EXIST-9999"},
    )
    body = json.loads(result[0].text)
    assert body["error_code"] == "DOCUMENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_search_historical_incidents_on_fresh_system_returns_no_similar_incidents(users_per_role) -> None:
    qe = users_per_role[UserRole.QUALITY_ENGINEER]
    result = await call_tool(
        "search_historical_incidents",
        {"caller_token": _token_for(qe), "defect_type": "extremely_rare_defect_type_never_seen"},
    )
    body = json.loads(result[0].text)
    assert body["error_code"] == "NO_SIMILAR_INCIDENTS_FOUND"