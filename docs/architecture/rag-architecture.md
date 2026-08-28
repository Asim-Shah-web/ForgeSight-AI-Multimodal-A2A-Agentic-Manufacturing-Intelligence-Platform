# RAG Architecture

## 1. RAG Problem Definition & Knowledge Requirements

### 1.1 Problem Statement

ForgeSight's RAG subsystem does not perform generic document question-answering. It performs a narrowly scoped task:

> Given an active quality incident investigation (incident ID, defect type, affected component, machine, investigation stage), retrieve the most relevant SOP passages, machine manual sections, IPC standards references, and historical investigation summaries a Quality Engineer needs to interpret evidence and validate root-cause hypotheses.

RAG in ForgeSight is an **evidence retrieval mechanism**, not a conversational assistant. Every retrieval call is anchored to an investigation context object, not a freeform chat message.

### 1.2 Three Retrieval Scenarios

| Scenario | User Intent | Query Type | Expected Document Type | Expected Output | Evidence Use |
|---|---|---|---|---|---|
| SOP/Standards Retrieval | QE needs IPC-A-610 Class 3 placement tolerance or Placer-07-specific procedure | Semantic (concept-based) | SOP, IPC standard reference excerpt | Ranked passages with section reference | Attached to Stage 7 (Technical SOP & Manual Retrieval) as supporting evidence for hypothesis validation |
| Machine Manual Retrieval | Maintenance Engineer needs reflow oven Zone 4 calibration procedure | Semantic + keyword hybrid (machine/zone are exact terms) | Machine manual section | Ranked passages tied to machine ID | Attached to Stage 5 (Machine & Maintenance Check) as procedural reference |
| Historical Incident Retrieval | QE needs prior incidents involving nozzle wear + component misalignment on the same line | Semantic similarity over incident summaries | Historical incident record (not a document chunk) | Ranked list of similar incidents with outcome | Attached to Stage 9 (Root-Cause Hypothesis Ranking) as precedent evidence |

### 1.3 What Must NOT Be Retrieved

- Documents outside the approved, versioned corpus (no open internet retrieval at query time)
- Retired/superseded document versions, unless explicitly requested for historical audit
- Unverified or unapproved draft documents
- Any content the LLM invents when no supporting passage exists — the system must return "no relevant document found" rather than fabricate a citation

### 1.4 Retrieval Contract

**Input (Investigation Context):**

| Field | Type | Description |
|---|---|---|
| `incident_id` | UUID | Active investigation |
| `defect_type` | string | e.g. "component misalignment" |
| `component_id` | string | e.g. "C17" |
| `machine_id` | string | e.g. "PLACER-07" |
| `investigation_stage` | enum | One of the 12 workflow stages |
| `free_text_query` | string (optional) | QE-typed refinement of the query |

**Output:** ranked list of `RetrievedPassage` objects (defined in full in Section 6), each carrying document title, version, section reference, passage text, retrieval score, query used, and timestamp.

### 1.5 "Good Enough" Thresholds

Because ForgeSight is a decision-support tool feeding human sign-off (not an autonomous actor), retrieval quality targets are set conservatively:

| Metric | Target | Rationale |
|---|---|---|
| Precision@5 | ≥ 0.80 | Of the top 5 passages shown to a QE, at least 4 should be genuinely relevant to avoid eroding trust |
| NDCG@5 | ≥ 0.75 | Most relevant passage should rank near the top, not buried at position 5 |
| Recall@10 | ≥ 0.90 (on golden dataset) | The correct SOP section should almost always appear somewhere in the candidate pool before reranking |

These are **development-phase targets** validated against the synthetic golden dataset (Section 7), not production SLAs.

---

## 2. Document Strategy & Knowledge Source Planning

### 2.1 Four Knowledge Categories

