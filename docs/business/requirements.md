# ForgeSight AI — System Requirements & Traceability Specification (Step 2.17)

## 1. Overview

This document formalizes the business, functional, non-functional, safety, human-in-the-loop, audit, and security requirements for ForgeSight AI. All requirements are derived from the 12-stage manufacturing incident investigation workflow and the stakeholder persona analysis.

---

## 2. Functional Requirements (FR)

| ID | Requirement Statement | Rationale | Persona | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **FR-001** | The system shall allow authorized users to create quality incidents manually or via inspection threshold triggers. | Establishes the digital incident context. | Operator, QE | **Critical** |
| **FR-002** | The system shall associate inspection images, coordinates, and board metadata with an incident. | Preserves raw physical evidence. | Operator, QE | **Critical** |
| **FR-003** | The system shall analyze optical inspection images using Computer Vision to extract defect class, bounding box, and confidence. | Converts raw images into structured visual evidence. | QE, ME | **High** |
| **FR-004** | The system shall retrieve production line telemetry and process parameters corresponding to the incident timestamp and batch. | Identifies upstream process shifts. | QE, ME | **High** |
| **FR-005** | The system shall retrieve SMT equipment maintenance history, nozzle inspection records, and feeder calibration logs. | Detects mechanical machine wear causes. | QE, Maint Eng | **High** |
| **FR-006** | The system shall retrieve component lot genealogy and supplier incoming quality records for affected boards. | Identifies component batch defects. | QE, SQE | **High** |
| **FR-007** | The system shall retrieve relevant technical passages from approved SOPs and manuals using semantic search (RAG). | Ground investigation in IPC/SOP standards. | QE, ME | **High** |
| **FR-008** | The system shall query historical quality incidents to identify recurring defect patterns and previous root causes. | Prevents redundant investigation effort. | QE, QM | **Medium** |
| **FR-009** | The system shall synthesize multi-source evidence into an evidence correlation graph highlighting temporal and causal links. | Fuses fragmented factory data. | QE | **High** |
| **FR-010** | The system shall formulate and rank probabilistic root-cause hypotheses with supporting and contradicting evidence lists. | Provides transparent candidate causes. | QE | **Critical** |
| **FR-011** | The system shall generate corrective action recommendations categorized by risk level and operational impact. | Translates findings into action. | QE, ME, Maint | **High** |
| **FR-012** | The system shall provide an interactive approval interface allowing engineers to modify, confirm, or reject AI hypotheses. | Enforces human-in-the-loop control. | QE | **Critical** |
| **FR-013** | The system shall generate formal Markdown and PDF incident reports containing evidence provenance and human sign-off timestamps. | Fulfills ISO 9001 audit requirements. | QE, QM | **High** |
| **FR-014** | The system shall enforce Role-Based Access Control (RBAC) across all API endpoints, views, and tool invocations. | Prevents unauthorized actions. | Admin, All | **Critical** |
| **FR-015** | The system shall display line yield metrics and incident resolution status on an executive management dashboard. | Provides macro-level plant visibility. | QM | **Medium** |

---

## 3. Non-Functional Requirements (NFR)

| ID | Requirement Statement | Rationale | Persona | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **NFR-001** | The system shall return CV analysis results within 2.0 seconds of image submission. | Ensures rapid shop-floor feedback. | Operator, QE | **High** |
| **NFR-002** | The RAG retrieval pipeline shall return relevant SOP passages within 1.5 seconds of query execution. | Maintains interactive UI response. | QE | **High** |
| **NFR-003** | The system shall maintain 99.9% uptime for incident capture endpoints. | Prevents shop-floor logging downtime. | Operator | **Critical** |
| **NFR-004** | All evidence snapshots and audit logs shall be immutable once recorded. | Ensures regulatory compliance. | QM, Admin | **Critical** |
| **NFR-005** | The LLM reasoning and RAG backend shall support configurable model providers (Groq, local LLM). | Avoids vendor lock-in. | Admin | **High** |
| **NFR-006** | The system database shall store up to 1,000,000 incident evidence records without performance degradation. | Supports enterprise scale. | Admin | **Medium** |
| **NFR-007** | The UI shall support responsive display across shop-floor tablets and desktop workstations. | Ensures shop-floor usability. | Operator, QE | **High** |
| **NFR-008** | Sensitive supplier and quality data shall be encrypted at rest (AES-256) and in transit (TLS 1.3). | Protects corporate IP. | Admin | **Critical** |

---

## 4. Safety Requirements (SR)

| ID | Requirement Statement | Rationale | Persona | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **SR-001** | The system shall NOT autonomously modify physical SMT machine parameters or reflow thermal profiles. | Prevents unverified line disruption. | All | **Critical** |
| **SR-002** | The system shall NOT execute automated quality holds on global component inventory without authorized human sign-off. | Prevents unauthorized supply chain halt.| QE, QM | **Critical** |
| **SR-003** | The system shall NOT expose raw LLM chain-of-thought private reasoning traces as a user-facing system feature. | Prevents confusing model speculation. | QE | **High** |
| **SR-004** | The system shall enforce explicit correlation vs. causation warnings when component lot defect rates increase. | Prevents unproven vendor accusations. | SQE, QE | **High** |

