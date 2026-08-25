# ForgeSight AI — Manufacturing Incident User Journeys (Step 2.12)

## 1. Overview & Operational Principles

User journeys map how human personas interact with ForgeSight and each other across the 12-stage manufacturing incident investigation workflow. Each journey highlights the trigger, inputs, system responses, decision points, human approval gates, and next steps.

---

## 2. Journey 1: Production Operator → Quality Engineer (Incident Initiation)

- **Journey ID**: `JRN-001`
- **Primary Actor**: Production Operator
- **Secondary Actor**: Quality Engineer (QE)
- **Trigger**: SMT line AOI station flags a component shift defect exceeding process tolerance.
- **Preconditions**: SMT Line SMT-LINE-03 is running active batch `B-24017` for product `ECU-2026`.

### Flow Diagram
```text
[ AOI Flag at Station ]
          │
          ▼
[ Operator Inspects Physical PCB ]
          │
          ▼
[ Operator Opens Line UI Capture Form ]
          │
          ▼
[ Submits Photo + Batch Context + Notes ]
          │
          ▼
[ ForgeSight Instantiates Incident Context (INCIDENT-2026-00421) ]
          │
          ▼
[ Automated Notification Sent to Duty Quality Engineer ]
          │
          ▼
[ Operator Receives Confirmation Badge ("Under Investigation") ]
```

### Detailed Steps

| Step | Actor | Action | System Response | Decision Point | Next Step |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Detection** | AOI Station | Flags component shift at C17 (0.15mm shift) on Board #140. | Displays red alert flag on shop-floor terminal screen. | Is flag a real defect or optical false alarm? | Operator physical inspection. |
| **2. Physical Check** | Operator | Removes PCB from conveyor and inspects under digital microscope. | None (physical task). | Confirms component C17 is physically shifted on wet paste. | Log incident. |
| **3. Submission** | Operator | Scans PCB barcode, attaches microscope photo, adds note: "C17 shifted on 3 consecutive boards". | Captures metadata, uploads photo, generates `INCIDENT-2026-00421`. | None (standard creation). | Initiate backend context. |
| **4. Notification** | ForgeSight | Creates incident record, links batch `B-24017` and line `SMT-LINE-03`. | Dispatches alert push notification to duty QE dashboard. | None. | QE investigation initiation. |

---

## 3. Journey 2: Quality Engineer → Full Incident Investigation

- **Journey ID**: `JRN-002`
- **Primary Actor**: Quality Engineer (Primary Human-in-the-Loop Authority)
- **Trigger**: QE receives notification for `INCIDENT-2026-00421`.
- **Preconditions**: Incident context created with AOI evidence attached.

### Flow Diagram
```text
[ QE Opens Investigation Workspace ]
                 │
                 ▼
[ CV Pipeline Analyzes Inspection Image ]
                 │
                 ▼
[ ForgeSight Queries MES Telemetry & Machine Logs ]
                 │
                 ▼
[ RAG Pipeline Retrieves Governing SOP (SOP-QUAL-042) ]
                 │
                 ▼
[ Evidence Graph Correlates Findings ]
                 │
                 ▼
[ AI Ranks Hypotheses: #1 Worn Nozzle (85%), #2 Thermal Drift (15%) ]
                 │
                 ▼
[ QE Reviews Evidence & Confirms Hypothesis #1 ]
                 │
                 ▼
[ QE Approves Corrective Action: Replace Nozzle #3 on Placer 7 ]
                 │
                 ▼
[ System Generates Signed PDF Report & Audit Record ]
```

### Detailed Steps

| Step | Actor | Action | System Response | Decision Point | Next Step |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Workspace Open**| QE | Clicks incident notification to open `INCIDENT-2026-00421`. | Renders Investigation Workspace with Groups 1-6 layout. | What evidence is available? | Review visual findings. |
| **2. CV Processing** | ForgeSight (CV) | Runs detection on inspection photo. | Displays bounding box around C17, class `component_misalignment`, confidence `0.94`. | Does CV analysis match physical board photo? | Query telemetry & machine. |
| **3. Correlation** | ForgeSight (MCP/DB)| Queries MES batch telemetry and Placer-07 nozzle logs. | Identifies nozzle vacuum pick drop frequency and 47-day nozzle cleaning delay. | Are machine sensors drifting? | Search SOP guidelines. |
| **4. RAG Search** | ForgeSight (RAG)| Searches SOP corpus for IPC-A-610 Class 3 placement alignment specs. | Retrieves `SOP-QUAL-042 Section 4.2` with page and passage citation. | What is allowable alignment tolerance? | Evaluate hypotheses. |
| **5. Hypothesis Review**| QE | Inspects ranked hypotheses list. | Displays supporting evidence (nozzle delay) vs contra evidence (reflow temp stable). | Does QE agree with AI ranking? | Approve or modify action. |
| **6. Human Sign-Off**| QE | Validates Hypothesis #1, selects corrective action "Replace Nozzle #3", clicks Approve. | Executes Stage 11 Sign-off, logs immutable audit record, generates PDF report. | Final human approval gate. | Incident Closure (Stage 12). |

