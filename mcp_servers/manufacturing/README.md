# Manufacturing MCP Server

Bridges ForgeSight to MES, CMMS, ERP, and Inspection DB. See `docs/architecture/mcp-architecture.md` Section 2 for full schema detail; this README is the server-local quick reference.

## Tools

| Tool | Risk Tier | Source System | Workflow Stage |
|---|---|---|---|
| `get_board_inspection_data` | Low | Inspection DB | Stage 2, 3 |
| `get_production_telemetry` | Low | MES | Stage 4 |
| `get_machine_maintenance_history` | Low | CMMS | Stage 5 |
| `get_component_lot_history` | Low | ERP | Stage 6 |
| `recommend_preventative_maintenance` | Medium | CMMS (writes a pending recommendation only) | Stage 5, 10 |

## Permission Requirements

| Tool | Minimum Required Persona Permission |
|---|---|
| `get_board_inspection_data` | `READ` (Quality Engineer, Manufacturing Engineer, Maintenance Engineer, Quality Manager) |
| `get_production_telemetry` | `READ` / `ANALYZE` |
| `get_machine_maintenance_history` | `READ` (Maintenance Engineer, Quality Engineer, Quality Manager) |
| `get_component_lot_history` | `READ` (SQE, Quality Engineer, Quality Manager) |
| `recommend_preventative_maintenance` | `RECOMMEND_PROCESS_CHANGE` equivalent — caller must be Maintenance Engineer or Quality Engineer; approval authority remains with Maintenance Engineer |

## Not Implemented (Reserved / Blocked)

- `execute_batch_hold` — High risk; reserved for a future phase with explicit Quality Manager sign-off gating. Not callable today.
- `modify_machine_parameters` — High risk; reserved, requires physical lockout procedure and Manufacturing/Maintenance Engineer approval. Not callable today.

## Error Codes (Common)

| Code | Meaning |
|---|---|
| `PERMISSION_DENIED` | Caller persona lacks required permission for this tool |
| `*_NOT_FOUND` | Requested entity (board/machine/nozzle/lot) does not exist |
| `INVALID_TIME_RANGE` | Malformed or inverted time window |

## Audit

Every call emits an `AuditEvent` per `docs/architecture/mcp-architecture.md` Section 4.3. No tool in this server executes a physical or financial state change; `recommend_preventative_maintenance` only ever produces a `PendingApprovalRequest`.

## Status

Specification only — no server implementation exists yet in this phase.