| Category | Document Type | Format | Approx. Volume (dev phase) | Update Frequency | Access Control |
|---|---|---|---|---|---|
| Manufacturing SOPs | Quality inspection procedures, defect containment, IPC-A-610 acceptance criteria references | Markdown (synthetic), PDF (real-world) | 5 synthetic docs, 5–15 pages each | Low (quarterly review) | Read: all personas; Write: Quality Manager approval required |
| Machine Manuals | Placer setup, nozzle maintenance, reflow profiling, stencil printer setup | Markdown/PDF | 2–4 docs (subset covered by synthetic SOPs) | Low (tied to equipment revisions) | Read: Manufacturing/Maintenance Engineer, QE; Write: Maintenance Engineer + Quality Manager sign-off |
| Engineering Documents | Process capability studies, FPY guidelines, FMEA templates | Markdown/PDF | 2–3 docs | Medium (per process change) | Read: Manufacturing Engineer, QE; Write: Manufacturing Engineer |
| Historical Investigation Reports | Past incident summaries with confirmed root cause + corrective action | Structured record (not chunked like SOPs) | Grows continuously (1 per closed incident) | Continuous | Read: all quality-related personas; Write: system-generated at Stage 12 sign-off |

### 2.2 Document Corpus Design (Development Phase)

- **Real documents**: publicly available IPC standard *references* (citation of clause numbers, e.g. IPC-A-610 Class 3 placement tolerance categories) may be referenced by name/number in synthetic SOPs; full IPC standard text is licensed and is NOT reproduced in the corpus.
- **Synthetic documents**: five SOPs authored specifically for ForgeSight, each written to be realistically retrievable as evidence for the `INCIDENT-2026-00421` scenario (C17 misalignment on PLACER-07).

| Document ID | Title | Covers |
|---|---|---|
| SOP-QUAL-042 | Component Placement Alignment Inspection | AOI inspection criteria for placement deviation, tied to IPC-A-610 Class 3 |
| SOP-MAINT-017 | SMT Placer Nozzle Inspection & Replacement | Nozzle wear thresholds, cleaning cadence, replacement procedure for Placer machines |
| SOP-PROC-031 | Reflow Oven Thermal Profile Verification | Zone temperature verification, profile deviation handling |
| SOP-SUPP-008 | Incoming Component Lot Inspection | Incoming inspection sampling plan, lot rejection criteria |
| SOP-QUAL-055 | Defect Containment & Batch Hold Procedure | Batch hold triggers, containment steps, escalation path |

Full content for each is provided as separate files below (Section 2.3 lists structure; actual files are `data/documents/synthetic/SOP-*.md`).

### 2.3 Document Governance Model

- **Approval authority**: Quality Manager approves SOP/QUAL and SOP/SUPP documents for ingestion; Maintenance Engineer + Quality Manager jointly approve SOP/MAINT documents; Manufacturing Engineer + Quality Manager approve SOP/PROC documents.
- **Version control**: every document has an incrementing `version` field (e.g. `v1.0`, `v1.1`). Ingestion is version-aware — see Section 3.5.
- **Mandatory metadata**: every document must carry the full metadata schema below before ingestion is permitted.

### 2.4 Document Metadata Schema

| Field | Type | Description |
|---|---|---|
| `document_id` | VARCHAR | Stable identifier, e.g. `SOP-QUAL-042` |
| `title` | VARCHAR | Human-readable title |
| `category` | ENUM | `sop`, `machine_manual`, `engineering_doc`, `historical_report` |
| `version` | VARCHAR | Semantic version string |
| `date` | DATE | Document effective date |
| `author` | VARCHAR | Author/owning role |
| `approved_by` | VARCHAR | Approving persona |
| `file_path` | TEXT | Storage location |
| `status` | ENUM | `active`, `retired` |
| `language` | VARCHAR | ISO language code |

---

## 3. Document Ingestion & Chunking Strategy Design

### 3.1 Ingestion Pipeline Stages

1. **Document Loading** — Markdown documents are parsed directly by heading structure; PDF documents (real-world IPC excerpts, machine manuals) would be parsed via a text/layout extraction library (conceptual only — no library selection or code at this stage).
2. **Metadata Extraction** — title, version, and section headers are extracted from document front-matter and Markdown heading hierarchy (`#`, `##`, `###`).
3. **Chunking** — document is split into retrievable units per the strategy in 3.2.
4. **Embedding** — each chunk is vectorized (Section 4).
5. **Indexing** — chunk text + embedding + metadata are stored in the `document_chunks` pgvector table.
6. **Verification** — an ingestion job confirms: chunk count matches expected section count, embedding dimension matches `vector(1024)`, and no chunk is missing required metadata (title, version, section reference).

### 3.2 Chunking Strategy Evaluation

