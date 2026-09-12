"""DocumentRetrievalAgent — Stage 7. Wraps search_technical_sops."""

from __future__ import annotations

from forgesight.agents.mcp_client import McpToolError, call_documents_tool
from forgesight.agents.schemas import DocumentRetrievalOutput, RetrievedPassageSummary
from forgesight.agents.state import InvestigationState
from forgesight.config.logging import get_logger
from forgesight.observability.tracing import agent_span

logger = get_logger(__name__)

AGENT_NAME = "DocumentRetrievalAgent"
STAGE = 7


async def run(state: InvestigationState, defect_type: str, component_id: str, machine_id: str) -> InvestigationState:
    with agent_span(AGENT_NAME, state["incident_id"], STAGE, "agent_node"):
        query = f"Inspection and containment procedure for {defect_type}. Component: {component_id}. Machine: {machine_id}."
        try:
            raw = await call_documents_tool(
                "search_technical_sops",
                state["orchestrator_token"],
                AGENT_NAME,
                state["incident_id"],
                STAGE,
                query=query,
                machine_id=machine_id,
            )
            output = DocumentRetrievalOutput(
                passages=[
                    RetrievedPassageSummary(
                        passage_id=r["passage_id"],
                        document_id=r["document_id"],
                        document_title=r["document_title"],
                        section_reference=r.get("section_reference"),
                        chunk_text=r["chunk_text"],
                        retrieval_score=r["retrieval_score"],
                    )
                    for r in raw.get("results", [])
                ],
                gap=False,
            )
        except McpToolError as exc:
            # NO_RELEVANT_DOCUMENT_FOUND becomes an explicit gap marker,
            # never a fabricated passage.
            logger.info("document_retrieval_gap", extra={"error_code": exc.error_code})
            output = DocumentRetrievalOutput(passages=[], gap=True)

        state["evidence_graph"]["documents"] = output.model_dump()
        state["agent_results"][AGENT_NAME] = output.model_dump()
        if STAGE not in state["completed_stages"]:
            state["completed_stages"].append(STAGE)
        state["current_stage"] = max(state["current_stage"], STAGE)
        return state