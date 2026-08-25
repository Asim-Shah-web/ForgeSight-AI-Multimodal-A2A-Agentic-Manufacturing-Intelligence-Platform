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

---

## 4. Deep Analysis — BATCH 2 Personas

### 4.1 Maintenance Engineer (Step 2.5)

#### Role & Function
The Maintenance Engineer manages electromechanical machine health, SMT placer nozzle wear, feeder tensioning, reflow oven conveyor maintenance, and preventive/corrective work orders.

#### Operational Boundaries
- **ForgeSight Can READ**: Machine maintenance history, nozzle inspection records, feeder calibration logs, machine fault logs.
- **ForgeSight Can RECOMMEND**: Generating a preventative maintenance work order (e.g. *"Recommend replacing Placer Nozzle #3 on Machine PLACER-07 due to recurring vacuum pick drops"*).
- **Requires Human Approval**: Authorizing a work order, taking a production machine offline.
- **NEVER Execute Automatically**: Physical machine shutdown, altering physical calibration offsets without engineer sign-off.

#### Conceptual MCP Integration
Maintenance systems (SAP PM, Maximo) operate as external enterprise resources. ForgeSight will expose maintenance operations via **MCP Tools**:
- `get_machine_maintenance_history(machine_id)`
- `get_nozzle_wear_status(machine_id, nozzle_id)`
- `recommend_work_order(machine_id, maintenance_type, urgency)`

---

### 4.2 Quality Manager (Step 2.6)

#### Role & Function
The Quality Manager oversees plant-wide quality metrics, ISO 9001 / IATF 16949 audit compliance, customer RMA reduction, and high-impact risk management.

#### Quality Engineer (QE) vs. Quality Manager (QM) Comparison

| Dimension | Quality Engineer (QE) | Quality Manager (QM) |
| :--- | :--- | :--- |
| **Scope** | Single-incident deep dive, root-cause validation, technical evidence correlation | Plant-wide quality trends, multi-line risk oversight, executive escalation |
| **Primary Metric** | Mean Time To Investigate (MTTI), Root Cause Accuracy | Plant First-Pass Yield (FPY), Customer RMA rate, Scrap Cost Reduction |
| **High-Risk Authority** | Recommends quality holds, signs off on incident investigations | Authorizes high-impact global inventory holds ($100k+), halts production lines |

#### Decision Authority & Permissions
- **Permissions**: `READ`, `ANALYZE`, `APPROVE_HIGH_RISK_HOLD`, `ESCALATE_INCIDENT`, `REQUEST_AUDIT`.

---

### 4.3 Supplier Quality Engineer (Step 2.7)

#### Role & Function
The Supplier Quality Engineer (SQE) tracks component lot quality across external vendors, manages incoming inspection standards, and handles Supplier Corrective Action Requests (SCARs).

#### Correlation vs. Evidence vs. Root Cause

```text
[ Statistical Correlation ] ──► [ Multimodal Evidence ] ──► [ Root-Cause Hypothesis ] ──► [ Confirmed Root Cause ]
(Lot B-9921 present during      (IPC solderability test      (Component lead oxidation     (QE/SQE physical audit
 high defect rate)               failure under microscopy)    hypothesis ranked #1)         sign-off & SCAR issuance)
```

- **Correlation**: Statistical co-occurrence (e.g., component lot present during 80% of defects). *Never sufficient on its own to penalize a vendor*.
- **Evidence**: Physical or empirical verification (e.g., solderability test under IPC-J-STD-002).
- **Root-Cause Hypothesis**: Ranked multi-factor hypothesis combining correlation, process telemetry, and lot history.
- **Confirmed Root Cause**: Human SQE validated finding backed by evidence.
- **Required Evidence for SCAR Issuance**: Proof excluding internal SMT machine/thermal variables, IPC solderability test report, and historical defect delta.

---

### 4.4 System Administrator (Step 2.8)

#### Role & Function
The System Administrator maintains platform uptime, identity & access management (RBAC), API keys, MCP server transport bridges, model endpoints, audit log immutability, and system monitoring.

#### Crucial Boundary: Technical Administration ≠ Business Approval Authority

