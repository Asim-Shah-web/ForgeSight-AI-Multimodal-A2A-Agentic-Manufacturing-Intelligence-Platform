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

## 3. Candidate Personas Summary & Organizational Justification

### 1. Production Operator
- **Why Needed**: Acts as the first line of defense on the shop floor. Identifies physical defects at AOI/manual stations and initiates the digital incident lifecycle.

### 2. Quality Engineer (Primary Human-in-the-Loop Authority)
- **Why Needed**: Owns overall root-cause investigation, cross-correlates multi-source evidence, and holds legal/ISO accountability for approving quality findings.

### 3. Manufacturing Engineer
- **Why Needed**: Focuses on SMT process physics, stencil printing squeegee speeds, placer mounting force, and reflow thermal profiles.

### 4. Maintenance Engineer
- **Why Needed**: Focuses on electromechanical machine health, feeder tension, vacuum nozzle wear, and preventative maintenance schedules.

### 5. Quality Manager
- **Why Needed**: Needs macro-level oversight across batches and lines, manages plant-wide risk, and authorizes high-impact actions like placing entire production runs on hold.

### 6. Supplier Quality Engineer
- **Why Needed**: Handles external vendor component lot issues and requires rigorous evidence before issuing formal Supplier Corrective Action Requests (SCARs).

### 7. System Administrator
- **Why Needed**: Controls platform security, model API keys, MCP server connections, and system audit logs without interfering with manufacturing engineering decisions.
