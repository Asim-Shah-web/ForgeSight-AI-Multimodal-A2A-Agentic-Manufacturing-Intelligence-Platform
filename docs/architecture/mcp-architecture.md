# MCP Architecture — ForgeSight AI

## 1. Boundary Discovery & Overview

### 1.1 Why MCP

ForgeSight agents and workflow stages need read access to several independent enterprise systems (MES, CMMS, ERP, Inspection DB) and to the RAG/document subsystem. Ad-hoc direct database queries or a monolithic integration API were rejected for three reasons:

- **Tool-level auditability**: MCP calls are discrete, named, parameterized operations (`get_production_telemetry(...)`), which map directly onto the audit event schema (`who`, `tool_name`, `arguments`, `result_hash`) already defined in Phase 1/2. A raw SQL query or a generic REST call does not carry the same self-describing semantics.
- **Uniform permission scoping**: MCP lets each tool declare its own risk tier and required persona scope independent of the underlying system's native access model, so a Production Operator and a Quality Engineer can hit the same enterprise system through different, appropriately scoped tools.
- **Server/domain separation**: MCP naturally partitions "manufacturing operational data" (MES/CMMS/ERP/Inspection DB) from "knowledge data" (documents/RAG), which mirrors the Phase 2 domain boundary and lets each server evolve, scale, and be secured independently.

### 1.2 Enterprise Boundaries Bridged by MCP

**1. Manufacturing Data Boundary** — bridged by the Manufacturing MCP Server:
- MES: batch records, production telemetry
- CMMS: machine health, nozzle/feeder maintenance history
- ERP: component lots, supplier records
- Inspection DB: AOI images, CV findings

**2. Document Data Boundary** — bridged by the Document MCP Server:
- Technical document repository (SOPs, machine manuals)
- pgvector store (chunk embeddings, incident embeddings)
- Historical incident corpus

### 1.3 What MCP Is NOT Allowed To Do

- MCP tools never directly actuate physical equipment (no machine parameter writes, no shutdown commands).
- MCP tools never autonomously finalize a quality hold, SCAR, or root-cause attribution — any tool whose effect would change manufacturing or supplier state must terminate in a `PendingApprovalRequest` (Section 5), not a completed action.
- MCP tools never bypass persona permission scopes established in `docs/business/personas.md` — a tool call is rejected, not down-scoped silently, if the caller's persona lacks the required permission.
- MCP tools never return unresolved chain-of-thought or model-internal reasoning — only structured data and provenance, consistent with the Phase 1 "no hidden reasoning" rule.

---

## 2. Manufacturing MCP Server Specification (`mcp_servers/manufacturing/`)

All tools below are read-only or recommendation-only (Low/Medium risk — see Section 5) unless noted. Full schemas are also captured in `mcp_servers/manufacturing/README.md`.

### 2.1 `get_board_inspection_data`

**Purpose**: Retrieve raw board-level AOI inspection detail for evidence gathering (Stage 3).

**Input:**
| Parameter | Type | Required | Description |
|---|---|---|---|
| `board_id` | string | Yes | Unique board serial identifier |

**Output (JSON):**
```json
{
  "board_id": "BRD-24017-00432",
  "batch_id": "B-24017",
  "product_id": "ECU-2026",
  "aoi_flags": [
    {
      "component_designator": "C17",
      "defect_type": "component_misalignment",
      "confidence": 0.91,
      "bounding_box": [412, 188, 40, 40],
      "image_reference": "s3://forgesight-images/BRD-24017-00432/aoi_01.png",
      "cv_finding_id": "CVF-88213"
    }
  ],
  "inspection_timestamp": "2026-02-03T08:14:22Z",
  "source_system": "InspectionDB",
  "retrieved_at": "2026-02-03T09:02:11Z"
}
```

**Errors:**
| Code | Meaning |
|---|---|
| `BOARD_NOT_FOUND` | No record for `board_id` |
| `PERMISSION_DENIED` | Caller persona lacks READ scope for InspectionDB |

**Risk Tier**: Low (read-only)

---

### 2.2 `get_production_telemetry`

**Purpose**: Retrieve time-series sensor/process data for a machine/batch window (Stage 4).

**Input:**
| Parameter | Type | Required | Description |
|---|---|---|---|
| `machine_id` | string | Yes | e.g. `PLACER-07` |
| `batch_id` | string | Yes | e.g. `B-24017` |
| `start_time` | string (ISO 8601 UTC) | Yes | Window start |
| `end_time` | string (ISO 8601 UTC) | Yes | Window end |

