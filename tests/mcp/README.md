# MCP Test Strategy — ForgeSight AI

Documents the intended test strategy for both MCP servers once implementation begins. No test code exists yet.

## Test Categories

### Tool Contract Tests
- For each tool in `mcp_servers/manufacturing/` and `mcp_servers/documents/`: verify input validation (required parameters, type checking) and that output matches the documented JSON schema exactly, including all provenance fields.
- Verify every documented error code is triggered under the corresponding invalid-input condition (e.g. `BOARD_NOT_FOUND`, `INVALID_TIME_RANGE`).

### RBAC Tests
- For each tool, verify a caller with insufficient persona permission receives `PERMISSION_DENIED` and no partial or downgraded data is returned.
- Verify a System Administrator identity can invoke server configuration operations but is rejected on every investigation-domain tool (per the persona boundary in `docs/business/personas.md` Section 4.7).
- Verify persona-to-tool permission mapping matches Section "Permission Requirements" in each server's README exactly.

### Approval Gate Tests
- Verify `recommend_preventative_maintenance` always returns a `PendingApprovalRequest`-shaped payload with `status: "pending"` and never a completed/executed action.
- Verify no test or code path can programmatically set `approved_by`/`status: "approved"` on a `PendingApprovalRequest` without a simulated human approval action.
- Verify High-risk tools (`execute_batch_hold`, `modify_machine_parameters`) are not registered/callable in the current tool registry.

### Audit Logging Tests
- Verify every tool call (success or error) produces exactly one `AuditEvent` with all required fields populated (`who`, `tool_name`, `arguments`, `timestamp`, `result_hash`, `incident_id` where applicable).
- Verify `result_hash` changes if and only if the returned payload changes (tamper-evidence check).

### RAG Integration Tests (Document Server)
- Verify `search_technical_sops` returns `NO_RELEVANT_DOCUMENT_FOUND` rather than any passage when queried against an out-of-corpus topic.
- Verify `RetrievedPassage` fields returned by the tool match the schema in `rag-architecture.md` Section 6.1 field-for-field.

### Supplier Safety Tests
- Verify `get_component_lot_history` output never includes a `root_cause` or supplier-fault field, only observed statistics (sample size, defect count, historical defect rate), per SOP-SUPP-008 and the persona supplier attribution rule.

## Status

No test code exists yet — this phase is documentation only. Implementation is deferred to the phase in which the MCP servers are actually built.