| Strategy | Description | Fit for ForgeSight SOPs |
|---|---|---|
| Fixed-size (e.g. 512 tokens) | Simple sliding window | Poor — breaks numbered procedure steps and tables mid-unit |
| Sentence-level | One or few sentences per chunk | Poor — loses procedural context (a single inspection step often needs surrounding criteria) |
| Paragraph/section-level | Chunk boundaries follow document headings | **Good** — SOPs are already organized into clearly labeled sections (Purpose, Scope, Procedure, Acceptance Criteria) |
| Hierarchical (parent-child) | Store both section-level and sentence-level chunks | Best long-term, but adds complexity not justified at current corpus size |

**Selected strategy: Paragraph/section-level chunking.** ForgeSight's synthetic SOPs are authored with explicit section headings (Purpose, Scope, Referenced Standards, Procedure, Acceptance Criteria, Related Records). Chunking along these boundaries preserves the semantic unit a QE actually needs (e.g., the full "Acceptance Criteria" section for C17 placement tolerance), rather than a fragment of it. Hierarchical chunking is noted as a future enhancement if the corpus grows to include long, unstructured engineering documents.

- **Chunk size**: bounded by section length, target 150–400 tokens per chunk; sections longer than ~400 tokens are split at sub-heading or numbered-step boundaries.
- **Chunk overlap**: 1–2 sentences of overlap at chunk boundaries within an oversized section, to preserve continuity across a split.
- **Metadata stored per chunk**: see 3.3.

### 3.3 Chunk Metadata Schema

| Field | Type | Description |
|---|---|---|
| `chunk_id` | UUID | Unique chunk identifier |
| `document_id` | VARCHAR | Parent document |
| `document_title` | VARCHAR | Denormalized for fast display |
| `document_version` | VARCHAR | Version this chunk belongs to |
| `section_title` | VARCHAR | e.g. "Acceptance Criteria" |
| `section_reference` | VARCHAR | e.g. "Section 4.2" |
| `chunk_index` | INTEGER | Order within document |
| `chunk_text` | TEXT | Retrievable content |
| `token_count` | INTEGER | For diagnostics and re-chunking decisions |
| `created_at` | TIMESTAMP WITH TIME ZONE | Ingestion timestamp |

### 3.4 Document Update Handling

When a document version is bumped:

1. New version is ingested and chunked independently.
2. All chunks belonging to the prior version are marked `status = retired` (not deleted — retained for audit trail).
3. New chunks are indexed and marked `status = active`.
4. Retrieval queries by default only search `status = active` chunks, unless an audit/historical query explicitly requests retired versions.

### 3.5 Conceptual Module Responsibilities

- `src/forgesight/rag/ingestion/` — orchestrates document loading, metadata extraction, and the ingestion job (steps 1–2 and 6 above). Owns the "is this document allowed into the corpus" governance check.
- `src/forgesight/rag/chunking/` — owns the paragraph/section-level chunking logic and chunk metadata construction (step 3). Has no knowledge of embeddings or storage.

---

## 4. Embedding Strategy & Vector Store Design

### 4.1 Embedding Model Candidates

| Model | Dimension | Max Input Tokens | License | Deployment | MTEB Retrieval Avg (approx.) | Verdict |
|---|---|---|---|---|---|---|
| OpenAI text-embedding-3-small | 1536 | 8191 | Commercial API | API | ~62 | High quality, but introduces external API dependency and per-call cost inconsistent with an on-prem manufacturing tool |
| OpenAI text-embedding-ada-002 | 1536 | 8191 | Commercial API | API | ~61 (legacy) | Superseded by text-embedding-3 family; not preferred |
| sentence-transformers/all-mpnet-base-v2 | 768 | 384 | Apache 2.0 | Local | ~57 | Solid general-purpose baseline, but shorter max input truncates longer SOP sections |
| BAAI/bge-large-en-v1.5 | 1024 | 512 | MIT | Local | ~64 | Strong retrieval-specific benchmark performance, open-source, runs locally |
| nomic-embed-text | 768 | 8192 | Apache 2.0 | Local | ~62 | Long context window, open, but slightly behind bge-large on pure retrieval benchmarks |

### 4.2 Selected Embedding Model: **BAAI/bge-large-en-v1.5**