**Output (JSON):**
```json
{
  "machine_id": "PLACER-07",
  "batch_id": "B-24017",
  "telemetry": [
    {
      "timestamp": "2026-02-03T07:58:00Z",
      "parameter": "placement_head_pressure",
      "value": 4.82,
      "unit": "bar"
    },
    {
      "timestamp": "2026-02-03T07:58:00Z",
      "parameter": "vacuum_level",
      "value": 0.71,
      "unit": "relative"
    }
  ],
  "source_system": "MES",
  "data_snapshot_timestamp": "2026-02-03T09:03:00Z",
  "retrieved_at": "2026-02-03T09:03:05Z"
}
```

**Errors:**
| Code | Meaning |
|---|---|
| `MACHINE_NOT_FOUND` | Invalid `machine_id` |
| `NO_TELEMETRY_IN_WINDOW` | No data in the given range |
| `INVALID_TIME_RANGE` | `start_time` ≥ `end_time` |

**Risk Tier**: Low (read-only)

---

### 2.3 `get_machine_maintenance_history`

**Purpose**: Retrieve maintenance/nozzle wear history for a machine (Stage 5).

**Input:**
| Parameter | Type | Required | Description |
|---|---|---|---|
| `machine_id` | string | Yes | e.g. `PLACER-07` |
| `nozzle_id` | string | No | Filter to a specific nozzle position |

**Output (JSON):**
```json
{
  "machine_id": "PLACER-07",
  "maintenance_records": [
    {
      "record_id": "MR-55210",
      "nozzle_id": "NZ-07-03",
      "last_cleaned": "2026-01-05T00:00:00Z",
      "days_since_cleaning": 29,
      "wear_measurement_mm": 0.04,
      "vacuum_test_result": "pass",
      "disposition": "clean_recommended"
    }
  ],
  "source_system": "CMMS",
  "retrieved_at": "2026-02-03T09:05:00Z"
}
```

**Errors:**
| Code | Meaning |
|---|---|
| `MACHINE_NOT_FOUND` | Invalid `machine_id` |
| `NOZZLE_NOT_FOUND` | Invalid `nozzle_id` for given machine |

**Risk Tier**: Low (read-only)

---

### 2.4 `get_component_lot_history`

**Purpose**: Retrieve lot genealogy, supplier linkage, and incoming inspection stats (Stage 6).

**Input:**
| Parameter | Type | Required | Description |
|---|---|---|---|
| `lot_number` | string | Yes | e.g. `LOT-9921` |
| `part_number` | string | Yes | e.g. `CAP-10UF-0603` |

**Output (JSON):**
```json
{
  "lot_number": "LOT-9921",
  "part_number": "CAP-10UF-0603",
  "supplier_id": "SUP-0042",
  "supplier_name": "Acme Passive Components",
  "incoming_inspection": {
    "sample_size": 50,
    "defect_count": 2,
    "rejection_threshold": 3,
    "disposition": "accepted"
  },
  "historical_defect_rate_pct": 1.8,
  "plant_wide_defect_rate_pct": 0.6,
  "source_system": "ERP",
  "retrieved_at": "2026-02-03T09:07:00Z"
}
```

**Note**: This tool never returns a `root_cause` or `supplier_fault` field — only observed statistics, consistent with the supplier attribution rule in `personas.md` Section 4.6 and SOP-SUPP-008.

**Errors:**
| Code | Meaning |
|---|---|
| `LOT_NOT_FOUND` | Invalid `lot_number`/`part_number` combination |

**Risk Tier**: Low (read-only)

---

### 2.5 `recommend_preventative_maintenance`

**Purpose**: Generate a pending maintenance recommendation from investigation evidence (does not create a Work Order by itself).

**Input:**
| Parameter | Type | Required | Description |
|---|---|---|---|
| `machine_id` | string | Yes | Target machine |
| `nozzle_id` | string | Yes | Target nozzle |
| `reason` | string | Yes | Evidence-based justification |

**Output (JSON):**
```json
{
  "recommendation_id": "REC-3391",
  "status": "pending_approval",
  "machine_id": "PLACER-07",
  "nozzle_id": "NZ-07-03",
  "reason": "Nozzle NZ-07-03 last cleaned 29 days ago; associated with 3 component_misalignment defects on C17 in batch B-24017.",
  "recommended_action": "clean_and_inspect",
  "requires_approval_by": "Maintenance Engineer",
  "created_at": "2026-02-03T09:10:00Z"
}
```

**Errors:**
| Code | Meaning |
|---|---|
| `MACHINE_NOT_FOUND` / `NOZZLE_NOT_FOUND` | Invalid target |
| `PERMISSION_DENIED` | Caller not authorized to submit recommendations |

**Risk Tier**: Medium (record/recommendation — output is a `PendingApprovalRequest`-shaped payload, never an executed Work Order)

---

## 3. Document & Knowledge MCP Server Specification (`mcp_servers/documents/`)

These tools wrap the Phase 4 RAG subsystem contract. All outputs reuse the `RetrievedPassage` schema defined in `docs/architecture/rag-architecture.md` Section 6.

