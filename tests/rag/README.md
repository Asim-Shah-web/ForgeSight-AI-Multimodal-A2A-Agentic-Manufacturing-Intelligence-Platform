# RAG Module Test Strategy — ForgeSight AI

This directory will hold tests for `src/forgesight/rag/` once implementation begins. This file documents the intended test strategy only — no test code exists yet.

## Test Categories

### Unit Tests

- `chunking/`: verify paragraph/section-level chunking respects target chunk size (150–400 tokens), correct overlap handling, and correct chunk metadata population (`section_title`, `section_reference`, `chunk_index`).
- `ingestion/`: verify metadata extraction correctness, rejection of documents missing required metadata, and correct handling of document version bumps (old chunks retired, new chunks active).
- `embeddings/`: verify embedding dimension matches `vector(1024)`, and correct `embedding_model` stamping.
- `retrieval/`: verify query construction template correctly incorporates investigation context fields (machine_id, defect_type, component_id).
- `reranking/`: verify reranked output ordering differs appropriately from pre-rerank ordering on known test cases.

### Integration Tests

- End-to-end: document ingestion → chunking → embedding → indexing → retrieval → `RetrievedPassage` output, using the five synthetic SOPs as fixtures.
- Version update flow: ingest v1.0 of a synthetic SOP, then v1.1, and verify only `status = active` chunks are returned by default retrieval.

### Evaluation Tests

- Run the golden dataset (`data/evaluation/rag_golden_dataset.json`) through the retrieval pipeline and assert Precision@5 ≥ 0.80 and NDCG@5 ≥ 0.75, per the thresholds defined in `docs/architecture/rag-architecture.md` Section 1.5.

### Safety/Compliance Tests

- Assert that a query with no relevant passage above threshold returns "No relevant document found" rather than any fabricated passage.
- Assert that `status = retired` chunks are excluded from default retrieval results.
- Assert that historical incident retrieval never returns a `root_cause_confirmed` value for an incident that has not passed human sign-off (Stage 11).

## Status

No test code exists yet — this phase is documentation only. Implementation of these tests is deferred to the phase in which `src/forgesight/rag/` is actually built.
