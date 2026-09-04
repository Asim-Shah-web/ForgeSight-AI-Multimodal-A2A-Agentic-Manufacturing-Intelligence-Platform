# ADR 002: A2A Agent Decomposition Boundaries

## Status

Accepted

## Context

ForgeSight requires multiple specialist AI capabilities (vision analysis, telemetry analysis, evidence correlation, hypothesis ranking, etc.) to cooperate across a 12-stage investigation workflow, while strictly preserving human-in-the-loop control at every high-risk decision point.

## Decision

Agents are decomposed by **software capability**, not by human persona, and are coordinated by a single stateful **`InvestigationOrchestratorAgent`** rather than a peer-to-peer agent mesh.

## Rationale

### Capability-based decomposition, not persona-based

An agent-per-persona model (e.g. `QualityEngineerAgent`, `MaintenanceEngineerAgent`) was explicitly rejected because it conflates *who acts on the output* with *what cognitive task produces it*. A single investigation routinely needs vision analysis, telemetry analysis, and document retrieval regardless of which persona is currently viewing the workspace — decomposing by persona would force duplicate or ambiguous capability logic across agents. Capability-based decomposition (`VisionAnalysisAgent`, `EvidenceCorrelationAgent`, etc.) keeps each agent single-purpose, independently testable, and reusable across investigation branches (standard, maintenance, and supplier journeys per `docs/business/user-journeys.md`).

### Orchestrator pattern over peer-to-peer mesh

A peer-to-peer mesh, where agents directly message one another and negotiate sequencing, was rejected in favor of a central `InvestigationOrchestratorAgent` because:

- **Auditability**: a single component owning `InvestigationContext` and stage sequencing gives one authoritative place to verify that no stage was skipped and no HITL gate was bypassed.
- **HITL enforcement**: it is materially harder to guarantee a mandatory approval gate is never bypassed in a mesh, where any agent could in principle trigger the next stage directly. Centralizing stage transitions in the Orchestrator makes the HITL gate a single, auditable chokepoint.
- **State durability**: a mesh has no natural place to persist cross-cutting investigation state (evidence graph, completed stages, pending approvals); the Orchestrator gives this a clear owner.

## Alternatives Considered

| Alternative | Reason Rejected |
| --- | --- |
| Monolithic workflow service (single large service performing all stages inline) | Loses the benefit of independently testable, reusable capabilities; a change to vision inference logic would require redeploying the entire workflow service |
| Pure LangGraph graph with implicit node-to-node routing | Still viable as an eventual *implementation* detail for the Orchestrator's internal state machine, but does not by itself resolve the agent boundary question — the capability decomposition and HITL enforcement documented here would still be required regardless of the graph execution engine chosen |
| Pure CrewAI-style autonomous crew (agents self-organize and delegate) | Rejected because autonomous inter-agent delegation makes it harder to guarantee that no agent sequence can skip a HITL gate; ForgeSight's non-negotiable human-approval requirement favors an explicit, centrally-enforced orchestration model over emergent agent coordination |

## Consequences

- Every specialist agent has a narrow, single-purpose contract (Section 3 of `agent-topology.md`), making unit testing and failure isolation straightforward.
- All A2A messages carry `incident_id` as a mandatory context anchor, so no agent can act without knowing which investigation it belongs to.
- The Orchestrator becomes a single point of coordination — its correctness (especially never bypassing a HITL gate) is the most safety-critical piece of the agent architecture and warrants the most rigorous test coverage (see `tests/a2a/README.md`).
- Adding a new capability in the future means adding a new specialist agent with its own contract, not modifying an existing agent's scope or introducing a new persona-named agent.

## Risks

- Centralizing sequencing in one Orchestrator creates a potential single point of failure for investigation progress; this is mitigated by durable PostgreSQL-backed state (Section 3 of `a2a-architecture.md`) so a crashed Orchestrator process can resume rather than losing investigation state.
- Capability boundaries must be revisited if a future capability (e.g. multimodal cross-referencing) doesn't cleanly fit an existing agent — this ADR does not freeze the agent list permanently, only the *principle* that boundaries follow capability, not persona.
