"""
HypothesisRankingAgent — Stage 9. LLM call producing ranked hypotheses.

Always ends by adding an entry to state["pending_approvals"] and setting
status to "awaiting_approval" — the LangGraph edge out of this node leads
to an interrupt, never directly to corrective_action (Mandatory Rule 9,
enforced structurally in orchestrator.py, not just by this node's behavior).
"""

from __future__ import annotations

import json

from forgesight.agents.llm_client import call_llm
from forgesight.agents.schemas import RootCauseHypothesisOutput
from forgesight.agents.state import InvestigationState
from forgesight.config.logging import get_logger
from forgesight.observability.tracing import agent_span

logger = get_logger(__name__)

AGENT_NAME = "HypothesisRankingAgent"
STAGE = 9

_SYSTEM_PROMPT = """You are the ForgeSight HypothesisRankingAgent for SMT/PCB manufacturing \
quality investigations. Given a cross-domain evidence graph and similar historical incidents, \
generate 1-3 ranked root-cause hypotheses. Every hypothesis must cite specific supporting \
evidence node IDs. If evidence suggests a supplier/component lot issue, you MUST use \
correlation-only wording ("the evidence indicates a correlation...") and NEVER state a \
supplier caused the defect. Never include your raw reasoning process — reasoning_summary must \
be a concise, evidence-grounded explanation only. Respond ONLY with a JSON array of objects \
matching this schema, no other text: \
[{"conclusion": str, "supporting_evidence_refs": [str], "contradicting_evidence_refs": [str], \
"confidence_level": float, "reasoning_summary": str, "rank": int}]"""


async def run(state: InvestigationState) -> InvestigationState:
    with agent_span(AGENT_NAME, state["incident_id"], STAGE, "agent_node"):
        evidence_summary = json.dumps(
            {"evidence_graph": state["evidence_graph"], "historical": state["evidence_graph"].get("historical")},
            default=str,
        )
        response = await call_llm(AGENT_NAME, state["incident_id"], STAGE, _SYSTEM_PROMPT, evidence_summary)

        try:
            parsed = json.loads(response.content)
            hypotheses = [RootCauseHypothesisOutput.model_validate(h) for h in parsed]
        except (json.JSONDecodeError, ValueError) as exc:
            logger.error("hypothesis_ranking_output_invalid", extra={"error": str(exc)})
            hypotheses = []

        state["agent_results"][AGENT_NAME] = [h.model_dump() for h in hypotheses]

        # Mandatory: this node ALWAYS routes to a human decision point,
        # regardless of hypothesis count or confidence — never auto-proceeds.
        state["pending_approvals"].append(
            {
                "gate": "hypothesis_confirmation",
                "hypotheses": [h.model_dump() for h in hypotheses],
                "requires_approval_by": "Quality Engineer",
                "status": "pending",
            }
        )
        state["status"] = "awaiting_approval"
        if STAGE not in state["completed_stages"]:
            state["completed_stages"].append(STAGE)
        state["current_stage"] = STAGE
        return state