**Justification:**
- Purpose-built and benchmark-leading among open, locally-deployable models on MTEB retrieval sub-tasks, which is the exact task ForgeSight needs (not classification or clustering).
- Open license (MIT) with no per-call API cost or external data egress — important for a manufacturing environment handling proprietary process/supplier data.
- 1024-dimension vectors are a reasonable storage/performance tradeoff versus the 1536-dim OpenAI models.
- 512-token max input aligns well with the paragraph/section-level chunk sizes chosen in Section 3.2 (150–400 tokens), so truncation risk is low.

This selection resolves the Phase 2 placeholder: `vector(N)` → **`vector(1024)`**.

Full reasoning is recorded as a formal ADR (see `docs/decisions/adr/005-embedding-model-selection.md`).

### 4.3 Vector Store Design

**`document_chunks` table (conceptual, fills Phase 2 placeholder):**

| Column | Type | Constraints | Description |
|---|---|---|---|
| `chunk_id` | UUID | PRIMARY KEY | Unique chunk identifier |
| `document_id` | VARCHAR | NOT NULL, FK → documents | Parent document |
| `document_title` | VARCHAR | NOT NULL | Denormalized title |
| `document_version` | VARCHAR | NOT NULL | Version tag |
| `section_title` | VARCHAR | NULLABLE | Section heading |
| `section_reference` | VARCHAR | NULLABLE | e.g. "Section 4.2" |
| `chunk_index` | INTEGER | NOT NULL | Order within document |
| `chunk_text` | TEXT | NOT NULL | Retrievable passage |
| `token_count` | INTEGER | NOT NULL | Diagnostic field |
| `embedding` | vector(1024) | NOT NULL | bge-large-en-v1.5 embedding |
| `embedding_model` | VARCHAR | NOT NULL | Model name/version used |
| `status` | VARCHAR | NOT NULL, DEFAULT 'active' | active / retired |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL | Ingestion time |

**`incident_embeddings` table:**

| Column | Type | Constraints | Description |
|---|---|---|---|
| `embedding_id` | UUID | PRIMARY KEY | Unique identifier |
| `incident_id` | UUID | NOT NULL, FK → incidents | Source incident |
| `summary_text` | TEXT | NOT NULL | Human/AI-authored incident summary used for embedding |
| `embedding` | vector(1024) | NOT NULL | Semantic representation of the incident |
| `embedding_model` | VARCHAR | NOT NULL | Model name/version |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL | When embedded |

### 4.4 Index Type: HNSW vs. IVFFlat

| Index Type | Characteristics | Fit |
|---|---|---|
| IVFFlat | Requires pre-training on data distribution (a `lists` parameter tuned to table size); faster to build; slightly lower recall at low `probes` | Reasonable for very large, mostly-static corpora |
| HNSW | No training step required, higher recall at comparable speed, incrementally updatable as new SOPs/incidents are added | Better fit for ForgeSight, where the historical incident corpus grows continuously and SOPs are updated periodically |

**Selected: HNSW.** ForgeSight's corpus is small-to-medium and grows incrementally (new incidents daily); HNSW avoids the retraining overhead IVFFlat would require every time list boundaries drift, and gives better recall without needing corpus-size-dependent tuning.

### 4.5 Distance Metric: Cosine vs. L2

**Selected: Cosine similarity.** Text embeddings from transformer-based models like bge-large are typically compared by direction rather than magnitude; cosine similarity is the standard and recommended metric for this model family and directly matches the retrieval-score semantics used in the `RetrievedPassage` schema (0.0–1.0 range).

### 4.6 Conceptual Module Responsibilities

`src/forgesight/rag/embeddings/` — owns invoking the embedding model on chunk text and incident summaries, and stamping `embedding_model` metadata. Has no knowledge of chunking logic or retrieval scoring.

### 4.7 Embedding Versioning Strategy

If the embedding model changes (e.g. upgrading to a newer bge release):

1. All existing chunks and incident embeddings are flagged for re-embedding — embeddings are not mixed across model versions in a single similarity search.
2. Re-embedding runs as a batch job against `status = active` chunks and all incident summaries.
3. `embedding_model` field is updated per row on re-embedding.
4. Old embeddings are retained only if needed for audit; production retrieval always filters by the current `embedding_model` value to avoid comparing vectors from incompatible model spaces.

---

## 5. Retrieval Strategy & Reranking Pipeline Design

### 5.1 Retrieval Pipeline Stages