```text
+------------------------------------------+       +------------------------------------------+
|       SYSTEM ADMINISTRATOR (TECHNICAL)   |       |    QUALITY ENGINEER / MANAGER (BUSINESS) |
+------------------------------------------+       +------------------------------------------+
| - Manage API keys & JWT secrets          |       | - Approve root-cause hypotheses          |
| - Configure MCP server connection ports  |       | - Sign off on ISO 9001 incident reports  |
| - Assign RBAC roles (QE, Operator, etc.) |       | - Place component lots on quality hold   |
| - Monitor system CPU / RAM / Latency     |       | - Authorize production line restarts     |
+------------------------------------------+       +------------------------------------------+
```

> **Architectural Rule**: Having root technical privileges to configure software or update database connections does **NOT** grant authorization to sign off on quality investigations or alter manufacturing compliance records. Technical administration and domain business authority are strictly separated.

---

## 5. Persona Comparison & Permission Matrices (Step 2.9)

### 5.1 Matrix A — Persona Overview

| Persona | Main Goal | Main Pain | ForgeSight Usage | Required Information | Allowed Actions | Approval Authority |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Production Operator | Keep the SMT line running safely and report anomalies quickly | Fragmented terminals, paper logs, weak feedback loop | Rapid incident creation and evidence capture | AOI result, board ID, batch, machine, image, defect description | Create incident, attach evidence, view status | None |
| Quality Engineer | Investigate defects, establish evidence-grounded root causes, prevent escapes | Manually querying multiple systems and documents | Primary investigation workspace | Inspection, production, machine, maintenance, lot, supplier, documents, historical incidents | Read, analyze, create, modify hypotheses, review, approve/reject, sign off | Final investigation sign-off |
| Manufacturing Engineer | Identify and eliminate SMT process drift | Process information distributed across machine and production systems | Process and telemetry analysis | Printer parameters, placement parameters, reflow profiles, yield trends, process deviations | Read, analyze, recommend process changes | Process-change approval within assigned authority |
| Maintenance Engineer | Identify and eliminate machine-related causes | Maintenance records and machine health information are disconnected from quality events | Maintenance investigation branch | Machine history, nozzle records, feeder calibration, fault codes, work orders | Read, analyze, recommend maintenance | Maintenance/work-order authorization |
| Quality Manager | Monitor plant-wide quality risk and authorize high-impact quality decisions | Limited cross-line visibility and delayed escalation | Escalation, trend, and high-risk decision views | Incident trends, yield, holds, escalations, customer-impact information | Read, analyze, escalate, approve high-risk holds, request audits | High-risk quality holds and escalations |
| Supplier Quality Engineer | Determine whether supplier-related evidence supports supplier action | Correlation can be mistaken for supplier causation | Component-lot and supplier investigation branch | Lot genealogy, incoming quality, historical defect rates, internal process evidence, verification results | Read, analyze, recommend supplier action | SCAR decision/sign-off |
| System Administrator | Maintain secure and reliable platform operation | Security, configuration, identity, and system-health responsibilities | Administrative and platform-management functions | Users, roles, configuration, service health, audit records | Configure platform, manage identities and technical access | Technical platform administration only; no manufacturing approval |

### 5.2 Permission Interpretation
- **Read**: Accessing information within the persona's authorized scope.
- **Analyze**: Performing or requesting analytical processing without automatically changing manufacturing state.
- **Create**: Creating an authorized business record such as an incident.
- **Modify**: Applies only to entities and fields permitted for that persona (does not mean unrestricted overwrite).
- **Recommend**: Producing a proposed action or conclusion that remains subject to the appropriate approval boundary.
- **Approve**: Exercising actual business authority. AI-generated recommendations do not constitute approval.
- **Execute**: Carrying out an operational action with real-world consequences. Tightly restricted.

### 5.3 Matrix B — Permission Matrix

| Persona | READ | ANALYZE | CREATE | MODIFY | RECOMMEND | APPROVE | EXECUTE |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Production Operator | ✅ | 🔸 | ✅ | ❌ | 🔸 | ❌ | ❌ |
| Quality Engineer | ✅ | ✅ | ✅ | 🔸 | ✅ | ✅ | 🔸 |
| Manufacturing Engineer | ✅ | ✅ | ❌ | 🔸 | ✅ | 🔸 | 🔸 |
| Maintenance Engineer | ✅ | ✅ | 🔸 | 🔸 | ✅ | 🔸 | 🔸 |
| Quality Manager | ✅ | ✅ | 🔸 | 🔸 | ✅ | ✅ | 🔸 |
| Supplier Quality Engineer | ✅ | ✅ | 🔸 | 🔸 | ✅ | ✅ | 🔸 |
| System Administrator | ✅ | 🔸 | 🔸 | 🔸 | ❌ | ❌ | 🔸 |