---

## 4. Journey 3: Quality Engineer → Maintenance Investigation Branch

- **Journey ID**: `JRN-003`
- **Primary Actor**: Quality Engineer & Maintenance Engineer
- **Trigger**: Root-cause hypothesis indicates mechanical equipment failure on Placer-07.
- **Preconditions**: QE is actively investigating `INCIDENT-2026-00421`.

### Flow Diagram
```text
[ Investigation Workspace Identifies Machine Condition as Lead Cause ]
                                │
                                ▼
[ QE Initiates Maintenance Verification Request via ForgeSight ]
                                │
                                ▼
[ Maintenance Engineer Receives Machine Diagnostic Alert ]
                                │
                                ▼
[ Maintenance Engineer Inspects Nozzle #3 Physical Vacuum Seal ]
                                │
                                ▼
[ Maintenance Engineer Confirms Nozzle Tip Wear & Replaces Nozzle ]
                                │
                                ▼
[ Maintenance Work Order Recorded in ForgeSight Audit Log ]
```

### Detailed Steps

| Step | Actor | Action | System Response | Decision Point | Next Step |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Branch Trigger**| QE | Flags machine health as primary suspect based on nozzle wear logs. | Routes maintenance diagnostic context to Maintenance Engineer portal. | Is machine hardware at fault? | Maintenance physical check. |
| **2. Inspection** | Maintenance Eng| Reviews placer nozzle vacuum pressure logs and inspects physical nozzle tip. | Displays historical nozzle maintenance interval and error code count. | Is nozzle physically damaged or clogged? | Execute maintenance. |
| **3. Repair & Log** | Maintenance Eng| Replaces Nozzle #3, logs calibration run in CMMS, updates ForgeSight. | Records work order execution in `INCIDENT-2026-00421` evidence graph. | Is machine recalibrated and ready? | Notify QE. |
| **4. Verification** | QE | Reviews completed maintenance record and authorizes line restart test. | Updates incident status to "Corrective Action Completed". | Are placement defects resolved on test board? | Close incident. |

---

## 5. Journey 4: Quality Engineer → Supplier Quality Investigation Branch

- **Journey ID**: `JRN-004`
- **Primary Actor**: Quality Engineer & Supplier Quality Engineer (SQE)
- **Trigger**: Placer telemetry shows normal vacuum force, but component placement shifts correlate with Component Lot `LOT-9921`.
- **Preconditions**: Machine and thermal variables have been excluded as primary causes.

### Flow Diagram
```text
[ Machine & Thermal Variables Excluded as Defect Cause ]
                           │
                           ▼
[ Statistical Correlation Shows 82% Defects on Component Lot LOT-9921 ]
                           │
                           ▼
[ QE Escalates Context to Supplier Quality Engineer (SQE) ]
                           │
                           ▼
[ SQE Reviews Correlation vs Physical Evidence Rule ]
                           │
                           ▼
[ SQE Performs IPC Solderability Test (IPC-J-STD-002) on Sample Parts ]
                           │
                           ▼
[ Solderability Test Confirms Severe Lead Oxidation on Lot LOT-9921 ]
                           │
                           ▼
[ SQE Approves Formal Supplier Corrective Action Request (SCAR) ]
```

### Detailed Steps

| Step | Actor | Action | System Response | Decision Point | Next Step |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Correlation** | ForgeSight | Identifies statistical correlation: 82% of shifted components belong to Capacitor Lot `LOT-9921` (Vendor: Acme Micro). | Displays lot correlation warning, highlighting correlation ≠ causation rule. | Is correlation sufficient to blame supplier? **(No)** | Request SQE physical audit. |
| **2. SQE Review** | SQE | Opens supplier branch, reviews incoming inspection records and lot genealogy. | Displays supplier quality history and component datasheet specs. | What physical evidence is needed? | Perform IPC test. |
| **3. Physical Test**| SQE | Performs IPC-J-STD-002 solderability dip test under microscopy. | Uploads test result report showing un-wettable lead oxidation. | Does physical evidence prove vendor defect? | Issue SCAR. |
| **4. SCAR Approval**| SQE | Authorizes formal SCAR issuance against Acme Micro for Lot `LOT-9921`. | Logs SCAR record, triggers inventory hold on remaining Lot `LOT-9921` reels. | High-risk action approval gate. | Notify vendor. |
