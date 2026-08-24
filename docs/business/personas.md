# Stakeholder Personas & Authorization Specification

## 1. Overview & Persona Discovery Rationale

In high-reliability SMT/PCB electronics manufacturing, software must enforce strict operational and authorization boundaries. ForgeSight serves distinct human stakeholders across the factory floor, engineering office, and management suite.

---

## 2. High-Level Persona Comparison Matrix

| Persona | Primary Goal | Main Pain Point | ForgeSight Usage | Required Information | Allowed Actions | Approval Authority | Risk Level |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Production Operator** | Keep line running safely & report defect anomalies | Manual paper logs, complex UI software | Rapid incident logging & image capture | Line status, active batch, submit form | Create incident, attach image | None | **Low** |
| **Quality Engineer (Primary)** | Perform root-cause analysis & prevent defect escapes | Hours spent querying 5 isolated databases | Multi-system investigation workspace | Full evidence graph, CV findings, SOPs | Modify hypothesis, request data, sign off | Final Incident Approval | **Medium–High** |
| **Manufacturing Engineer** | Optimize line throughput, yield, & SMT process parameters | Isolating thermal/mechanical process drift | Process deviation & line telemetry analysis | Telemetry logs, placer parameters, yield trend | Recommend process parameter adjustments | Process Change Recs | **Medium** |
| **Maintenance Engineer** | Maintain SMT machine health & eliminate mechanical faults | Sudden machine downtime & nozzle/feeder wear | Machine health & calibration diagnostics | Maintenance history, nozzle wear, feeder logs | Recommend work orders, log calibration | Work Order Recs | **Medium** |
| **Quality Manager** | Maintain plant yield, ISO compliance, & prevent customer RMAs | Lack of visibility into recurring quality trends | Executive summary dashboard & trend metrics | Plant KPIs, incident resolution time, audit logs | Escalate incident, request deep audit | High-Risk Hold Approvals | **High** |
| **Supplier Quality Engineer** | Track component lot quality & hold vendors accountable | Distinguishing internal process failure from vendor lot defect | Supplier lot correlation & defect statistics | Supplier lot IDs, component datasheets, lot defect history | Draft Supplier Action Request (SCAR) | SCAR Issuance | **High** |
| **System Administrator** | Ensure platform security, uptime, & model/MCP integration | Managing permissions & API integration health | Admin console, RBAC, API/MCP health monitor | Audit logs, system metrics, API keys, MCP status | Manage users, configure models, toggle MCP tools | System Config & Access | **Critical** |

---

## 3. Deep Analysis — BATCH 1 Personas

### 3.1 Production Operator (Step 2.2)

#### Role & Function
The Production Operator works directly on the SMT assembly line floor. They monitor stencil printers, pick-and-place feeders, reflow ovens, and AOI inspection stations.

#### Goals & Responsibilities
- Keep the SMT line running safely and efficiently.
- Perform visual confirmation when AOI/SPI flags a potential defect.
- Log defect incidents quickly with clear shop-floor context.

#### Pain Points & Current Systems
- Currently forced to enter details in complex MES terminals or physical paper logs.
- Disconnected systems mean operators rarely get feedback on whether logged issues were investigated or resolved.

#### ForgeSight Interaction & Permissions
- **Allowed Actions**: `CREATE_INCIDENT`, `ATTACH_EVIDENCE`, `VIEW_INCIDENT_STATUS`.
- **Forbidden Actions**: `MODIFY_MACHINE_PARAMS`, `APPROVE_QUALITY_HOLD`, `MODIFY_RECORDS`, `APPROVE_ROOT_CAUSE`, `APPROVE_SUPPLIER_ACTION`.
- **Why Forbidden**: Operators lack total system visibility across maintenance, supplier lots, and thermal physics. Allowing unverified parameter tweaks or holds from shop-floor terminals risks line stoppage and process instability.

#### User Journey — Production Operator
```text
[ AOI Flag / Visual Defect Noticed ]
                 │
                 ▼
[ Operator Reviews Physical PCB Board ]
                 │
                 ▼
[ Opens ForgeSight Mobile/Line Capture UI ]
                 │
                 ▼
[ Submits Image + Batch Context + Operator Notes ]
                 │
                 ▼
[ ForgeSight Creates Incident Context (e.g. INCIDENT-2026-00421) ]
                 │
                 ▼
[ Quality Engineer Automatically Notified ──► Investigation Begins ]
                 │
                 ▼
[ Operator Receives Confirmation & Status Badge ("Under Investigation") ]
```

