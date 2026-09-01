# A2A & Agent Test Strategy — ForgeSight AI

Documents the intended test strategy for the agent layer and A2A protocol once implementation begins. No test code exists yet — this phase is documentation only.

## Test Categories

### Unit Tests (Per Agent, Isolated)
- Each specialist agent (`VisionAnalysisAgent`, `TelemetryAnalysisAgent`, `MachineHealthAgent`, `ComponentLotAgent`, `DocumentRetrievalAgent`, `HistoricalIncidentAgent`, `EvidenceCorrelationAgent`, `HypothesisRankingAgent`, `CorrectiveActionAgent`, `ReportGenerationAgent`) is tested with mocked MCP tool responses and, where applicable, mocked LLM responses.
- Verify each agent's output matches its documented Output Schema (`agent-topology.md` Section 3) exactly, including all provenance fields (evidence refs, model version, timestamps).
- Verify `ComponentLotAgent` never emits a supplier-fault statement, only the mandated correlation wording, regardless of how extreme the input defect-rate delta is.
- Verify `HypothesisRankingAgent` never omits `contradicting_evidence_list` when contradictions exist in the input evidence graph.

### Integration Tests (Orchestrator Sequencing)
- Run the full 12-stage sequence against the known `INCIDENT-2026-00421` scenario (C17 misalignment on PLACER-07) using fixture data derived from the Phase 2 synthetic datasets and Phase 4 synthetic SOPs.
- Verify the Orchestrator dispatches agents in the correct stage order and does not dispatch `EvidenceCorrelationAgent` before all of Stage 3–7 have returned results (or explicit errors).
- Verify `InvestigationContext.completed_stages` and `agent_results` are updated correctly after each stage.

### HITL (Human-in-the-Loop) Tests
- Assert that no `PendingApprovalRequest` can transition to `approved` without a simulated human approval action — no code path in the Orchestrator or any agent can self-approve.
- Assert that `HypothesisRankingAgent` output always stops at Stage 9 for QE confirmation before `CorrectiveActionAgent` is dispatched, even when the evidence graph strongly supports a single hypothesis (per the mandatory rule that the Orchestrator never bypasses a HITL gate regardless of evidence clarity).
- Assert that `CorrectiveActionAgent` output is always `PendingApprovalRequest`-shaped and never marked as an executed action.
- Assert High-risk tools (`execute_batch_hold`, `modify_machine_parameters`) remain uncallable from any agent, consistent with Phase 5's reserved/blocked status for those tools.

### A2A Message Tests
- Validate every emitted `A2AMessage` against the schema in `a2a-architecture.md` Section 1.1, including mandatory presence of `incident_id` on every message.
- Verify `correlation_id` on a `task_result` or `error` message always matches the `correlation_id` of its originating `task_request`.
- Verify `error` messages correctly set `retryable` and that the Orchestrator's retry behavior (2 retries with backoff for transient errors, no retry for terminal errors) matches the policy in `a2a-architecture.md` Section 1.3.

### Failure Mode Tests
- Simulate `VisionAnalysisAgent` failure mid-investigation (e.g. `BOARD_NOT_FOUND`) and verify: Stage 3 is marked `failed` in `InvestigationContext`, the Orchestrator does not proceed to Stage 8 with fabricated vision evidence, and the QE receives a `status_update` describing the gap.
- Simulate three consecutive terminal errors across different tools for the same incident and verify the Orchestrator emits an escalation `status_update` rather than looping indefinitely.
- Simulate a QE logging off mid-investigation (pause) and resuming later; verify `InvestigationContext` is correctly rehydrated from PostgreSQL and no already-completed stage is re-executed.

## Status

No test code exists yet — this phase is documentation only. Implementation of these tests is deferred to the phase in which `src/forgesight/agents/` and `src/forgesight/a2a/` are actually built.