---

## 5. Human-in-the-Loop Requirements (HITL)

| ID | Requirement Statement | Rationale | Persona | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **HITL-001**| Stage 11 Incident Sign-Off requires explicit authorized human QE user identity, role, timestamp, and comments. | Enforces legal/ISO sign-off gate. | QE | **Critical** |
| **HITL-002**| High-risk corrective actions (machine parameter changes, lot holds) shall require multi-factor human approval. | Gated operational risk. | QE, QM, ME | **Critical** |
| **HITL-003**| The Quality Engineer shall have explicit UI controls to edit, reorder, or override AI-generated root-cause hypotheses. | Human judgment over AI inference. | QE | **High** |
| **HITL-004**| Issuance of a Supplier Corrective Action Request (SCAR) requires explicit SQE sign-off backed by IPC test evidence. | Prevents commercial vendor friction. | SQE | **High** |
| **HITL-005**| Operators shall have simple confirmation/rejection controls when verifying automated AOI inspection flags. | Filters false optical alerts. | Operator | **High** |

---

## 6. Audit Requirements (AR)

| ID | Requirement Statement | Rationale | Persona | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **AR-001** | The system shall log an immutable audit record for every incident creation, evidence submission, and sign-off event. | Fulfills ISO 9001 compliance. | All | **Critical** |
| **AR-002** | Every audit log entry shall conform to the standardized `AuditEvent` schema (who, what, when, target, action, result, approval, evidence_version). | Standardized audit structure. | Admin, QM | **High** |
| **AR-003** | Human modifications to AI recommendations shall record both the original AI output and the modified human version. | Ensures complete provenance. | QE, QM | **High** |
| **AR-004** | Audit records shall be append-only and protected against modification or deletion by non-administrative users. | Prevents audit tampering. | Admin | **Critical** |
| **AR-005** | Audit logs shall link exact CV model versions and RAG document versions used during an investigation. | Allows investigation reconstruction. | QE, Admin | **High** |

---

## 7. Security Requirements (SEC)

| ID | Requirement Statement | Rationale | Persona | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **SEC-001**| The API layer shall enforce JWT authentication and fine-grained Role-Based Access Control (RBAC). | Restricts unauthorized access. | Admin | **Critical** |
| **SEC-002**| API keys and database credentials shall be injected via centralized environment variables and Pydantic settings. | Prevents credential leaks in code. | Admin | **Critical** |
| **SEC-003**| System Administration privileges shall NOT grant authorization to sign off on quality investigations or alter audit records. | Enforces segregation of duties. | Admin, QE | **Critical** |
| **SEC-004**| MCP server connections shall operate over secure transport channels with explicit capability token scopes. | Restricts MCP tool permissions. | Admin | **High** |
| **SEC-005**| User sessions shall automatically expire after 8 hours of inactivity. | Secures shop-floor terminals. | Operator, QE | **Medium** |

---

## 8. Traceability Matrix

| Business Problem | Persona | User Journey | Requirement ID | System Capability |
| :--- | :--- | :--- | :--- | :--- |
| Fragmented inspection evidence across factory systems | Quality Engineer | `JRN-002` | `FR-002`, `FR-009` | Evidence Correlation Workspace |
| Unreliable manual defect logging on shop floor | Production Operator | `JRN-001` | `FR-001`, `HITL-005` | Rapid Mobile Capture UI |
| Slow manual query time across 5 isolated databases | Quality Engineer | `JRN-002` | `FR-004`, `FR-005`, `NFR-002` | Automated MCP & Telemetry Query |
| Unproven accusations against component suppliers | Supplier Quality Engineer | `JRN-004` | `SR-004`, `HITL-004` | Evidence vs Correlation Enforcement |
| Lack of standardized ISO 9001 audit trails | Quality Manager | `JRN-002` | `AR-001`, `AR-003`, `NFR-004` | Immutable Audit Event Service |
| Unapproved high-risk machine parameter changes | Manufacturing Engineer | `JRN-003` | `SR-001`, `HITL-002` | Human Approval Gate Middleware |
| Opaque AI recommendations without source evidence | Quality Engineer | `JRN-002` | `FR-010`, `SR-003` | Grounded Hypothesis Ranking View |
| Unauthorized technical access bypassing quality rules | System Administrator | N/A | `SEC-001`, `SEC-003` | RBAC & Segregation of Duties Layer |
| Mechanical machine wear causing component shifts | Maintenance Engineer | `JRN-003` | `FR-005`, `FR-011` | Equipment Health Diagnostic View |
| Long time required to search complex SOP manuals | Quality Engineer | `JRN-002` | `FR-007`, `NFR-002` | RAG SOP Document Retrieval |
