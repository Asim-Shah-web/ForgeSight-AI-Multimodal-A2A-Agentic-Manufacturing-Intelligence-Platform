"""
CorrectiveActionAgent — Stage 10. Only reachable after the hypothesis
confirmation interrupt resolves with human approval. Output is always
PendingApprovalRequest-shaped and added to pending_approvals with its own
subsequent interrupt.
"""

from __future__ import annotations

import json

from forgesight.agents.llm_client import call_llm
from forgesight.agents.schemas import CorrectiveActionOutput
from forgesight.agents.state import InvestigationState
from forgesight.config.logging import get_logger
from forgesight.observability.tracing import agent_span

logger = get_logger(__name__)

AGENT_NAME = "CorrectiveActionAgent"
STAGE = 10

_SYSTEM_PROMPT = """You are the ForgeSight CorrectiveActionAgent for SMT/PCB manufacturing \
quality investigations. Given a human-confirmed root-cause hypothesis, propose ONE concrete \
corrective action grounded in the cited evidence. Do not propose actions unrelated to the \
confirmed hypothesis. Respond ONLY with a JSON object matching this schema, no other text: \
{"proposed_action": str, "supporting_evidence_refs": [str], "requires_approval_by": str}"""


async def run(state: InvestigationState, confirmed_hypothesis: dict) -> InvestigationState:
    with agent_span(AGENT_NAME, state["incident_id"], STAGE, "agent_node"):
        user_prompt = f"Confirmed hypothesis:\n{json.dumps(confirmed_hypothesis, default=str)}"
        response = await call_llm(AGENT_NAME, state["incident_id"], STAGE, _SYSTEM_PROMPT, user_prompt)

        try:
            parsed = json.loads(response.content)
            action = CorrectiveActionOutput.model_validate(parsed)
        except (json.JSONDecodeError, ValueError) as exc:
            logger.error("corrective_action_output_invalid", extra={"error": str(exc)})
            action = CorrectiveActionOutput(
                proposed_action="Manual review required — automated recommendation generation failed.",
                supporting_evidence_refs=[],
                requires_approval_by="Quality Engineer",
            )

        pending_request = {
            "gate": "corrective_action_approval",
            "proposed_action": action.proposed_action,
            "supporting_evidence_refs": action.supporting_evidence_refs,
            "requires_approval_by": action.requires_approval_by,
            "status": "pending",
        }
        state["pending_approvals"].append(pending_request)
        state["agent_results"][AGENT_NAME] = action.model_dump()
        state["status"] = "awaiting_approval"
        if STAGE not in state["completed_stages"]:
            state["completed_stages"].append(STAGE)
        state["current_stage"] = STAGE
        return state