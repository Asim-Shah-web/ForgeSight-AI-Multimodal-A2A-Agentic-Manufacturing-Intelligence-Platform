# ADR 005: Embedding Model Selection for RAG Subsystem

## Status

Accepted

## Context

ForgeSight's RAG subsystem requires a text embedding model to vectorize SOP/manual chunks and historical incident summaries for semantic similarity search in pgvector. The model must be selected before the `vector(N)` dimension placeholder from Phase 2 can be finalized.

## Candidates Considered

- OpenAI text-embedding-3-small (1536-dim, API-hosted)
- OpenAI text-embedding-ada-002 (1536-dim, API-hosted, legacy)
- sentence-transformers/all-mpnet-base-v2 (768-dim, local, Apache 2.0)
- BAAI/bge-large-en-v1.5 (1024-dim, local, MIT)
- nomic-embed-text (768-dim, local, Apache 2.0)

## Decision

**BAAI/bge-large-en-v1.5** is selected, with embedding dimension **1024**.

## Rationale

1. **Retrieval-specific benchmark strength**: bge-large-en-v1.5 ranks among the strongest open, locally-deployable models on MTEB retrieval sub-tasks, which directly matches ForgeSight's use case (passage retrieval, not classification/clustering).
2. **Local deployment**: avoids sending proprietary manufacturing, supplier, and incident data to an external API, which matters given the sensitivity of supplier quality and process data.
3. **License**: MIT license imposes no usage restriction concerns for a portfolio/production-track project.
4. **Input length fit**: 512-token max input aligns with the paragraph/section-level chunking strategy (150–400 tokens per chunk), keeping truncation risk low.
5. **Dimension tradeoff**: 1024 dimensions balance retrieval quality against storage/index size better than the 1536-dim OpenAI models, without sacrificing benchmark competitiveness.

## Consequences

- `vector(N)` in the Phase 2 conceptual schema is finalized as `vector(1024)` for both `document_chunks.embedding` and `incident_embeddings.embedding`.
- If a future phase requires switching embedding models, all existing chunks and incident summaries must be re-embedded per the versioning strategy in `rag-architecture.md` Section 4.7 — embeddings from different models are never compared directly.
- No API cost is introduced for embedding generation, but local compute/inference resourcing must be planned for in the deployment architecture (a later phase).

## Alternatives Rejected

- OpenAI models: rejected primarily due to external data egress for a manufacturing quality context, and per-call API cost at scale.
- all-mpnet-base-v2 / nomic-embed-text: both reasonable open alternatives, but bge-large-en-v1.5 has a stronger retrieval-benchmark profile at a comparable deployment cost.
