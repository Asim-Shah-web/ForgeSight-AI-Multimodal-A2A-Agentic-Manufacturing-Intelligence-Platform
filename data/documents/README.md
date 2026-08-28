# Document Corpus — ForgeSight AI

This directory holds the source documents ingested into ForgeSight's RAG subsystem.

## Structure

data/documents/
├── README.md
└── synthetic/
├── SOP-QUAL-042.md
├── SOP-MAINT-017.md
├── SOP-PROC-031.md
├── SOP-SUPP-008.md
└── SOP-QUAL-055.md

## Document Categories

| Category | Description |
| --- | --- |
| `sop` | Manufacturing SOPs — quality inspection, defect containment, IPC-A-610-referenced criteria |
| `machine_manual` | Placer, reflow oven, stencil printer operational/maintenance procedures |
| `engineering_doc` | Process capability studies, FMEA templates, yield guidelines |
| `historical_report` | Closed-incident summaries generated at Stage 12 sign-off (not stored as files here — generated records in the database) |

## Required Metadata (per document, before ingestion)

| Field | Description |
| --- | --- |
| `document_id` | Stable ID, e.g. `SOP-QUAL-042` |
| `title` | Document title |
| `category` | One of the categories above |
| `version` | Semantic version |
| `date` | Effective date |
| `author` | Authoring role |
| `approved_by` | Approving persona |
| `file_path` | Storage location |
| `status` | `active` or `retired` |
| `language` | ISO language code |

## Ingestion Instructions (Conceptual)

1. Confirm the document carries all required metadata above and has been approved per the governance model in `docs/architecture/rag-architecture.md` Section 2.3.
2. Submit the document to the ingestion pipeline (`src/forgesight/rag/ingestion/`), which loads, extracts metadata, and hands off to chunking.
3. Verify post-ingestion: chunk count, embedding dimension (`vector(1024)`), and metadata completeness, per the verification stage defined in `rag-architecture.md` Section 3.1.
4. On document update, bump `version`, re-ingest, and confirm prior-version chunks are marked `retired` per Section 3.4.

No ingestion code exists yet — this is a documentation-only phase.
