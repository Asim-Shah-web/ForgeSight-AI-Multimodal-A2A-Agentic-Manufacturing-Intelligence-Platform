
# A2A Protocol Architecture — ForgeSight AI

## 1. A2A Message Schema & Examples

### 1.1 Standard Message Envelope

No agent may emit or accept a message without a populated `incident_id` — this is the mandatory context anchor referenced throughout Phase 1–5.

### 1.2 Message Types by Interaction

| Interaction | Message Type | Notes |
|---|---|---|
| Orchestrator → specialist agent | `task_request` | Dispatches work for a given stage |
| Specialist agent → Orchestrator | `task_result` | Returns evidence/output; `correlation_id` matches the originating `task_request` |
| Specialist agent → Orchestrator (blocked) | `approval_request` | Emitted when the agent's output requires human sign-off (e.g. `MachineHealthAgent` recommendation) |
| Any agent → Orchestrator (failure) | `error` | Tool failure, missing evidence, or timeout; includes `error_code` and whether retry is possible |
| Orchestrator → QE UI (via API layer) | `status_update` | Stage progress notifications, not consumed by other agents |

### 1.3 Error Handling & Retry Strategy

- **Transient errors** (e.g. MCP tool timeout): the dispatching agent retries up to 2 times with exponential backoff before emitting an `error` message to the Orchestrator.
- **Terminal errors** (e.g. `BOARD_NOT_FOUND`, `PERMISSION_DENIED`): no retry — the agent immediately emits an `error` message; the Orchestrator marks the corresponding stage `failed` in `InvestigationContext` and surfaces this to the QE via `status_update` rather than silently proceeding with partial or fabricated evidence.
- **Escalation**: three consecutive terminal errors across different tools for the same incident triggers an Orchestrator-level `status_update` recommending manual QE intervention — the Orchestrator does not indefinitely retry or auto-skip stages.

### 1.4 Example Messages

**Example 1 — Orchestrator → VisionAnalysisAgent (`task_request`)**
```json
{
  "message_id": "MSG-10001",
  "sender_agent": "InvestigationOrchestratorAgent",
  "receiver_agent": "VisionAnalysisAgent",
  "incident_id": "INCIDENT-2026-00421",
  "message_type": "task_request",
  "investigation_stage": 3,
  "payload": {
    "board_id": "BRD-24017-00432"
  },
  "evidence_refs": [],
  "model_version": null,
  "timestamp": "2026-02-03T09:00:00Z",
  "correlation_id": "CORR-5001"
}
```

**Example 2 — VisionAnalysisAgent → Orchestrator (`task_result`)**
```json
{
  "message_id": "MSG-10002",
  "sender_agent": "VisionAnalysisAgent",
  "receiver_agent": "InvestigationOrchestratorAgent",
  "incident_id": "INCIDENT-2026-00421",
  "message_type": "task_result",
  "investigation_stage": 3,
  "payload": {
    "cv_findings": [
      {
        "cv_finding_id": "CVF-88213",
        "defect_type": "component_misalignment",
        "component_designator": "C17",
        "confidence": 0.91,
        "bounding_box": [412, 188, 40, 40]
      }
    ]
  },
  "evidence_refs": ["CVF-88213"],
  "model_version": "yolov8-forgesight-v1.2",
  "timestamp": "2026-02-03T09:00:04Z",
  "correlation_id": "CORR-5001"
}
```

**Example 3 — Orchestrator → EvidenceCorrelationAgent (`task_request`, aggregated inputs)**
```json
{
  "message_id": "MSG-10015",
  "sender_agent": "InvestigationOrchestratorAgent",
  "receiver_agent": "EvidenceCorrelationAgent",
  "incident_id": "INCIDENT-2026-00421",
  "message_type": "task_request",
  "investigation_stage": 8,
  "payload": {
    "vision_result_ref": "MSG-10002",
    "telemetry_result_ref": "MSG-10006",
    "machine_health_result_ref": "MSG-10009",
    "component_lot_result_ref": "MSG-10012",
    "document_result_ref": "MSG-10014"
  },
  "evidence_refs": ["CVF-88213", "CVF-88214", "MR-55210", "PSG-77120"],
  "model_version": null,
  "timestamp": "2026-02-03T09:15:00Z",
  "correlation_id": "CORR-5015"
}
```

