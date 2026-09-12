"""HistoricalIncidentAgent — Stage 9. Wraps search_historical_incidents."""

from __future__ import annotations

from forgesight.agents.mcp_client import McpToolError, call_documents_tool
from forgesight.agents.schemas import HistoricalIncidentOutput, SimilarIncidentSummary
from forgesight.agents.state import InvestigationState
from forgesight.config.logging import get_logger
from forgesight.observability.tracing import agent_span

logger = get_logger(__name__)

AGENT_NAME = "HistoricalIncidentAgent"
STAGE = 9


async def run(state: InvestigationState, defect_type: str, component_id: str) -> InvestigationState:
    with agent_span(AGENT_NAME, state["incident_id"], STAGE, "agent_node"):
        try:
            raw = await call_documents_tool(
                "search_historical_incidents",
                state["orchestrator_token"],
                AGENT_NAME,
                state["incident_id"],
                STAGE,
                defect_type=defect_type,
                component_id=component_id,
            )
            output = HistoricalIncidentOutput(
                matches=[
                    SimilarIncidentSummary(
                        incident_id=m["incident_id"],
                        defect_type=m["defect_type"],
                        root_cause_confirmed=m.get("root_cause_confirmed"),
                        similarity_score=m["similarity_score"],
                    )
                    for m in raw.get("results", [])
                ],
                gap=False,
            )
        except McpToolError as exc:
            logger.info("historical_incident_gap", extra={"error_code": exc.error_code})
            output = HistoricalIncidentOutput(matches=[], gap=True)

        state["evidence_graph"]["historical"] = output.model_dump()
        state["agent_results"][AGENT_NAME] = output.model_dump()
        if STAGE not in state["completed_stages"]:
            state["completed_stages"].append(STAGE)
        state["current_stage"] = max(state["current_stage"], STAGE)
        return state