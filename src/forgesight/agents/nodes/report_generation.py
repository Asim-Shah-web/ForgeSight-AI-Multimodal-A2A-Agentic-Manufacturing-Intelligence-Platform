"""ReportGenerationAgent — Stage 12. Only ever summarizes already-approved
state; introduces no new claims."""

from __future__ import annotations

import json

from forgesight.agents.llm_client import call_llm
from forgesight.agents.schemas import ReportOutput
from forgesight.agents.state import InvestigationState
from forgesight.config.logging import get_logger
from forgesight.observability.tracing import agent_span

logger = get_logger(__name__)

AGENT_NAME = "ReportGenerationAgent"
STAGE = 12

_SYSTEM_PROMPT = """You are the ForgeSight ReportGenerationAgent. Given a fully signed-off \
investigation (confirmed hypothesis, approved corrective action, full evidence graph), write a \
concise narrative report summarizing the investigation. Strictly reformat and summarize \
already-approved content — introduce NO new claims, conclusions, or evidence not already \
present in the input. Respond ONLY with a JSON object matching this schema, no other text: \
{"narrative": str, "sections_included": [str]}"""


async def run(state: InvestigationState) -> InvestigationState:
    with agent_span(AGENT_NAME, state["incident_id"], STAGE, "agent_node"):
        signed_off_summary = json.dumps(
            {
                "evidence_graph": state["evidence_graph"],
                "agent_results": state["agent_results"],
                "pending_approvals": state["pending_approvals"],
            },
            default=str,
        )
        response = await call_llm(AGENT_NAME, state["incident_id"], STAGE, _SYSTEM_PROMPT, signed_off_summary)

        try:
            parsed = json.loads(response.content)
            report = ReportOutput.model_validate(parsed)
        except (json.JSONDecodeError, ValueError) as exc:
            logger.error("report_generation_output_invalid", extra={"error": str(exc)})
            report = ReportOutput(narrative="Report generation failed; manual compilation required.", sections_included=[])

        state["agent_results"][AGENT_NAME] = report.model_dump()
        state["status"] = "complete"
        if STAGE not in state["completed_stages"]:
            state["completed_stages"].append(STAGE)
        state["current_stage"] = STAGE
        return state