### 3.1 `search_technical_sops`

**Purpose**: Semantic/hybrid retrieval of SOP and machine manual passages (Stage 7).

**Input:**
| Parameter | Type | Required | Description |
|---|---|---|---|
| `query` | string | Yes | Free-text or templated query |
| `category` | string | No | `sop`, `machine_manual`, `engineering_doc` |
| `machine_id` | string | No | Filter/boost context, e.g. `PLACER-07` |

**Output (JSON):**
```json
{
  "results": [
    {
      "passage_id": "PSG-77120",
      "document_id": "SOP-QUAL-042",
      "document_title": "Component Placement Alignment Inspection",
      "document_version": "v1.0",
      "section_title": "Acceptance Criteria — Placement Alignment (IPC-A-610 Class 3)",
      "section_reference": "Section 4.2",
      "chunk_text": "Chip capacitors/resistors (0402–1210): Maximum lateral offset 25% of component width or 0.2 mm, whichever is smaller...",
      "retrieval_score": 0.88,
      "rerank_score": 0.93,
      "retrieval_query": "placement tolerance 10uF capacitor C17",
      "retrieval_timestamp": "2026-02-03T09:12:00Z",
      "embedding_model": "bge-large-en-v1.5",
      "retrieved_by": "agent"
    }
  ],
  "result_count": 1
}
```

**Errors:**
| Code | Meaning |
|---|---|
| `NO_RELEVANT_DOCUMENT_FOUND` | No passage cleared the minimum relevance threshold — per Phase 4 hallucination mitigation, this is returned explicitly rather than an empty/fabricated result |

**Risk Tier**: Low (read-only)

---

### 3.2 `get_document_by_id`

**Purpose**: Retrieve the full text and metadata of a specific document version.

**Input:**
| Parameter | Type | Required | Description |
|---|---|---|---|
| `document_id` | string | Yes | e.g. `SOP-MAINT-017` |
| `version` | string | No | Defaults to latest `active` version |

**Output (JSON):**
```json
{
  "document_id": "SOP-MAINT-017",
  "title": "SMT Placer Nozzle Inspection & Replacement",
  "version": "v1.0",
  "status": "active",
  "category": "sop",
  "full_text": "... full document markdown ...",
  "approved_by": "Maintenance Engineer; Quality Manager",
  "date": "2026-01-15"
}
```

**Errors:**
| Code | Meaning |
|---|---|
| `DOCUMENT_NOT_FOUND` | Invalid `document_id` |
| `VERSION_NOT_FOUND` | Invalid `version` for given document |

**Risk Tier**: Low (read-only)

---

### 3.3 `search_historical_incidents`

**Purpose**: Semantic retrieval of similar closed incidents (Stage 9).

**Input:**
| Parameter | Type | Required | Description |
|---|---|---|---|
| `defect_type` | string | Yes | e.g. `component_misalignment` |
| `component_id` | string | No | e.g. `C17` |
| `top_k` | integer | No (default 5) | Number of results |

**Output (JSON):**
```json
{
  "results": [
    {
      "incident_id": "INCIDENT-2025-00317",
      "title": "C11 misalignment cluster, SMT-LINE-02",
      "defect_type": "component_misalignment",
      "root_cause_confirmed": "Nozzle wear on PLACER-05, position NZ-05-02",
      "corrective_action_taken": "Nozzle replacement + revised cleaning interval",
      "similarity_score": 0.86,
      "retrieval_timestamp": "2026-02-03T09:14:00Z"
    }
  ],
  "result_count": 1
}
```

**Errors:**
| Code | Meaning |
|---|---|
| `NO_SIMILAR_INCIDENTS_FOUND` | No historical incident above similarity threshold |

**Risk Tier**: Low (read-only)

---

## 4. MCP Security, Transport, and RBAC Architecture

### 4.1 Transport Protocol

| Mode | Use Case |
|---|---|
| **stdio** | Local agent subprocess invocation during development/testing — an agent process spawns the MCP server directly and communicates over stdin/stdout |
| **SSE / HTTP** | Production deployment — MCP servers run as long-lived services callable by multiple agents/workflow instances over the network, behind the platform's existing authentication layer |

Development and CI use stdio for simplicity and reproducibility; the deployment architecture (a later phase) will finalize SSE/HTTP hosting details.

### 4.2 Token Authentication & RBAC Scoping