---

### 3.2 Quality Engineer — Primary Persona (Step 2.3)

#### Role & Function
The Quality Engineer (QE) is the primary human-in-the-loop authority in ForgeSight. They own quality compliance (ISO 9001, IPC-A-610 Class 3), defect containment, root-cause investigation, and scrap reduction.

#### Goals & Responsibilities
- Conduct thorough, evidence-grounded root-cause investigations.
- Prevent escaped defects from reaching downstream assembly or customers.
- Validate AI-generated hypotheses and approve formal incident reports.

#### Pain Points
- QEs currently spend 70%+ of their time running manual queries across 5 separate systems (AOI image database, MES batch records, placer machine logs, maintenance databases, and PDF SOPs).

#### Decision Authority & Permission Matrix
- **Permissions**: `READ`, `ANALYZE`, `CREATE`, `MODIFY_HYPOTHESIS`, `REVIEW`, `APPROVE_INVESTIGATION`, `REJECT_HYPOTHESIS`, `SIGN_OFF`.
- **Why QE is the Human-in-the-Loop Authority**: Quality compliance requires single-point legal and technical accountability. AI can summarize and correlate evidence, but only a human QE has the contextual judgement to sign off on an ISO 9001 audit trail.

#### Investigation Workflow
```text
[ Incident Created ] ──► [ Review Visual & CV Findings ]
                                  │
                                  ▼
                     [ Inspect Telemetry & Machine Logs ]
                                  │
                                  ▼
                     [ Search Technical SOPs & Manuals (RAG) ]
                                  │
                                  ▼
                     [ Evaluate Ranked Root-Cause Hypotheses ]
                                  │
                                  ▼
                     [ Modify / Confirm Corrective Actions ]
                                  │
                                  ▼
                     [ Human QE Approval & Sign-Off ] ──► [ Final Report Generated ]
```

#### Trust & Explainability Requirements
For a QE to trust an AI recommendation, ForgeSight must provide:
1. **Visual Grounding**: Defect bounding box, class, confidence score, and raw image.
2. **Telemetry Provenance**: Exact timestamped machine sensor readings and delta deviations.
3. **Document Citation**: Document title, version, exact section, and passage text (no un-cited assertions).
4. **Hypothesis Transparency**: Pro and contra evidence lists for each ranked hypothesis (no hidden chain-of-thought).

---

### 3.3 Manufacturing Engineer (Step 2.4)

#### Role & Function
The Manufacturing Engineer (ME) focuses on SMT process engineering, machine physics, stencil printing squeegee speeds/pressures, placer mounting force, and reflow furnace thermal profiling.

#### Goals & Responsibilities
- Maximize SMT line throughput and first-pass yield (FPY).
- Eliminate process drift and optimize machine operational parameters.
- Implement physical process improvements.

#### Quality Engineer (QE) vs. Manufacturing Engineer (ME) Comparison

| Dimension | Quality Engineer (QE) | Manufacturing Engineer (ME) |
| :--- | :--- | :--- |
| **Primary Focus** | Defect containment, IPC-A-610 standards, ISO compliance, root-cause sign-off | SMT machine physics, thermal profiles, stencil printing, line speed & yield optimization |
| **Key Question** | *"Is this product defective, what caused it, and is it safe to release?"* | *"What machine/process parameter drifted, and how do we adjust it to optimize yield?"* |
| **Primary Systems** | AOI/SPI inspection DB, QMS, SOPs, Supplier Lot History | Placer telemetry, Reflow zone temperature logs, Stencil printer settings |
| **Decision Authority** | Final Incident Investigation Approval, Batch Quality Hold Recommendation | Process Parameter Adjustment Approval, Machine Setup Optimization |
| **Overlapping Area** | Both review defect statistics, historical incident trends, and root-cause evidence | Both review defect statistics, historical incident trends, and root-cause evidence |

#### Why This Distinction Matters for System Architecture
- **Permissions**: MEs can recommend process parameter changes, whereas QEs sign off on defect root causes.
- **Future Software Capabilities**: MEs require deep telemetry correlation tools, while QEs require visual evidence and compliance document retrieval tools.
