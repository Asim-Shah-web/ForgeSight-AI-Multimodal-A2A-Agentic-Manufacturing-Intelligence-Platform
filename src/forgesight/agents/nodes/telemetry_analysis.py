"""TelemetryAnalysisAgent — Stage 4. Pure threshold logic, no LLM call needed."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from forgesight.agents.mcp_client import McpToolError, call_manufacturing_tool
from forgesight.agents.schemas import TelemetryAnalysisOutput, TelemetryDeviation
from forgesight.agents.state import InvestigationState
from forgesight.config.logging import get_logger
from forgesight.observability.tracing import agent_span

logger = get_logger(__name__)

AGENT_NAME = "TelemetryAnalysisAgent"
STAGE = 4

# Simple placeholder qualified-window check; a real implementation would
# reference the specific parameter's qualified range per SOP-PROC-031-style
# documents rather than a single hardcoded pair.
_PARAMETER_TARGET_RANGES: dict[str, tuple[float, float]] = {
    "placement_head_pressure": (4.5, 5.2),
}


async def run(state: InvestigationState, machine_id: str, batch_id: str) -> InvestigationState:
    with agent_span(AGENT_NAME, state["incident_id"], STAGE, "agent_node"):
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=12)

        try:
            raw = await call_manufacturing_tool(
                "get_production_telemetry",
                state["orchestrator_token"],
                AGENT_NAME,
                state["incident_id"],
                STAGE,
                machine_id=machine_id,
                batch_id=batch_id,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
            )
            deviations: list[TelemetryDeviation] = []
            for reading in raw.get("telemetry", []):
                target_range = _PARAMETER_TARGET_RANGES.get(reading["parameter"])
                if target_range and not (target_range[0] <= reading["value"] <= target_range[1]):
                    deviations.append(
                        TelemetryDeviation(
                            parameter=reading["parameter"],
                            timestamp=reading["timestamp"],
                            value=reading["value"],
                            note=f"Outside qualified range {target_range}.",
                        )
                    )
            output = TelemetryAnalysisOutput(
                machine_id=machine_id, batch_id=batch_id, flagged_deviations=deviations, gap=False
            )
        except McpToolError as exc:
            logger.warning("telemetry_analysis_gap", extra={"error_code": exc.error_code})
            output = TelemetryAnalysisOutput(
                machine_id=machine_id, batch_id=batch_id, flagged_deviations=[], gap=True
            )

        state["evidence_graph"]["telemetry"] = output.model_dump()
        state["agent_results"][AGENT_NAME] = output.model_dump()
        if STAGE not in state["completed_stages"]:
            state["completed_stages"].append(STAGE)
        state["current_stage"] = max(state["current_stage"], STAGE)
        return state