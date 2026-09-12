"""ComponentLotAgent — Stage 6. Template-only wording; never LLM-generated
fault attribution, per SOP-SUPP-008's mandated correlation-only phrasing."""

from __future__ import annotations

from forgesight.agents.mcp_client import McpToolError, call_manufacturing_tool
from forgesight.agents.schemas import LotStatistics
from forgesight.agents.state import InvestigationState
from forgesight.config.logging import get_logger
from forgesight.observability.tracing import agent_span

logger = get_logger(__name__)

AGENT_NAME = "ComponentLotAgent"
STAGE = 6

_CORRELATION_TEMPLATE = (
    "The available evidence indicates a correlation between Component Lot {lot_number} "
    "and elevated defect frequency. Additional evidence is required before attributing "
    "root cause to the supplier."
)


async def run(state: InvestigationState, lot_number: str, part_number: str) -> InvestigationState:
    with agent_span(AGENT_NAME, state["incident_id"], STAGE, "agent_node"):
        try:
            raw = await call_manufacturing_tool(
                "get_component_lot_history",
                state["orchestrator_token"],
                AGENT_NAME,
                state["incident_id"],
                STAGE,
                lot_number=lot_number,
                part_number=part_number,
            )
            output = LotStatistics(
                lot_number=lot_number,
                part_number=part_number,
                supplier_id=raw["supplier_id"],
                historical_defect_rate_pct=raw.get("historical_defect_rate_pct"),
                correlation_statement=_CORRELATION_TEMPLATE.format(lot_number=lot_number),
                gap=False,
            )
        except McpToolError as exc:
            logger.warning("component_lot_gap", extra={"error_code": exc.error_code})
            output = LotStatistics(
                lot_number=lot_number,
                part_number=part_number,
                supplier_id="unknown",
                correlation_statement="No lot data available for correlation analysis.",
                gap=True,
            )

        state["evidence_graph"]["component_lot"] = output.model_dump()
        state["agent_results"][AGENT_NAME] = output.model_dump()
        if STAGE not in state["completed_stages"]:
            state["completed_stages"].append(STAGE)
        state["current_stage"] = max(state["current_stage"], STAGE)
        return state