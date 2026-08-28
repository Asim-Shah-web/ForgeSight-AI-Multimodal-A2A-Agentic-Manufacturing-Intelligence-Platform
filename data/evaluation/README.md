# RAG Evaluation Data — ForgeSight AI

This directory holds the evaluation assets for the RAG subsystem, per `docs/architecture/rag-architecture.md` Section 7.

## Contents

data/evaluation/
├── README.md
└── rag_golden_dataset.json (to be created when evaluation is implemented)

## Golden Dataset Strategy

`rag_golden_dataset.json` will contain 20 synthetic investigation questions, each mapped to the SOP document(s) and section(s) that should be retrieved as the correct answer. The dataset is derived directly from the five synthetic SOPs in `data/documents/synthetic/`.

### Record Format

```json
{
  "query": "What is the placement tolerance for a 10µF capacitor under IPC-A-610 Class 3?",
  "expected_documents": ["SOP-QUAL-042"],
  "expected_sections": ["Section 4.2 - Acceptance Criteria"]
}
```

### Coverage Targets

| SOP | Approx. Question Count |
| --- | --- |
| SOP-QUAL-042 | 5 |
| SOP-MAINT-017 | 4 |
| SOP-PROC-031 | 4 |
| SOP-SUPP-008 | 4 |
| SOP-QUAL-055 | 3 |

## Evaluation Metrics

Computed against this dataset once retrieval is implemented:

- Precision@k, Recall@k, NDCG@k, MRR (retrieval-level)
- Faithfulness and relevance via RAGAS (end-to-end, conceptual only at this phase)

## Status

This is a documentation-only phase. No `rag_golden_dataset.json` file, evaluation script, or retrieval implementation exists yet. Creation of the actual golden dataset file and `scripts/evaluate_rag.py` is deferred to the implementation phase.
