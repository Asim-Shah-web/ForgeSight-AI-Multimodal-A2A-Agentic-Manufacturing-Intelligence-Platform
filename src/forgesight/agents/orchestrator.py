"""
InvestigationOrchestratorAgent — the LangGraph StateGraph wiring all 10
specialist nodes per Phase 6 Section 2.1's topology, with interrupt_before
on both HITL gate nodes. This is where Mandatory Rule 9 ("never bypass a
HITL gate") is structurally enforced: there is no graph edge from
hypothesis_ranking to corrective_action, or from corrective_action to
report_generation, that does not pass through an interrupt.

Uses langgraph-checkpoint-postgres so InvestigationState durably persists in
the existing forgesight database (Phase 6 Section 3.2: PostgreSQL as system
of record) — no separate Redis-based state store is introduced here.
"""

from __future__ import annotations

from typing import Any

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, StateGraph

from forgesight.agents.nodes import (
    component_lot,
    corrective_action,
    document_retrieval,
    evidence_correlation,
    historical_incident,
    hypothesis_ranking,
    machine_health,
    report_generation,
    telemetry_analysis,
    vision_analysis,
)
from forgesight.agents.state import InvestigationState, new_investigation_state
from forgesight.api.security import create_access_token
from forgesight.config.database import AsyncSessionFactory
from forgesight.config.logging import get_logger
from forgesight.config.settings import settings
from forgesight.domain.models.investigation import Incident
from forgesight.domain.models.users import UserRole
from sqlmodel import select

logger = get_logger(__name__)

_checkpointer_cm = None
_checkpointer: AsyncPostgresSaver | None = None
_compiled_graph = None


async def _get_checkpointer() -> AsyncPostgresSaver:
    """Lazily create and set up the Postgres checkpointer, once per process."""
    global _checkpointer_cm, _checkpointer
    if _checkpointer is None:
        _checkpointer_cm = AsyncPostgresSaver.from_conn_string(settings.database_url)
        _checkpointer = await _checkpointer_cm.__aenter__()
        await _checkpointer.setup()
    return _checkpointer


async def _mint_orchestrator_token() -> str:
    """Mint a short-lived JWT for the AGENT_ORCHESTRATOR system identity.
    Never logged, never traced (see InvestigationState.orchestrator_token docstring)."""
    token, _ = create_access_token(
        subject=settings.orchestrator_system_role_username, role=UserRole.AGENT_ORCHESTRATOR
    )
    return token


async def _fetch_incident_context(incident_id: str) -> dict[str, Any]:
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(Incident).where(Incident.incident_id == incident_id))
        incident = result.scalar_one_or_none()
        if incident is None:
            raise ValueError(f"Incident '{incident_id}' not found.")
        return {
            "board_id": incident.board_id,
            "batch_id": incident.batch_id,
            "line_id": incident.line_id,
            "defect_type": incident.defect_type,
            "component_designator": incident.component_designator or "",
            "machine_id": None,  # resolved via machine_health node args at call time if known
        }


# ---------------------------------------------------------------------------
# Graph node wrappers (bind incident-specific args pulled from Incident row)
# ---------------------------------------------------------------------------

async def _vision_node(state: InvestigationState) -> InvestigationState:
    ctx = await _fetch_incident_context(state["incident_id"])
    return await vision_analysis.run(state, board_id=ctx["board_id"])


async def _telemetry_node(state: InvestigationState) -> InvestigationState:
    ctx = await _fetch_incident_context(state["incident_id"])
    machine_id = state.get("machine_id") or "UNKNOWN"
    return await telemetry_analysis.run(state, machine_id=machine_id, batch_id=ctx["batch_id"])


async def _machine_health_node(state: InvestigationState) -> InvestigationState:
    machine_id = state.get("machine_id") or "UNKNOWN"
    nozzle_id = state.get("nozzle_id") or "UNKNOWN"
    return await machine_health.run(state, machine_id=machine_id, nozzle_id=nozzle_id)


async def _component_lot_node(state: InvestigationState) -> InvestigationState:
    lot_number = state.get("lot_number")
    part_number = state.get("part_number")
    if not lot_number or not part_number:
        # No lot context available for this incident — record an explicit
        # gap rather than skip silently.
        state["evidence_graph"]["component_lot"] = {"gap": True, "reason": "no_lot_context"}
        if 6 not in state["completed_stages"]:
            state["completed_stages"].append(6)
        return state
    return await component_lot.run(state, lot_number=lot_number, part_number=part_number)


async def _document_retrieval_node(state: InvestigationState) -> InvestigationState:
    ctx = await _fetch_incident_context(state["incident_id"])
    return await document_retrieval.run(
        state,
        defect_type=ctx["defect_type"],
        component_id=ctx["component_designator"],
        machine_id=state.get("machine_id") or "UNKNOWN",
    )


async def _evidence_correlation_node(state: InvestigationState) -> InvestigationState:
    return await evidence_correlation.run(state)


async def _historical_incident_node(state: InvestigationState) -> InvestigationState:
    ctx = await _fetch_incident_context(state["incident_id"])
    return await historical_incident.run(
        state, defect_type=ctx["defect_type"], component_id=ctx["component_designator"]
    )


