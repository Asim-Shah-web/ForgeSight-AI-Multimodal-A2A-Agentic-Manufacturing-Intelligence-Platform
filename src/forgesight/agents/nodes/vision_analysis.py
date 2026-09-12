"""VisionAnalysisAgent — Stage 2/3. Calls get_board_inspection_data."""

from __future__ import annotations

from forgesight.agents.mcp_client import McpToolError, call_manufacturing_tool
from forgesight.agents.schemas import CvFindingSummary, VisionAnalysisOutput
from forgesight.agents.state import InvestigationState
from forgesight.config.logging import get_logger
from forgesight.observability.tracing import agent_span

logger = get_logger(__name__)

AGENT_NAME = "VisionAnalysisAgent"
STAGE = 3


async def run(state: InvestigationState, board_id: str) -> InvestigationState:
    with agent_span(AGENT_NAME, state["incident_id"], STAGE, "agent_node"):
        try:
            raw = await call_manufacturing_tool(
                "get_board_inspection_data",
                state["orchestrator_token"],
                AGENT_NAME,
                state["incident_id"],
                STAGE,
                board_id=board_id,
            )
            output = VisionAnalysisOutput(
                board_id=raw["board_id"],
                cv_findings=[
                    CvFindingSummary(
                        cv_finding_id=f["cv_finding_id"],
                        defect_type=f["defect_type"],
                        component_designator=f.get("component_designator"),
                        confidence=f["confidence"],
                        bounding_box=f["bounding_box"],
                    )
                    for f in raw.get("aoi_flags", [])
                ],
                gap=False,
            )
        except McpToolError as exc:
            logger.warning("vision_analysis_gap", extra={"error_code": exc.error_code})
            output = VisionAnalysisOutput(board_id=board_id, cv_findings=[], gap=True)

        state["evidence_graph"]["vision"] = output.model_dump()
        state["agent_results"][AGENT_NAME] = output.model_dump()
        if STAGE not in state["completed_stages"]:
            state["completed_stages"].append(STAGE)
        state["current_stage"] = max(state["current_stage"], STAGE)
        return state