
# ForgeSight AI — Data Flow Architecture

## Document Status

- **Project:** ForgeSight AI
- **Phase:** Phase 2 — Domain Model & Data Architecture
- **Purpose:** Define how manufacturing evidence moves from source systems into the ForgeSight investigation workspace.
- **Architecture Type:** Conceptual
- **Implementation Status:** Documentation only
- **Primary Consumer:** Quality Engineer
- **Important Boundary:** This document does not define FastAPI routes, MCP implementations, agent implementations, A2A boundaries, or production infrastructure configuration.

---

# 1. Data Flow Architecture Overview

ForgeSight receives evidence from multiple manufacturing and knowledge sources.

The central architectural goal is to preserve the relationship between:

```text
Source Evidence
      ↓
Source Identity
      ↓
Transformation / Analysis
      ↓
ForgeSight Record
      ↓
Evidence Correlation
      ↓
Investigation Workspace
      ↓
Human Review
      ↓
Audit Trail
```


# Investigation Workflow Mapping

| Investigation Stage                            | Synthetic Data Used                         |
| :--------------------------------------------- | :------------------------------------------ |
| Stage 1 — Defect Detection & Threshold Trigger | `synthetic_defects.csv`, inspection images  |
| Stage 2 — Incident Creation & Context Setup    | `synthetic_incidents.csv`, boards, batches  |
| Stage 3 — Visual Evidence Extraction           | inspection images, CV-linked defect records |
| Stage 4 — Production & Telemetry Investigation | `synthetic_production_telemetry.csv`        |
| Stage 5 — Machine & Maintenance Check          | machines, nozzles, maintenance              |
| Stage 6 — Component Lot & Supplier Correlation | component lots, suppliers                   |
| Stage 7 — Technical SOP & Manual Retrieval     | technical document corpus                   |
| Stage 8 — Evidence Correlation & Synthesis     | all connected datasets                      |
| Stage 9 — Root-Cause Hypothesis Ranking        | evidence from all sources                   |
| Stage 10 — Corrective Action Recommendation    | machine/process/supplier evidence           |
| Stage 11 — Human Engineer Review & Sign-Off    | user and approval context                   |
| Stage 12 — Report Generation & Audit Trail     | incident, report, audit data                |

# 1. Inspection Image Flow

AOI Hardware
     │
     ▼
Inspection Image
     │
     ▼
Evidence Upload / Registration
     │
     ▼
Image Validation
     │
     ▼
CV Pipeline
     │
     ▼
CvFinding
     │
     ├── defect_type
     ├── confidence
     ├── bounding_box
     ├── model_name
     ├── model_version
     └── inference_timestamp
     │
     ▼
Incident Evidence
     │
     ▼
Quality Engineer Workspace





# Investigation Stage Data Flow

| Stage                                | Input Source                     | Output / Result                              |
| :----------------------------------- | :------------------------------- | :------------------------------------------- |
| 1. Threshold Trigger               | Defect thresholds                | Threshold-exceeded defects ready for review  |
| 2. Incident Creation               | Manual / Automated               | Incident record with initial evidence        |
| 3. Visual Evidence Extraction        | Inspection images, CV findings   | Extracted defect regions, component data     |
| 4. Production Telemetry Analysis     | Telemetry API                    | Telemetry metrics window                     |
| 5. Machine Health                  | Machine API, Maintenance records | Machine state, maintenance history           |
| 6. Component Lot & Supplier          | Inventory API                    | Lot traceability and supplier quality history |
| 7. Technical SOP & Manual Retrieval    | Knowledgebase API                | Related technical documents                  |
| 8. Evidence Correlation              | All evidence                     | Correlated evidence set                      |
| 9. Hypothesis Ranking                | Evidence                       | Ranked root-cause hypotheses                 |
| 10. Corrective Action Recommendation | Recommendations engine           | Action list                                  |
| 11. Human Review                   | Quality Engineer                 | Approved actions                             |
| 12. Report & Audit                   | All records                      | Final report and audit trail                 |








# Source-to-Workspace Flow Matrix

| Flow                 | Source               | Transformation             | Permanent Storage             | Workspace Output            | Key Provenance                                 |
| :------------------- | :------------------- | :------------------------- | :---------------------------- | :-------------------------- | :--------------------------------------------- |
| Inspection Image     | AOI                  | CV analysis                | Inspection/CV records         | Image + findings            | Image ID, station, timestamp, model version    |
| Telemetry            | MES / sensors        | Normalize/analyze          | Production telemetry          | Timeline / anomaly evidence | Machine, parameter, timestamp, source          |
| Maintenance          | CMMS / ERP           | Normalize                  | Maintenance records           | Maintenance history         | Machine, nozzle, action, technician, timestamp |
| Component/Lot        | ERP                  | Traceability normalization | Lots/suppliers                | Lot/supplier context        | Part, lot, supplier, source                    |
| Documents            | Controlled documents | Chunk/embed/retrieve       | Documents + pgvector          | Retrieved passages          | Title, version, section, score                 |
| Historical Incidents | Incident DB          | Embed/search               | Historical records + pgvector | Similar cases               | Incident reference, similarity, source         |
