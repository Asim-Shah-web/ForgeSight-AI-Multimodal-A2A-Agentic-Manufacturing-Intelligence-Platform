# ADR 003: MCP Server Boundaries for ForgeSight AI

## Status
Accepted

## Context
ForgeSight needs standardized, auditable access to several independent enterprise systems (MES, CMMS, ERP, Inspection DB) and to its own RAG/document subsystem, without granting agents or workflow stages direct database or API access.

## Decision
Two MCP servers are established:

1. **Manufacturing MCP Server** (`mcp_servers/manufacturing/`) — bridges MES, CMMS, ERP, and Inspection DB. Tools: `get_board_inspection_data`, `get_production_telemetry`, `get_machine_maintenance_history`, `get_component_lot_history`, `recommend_preventative_maintenance`.
2. **Document MCP Server** (`mcp_servers/documents/`) — bridges the technical document repository and pgvector store. Tools: `search_technical_sops`, `get_document_by_id`, `search_historical_incidents`.

## Rationale

**Why two servers, not one:** the manufacturing boundary and the knowledge boundary have different data owners, different update cadences (telemetry is near-real-time; SOPs update quarterly), and different underlying storage (operational systems of record vs. pgvector). Separating them lets each evolve and scale independently and keeps each server's permission surface narrow and legible.

**Why not ad-hoc integration:** direct SQL/API access from agents would bypass the audit event schema, make RBAC enforcement inconsistent per-caller, and blur the boundary between read access and state-changing actions. MCP's discrete, named tool contract makes every access auditable and independently permission-scoped.

**Tool scoping principle:** every tool is scoped to the minimum data it needs to answer one investigation question (e.g., `get_component_lot_history` returns lot/supplier statistics, never a supplier-fault conclusion), keeping tool output aligned with the "correlation vs. evidence vs. confirmed root cause" distinction established for the Supplier Quality Engineer persona.

**HITL enforcement:** any tool whose effect would change manufacturing, maintenance, or supplier state is restricted to emitting a `PendingApprovalRequest` rather than executing directly. High-risk tools (`execute_batch_hold`, `modify_machine_parameters`) are deliberately not exposed as callable in this phase — only documented as future, gated capabilities — to prevent any accidental autonomous state change during agent development.

## Consequences
- Every MCP tool call is auditable via a uniform `AuditEvent` shape (`who`, `tool_name`, `arguments`, `timestamp`, `result_hash`, `incident_id`).
- Agents (Phase 6) will compose these tools according to the Stage Mapping in `mcp-architecture.md` Section 6, rather than issuing free-form queries against enterprise systems.
- Adding a new data source in the future means adding a new scoped tool (and, if the domain is distinct enough, a new server) rather than widening an existing tool's access.

## Alternatives Rejected
- **Single monolithic MCP server** for all data sources: rejected because it would mix operational and knowledge data governance, permission models, and update cadences into one surface.
- **Direct database/API access per agent**: rejected due to loss of uniform auditability and inconsistent RBAC enforcement across call sites.