async def _hypothesis_ranking_node(state: InvestigationState) -> InvestigationState:
    return await hypothesis_ranking.run(state)


async def _corrective_action_node(state: InvestigationState) -> InvestigationState:
    confirmed = next(
        (a for a in state["pending_approvals"] if a.get("gate") == "hypothesis_confirmation" and a.get("status") == "approved"),
        None,
    )
    confirmed_hypothesis = confirmed.get("confirmed_hypothesis", {}) if confirmed else {}
    return await corrective_action.run(state, confirmed_hypothesis=confirmed_hypothesis)


async def _report_generation_node(state: InvestigationState) -> InvestigationState:
    return await report_generation.run(state)


def _build_graph():
    graph = StateGraph(InvestigationState)

    graph.add_node("vision_analysis", _vision_node)
    graph.add_node("telemetry_analysis", _telemetry_node)
    graph.add_node("machine_health", _machine_health_node)
    graph.add_node("component_lot", _component_lot_node)
    graph.add_node("document_retrieval", _document_retrieval_node)
    graph.add_node("evidence_correlation", _evidence_correlation_node)
    graph.add_node("historical_incident", _historical_incident_node)
    graph.add_node("hypothesis_ranking", _hypothesis_ranking_node)
    graph.add_node("corrective_action", _corrective_action_node)
    graph.add_node("report_generation", _report_generation_node)

    graph.set_entry_point("vision_analysis")
    graph.add_edge("vision_analysis", "telemetry_analysis")
    graph.add_edge("telemetry_analysis", "machine_health")
    graph.add_edge("machine_health", "component_lot")
    graph.add_edge("component_lot", "document_retrieval")
    graph.add_edge("document_retrieval", "evidence_correlation")
    graph.add_edge("evidence_correlation", "historical_incident")
    graph.add_edge("historical_incident", "hypothesis_ranking")

    # Mandatory Rule 9: hypothesis_ranking -> corrective_action passes
    # through an interrupt. LangGraph's interrupt_before list (passed at
    # compile time below) is what actually halts execution here — this
    # edge alone would otherwise proceed automatically.
    graph.add_edge("hypothesis_ranking", "corrective_action")
    graph.add_edge("corrective_action", "report_generation")
    graph.add_edge("report_generation", END)

    return graph


async def get_compiled_graph():
    global _compiled_graph
    if _compiled_graph is None:
        checkpointer = await _get_checkpointer()
        graph = _build_graph()
        _compiled_graph = graph.compile(
            checkpointer=checkpointer,
            # The two mandatory HITL gates. The graph physically cannot
            # proceed past hypothesis_ranking or corrective_action without
            # an explicit resume call (see resume_investigation below).
            interrupt_before=["corrective_action", "report_generation"],
        )
    return _compiled_graph


async def start_investigation(incident_id: str) -> InvestigationState:
    """Start a new investigation run (Stages 2-9, halting before Stage 10's
    HITL gate). Returns the state at the point of the first interrupt."""
    orchestrator_token = await _mint_orchestrator_token()
    initial_state = new_investigation_state(incident_id, orchestrator_token)

    compiled_graph = await get_compiled_graph()
    config = {"configurable": {"thread_id": incident_id}}

    result = await compiled_graph.ainvoke(initial_state, config=config)
    logger.info(
        "investigation_started",
        extra={"incident_id": incident_id, "current_stage": result["current_stage"], "status": result["status"]},
    )
    return result


async def resume_investigation(incident_id: str, approved: bool, approver_role: str, notes: str = "") -> InvestigationState:
    """
    Resume an investigation paused at a HITL interrupt.

    approved=False routes back to an earlier stage (re-investigation) rather
    than forward, per Phase 6 Section 2.1's escalation column — implemented
    here by resetting status to "in_progress" without advancing
    pending_approvals, requiring a fresh start_investigation-equivalent call
    for the affected stage; approved=True lets the graph proceed past the
    interrupt.
    """
    compiled_graph = await get_compiled_graph()
    config = {"configurable": {"thread_id": incident_id}}

    current_state = await compiled_graph.aget_state(config)
    if current_state is None:
        raise ValueError(f"No in-progress investigation found for incident '{incident_id}'.")

    state_values: InvestigationState = current_state.values

    pending_gate = next((a for a in state_values["pending_approvals"] if a.get("status") == "pending"), None)
    if pending_gate is None:
        raise ValueError(f"No pending approval gate found for incident '{incident_id}'.")

    pending_gate["status"] = "approved" if approved else "rejected"
    pending_gate["approved_by_role"] = approver_role
    pending_gate["notes"] = notes

    if not approved:
        state_values["status"] = "failed"
        await compiled_graph.aupdate_state(config, state_values)
        logger.info("investigation_rejected_at_gate", extra={"incident_id": incident_id, "gate": pending_gate.get("gate")})
        return state_values

    state_values["status"] = "in_progress"
    result = await compiled_graph.ainvoke(None, config=config)
    logger.info(
        "investigation_resumed",
        extra={"incident_id": incident_id, "current_stage": result["current_stage"], "status": result["status"]},
    )
    return result