1. **Query Construction** — built from investigation context, not raw free text alone (Section 5.2).
2. **Dense Retrieval** — cosine similarity search over `document_chunks.embedding` via pgvector HNSW index, top-k candidates (k defined in 5.4).
3. **Sparse Retrieval (optional)** — BM25 keyword search to catch exact-term matches (machine IDs, part numbers) that dense embeddings can under-weight.
4. **Hybrid Fusion (optional)** — Reciprocal Rank Fusion (RRF) combines dense and sparse result lists into one ranked candidate set.
5. **Reranking** — cross-encoder rescoring of the fused candidate set for final precision (Section 5.3).
6. **Result Filtering** — removes chunks below a minimum relevance threshold, `status = retired` chunks, and any document category the requesting persona is not authorized to read.
7. **Context Assembly** — formats final passages with full provenance for either LLM reasoning context or direct UI display.

### 5.2 Query Construction Strategy

Queries are template-assembled from investigation context fields rather than passed as raw QE text, so that machine IDs and component identifiers are always present:


If the QE supplies `free_text_query`, it is appended to the templated query rather than replacing it, so structured context is never lost.

### 5.3 Reranking Decision

| Option | Description | Tradeoff |
|---|---|---|
| A — No reranking | Pure vector similarity ranking | Simpler, faster, but dense retrieval alone can rank a loosely-related passage above a precisely relevant one when vocabulary overlap is low |
| B — Cross-encoder reranker (e.g. `ms-marco-MiniLM-L-6-v2`) | Rescore top dense/hybrid candidates with a query-passage cross-encoder | Meaningfully better precision on short technical passages, modest extra compute on a small candidate set |

**Selected: Option B — cross-encoder reranking.** Because retrieved passages become evidence a QE relies on for root-cause sign-off, precision at the top of the list matters more than raw retrieval speed. Reranking is applied only to the top ~20 fused candidates, keeping compute cost bounded.

### 5.4 Top-k Configuration

- Dense/sparse retrieval candidate pool: top 20 (pre-rerank)
- Post-rerank passages surfaced to the QE: top 5
- Historical incident retrieval: top 5 similar incidents shown, ranked by similarity score

### 5.5 Conceptual Module Responsibilities

- `src/forgesight/rag/retrieval/` — owns query construction, dense/sparse retrieval execution, and RRF fusion.
- `src/forgesight/rag/reranking/` — owns cross-encoder scoring and final top-k selection; consumes retrieval's candidate list, produces the final ranked `RetrievedPassage` list.

### 5.6 Retrieval Interface Contract

**Input:** query string (templated) + investigation context filter (document category, machine ID, active-status-only flag).

**Output:** ordered list of `RetrievedPassage` objects (full schema in Section 6), each with `retrieval_score` and, when reranking is applied, `rerank_score`.

---

## 6. RAG Output Schema & Integration Contract

### 6.1 RetrievedPassage Schema

| Field | Type | Purpose / Trust-Chain Role |
|---|---|---|
| `passage_id` | UUID | Unique identifier for this specific retrieval result, referenced in audit events |
| `incident_id` | UUID | Ties the retrieval back to the investigation it supported |
| `document_id` | VARCHAR | Identifies the source document for provenance |
| `document_title` | string | Human-readable source shown to the QE |
| `document_version` | string | Confirms the QE is viewing the version in effect at retrieval time |
| `document_date` | date | Supports currency judgment ("is this SOP still current?") |
| `section_title` | string | Orients the QE within the document |
| `section_reference` | string | Exact locator (e.g. "Section 4.2, Page 7") for manual verification |
| `chunk_text` | string | The actual evidence text shown in the workspace |
| `retrieval_score` | float (0.0–1.0) | Dense/hybrid similarity score, shown to convey retrieval confidence |
| `rerank_score` | float, nullable | Cross-encoder score when reranking was applied; supersedes `retrieval_score` for display ranking |
| `retrieval_query` | string | The exact query used, so the QE can judge whether the retrieval context was appropriate |
| `retrieval_timestamp` | UTC datetime | When retrieval occurred, for audit |
| `embedding_model` | string | Which model produced the vectors involved, for reproducibility |
| `retrieved_by` | enum (`rag_pipeline`, `agent`, `direct_search`) | Distinguishes automatic workflow retrieval from an agent-triggered or QE-initiated manual search |

Every field above exists to support the Phase 1 trust/explainability requirement that a QE must be able to trace any AI-surfaced evidence back to an authoritative, versioned source — never an opaque or unverifiable claim.

