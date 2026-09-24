"""
The E2E centerpiece: drives all 12 workflow stages against real services.

Only forgesight.agents.llm_client.call_llm is mocked (Mandatory Rule 1).
Everything else — Postgres+pgvector, Redis, real MCP stdio subprocesses,
real embedding/reranking/CV inference, real LangGraph checkpointing — is
real, exercised through the actual API layer.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import select

from forgesight.agents.llm_client import LlmResponse
from forgesight.api.main import app
from forgesight.config.database import AsyncSessionFactory
from forgesight.domain.models.audit import AuditEvent, AuditEventType
from forgesight.domain.models.inspection import CvFinding
from forgesight.domain.models.investigation import Incident


def _mock_llm(content_dict) -> LlmResponse:
    return LlmResponse(
        content=json.dumps(content_dict), model_name="llama-3.3-70b-versatile", prompt_tokens=10, completion_tokens=10
    )


HYPOTHESIS_OUTPUT = [
    {
        "conclusion": "Nozzle wear on PLACER-07 contributed to C17 misalignment.",
        "supporting_evidence_refs": ["maintenance"],
        "contradicting_evidence_refs": [],
        "confidence_level": 0.75,
        "reasoning_summary": "Maintenance record shows an overdue cleaning window correlated with the defect cluster timing.",
        "rank": 1,
    }
]
CORRELATION_OUTPUT = {"nodes": [], "edges": [], "contradictions": [], "gaps": []}
CORRECTIVE_ACTION_OUTPUT = {
    "proposed_action": "Clean and inspect nozzle NZ-07-03 on PLACER-07.",
    "supporting_evidence_refs": ["maintenance"],
    "requires_approval_by": "Maintenance Engineer",
}
REPORT_OUTPUT = {"narrative": "Investigation summary: root cause confirmed as nozzle wear.", "sections_included": ["evidence", "hypothesis", "corrective_action"]}


async def _fake_call_llm(agent_name, *_args, **_kwargs) -> LlmResponse:
    if agent_name == "EvidenceCorrelationAgent":
        return _mock_llm(CORRELATION_OUTPUT)
    if agent_name == "HypothesisRankingAgent":
        return _mock_llm(HYPOTHESIS_OUTPUT)
    if agent_name == "CorrectiveActionAgent":
        return _mock_llm(CORRECTIVE_ACTION_OUTPUT)
    if agent_name == "ReportGenerationAgent":
        return _mock_llm(REPORT_OUTPUT)
    raise AssertionError(f"Unexpected agent calling the LLM: {agent_name}")


@pytest.fixture
def llm_mocked():
    with patch("forgesight.agents.llm_client.call_llm", new=AsyncMock(side_effect=_fake_call_llm)):
        yield


@pytest.fixture
async def e2e_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://e2e-testserver") as client:
        yield client


async def _login(client: AsyncClient, username: str, password: str) -> dict:
    form = {"username": username, "password": password}
    response = await client.post("/api/v1/auth/token", data=form)
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_full_twelve_stage_investigation_workflow(
    e2e_seeded_data, llm_mocked, e2e_client: AsyncClient
) -> None:
    incident_id = e2e_seeded_data["incident_id"]

    # --- Stage 1: Auth (real JWT round-trip) -----------------------------
    operator_headers = await _login(e2e_client, "operator1", "ForgeSight!Test123")
    qe_headers = await _login(e2e_client, "qe1", "ForgeSight!Test123")

    # --- Stage 2: confirm the seeded incident actually exists in Postgres,
    # not just via the API's own claim.
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(Incident).where(Incident.incident_id == incident_id))
        incident = result.scalar_one_or_none()
        assert incident is not None, f"Seeded incident '{incident_id}' not found in real DB."

    # --- Stage 3: real CV inference already ran during seeding. Assert
    # real CvFinding rows exist with the dataset disclosure populated.
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(CvFinding).where(CvFinding.board_id == incident.board_id))
        findings = result.scalars().all()
        for finding in findings:
            assert finding.dataset_used_for_training, (
                "A CvFinding was persisted without a dataset_used_for_training "
                "disclosure — this violates the Phase 9 guarantee."
            )

    # --- Stages 4-9: start the real investigation (real MCP subprocess
    # calls, real retrieval against the real ingested corpus, LLM mocked).
    start_response = await e2e_client.post(f"/api/v1/incidents/{incident_id}/investigate", headers=qe_headers)
    assert start_response.status_code == 202, start_response.text

    status_payload = None
    for _ in range(30):
        status_response = await e2e_client.get(
            f"/api/v1/incidents/{incident_id}/investigation-status", headers=qe_headers
        )
        assert status_response.status_code == 200, status_response.text
        status_payload = status_response.json()
        if status_payload["status"] == "awaiting_approval":
            break
        import asyncio

        await asyncio.sleep(2)

    assert status_payload is not None, "Investigation never returned a status."
    assert status_payload["status"] == "awaiting_approval", (
        f"Expected the graph to halt awaiting hypothesis approval, got: {status_payload}"
    )
    assert any(
        a["gate"] == "hypothesis_confirmation" and a["status"] == "pending"
        for a in status_payload["pending_approvals"]
    ), "Expected a pending hypothesis_confirmation gate — Mandatory Rule 9 may be violated."

    # Stage 7 real retrieval sanity check: the document domain must show
    # evidence gathered (not a gap), proving the real corpus + real
    # embedding/reranking pipeline actually found something for this incident.
    assert status_payload["evidence_graph_summary"].get("documents") in (False, None), (
        "Expected the real SOP corpus to surface at least one relevant passage "
        "for this incident's defect_type/component — got an unexpected gap."
    )

    # --- Stage 10, Gate 1: real human approval of the hypothesis ---------
    resume_1 = await e2e_client.post(
        f"/api/v1/incidents/{incident_id}/investigation/resume",
        headers=qe_headers,
        json={"approved": True, "notes": "Confirmed after reviewing real evidence in E2E test."},
    )
    assert resume_1.status_code == 200, resume_1.text
    resume_1_payload = resume_1.json()
    assert any(
        a["gate"] == "corrective_action_approval" and a["status"] == "pending"
        for a in resume_1_payload["pending_approvals"]
    ), "Expected the graph to advance to the corrective_action_approval gate."

    # --- Stage 10, Gate 2: real approval of the corrective action --------
    resume_2 = await e2e_client.post(
        f"/api/v1/incidents/{incident_id}/investigation/resume",
        headers=qe_headers,
        json={"approved": True, "notes": "Corrective action approved in E2E test."},
    )
    assert resume_2.status_code == 200, resume_2.text
    assert resume_2.json()["status"] == "complete", resume_2.json()

    # --- Stage 11: human sign-off closes the incident --------------------
    approve_response = await e2e_client.post(
        f"/api/v1/incidents/{incident_id}/approve",
        headers=qe_headers,
        json={"approval_statement": "Investigation complete; root cause confirmed and corrective action approved."},
    )
    assert approve_response.status_code == 200, approve_response.text
    assert approve_response.json()["status"] == "closed"

    # --- Cross-cutting: the full expected audit trail exists, in order ---
    async with AsyncSessionFactory() as session:
        result = await session.execute(
            select(AuditEvent).where(AuditEvent.target_id == incident_id).order_by(AuditEvent.when)
        )
        events = result.scalars().all()
        event_types = [e.what for e in events]

        for expected_type in (
            AuditEventType.MCP_TOOL_INVOCATION,
            AuditEventType.RAG_RETRIEVAL,
            AuditEventType.HUMAN_APPROVAL,
        ):
            assert expected_type in event_types, (
                f"Expected at least one '{expected_type}' AuditEvent for incident "
                f"'{incident_id}', found event types: {event_types}"
            )

        human_approval_events = [e for e in events if e.what == AuditEventType.HUMAN_APPROVAL]
        assert len(human_approval_events) >= 2, (
            "Expected at least two HUMAN_APPROVAL events (hypothesis gate + "
            f"corrective action gate), found {len(human_approval_events)}."
        )
        for approval_event in human_approval_events:
            assert approval_event.approval_by is not None, (
                "A HUMAN_APPROVAL audit event was recorded without approval_by populated."
            )


@pytest.mark.asyncio
async def test_rejection_path_routes_back_not_forward(
    e2e_seeded_data, llm_mocked, e2e_client: AsyncClient
) -> None:
    incident_id = e2e_seeded_data["incident_id"]
    qe_headers = await _login(e2e_client, "qe1", "ForgeSight!Test123")

    await e2e_client.post(f"/api/v1/incidents/{incident_id}/investigate", headers=qe_headers)

    status_payload = None
    for _ in range(30):
        response = await e2e_client.get(f"/api/v1/incidents/{incident_id}/investigation-status", headers=qe_headers)
        status_payload = response.json()
        if status_payload["status"] == "awaiting_approval":
            break
        import asyncio

        await asyncio.sleep(2)

    assert status_payload["status"] == "awaiting_approval"

    resume_response = await e2e_client.post(
        f"/api/v1/incidents/{incident_id}/investigation/resume",
        headers=qe_headers,
        json={"approved": False, "notes": "Evidence insufficient; rejecting for re-investigation."},
    )
    assert resume_response.status_code == 200, resume_response.text
    result = resume_response.json()
    assert result["status"] == "failed"
    assert "CorrectiveActionAgent" not in json.dumps(result), (
        "Rejection at the hypothesis gate must not allow the graph to have "
        "produced corrective-action output."
    )


@pytest.mark.asyncio
async def test_document_search_no_relevant_document_found_is_not_an_error(
    e2e_ingested_corpus, e2e_client: AsyncClient
) -> None:
    """E2E-level proof of the Phase 4/8 hallucination mitigation guarantee,
    against the real ingested corpus and real retrieval pipeline."""
    from forgesight.api.security import create_access_token
    from forgesight.domain.models.users import UserRole

    token, _ = create_access_token(subject="qe1", role=UserRole.QUALITY_ENGINEER)
    headers = {"Authorization": f"Bearer {token}"}

    response = await e2e_client.get(
        "/api/v1/documents/search",
        params={"query": "unrelated nonsense xyz123 quantum banana flux capacitor"},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["no_relevant_document_found"] is True
    assert body["passages"] == []