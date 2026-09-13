"""Unit tests for individual agent node functions, with MCP calls mocked."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from forgesight.agents.mcp_client import McpToolError
from forgesight.agents.nodes import component_lot, document_retrieval, vision_analysis
from forgesight.agents.state import new_investigation_state


def _fresh_state():
    return new_investigation_state("INCIDENT-TEST-001", "fake-token")


@pytest.mark.asyncio
async def test_vision_analysis_populates_evidence_graph_on_success() -> None:
    fake_response = {
        "board_id": "BRD-TEST-001",
        "aoi_flags": [
            {
                "component_designator": "C17",
                "defect_type": "component_misalignment",
                "confidence": 0.9,
                "bounding_box": [1, 2, 3, 4],
                "cv_finding_id": "CVF-1",
            }
        ],
    }
    with patch("forgesight.agents.nodes.vision_analysis.call_manufacturing_tool", new=AsyncMock(return_value=fake_response)):
        state = await vision_analysis.run(_fresh_state(), board_id="BRD-TEST-001")

    assert state["evidence_graph"]["vision"]["gap"] is False
    assert len(state["evidence_graph"]["vision"]["cv_findings"]) == 1
    assert 3 in state["completed_stages"]


@pytest.mark.asyncio
async def test_vision_analysis_records_gap_on_board_not_found() -> None:
    with patch(
        "forgesight.agents.nodes.vision_analysis.call_manufacturing_tool",
        new=AsyncMock(side_effect=McpToolError("BOARD_NOT_FOUND", "no such board")),
    ):
        state = await vision_analysis.run(_fresh_state(), board_id="BRD-DOES-NOT-EXIST")

    assert state["evidence_graph"]["vision"]["gap"] is True
    assert state["evidence_graph"]["vision"]["cv_findings"] == []


@pytest.mark.asyncio
async def test_document_retrieval_records_gap_never_fabricates_on_no_relevant_document() -> None:
    with patch(
        "forgesight.agents.nodes.document_retrieval.call_documents_tool",
        new=AsyncMock(side_effect=McpToolError("NO_RELEVANT_DOCUMENT_FOUND", "nothing above threshold")),
    ):
        state = await document_retrieval.run(
            _fresh_state(), defect_type="component_misalignment", component_id="C17", machine_id="PLACER-07"
        )

    assert state["evidence_graph"]["documents"]["gap"] is True
    assert state["evidence_graph"]["documents"]["passages"] == []


@pytest.mark.asyncio
async def test_component_lot_uses_correlation_only_wording() -> None:
    fake_response = {"supplier_id": "SUP-0042", "historical_defect_rate_pct": 1.8}
    with patch("forgesight.agents.nodes.component_lot.call_manufacturing_tool", new=AsyncMock(return_value=fake_response)):
        state = await component_lot.run(_fresh_state(), lot_number="LOT-9921", part_number="CAP-10UF-0603")

    statement = state["evidence_graph"]["component_lot"]["correlation_statement"]
    assert "correlation" in statement.lower()
    assert "caused" not in statement.lower()