**Example 4 — EvidenceCorrelationAgent → Orchestrator (`task_result`, evidence graph)**
```json
{
  "message_id": "MSG-10016",
  "sender_agent": "EvidenceCorrelationAgent",
  "receiver_agent": "InvestigationOrchestratorAgent",
  "incident_id": "INCIDENT-2026-00421",
  "message_type": "task_result",
  "investigation_stage": 8,
  "payload": {
    "evidence_graph_id": "EG-2201",
    "node_count": 6,
    "edges": [
      {"from": "CVF-88213", "to": "MR-55210", "relation": "temporal_overlap_nozzle_wear"}
    ],
    "contradictions": []
  },
  "evidence_refs": ["CVF-88213", "MR-55210"],
  "model_version": "claude-sonnet-4-6",
  "timestamp": "2026-02-03T09:16:30Z",
  "correlation_id": "CORR-5015"
}
```

**Example 5 — MachineHealthAgent → Orchestrator (`approval_request`)**
```json
{
  "message_id": "MSG-10010",
  "sender_agent": "MachineHealthAgent",
  "receiver_agent": "InvestigationOrchestratorAgent",
  "incident_id": "INCIDENT-2026-00421",
  "message_type": "approval_request",
  "investigation_stage": 5,
  "payload": {
    "recommendation_id": "REC-3391",
    "proposed_action": "clean_and_inspect nozzle NZ-07-03 on PLACER-07",
    "requires_approval_by": "Maintenance Engineer"
  },
  "evidence_refs": ["MR-55210", "CVF-88213", "CVF-88214"],
  "model_version": "claude-sonnet-4-6",
  "timestamp": "2026-02-03T09:08:00Z",
  "correlation_id": "CORR-5009"
}
```

**Example 6 — VisionAnalysisAgent → Orchestrator (`error`)**
```json
{
  "message_id": "MSG-10003",
  "sender_agent": "VisionAnalysisAgent",
  "receiver_agent": "InvestigationOrchestratorAgent",
  "incident_id": "INCIDENT-2026-00421",
  "message_type": "error",
  "investigation_stage": 3,
  "payload": {
    "error_code": "BOARD_NOT_FOUND",
    "retryable": false,
    "detail": "No inspection record for board_id BRD-24017-99999"
  },
  "evidence_refs": [],
  "model_version": null,
  "timestamp": "2026-02-03T09:00:04Z",
  "correlation_id": "CORR-5002"
}
```

---

## 2. Workflow Orchestration Map

### 2.1 Stage-to-Agent Mapping

| Stage | Stage Name | Primary Agent | Supporting Agents | MCP Tools Called | Human Decision Point |
|---|---|---|---|---|---|
| 1 | Defect Detection & Threshold Trigger | *(CV pipeline trigger, pre-agent)* | — | — | None (automatic threshold trigger) |
| 2 | Incident Creation & Context Setup | `InvestigationOrchestratorAgent` | `VisionAnalysisAgent` (initial context pull) | `get_board_inspection_data` | Production Operator confirms incident creation |
| 3 | Visual Evidence Extraction | `VisionAnalysisAgent` | — | `get_board_inspection_data` | None (Low risk, read-only) |
| 4 | Production & Telemetry Investigation | `TelemetryAnalysisAgent` | — | `get_production_telemetry` | None (Low risk, read-only) |
| 5 | Machine & Maintenance Check | `MachineHealthAgent` | — | `get_machine_maintenance_history`, `recommend_preventative_maintenance` | Maintenance Engineer approves any recommendation |
| 6 | Component Lot & Supplier Correlation | `ComponentLotAgent` | — | `get_component_lot_history` | None for retrieval; SQE required for any future SCAR |
| 7 | Technical SOP & Manual Retrieval | `DocumentRetrievalAgent` | — | `search_technical_sops`, `get_document_by_id` | None (Low risk, read-only) |
| 8 | Evidence Correlation & Synthesis | `EvidenceCorrelationAgent` | All Stage 3–7 agents (as data sources) | None directly | QE reviews evidence graph before proceeding |
| 9 | Root-Cause Hypothesis Ranking | `HypothesisRankingAgent` | `HistoricalIncidentAgent` | `search_historical_incidents` | **QE confirms/rejects ranked hypotheses (mandatory HITL gate)** |
| 10 | Corrective Action Recommendation | `CorrectiveActionAgent` | `MachineHealthAgent` (if maintenance-related) | `recommend_preventative_maintenance` | **Relevant approving persona signs the `PendingApprovalRequest` (mandatory HITL gate)** |
| 11 | Human Engineer Review & Sign-Off | *(human action)* | Any agent may be re-invoked for verification | Any Low-risk tool | **Quality Engineer sign-off (mandatory)** |
| 12 | Report Generation & Audit Trail | `ReportGenerationAgent` | — | None directly | QE reviews final report before distribution |

