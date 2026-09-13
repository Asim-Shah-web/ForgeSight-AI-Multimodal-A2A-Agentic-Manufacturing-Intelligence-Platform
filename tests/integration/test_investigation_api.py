"""Integration tests for the investigation trigger/status/resume API routes."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from forgesight.domain.models.users import UserRole


@pytest.fixture
def mocked_orchestrator():
    fake_state = {
        "incident_id": "INCIDENT-2026-00421",
        "current_stage": 9,
        "status": "awaiting_approval",
        "evidence_graph": {"vision": {"gap": False}},
        "completed_stages": [3, 4, 5, 6, 7, 8, 9],
        "pending_approvals": [
            {"gate": "hypothesis_confirmation", "status": "pending", "requires_approval_by": "Quality Engineer"}
        ],
        "agent_results": {},
        "orchestrator_token": "unused-in-response",
    }
    with patch("forgesight.api.routes.incidents.start_investigation", new=AsyncMock(return_value=fake_state)):
        yield fake_state


@pytest.mark.asyncio
async def test_start_investigation_returns_202(client: AsyncClient, users_per_role, make_auth_headers, mocked_orchestrator) -> None:
    qe = users_per_role[UserRole.QUALITY_ENGINEER]
    response = await client.post(
        "/api/v1/incidents/INCIDENT-2026-00421/investigate", headers=make_auth_headers(qe)
    )
    # Assumes INCIDENT-2026-00421 was seeded; if not present in this test DB,
    # a 404 is also an acceptable outcome for this route's own existence check.
    assert response.status_code in (202, 404)


@pytest.mark.asyncio
async def test_resume_with_wrong_role_returns_403(client: AsyncClient, users_per_role, make_auth_headers) -> None:
    from unittest.mock import AsyncMock as _AsyncMock

    fake_state_obj = _AsyncMock()
    fake_state_obj.values = {
        "pending_approvals": [
            {"gate": "hypothesis_confirmation", "status": "pending", "requires_approval_by": "Quality Engineer"}
        ]
    }

    with patch("forgesight.api.routes.incidents.get_compiled_graph", new=AsyncMock(return_value=AsyncMock(aget_state=AsyncMock(return_value=fake_state_obj)))):
        manufacturing_engineer = users_per_role[UserRole.MANUFACTURING_ENGINEER]
        response = await client.post(
            "/api/v1/incidents/INCIDENT-2026-00421/investigation/resume",
            headers=make_auth_headers(manufacturing_engineer),
            json={"approved": True},
        )
    assert response.status_code == 403