"""EvidenceCorrelationAgent — Stage 8. LLM call to identify cross-domain
correlations/contradictions across all prior agents' evidence."""

from __future__ import annotations

import json

from forgesight.agents.llm_client import call_llm
from forgesight.agents.schemas import EvidenceGraph
from forgesight.agents.state import InvestigationState
from forgesight.config.logging import get_logger
from forgesight.observability.tracing import agent_span

logger = get_logger(__name__)

AGENT_NAME = "EvidenceCorrelationAgent"
STAGE = 8

_SYSTEM_PROMPT = """You are the ForgeSight EvidenceCorrelationAgent for SMT/PCB manufacturing \
quality investigations. You are given per-domain evidence (vision, telemetry, maintenance, \
component_lot, documents) gathered for a single incident. Identify plausible correlations \
(e.g. temporal overlap between a maintenance gap and a defect cluster) and any contradictions \
between domains. Never draw a root-cause conclusion yourself — that is a separate agent's job. \
Respond ONLY with a JSON object matching this schema, no other text: \
{"nodes": [{"node_id": str, "domain": str, "summary": str}], \
"edges": [{"from_node_id": str, "to_node_id": str, "relation": str}], \
"contradictions": [str], "gaps": [str]}"""


async def run(state: InvestigationState) -> InvestigationState:
    with agent_span(AGENT_NAME, state["incident_id"], STAGE, "agent_node"):
        evidence_summary = json.dumps(state["evidence_graph"], default=str)
        user_prompt = f"Evidence collected so far:\n{evidence_summary}"

        response = await call_llm(AGENT_NAME, state["incident_id"], STAGE, _SYSTEM_PROMPT, user_prompt)

        try:
            parsed = json.loads(response.content)
            evidence_graph = EvidenceGraph.model_validate(parsed)
        except (json.JSONDecodeError, ValueError) as exc:
            logger.error("evidence_correlation_output_invalid", extra={"error": str(exc)})
            evidence_graph = EvidenceGraph(nodes=[], edges=[], contradictions=[], gaps=["llm_output_parse_failure"])

        state["evidence_graph"]["correlation"] = evidence_graph.model_dump()
        state["agent_results"][AGENT_NAME] = evidence_graph.model_dump()
        if STAGE not in state["completed_stages"]:
            state["completed_stages"].append(STAGE)
        state["current_stage"] = max(state["current_stage"], STAGE)
        return state