### 5.4 Non-Obvious Permission Explanations
- **Production Operator — ANALYZE: 🔸**: May provide descriptive information about an observed defect and review AI-generated analysis relevant to the incident. Not intended to perform formal root-cause analysis.
- **Quality Engineer — MODIFY: 🔸**: May modify investigation hypotheses, classifications, notes, and recommendations, but cannot overwrite immutable source evidence or audit records.
- **Quality Engineer — EXECUTE: 🔸**: May initiate only actions explicitly within approved business authority. High-impact physical manufacturing actions remain outside autonomous execution.
- **Manufacturing Engineer — MODIFY: 🔸**: Has authority over process-related records and recommendations, but machine/process changes remain subject to organizational authorization controls.
- **Maintenance Engineer — CREATE/MODIFY: 🔸**: May create/update maintenance records, but authorizing work orders or taking equipment offline requires human authorization.
- **Quality Manager — CREATE/MODIFY: 🔸**: May create escalation or quality-management records; existing evidence and immutable audit history must not be rewritten.
- **Supplier Quality Engineer — CREATE/MODIFY/EXECUTE: 🔸**: May prepare supplier-quality actions, but supplier escalation must not become automatic merely because statistical correlation exists.
- **System Administrator — APPROVE: ❌**: Technical administrative privilege must not confer manufacturing authority. Cannot approve a quality investigation or authorize a production hold.
- **System Administrator — EXECUTE: 🔸**: Limited to technical platform operations (no physical manufacturing actions).

---

## 6. Human vs. AI Responsibility Matrix (Step 2.10)

| Activity | Fully AI | Primarily Human | Human + AI | Approval Required |
| :--- | :---: | :---: | :---: | :---: |
| Defect flag detection from AOI hardware | ❌ | 🔸 | ✅ | ❌ |
| Incident creation | ❌ | 🔸 | ✅ | ❌ |
| Image / CV analysis | 🔸 | ❌ | ✅ | ❌ |
| Evidence retrieval | 🔸 | ❌ | ✅ | ❌ |
| Production telemetry analysis | 🔸 | ❌ | ✅ | ❌ |
| Maintenance history analysis | 🔸 | ❌ | ✅ | ❌ |
| Supplier history analysis | 🔸 | ❌ | ✅ | ❌ |
| Document retrieval through RAG | 🔸 | ❌ | ✅ | ❌ |
| Evidence correlation and synthesis | 🔸 | 🔸 | ✅ | ❌ |
| Root-cause hypothesis generation | 🔸 | 🔸 | ✅ | ❌ |
| Root-cause validation and approval | ❌ | ✅ | 🔸 | ✅ |
| Corrective-action recommendation | 🔸 | 🔸 | ✅ | Depends on action risk |
| Quality hold | ❌ | ✅ | 🔸 | ✅ |
| Machine parameter modification | ❌ | ✅ | 🔸 | ✅ |
| Supplier escalation / SCAR initiation | ❌ | ✅ | 🔸 | ✅ |
| Final incident closure | ❌ | ✅ | 🔸 | ✅ |
| Report generation | 🔸 | 🔸 | ✅ | Final sign-off where applicable |

### Classification Rationale & Architectural Implications
- **MCP tool permissions**: Read-only retrieval tools can generally support automated investigation. Write-capable tools require stronger authorization and explicit human approval for high-impact actions.
- **API authorization**: Authorization must be based on both **identity and action**, not merely logged-in state.
- **Agent capability design**: AI capabilities receive only minimum permissions required for business functions (e.g. analysis capabilities cannot modify machine state).
- **Audit logging**: Higher-risk operations require detailed audit evidence and explicit approval records.

---

## 7. Risk-Based Action Model (Step 2.11)

