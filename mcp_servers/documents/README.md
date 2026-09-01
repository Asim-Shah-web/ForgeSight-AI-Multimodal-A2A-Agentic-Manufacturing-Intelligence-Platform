# Document & Knowledge MCP Server

Bridges ForgeSight to the technical document repository and the RAG/pgvector subsystem defined in `docs/architecture/rag-architecture.md`. See `docs/architecture/mcp-architecture.md` Section 3 for full schema detail; this README is the server-local quick reference.

## Tools

| Tool | Risk Tier | Underlying RAG Component | Workflow Stage |
|---|---|---|---|
| `search_technical_sops` | Low | Retrieval + reranking pipeline (`rag-architecture.md` Section 5) | Stage 7 |
| `get_document_by_id` | Low | Document store (`data/documents/`) | Stage 7 |
| `search_historical_incidents` | Low | `incident_embeddings` similarity search | Stage 9 |

## Output Contract

All `search_technical_sops` results use the `RetrievedPassage` schema defined in `docs/architecture/rag-architecture.md` Section 6.1 — every result carries full provenance (document title, version, section reference, retrieval/rerank score, query, timestamp, embedding model).

`search_historical_incidents` results use the Historical Incident Retrieval schema in `rag-architecture.md` Section 6.3.

## Hallucination Mitigation (Mandatory)

If no passage clears the minimum relevance threshold, `search_technical_sops` returns `NO_RELEVANT_DOCUMENT_FOUND` rather than a low-confidence or fabricated result, per the Phase 4 citation-or-abstain rule. The same principle applies to `search_historical_incidents` via `NO_SIMILAR_INCIDENTS_FOUND`.

## Permission Requirements

| Tool | Minimum Required Persona Permission |
|---|---|
| `search_technical_sops` | `READ` (all quality-related personas) |
| `get_document_by_id` | `READ` |
| `search_historical_incidents` | `READ` / `ANALYZE` |

No document tool in this server can create, modify, or retire a document — document governance/versioning (`rag-architecture.md` Section 2.3–2.4) remains a human-approved authoring process outside MCP.

## Error Codes (Common)

| Code | Meaning |
|---|---|
| `DOCUMENT_NOT_FOUND` | Invalid `document_id` |
| `VERSION_NOT_FOUND` | Invalid `version` for a valid document |
| `NO_RELEVANT_DOCUMENT_FOUND` | No passage above relevance threshold |
| `NO_SIMILAR_INCIDENTS_FOUND` | No historical incident above similarity threshold |

## Status

Specification only — no server implementation exists yet in this phase.


