# Manufacturing Incident Investigation Workflow Specification

## 1. End-to-End Investigation Lifecycle

The following diagram represents the formalized incident investigation workflow designed for SMT/PCB quality engineering.

```
                  [ 1. Defect Detection & Threshold Trigger ]
                                      │
                                      ▼
                        [ 2. Incident Creation & Context ]
                                      │
                                      ▼
                      [ 3. Visual Evidence Extraction ]
                                      │
                                      ▼
                  [ 4. Production & Telemetry Investigation ]
                                      │
                                      ▼
                    [ 5. Machine & Maintenance Check ]
                                      │
                                      ▼
                  [ 6. Component Lot & Supplier Correlation ]
                                      │
                                      ▼
                  [ 7. Technical SOP & Manual Retrieval ]
                                      │
                                      ▼
                  [ 8. Evidence Correlation & Synthesis ]
                                      │
                                      ▼
                  [ 9. Root-Cause Hypothesis Ranking ]
                                      │
                                      ▼
                  [ 10. Corrective Action Recommendation ]
                                      │
                                      ▼
                  [ 11. Human Engineer Review & Sign-Off ]
                                      │
                                      ▼
                  [ 12. Report Generation & Audit Trail ]
```

---

## 2. Stage Breakdown & Architectural Rationale

### Stage 1: Defect Detection & Threshold Trigger
- **Goal**: Detect physical anomaly on PCB and determine if it exceeds statistical process thresholds.
- **Why It Exists**: Prevents isolated minor anomalies from creating unnecessary alarms, while ensuring systemic batch defects trigger an investigation immediately.
- **Primary Inputs**: SPI/AOI optical scan data, defect confidence score, board serial number.
- **Primary Outputs**: Automated trigger signal containing board ID, component ID (e.g., C17), and defect classification (e.g., component shift).

### Stage 2: Incident Creation & Context Setup
- **Goal**: Instantiate a formal Quality Incident record with initial metadata.
- **Why It Exists**: Creates a single source of truth (e.g., `INCIDENT-2026-00421`) for tracking the lifecycle, evidence, and investigation state.
- **Primary Inputs**: Trigger payload, Operator notes, MES line context (Product ECU-2026, Batch B-24017, Line SMT-LINE-03).
- **Primary Outputs**: Initialized Incident entity with assigned metadata and timestamp.

### Stage 3: Visual Evidence Extraction
- **Goal**: Analyze inspection images using Computer Vision to extract structured visual evidence.
- **Why It Exists**: Raw images cannot be directly parsed by relational queries or traditional rule engines. Structured visual evidence (bounding box, defect type, confidence, severity) is required for evidence-based reasoning.
- **Primary Inputs**: AOI high-resolution optical image, board reference layout (CAD coordinates).
- **Primary Outputs**: Bounding box, defect class (`component_misalignment`), severity index, visual confidence score.

### Stage 4: Production & Telemetry Investigation
- **Goal**: Analyze manufacturing process telemetry around the time of board assembly.
- **Why It Exists**: Visual defects are often caused by upstream process shifts (e.g., line speed, squeegee pressure, reflow zone temperature drift).
- **Primary Inputs**: Line ID, batch ID, timestamps, sensor telemetry logs.
- **Primary Outputs**: Process anomaly flags (e.g., "Reflow zone 4 temperature dropped by 3.2°C during batch execution").

### Stage 5: Machine & Maintenance Check
- **Goal**: Inspect state of equipment used during assembly (pick & place machines, nozzles, feeders).
- **Why It Exists**: Mechanical wear (e.g., clogged placer nozzle tip, degraded vacuum seal) directly causes component placement shifts.
- **Primary Inputs**: Machine ID (`PLACER-07`), nozzle ID (`Nozzle-03`), feeder ID, maintenance history.
- **Primary Outputs**: Equipment health status, days since last nozzle cleaning/calibration.

### Stage 6: Component Lot & Supplier Correlation
- **Goal**: Trace component batch origin to determine if defect correlates with a specific supplier lot.
- **Why It Exists**: Component lead oxidation, pin pitch variation, or poor solderability often stem from bad component lots across suppliers.
- **Primary Inputs**: Component part number (e.g., C17 10uF Capacitor), Component Lot Number (`LOT-9921`), Supplier ID.
- **Primary Outputs**: Supplier quality correlation index, historical defect rate for supplier lot `LOT-9921`.

### Stage 7: Technical SOP & Manual Retrieval
- **Goal**: Retrieve governing standards, IPC acceptability criteria, and machine troubleshooting manuals.
- **Why It Exists**: Grounded root-cause analysis must comply with official quality guidelines (IPC-A-610 Class 3) and vendor manuals.
- **Primary Inputs**: Defect type, machine model, quality procedure query.
- **Primary Outputs**: Retrieved document passages, standard defect acceptance criteria, vendor maintenance procedures.

### Stage 8: Evidence Correlation & Synthesis
- **Goal**: Fuse multi-source evidence (visual + telemetry + maintenance + supplier + documentation).
- **Why It Exists**: Isolated evidence leads to false conclusions; correlating evidence across modalities establishes true causality.
- **Primary Inputs**: Outputs from Stages 3, 4, 5, 6, and 7.
- **Primary Outputs**: Synthesized Evidence Graph connecting observed visual defect to line events.

### Stage 9: Root-Cause Hypothesis Ranking
- **Goal**: Formulate and rank probabilistic root-cause hypotheses with supporting/contradicting evidence.
- **Why It Exists**: Engineers need prioritized hypotheses with clear confidence levels rather than a single black-box guess.
- **Primary Inputs**: Synthesized Evidence Graph.
- **Primary Outputs**: Ranked hypotheses list (e.g., "Hypothesis 1: Worn nozzle tip on Placer 7 [Confidence: 85%]; Hypothesis 2: Reflow thermal profile drift [Confidence: 15%]").

### Stage 10: Corrective Action Recommendation
- **Goal**: Propose actionable corrective measures (e.g., replace placer nozzle, recalibrate feeder, place supplier lot on hold).
- **Why It Exists**: Converts investigation findings into concrete steps to restore yield and prevent future recurrence.
- **Primary Inputs**: Ranked Root-Cause Hypotheses.
- **Primary Outputs**: Proposed Action Plan categorized into READ actions and WRITE/HOLD actions.

### Stage 11: Human Engineer Review & Sign-Off
- **Goal**: Present findings and recommendations to a qualified Quality Engineer for review, modification, and authorization.
- **Why It Exists**: Ensures safety and prevents unvetted AI actions from disrupting production lines.
- **Primary Inputs**: Complete investigation workspace, evidence trail, proposed actions.
- **Primary Outputs**: Engineer approval, modification, or rejection decision.

### Stage 12: Report Generation & Audit Trail
- **Goal**: Generate a formal PDF/Markdown incident report and record an immutable audit trail.
- **Why It Exists**: Fulfills ISO 9001, IATF 16949, and customer quality compliance standards.
- **Primary Inputs**: Approved investigation summary, engineer sign-off timestamp, complete evidence provenance.
- **Primary Outputs**: Finalized Incident Report document and database audit log.
