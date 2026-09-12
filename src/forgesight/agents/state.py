"""
LangGraph state schema — implements InvestigationContext from Phase 6
Section 3.1 as a TypedDict, the shape LangGraph state graphs require.
"""

from __future__ import annotations

from typing import Any, TypedDict


class InvestigationState(TypedDict):
    incident_id: str
    current_stage: int
    status: str  # "in_progress" | "awaiting_approval" | "complete" | "failed"
    evidence_graph: dict[str, Any]
    completed_stages: list[int]
    pending_approvals: list[dict[str, Any]]
    agent_results: dict[str, Any]
    # Short-lived JWT for the AGENT_ORCHESTRATOR system identity. Never
    # logged or traced — deliberately excluded from any log/span attribute
    # set anywhere in this codebase.
    orchestrator_token: str


def new_investigation_state(incident_id: str, orchestrator_token: str) -> InvestigationState:
    """Construct a fresh InvestigationState for a newly started investigation."""
    return InvestigationState(
        incident_id=incident_id,
        current_stage=2,  # Stage 1 (threshold trigger) precedes agent involvement
        status="in_progress",
        evidence_graph={},
        completed_stages=[],
        pending_approvals=[],
        agent_results={},
        orchestrator_token=orchestrator_token,
    )