### 7.1 Low Risk
Read-only, analytical, or informational operations that do not alter manufacturing state:
1. Viewing an incident
2. Viewing AOI images
3. Retrieving production telemetry
4. Retrieving maintenance history
5. Retrieving component-lot information
6. Retrieving approved technical documents (RAG)
7. Searching historical incidents
8. Generating a descriptive CV finding
9. Viewing audit history
10. Generating a preliminary incident summary

### 7.2 Medium Risk
Operations that create or modify business records or generate conclusions influencing later decisions:
1. Creating a formal investigation record
2. Adding investigation notes
3. Modifying a root-cause hypothesis
4. Generating a ranked root-cause analysis
5. Generating corrective-action recommendations
6. Creating a maintenance recommendation
7. Creating a supplier-investigation recommendation
8. Editing an AI-generated report

### 7.3 High Risk
Actions directly affecting physical manufacturing, financial exposure, supplier relationships, compliance, or product release:
1. Putting a batch or lot on quality hold
2. Modifying machine parameters
3. Taking a machine offline
4. Authorizing corrective maintenance execution
5. Initiating a formal supplier SCAR
6. Approving a high-value inventory hold
7. Approving final incident disposition
8. Authorizing production-impacting process changes

### 7.4 Architectural Influence
- **MCP Permissions**: Low risk = Read-only; Medium risk = User context required; High risk = Explicit human approval required.
- **FastAPI Authorization**: Enforces persona, role, resource scope, and action risk.
- **Approval Gates**: Placed before actions whose physical/financial consequences cannot safely be reversed by a software record update.
- **Audit Granularity**: High-risk decisions require actor identity, authorization context, affected entity, evidence version, approval, result, and timestamp.

---

## 8. Investigation Workspace Design (Step 2.13)

### 8.1 Section Evaluation & Requirements

| Section | Purpose | Data Source | Producer | Consumer | Trust/Provenance Requirement | Decision |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Incident Summary** | Establish investigation identity and state | Incident DB, MES | Human + AI | All | Incident ID, creator, timestamps, status | **Keep** |
| **2. Visual Evidence** | Inspect raw physical evidence | AOI/SPI image DB | Inspection Hardware | QE, ME, SQE | Original reference, board ID, station, capture time | **Keep** |
| **3. CV Findings** | Present structured visual analysis | CV Pipeline | AI Model | QE, ME | Defect class, confidence, bounding box, model/ver | **Keep** |
| **4. Production Timeline** | Relate defect to process conditions | MES, Telemetry | Manufacturing Sys | QE, ME | Source system, timestamps, parameters | **Keep** |
| **5. Machine Health Status**| Correlate machine condition | Machine Sensors | Machine Sys / AI | QE, ME, Maint | Machine ID, sensor readings, timestamp | **Keep** |
| **6. Maintenance History** | Check maintenance causes | CMMS / ERP | Maintenance Sys | QE, Maint Eng | Work order IDs, timestamps, nozzle cleanings | **Keep** |
| **7. Lot Information** | Establish component genealogy | ERP / MES | Enterprise Sys | QE, SQE | Part number, lot number, board genealogy | **Keep** |
| **8. Supplier History** | Provide supplier context | QMS | Enterprise Quality | QE, SQE, QM | Supplier ID, lot history, correlation note | **Keep (as context)** |
| **9. Technical Docs** | Provide SOP/manual guidance | Document Corpus | RAG / AI | QE, ME, Maint | Title, version, passage, query, score | **Keep** |
| **10. Historical Incidents**| Identify recurring patterns | Incident DB | AI / DB | QE, QM | Incident IDs, similarity basis, product context | **Keep** |
| **11. Evidence Correlation**| Link evidence sources explicitly| All Sources | AI Synthesis | QE | Links to source evidence, correlation type | **Keep** |
| **12. Root-Cause Hypotheses**| Present ranked candidate causes| Correlated Evidence | AI + Human Edits | QE, ME | Pro/contra evidence, confidence, human edits | **Keep** |
| **13. Corrective Actions**| Recommend mitigation steps | Hypotheses, SOPs | AI + Human | QE, ME, Maint | Action rationale, risk tier, approval requirement | **Keep** |
| **14. Human Approval**| Enforce human authority | Conclusions | Human Approver | Approver | Approver identity, role, timestamp, decision | **Keep (Mandatory)** |
| **15. Audit Trail** | Reconstruct investigation | Audit Service | System-Generated | QE, QM, Admin | Immutable event log, snapshots, approver IDs | **Keep (Mandatory)** |