- Every MCP call carries a **caller identity token** resolved to a `User` record and its associated **persona** (Production Operator, Quality Engineer, Manufacturing Engineer, Maintenance Engineer, Quality Manager, SQE, System Administrator).
- Each tool declares a `required_permissions` list drawn from the persona permission vocabulary already defined in `docs/business/personas.md` (e.g. `READ`, `ANALYZE`, `RECOMMEND_PROCESS_CHANGE`).
- On invocation, the MCP server checks the caller's persona permissions against the tool's `required_permissions`. A mismatch returns `PERMISSION_DENIED` — the server never silently narrows the request or substitutes a lower-privilege response.
- System Administrator identity may configure server-level settings (endpoints, timeouts, model versions) but is never granted `required_permissions` for investigation-domain tools, consistent with the Section 4.7 persona boundary ("technical system access ≠ manufacturing business approval authority").

### 4.3 Audit Logging

Every MCP tool call produces an `AuditEvent` (schema per Phase 2 Section 18) with at minimum:

| Field | Description |
|---|---|
| `who` | Caller identity + persona |
| `tool_name` | e.g. `get_production_telemetry` |
| `arguments` | Full input parameters (redacted only if they contain no evidentiary value) |
| `timestamp` | UTC call time |
| `result_hash` | Hash of the returned payload, for tamper-evidence without duplicating full data in the audit log |
| `incident_id` | Associated investigation, when applicable |
| `result` | `success`, `error:<code>`, or `pending_approval` |

Audit records are append-only and are themselves subject to the Phase 1 immutability requirement.

---

## 5. Human Approval & High-Risk Tool Execution Model

### 5.1 Risk Tier Classification

| Tier | Tools | Characteristics |
|---|---|---|
| **Low (Read-only)** | `get_board_inspection_data`, `get_production_telemetry`, `get_machine_maintenance_history`, `get_component_lot_history`, `search_technical_sops`, `get_document_by_id`, `search_historical_incidents` | No state change; executes immediately, fully logged |
| **Medium (Record edits / recommendations)** | `recommend_preventative_maintenance`, SCAR drafting tools (future) | Produces a proposal record, not an authorized action; requires named-persona approval before downstream effect |
| **High (Physical/financial state change)** | `execute_batch_hold`, `modify_machine_parameters` (not exposed as callable tools in this phase — reserved/blocked) | Would alter physical production state or financial/supplier standing; never auto-executed |

### 5.2 HITL Approval Gate Pattern

Any Medium or High risk tool call terminates in a `PendingApprovalRequest` object rather than a completed action:

```json
{
  "request_id": "APR-2216",
  "tool_name": "recommend_preventative_maintenance",
  "proposed_action": "clean_and_inspect nozzle NZ-07-03 on PLACER-07",
  "supporting_evidence_refs": ["MR-55210", "CVF-88213", "CVF-88214"],
  "requires_approval_by": "Maintenance Engineer",
  "status": "pending",
  "created_at": "2026-02-03T09:10:00Z",
  "approved_by": null,
  "approved_at": null
}
```

- High-risk tools (`execute_batch_hold`, `modify_machine_parameters`) are **not implemented as directly callable MCP tools** in this phase; they are named here only to establish that, if implemented, they would require explicit persona sign-off (Quality Manager for batch holds, Manufacturing/Maintenance Engineer + physical lockout procedure for parameter changes) and would still only ever emit a `PendingApprovalRequest`, never execute directly.
- No MCP tool call is permitted to transition a `PendingApprovalRequest` to `approved` — approval is a human action captured through the Investigation Workspace UI and written back as an `AuditEvent` with `approval_by` populated.

---

## 6. Workflow Integration & Stage Mapping

| Workflow Stage | MCP Tool(s) Used | Server |
|---|---|---|
| Stage 1 — Defect Detection & Threshold Trigger | *(CV pipeline output, not an MCP tool call)* | — |
| Stage 2 — Incident Creation & Context Setup | `get_board_inspection_data` (initial context pull) | Manufacturing |
| Stage 3 — Visual Evidence Extraction | `get_board_inspection_data` | Manufacturing |
| Stage 4 — Production & Telemetry Investigation | `get_production_telemetry` | Manufacturing |
| Stage 5 — Machine & Maintenance Check | `get_machine_maintenance_history`, `recommend_preventative_maintenance` | Manufacturing |
| Stage 6 — Component Lot & Supplier Correlation | `get_component_lot_history` | Manufacturing |
| Stage 7 — Technical SOP & Manual Retrieval | `search_technical_sops`, `get_document_by_id` | Documents |
| Stage 8 — Evidence Correlation & Synthesis | *(consumes outputs of Stages 3–7; no new tool calls)* | — |
| Stage 9 — Root-Cause Hypothesis Ranking | `search_historical_incidents` | Documents |
| Stage 10 — Corrective Action Recommendation | `recommend_preventative_maintenance` (if maintenance-related) | Manufacturing |
| Stage 11 — Human Engineer Review & Sign-Off | *(human action; may re-invoke any Low-risk tool for verification)* | Both |
| Stage 12 — Report Generation & Audit Trail | *(aggregates prior tool call audit events; no new evidence tool calls)* | — |