### 6.2 Integration Contract

| Layer | Role |
|---|---|
| **FastAPI layer** | Exposes a retrieval endpoint invoked at Stage 7 (SOP retrieval) and Stage 9 (historical incident retrieval); accepts investigation context, returns ranked `RetrievedPassage` list |
| **Investigation Workflow** | At Stage 7, retrieved passages are attached to the incident record as evidence items; at Stage 9, historical incidents feed into hypothesis ranking as precedent evidence |
| **Database** | `document_chunks` and `incident_embeddings` are persisted; individual `RetrievedPassage` results are computed at query time and NOT persisted as a separate table — only the fact that a retrieval occurred, and which passages were surfaced, is recorded in `AuditEvent` |
| **Investigation Workspace UI** | Displays passage text, document title/version, section reference, and score; does not display raw embedding vectors or hidden reasoning |
| **Root-Cause Hypothesis Generation** | Retrieved SOP passages and similar historical incidents are supplied as grounding context; the hypothesis ranking step must cite which passages/incidents supported each hypothesis (see `evidence_provenance_references` in Phase 2 trust schema) |

### 6.3 Historical Incident Retrieval Output Schema

| Field | Type | Description |
|---|---|---|
| `incident_id` | UUID | Retrieved historical incident |
| `title` | string | Short incident description |
| `defect_type` | string | e.g. "component misalignment" |
| `root_cause_confirmed` | string | Human-validated root cause from that closed incident |
| `corrective_action_taken` | string | Action taken previously |
| `similarity_score` | float (0.0–1.0) | Semantic similarity to the current incident |
| `retrieval_timestamp` | UTC datetime | When this comparison was retrieved |

---

## 7. RAG Evaluation Strategy

### 7.1 Three Evaluation Levels

**1. Retrieval Evaluation (component-level)**
- Metrics: Precision@k, Recall@k, NDCG@k, MRR
- Requires a labeled set of (query, relevant document/section) pairs, built by hand from the five synthetic SOPs — for each SOP section, a QE-style question is authored whose known correct answer is that section.

**2. End-to-End RAG Evaluation**
- Metrics: Answer faithfulness (is the generated answer grounded only in retrieved passages?) and Answer relevance (does it address the investigation question?)
- Tool: RAGAS framework, described conceptually only — used to compute faithfulness/relevance scores against the golden dataset; no implementation in this phase.

**3. Human Evaluation**
- Captured via thumbs-up/down feedback on each retrieved passage in the Investigation Workspace UI.
- Feedback maps to a `human_reviewed` field on the corresponding audit/evidence record, feeding future retrieval tuning.

### 7.2 Evaluation Dataset Strategy

- A synthetic **golden dataset** of 20 investigation questions is authored, each mapped to the SOP document(s)/section(s) that should be retrieved.
- Format:
{
"query": "What is the placement tolerance for a 10µF capacitor under IPC-A-610 Class 3?",
"expected_documents": ["SOP-QUAL-042"],
"expected_sections": ["Section 4.2 - Acceptance Criteria"]
}

- Stored at `data/evaluation/rag_golden_dataset.json`.

### 7.3 Evaluation Script Strategy (Conceptual)

`scripts/evaluate_rag.py` — conceptually: loads the golden dataset, runs each query through the retrieval pipeline, computes Precision@k/NDCG@k against `expected_documents`/`expected_sections`, and writes a results CSV. No implementation in this phase.

### 7.4 Hallucination Risk & Mitigation (Mandatory)

- Every claim surfaced to a QE as AI-generated reasoning must cite a `RetrievedPassage`.
- If no retrieved passage clears the minimum relevance threshold, the system must respond "No relevant document found" — it must never fabricate a citation or section reference.
- This is a hard, non-negotiable rule consistent with the Phase 1 trust and explainability requirements and the Section 1.3 "what must not be retrieved" boundary.

### 7.5 Downstream Phase Dependency

Phase 4 deliverables — chunked/embedded SOPs, historical incident embeddings, and the `RetrievedPassage` contract — become the structured evidence inputs that:
- **Phase 5 (MCP)** tools reference when a QE or agent requests document evidence through a standardized tool call, and
- **Phase 6 (Agent Architecture)** agents reason over when generating root-cause hypotheses and corrective action recommendations, always subject to the citation-or-abstain rule above.