### 8.2 Recommended Final Workspace Grouping Layout

```text
Group 1 — Incident Context:  Incident Summary → Current Status → Incident Scope
Group 2 — Source Evidence:   Visual Evidence → CV Findings → Production Timeline → Machine Health → Maintenance History → Component/Lot Info → Supplier History
Group 3 — Knowledge Base:    Retrieved Technical Documents → Historical Similar Incidents
Group 4 — Investigation:     Evidence Correlation → Ranked Root-Cause Hypotheses → Corrective-Action Recommendations
Group 5 — Human Decision:    Human Approval Panel (Mandatory Gate)
Group 6 — Accountability:    Audit Trail (Immutable Log)
```

---

## 9. Trust & Explainability Requirements (Step 2.14)

### 9.1 Provenance Requirements per Data Source
- **CV Findings**: `defect_type`, `confidence`, `bounding_box`, `raw_image_reference`, `model_name`, `model_version`, `inference_timestamp`, `training_dataset_ref`.
- **RAG / Documents**: `document_title`, `document_version`, `document_date`, `retrieved_passage`, `section_reference`, `retrieval_score`, `retrieval_query`, `retrieval_timestamp`.
- **MCP / Operational Data**: `source_system`, `tool_name`, `query_parameters`, `query_timestamp`, `data_snapshot_timestamp`, `returned_data_summary`.
- **Agent Recommendations**: `conclusion`, `supporting_evidence_list`, `contradicting_evidence_list`, `confidence_level`, `evidence_provenance_references`, `reasoning_summary`.

### 9.2 Chain-of-Thought Boundary
ForgeSight **must NOT expose hidden LLM chain-of-thought or private reasoning traces in the UI**. Instead, it provides concise reasoning summaries, evidence references, and supporting/contradicting evidence lists. Industrial users need an investigation they can audit and challenge, not an opaque private model reasoning transcript.

---

## 10. Audit Requirements (Step 2.15)

### 10.1 Conceptual Audit Record Schema
```text
AuditEvent {
  audit_id:          unique identifier
  who:               user_id + role
  what:              event_type (enum)
  when:              timestamp (UTC)
  target:            incident_id / entity_id
  action:            specific action taken
  result:            outcome
  prior_state:       snapshot before action (where applicable)
  new_state:         snapshot after action (where applicable)
  approval_by:       approver user_id (where applicable)
  ai_version:        model/agent version used (where applicable)
  evidence_version:  evidence snapshot reference
  ip_address:        request origin
}
```

### 10.2 Retention & Immutability Rules
- Audit records associated with quality decisions are append-only and protected against user modification.
- Timestamps, ordering, and evidence snapshots are immutably linked.
- System Administrators manage audit log protection mechanisms but cannot silently rewrite investigation history.

---

## 11. Persona-to-System Layer Mapping (Step 2.16)

### 11.1 Layer Interaction Matrix

| Persona | React Frontend | FastAPI | Investigation Workflow | Specialized Capabilities | MCP Tools | RAG | CV Pipeline | Database |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Production Operator | Primary | Primary | Secondary | Secondary | Secondary | — | Secondary | Secondary |
| Quality Engineer | Primary | Primary | Primary | Primary | Primary | Primary | Primary | Secondary |
| Manufacturing Engineer | Primary | Primary | Primary | Primary | Primary | Secondary | Secondary | Secondary |
| Maintenance Engineer | Primary | Primary | Secondary | Primary | Primary | Secondary | — | Secondary |
| Quality Manager | Primary | Primary | Secondary | Secondary | Secondary | Secondary | Secondary | Primary |
| Supplier Quality Engineer | Primary | Primary | Secondary | Primary | Primary | Secondary | Secondary | Primary |
| System Administrator | Admin | Admin | — | Admin | Admin | Admin | Admin | Admin |

### 11.2 Deterministic Services vs. Potential AI Capabilities
- **Deterministic Services (Functions/Workflows)**: Authentication, RBAC authorization, incident state transitions, audit logging, evidence versioning, data validation, approval gates, immutable audit storage.
- **Potential AI Capabilities**: Visual defect interpretation, document relevance ranking, historical incident semantic search, telemetry anomaly explanation, evidence synthesis, hypothesis ranking, report drafting.
