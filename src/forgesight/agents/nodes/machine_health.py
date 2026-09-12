"""MachineHealthAgent — Stage 5/10. May add a PendingApprovalRequest."""

from __future__ import annotations

from forgesight.agents.mcp_client import McpToolError, call_manufacturing_tool
from forgesight.agents.schemas import MaintenanceAssessment
from forgesight.agents.state import InvestigationState
from forgesight.config.logging import get_logger
from forgesight.observability.tracing import agent_span

logger = get_logger(__name__)

AGENT_NAME = "MachineHealthAgent"
STAGE = 5

_WEAR_THRESHOLD_MM = 0.05
_DAYS_SINCE_CLEANING_THRESHOLD = 30


async def run(state: InvestigationState, machine_id: str, nozzle_id: str) -> InvestigationState:
    with agent_span(AGENT_NAME, state["incident_id"], STAGE, "agent_node"):
        try:
            raw = await call_manufacturing_tool(
                "get_machine_maintenance_history",
                state["orchestrator_token"],
                AGENT_NAME,
                state["incident_id"],
                STAGE,
                machine_id=machine_id,
                nozzle_id=nozzle_id,
            )
            records = raw.get("maintenance_records", [])
            most_recent = records[0] if records else {}

            exceeds_threshold = (
                (most_recent.get("wear_measurement_mm") or 0) > _WEAR_THRESHOLD_MM
                or (most_recent.get("days_since_cleaning") or 0) > _DAYS_SINCE_CLEANING_THRESHOLD
            )

            recommendation = None
            if exceeds_threshold:
                rec_raw = await call_manufacturing_tool(
                    "recommend_preventative_maintenance",
                    state["orchestrator_token"],
                    AGENT_NAME,
                    state["incident_id"],
                    STAGE,
                    machine_id=machine_id,
                    nozzle_id=nozzle_id,
                    reason=(
                        f"Nozzle {nozzle_id} last cleaned "
                        f"{most_recent.get('days_since_cleaning', 'unknown')} days ago; "
                        f"wear measurement {most_recent.get('wear_measurement_mm', 'unknown')} mm."
                    ),
                )
                recommendation = rec_raw
                state["pending_approvals"].append(rec_raw)

            output = MaintenanceAssessment(
                machine_id=machine_id,
                nozzle_id=nozzle_id,
                days_since_cleaning=most_recent.get("days_since_cleaning"),
                wear_measurement_mm=most_recent.get("wear_measurement_mm"),
                disposition=most_recent.get("disposition", "unknown"),
                recommendation=recommendation,
                gap=False,
            )
        except McpToolError as exc:
            logger.warning("machine_health_gap", extra={"error_code": exc.error_code})
            output = MaintenanceAssessment(machine_id=machine_id, nozzle_id=nozzle_id, disposition="unknown", gap=True)

        state["evidence_graph"]["maintenance"] = output.model_dump()
        state["agent_results"][AGENT_NAME] = output.model_dump()
        if STAGE not in state["completed_stages"]:
            state["completed_stages"].append(STAGE)
        state["current_stage"] = max(state["current_stage"], STAGE)
        return state