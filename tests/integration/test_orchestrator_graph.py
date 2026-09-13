"""
Integration tests for the full LangGraph orchestrator, run against the
seeded INCIDENT-2026-00421 scenario with MCP tool calls mocked and LLM
calls mocked, but real checkpoint persistence against the test Postgres DB.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from forgesight.agents.llm_client import LlmResponse


def _mock_llm_response(content_dict) -> LlmResponse:
    return LlmResponse(
        content=json.dumps(content_dict), model_name="llama-3.3-70b-versatile", prompt_tokens=10, completion_tokens=10
    )


@pytest.fixture
def mocked_mcp_and_llm():
    """Patch every MCP tool call and LLM call used across all 10 nodes with
    deterministic, evidence-consistent fake responses."""

    manufacturing_responses = {
        "get_board_inspection_data": {"board_id": "BRD-24017-00432", "aoi_flags": []},
        "get_production_telemetry": {"machine_id": "PLACER-07", "batch_id": "B-24017", "telemetry": []},
        "get_machine_maintenance_history": {"machine_id": "PLACER-07", "maintenance_records": []},
        "get_component_lot_history": {"supplier_id": "SUP-0042", "historical_defect_rate_pct": 1.8},
    }
    documents_responses = {
        "search_technical_sops": {"results": []},
        "search_historical_incidents": {"results": []},
    }

    async def fake_manufacturing_call(tool_name, *_args, **_kwargs):
        return manufacturing_responses.get(tool_name, {})

    async def fake_documents_call(tool_name, *_args, **_kwargs):
        return documents_responses.get(tool_name, {})

    hypothesis_llm_output = [
        {
            "conclusion": "Nozzle wear on PLACER-07 contributed to C17 misalignment.",
            "supporting_evidence_refs": ["maintenance"],
            "contradicting_evidence_refs": [],
            "confidence_level": 0.7,
            "reasoning_summary": "Maintenance record shows overdue cleaning correlated with defect timing.",
            "rank": 1,
        }
    ]
    correlation_llm_output = {"nodes": [], "edges": [], "contradictions": [], "gaps": []}
    corrective_action_llm_output = {
        "proposed_action": "Clean and inspect nozzle NZ-07-03 on PLACER-07.",
        "supporting_evidence_refs": ["maintenance"],
        "requires_approval_by": "Maintenance Engineer",
    }
    report_llm_output = {"narrative": "Investigation summary.", "sections_included": ["evidence", "hypothesis"]}

    async def fake_call_llm(agent_name, *_args, **_kwargs):
        if agent_name == "EvidenceCorrelationAgent":
            return _mock_llm_response(correlation_llm_output)
        if agent_name == "HypothesisRankingAgent":
            return _mock_llm_response(hypothesis_llm_output)
        if agent_name == "CorrectiveActionAgent":
            return _mock_llm_response(corrective_action_llm_output)
        if agent_name == "ReportGenerationAgent":
            return _mock_llm_response(report_llm_output)
        raise AssertionError(f"Unexpected agent calling LLM: {agent_name}")

    with patch("forgesight.agents.mcp_client.call_manufacturing_tool", new=AsyncMock(side_effect=fake_manufacturing_call)), \
         patch("forgesight.agents.mcp_client.call_documents_tool", new=AsyncMock(side_effect=fake_documents_call)), \
         patch("forgesight.agents.llm_client.call_llm", new=AsyncMock(side_effect=fake_call_llm)):
        yield


@pytest.mark.asyncio
async def test_investigation_stops_at_hypothesis_gate_never_auto_proceeds(mocked_mcp_and_llm) -> None:
    """Direct test of Mandatory Rule 9: even with a single, well-formed
    hypothesis, the graph must not reach corrective_action without a
    resolved interrupt."""
    from forgesight.agents.orchestrator import start_investigation

    result = await start_investigation("INCIDENT-2026-00421")

    assert result["status"] == "awaiting_approval"
    assert "CorrectiveActionAgent" not in result["agent_results"]
    assert any(a["gate"] == "hypothesis_confirmation" for a in result["pending_approvals"])


@pytest.mark.asyncio
async def test_resume_with_approval_advances_to_corrective_action_then_interrupts_again(mocked_mcp_and_llm) -> None:
    from forgesight.agents.orchestrator import resume_investigation, start_investigation

    await start_investigation("INCIDENT-2026-00421")
    result = await resume_investigation("INCIDENT-2026-00421", approved=True, approver_role="quality_engineer")

    assert "CorrectiveActionAgent" in result["agent_results"]
    assert "ReportGenerationAgent" not in result["agent_results"]
    assert result["status"] == "awaiting_approval"
    assert any(a["gate"] == "corrective_action_approval" and a["status"] == "pending" for a in result["pending_approvals"])


@pytest.mark.asyncio
async def test_resume_with_rejection_does_not_advance_forward(mocked_mcp_and_llm) -> None:
    from forgesight.agents.orchestrator import resume_investigation, start_investigation

    await start_investigation("INCIDENT-2026-00421")
    result = await resume_investigation("INCIDENT-2026-00421", approved=False, approver_role="quality_engineer")

    assert result["status"] == "failed"
    assert "CorrectiveActionAgent" not in result["agent_results"]


@pytest.mark.asyncio
async def test_checkpoint_survives_reload_via_fresh_state_fetch(mocked_mcp_and_llm) -> None:
    """Proves checkpointing (not just in-process state) — fetches state via
    a fresh compiled-graph reference rather than reusing the in-memory
    result object returned by start_investigation."""
    from forgesight.agents.orchestrator import get_compiled_graph, start_investigation

    await start_investigation("INCIDENT-2026-00421")

    compiled_graph = await get_compiled_graph()
    config = {"configurable": {"thread_id": "INCIDENT-2026-00421"}}
    reloaded_state = await compiled_graph.aget_state(config)

    assert reloaded_state is not None
    assert reloaded_state.values["status"] == "awaiting_approval"
    assert 9 in reloaded_state.values["completed_stages"]