### 2.2 Stage 8 Narrative — `EvidenceCorrelationAgent`

At Stage 8, the Orchestrator dispatches `EvidenceCorrelationAgent` only once all of Stage 3 (`VisionAnalysisAgent`), Stage 4 (`TelemetryAnalysisAgent`), Stage 5 (`MachineHealthAgent`), Stage 6 (`ComponentLotAgent`), and Stage 7 (`DocumentRetrievalAgent`) have returned `task_result` messages (or explicit `error` results, if a domain's evidence is genuinely unavailable).

The agent receives references to each prior `task_result` message rather than raw re-fetched data, preserving the exact evidence that was already shown to the QE at each stage. It performs three operations:

1. **Evidence graph construction**: each individual evidence item (a `CvFinding`, a telemetry deviation, a maintenance record, a lot statistic, an SOP passage) becomes a node; edges are added where the agent identifies a plausible relationship — most commonly temporal overlap (e.g. a nozzle overdue for cleaning and a cluster of misalignment defects occurring in the same window) or direct reference (e.g. an SOP passage whose acceptance criteria the CV finding violates).
2. **Contradiction flagging**: where two evidence items conflict (e.g. telemetry shows no reflow deviation, but a defect pattern typically associated with reflow issues is present), the agent explicitly records this as a `contradiction` node rather than silently dropping one side.
3. **Gap flagging**: if any domain's evidence is missing (an upstream agent errored), the graph explicitly marks that domain as `evidence_unavailable` rather than presenting a graph that looks complete.

**Output**: an `evidence_graph` object (nodes, edges, contradictions, gaps) is returned to the Orchestrator as a `task_result`, and is the sole structured input to Stage 9's `HypothesisRankingAgent`. The QE can view the evidence graph directly in the Investigation Workspace before hypothesis ranking proceeds, satisfying the Phase 1 trust/explainability requirement that reasoning inputs be visible, not just conclusions.

### 2.3 Stage 9 Narrative — `HypothesisRankingAgent`

`HypothesisRankingAgent` receives the Stage 8 evidence graph plus the Stage 9 `HistoricalIncidentAgent` output (semantically similar closed incidents with their confirmed root causes). It does not receive raw MCP tool outputs directly — only the already-correlated graph and precedent list, keeping its reasoning scope well-defined.

**Process:**
1. Enumerate candidate root-cause hypotheses supported by two or more evidence-graph nodes (a hypothesis with only one weak supporting node is retained but flagged with low confidence, never discarded silently).
2. For each candidate, populate the full `RootCauseHypothesis` schema: `conclusion`, `supporting_evidence_list` (evidence node IDs), `contradicting_evidence_list` (any conflicting nodes), `confidence_level`, `evidence_provenance_references`, and a `reasoning_summary` written in plain language citing the supporting evidence — never the model's raw internal reasoning trace.
3. Rank candidates by confidence, informed by both evidence-graph strength and precedent similarity from `HistoricalIncidentAgent` (a hypothesis matching a previously *confirmed* root cause on a similar incident is weighted higher, but precedent alone never overrides direct evidence).
4. If any candidate hypothesis would attribute fault to a supplier, the `reasoning_summary` must use the mandated correlation-only wording from SOP-SUPP-008 Section 6 — this is enforced regardless of how strong the statistical signal is.

**Output**: the ranked hypothesis list is presented to the QE via the Investigation Workspace as the Stage 9 HITL gate. The Orchestrator does not proceed to Stage 10 until the QE has explicitly confirmed or rejected each hypothesis — `HypothesisRankingAgent` output is a recommendation only, never a committed conclusion.

---

## 3. State Management & Context Propagation

### 3.1 `InvestigationContext` Object

InvestigationContext {
incident_id: UUID
current_stage: integer
status: enum (in_progress | awaiting_approval | complete | failed)
evidence_graph: dict (keyed by domain: vision, telemetry, machine_health, component_lot, documents)
completed_stages: list[integer]
pending_approvals: list[PendingApprovalRequest]
agent_results: dict (keyed by agent name → most recent task_result payload)
created_at: UTC datetime
last_updated: UTC datetime
}


### 3.2 Storage: PostgreSQL vs. Redis vs. In-Memory

| Store | Role | Justification |
|---|---|---|
| **PostgreSQL** | Durable system of record for `InvestigationContext` | Consistent with the Phase 2 principle that PostgreSQL is the persistent system of record; investigations must survive process restarts, span multiple QE sessions, and be fully auditable months later |
| **Redis** | Ephemeral live-session cache (e.g. current UI view state, in-flight agent dispatch tracking while a stage is actively executing) | Matches the Phase 2 Redis-vs-PostgreSQL boundary — fast, temporary state that can be safely rebuilt from PostgreSQL if lost |
| **In-memory only** | **Rejected** | An investigation is not a single-request transaction — it spans human review cycles, potential days-long pauses, and must be resumable after a service restart. In-memory-only state would be lost on any process crash, violating the durability and audit requirements established in Phase 1 |

**Pattern**: PostgreSQL is written on every stage completion and every human approval/rejection event (durable checkpoint). Redis holds a live cache of the current `InvestigationContext` for fast UI reads during active work, refreshed from PostgreSQL on cache miss or after a resume.

### 3.3 `PendingApprovalRequest` Schema (referenced from Phase 5, reused here)
PendingApprovalRequest {
request_id: UUID
incident_id: UUID
originating_agent: string
tool_name: string (nullable — populated if generated via an MCP tool call)
proposed_action: string
supporting_evidence_refs: list of UUIDs
requires_approval_by: string (persona)
status: enum (pending | approved | rejected)
created_at: UTC datetime
approved_by: string, nullable
approved_at: UTC datetime, nullable
}

This is the same object introduced in `mcp-architecture.md` Section 5.2 — the A2A layer does not redefine it, it propagates the identical schema so that a recommendation surfaced by an agent and a recommendation surfaced by a direct MCP tool call are indistinguishable to the approval workflow.

### 3.4 Pause & Resume Behavior

If a QE logs off mid-investigation:

1. The Orchestrator's last durable checkpoint in PostgreSQL reflects `status: in_progress` or `status: awaiting_approval` and the exact `completed_stages` list.
2. No agent continues executing in the background past the last completed stage — the investigation simply stops advancing until the QE (or another authorized QE) resumes.
3. On resume, the Orchestrator reloads `InvestigationContext` from PostgreSQL (rehydrating the Redis cache), determines `current_stage` from `completed_stages`, and re-renders any `pending_approvals` that were awaiting sign-off, rather than re-running already-completed stages.
4. If `pending_approvals` existed at pause time, they remain `pending` indefinitely until acted upon — no automatic expiration or auto-approval occurs.

### 3.5 Evidence Graph Accumulation

Each specialist agent's `task_result` payload is appended to `agent_results[agent_name]` and its evidence items are merged into `evidence_graph[domain]` as they arrive — not held back until all agents finish. This lets the QE inspect partial evidence in the Investigation Workspace while later stages are still executing, consistent with the transparency requirements from Phase 1. The full cross-domain graph (with edges and contradictions) is only materialized once `EvidenceCorrelationAgent` runs at Stage 8, but the underlying per-domain evidence is visible incrementally from Stage 3 onward.