# ForgeSight AI — Data Flow Architecture

## Phase 2 — Domain Model & Data Architecture

---

## 1. Purpose

This document defines how manufacturing data enters ForgeSight AI, how it is validated and transformed, where it is stored, and how it reaches the Quality Engineer's investigation workspace.

ForgeSight AI combines multiple evidence sources so that a Quality Engineer can investigate PCB manufacturing incidents using:

- AOI inspection images
- Computer Vision findings
- Production telemetry
- Machine health information
- Maintenance records
- Component and lot information
- Supplier history
- Technical documents and SOPs
- Historical incidents

The system preserves provenance throughout the investigation so that AI-generated findings and recommendations can be traced back to their underlying evidence.

The Quality Engineer remains the final decision-making authority.

---

# 2. High-Level Data Flow Architecture

```text
┌──────────────────────────────────────────────────────────────────────┐
│                    MANUFACTURING SOURCE SYSTEMS                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  AOI Hardware       MES / Sensors       CMMS / ERP       ERP         │
│      │                   │                  │              │          │
│      │                   │                  │              │          │
│      ▼                   ▼                  ▼              ▼          │
│  PCB Images          Telemetry         Maintenance     Component     │
│  + AOI Flags         Readings          Records         Lots/Suppliers│
│                                                                      │
│                    Technical Documents                               │
│                           │                                          │
│                           ▼                                          │
└──────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         INGESTION LAYER                              │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Evidence Upload      MCP Data Access       Document Ingestion       │
│       │                    │                       │                  │
│       ▼                    ▼                       ▼                  │
│  Metadata Validation   Source Validation     Document Validation    │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     PROCESSING / ANALYSIS LAYER                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   CV Pipeline       Telemetry Analysis      Evidence Correlation     │
│       │                    │                       │                  │
│       ▼                    ▼                       ▼                  │
│  CvFinding          Process Deviations       Correlated Evidence    │
│                                                                      │
│                    RAG Retrieval / Similarity Search                 │
│                           │                                          │
│                           ▼                                          │
│                  Retrieved Knowledge                                 │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       PERSISTENT STORAGE                             │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│                         PostgreSQL                                   │
│                                                                      │
│  Incidents | Boards | Batches | Defects | Machines                  │
│  Maintenance | Lots | Suppliers | Telemetry | CV Findings          │
│  Hypotheses | Corrective Actions | Reports | Audit Events           │
│                                                                      │
│                         pgvector                                     │
│                                                                      │
│  Document Embeddings | Historical Incident Embeddings               │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         INVESTIGATION                                │
│                           WORKSPACE                                  │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Incident Summary                                                    │
│  Visual Evidence                                                     │
│  CV Findings                                                         │
│  Production Timeline                                                 │
│  Machine / Maintenance History                                      │
│  Component / Supplier Information                                   │
│  Technical Documents                                                 │
│  Historical Similar Incidents                                       │
│  Evidence Correlation                                                │
│  Root-Cause Hypotheses                                               │
│  Corrective Actions                                                  │
│  Human Approval                                                      │
│  Audit Trail                                                         │
│                                                                      │
│                    ▼                                                 │
│              QUALITY ENGINEER                                       │
│             FINAL DECISION                                          │
└──────────────────────────────────────────────────────────────────────┘
```
# 3. Inspection Image Data Flow
## 3.1 Purpose

The inspection image flow connects physical PCB inspection evidence from an AOI station to structured Computer Vision findings that can be reviewed by a Quality Engineer.

## 3.2 Flow
AOI Hardware
     │
     ▼
PCB Inspection Image
     │
     ▼
Evidence Upload
     │
     ▼
Metadata Validation
     │
     ├── Board Serial
     ├── Inspection Station
     ├── Capture Timestamp
     └── Source System
     │
     ▼
Inspection Image Storage
     │
     ▼
CV Pipeline
     │
     ▼
CV Finding
     │
     ├── Defect Type
     ├── Confidence
     ├── Bounding Box
     ├── Model Name
     ├── Model Version
     └── Inference Timestamp
     │
     ▼
Incident Evidence
     │
     ▼
Investigation Workspace
     │
     ▼
Quality Engineer Review
## 3.3 Data Format
### Ingress

The inspection image enters ForgeSight as an image file accompanied by metadata.

Conceptual metadata includes:

Field	Description
board_serial	Identifies the physical PCB
station_id	Identifies the AOI/inspection station
capture_timestamp	Time the image was captured
source_system	Identifies the originating AOI system
image_reference	Reference to the stored image
batch_id	Manufacturing batch associated with the board, when available
Processing

The CV pipeline analyzes the inspection image and produces structured findings.

The output may contain:

defect type
confidence
bounding box
model name
model version
inference timestamp

The final CV model is intentionally TBD at this phase.

## 3.4 Storage

Permanent inspection metadata and CV findings are stored in PostgreSQL.

The physical image is referenced through its file_path or equivalent evidence reference.

## 3.5 Workspace Presentation

The Quality Engineer sees:

Original inspection image
Defect location
CV-detected defect type
Confidence
Model information
Capture timestamp
Link/reference to the original evidence
## 3.6 Provenance Requirements

The following provenance must remain attached to the finding:

raw image reference
board serial
inspection station
source system
capture timestamp
model name
model version
inference timestamp
# 4. Production Telemetry Data Flow
### 4.1 Purpose

Production telemetry allows ForgeSight to determine whether machine or process parameters changed around the time a defect occurred.

## 4.2 Flow
MES / Machine Sensors
          │
          ▼
Telemetry Records
          │
          ▼
MCP Data Access
          │
          ▼
Source + Parameter Validation
          │
          ▼
production_telemetry
          │
          ▼
Telemetry Analysis
          │
          ▼
Evidence Correlation
          │
          ▼
Investigation Workspace
          │
          ▼
Quality Engineer
## 4.3 Data Format

Typical telemetry records contain:

Field	Description
machine_id	Machine that produced the reading
batch_id	Manufacturing batch
timestamp	Time of reading
parameter_name	Parameter being measured
parameter_value	Measured value
unit	Engineering unit
source_system	Originating system

Examples of parameters include:

temperature
pressure
placement speed
mounting force
conveyor speed
printer pressure
reflow zone temperature
## 4.4 Processing

ForgeSight retrieves telemetry through the appropriate MCP data access capability.

The retrieved data can then be analyzed for:

parameter drift
abnormal values
changes around incident time
differences between good and defective production periods
correlation with machine or batch events
## 4.5 Storage

Permanent investigation-relevant telemetry is stored in PostgreSQL.

Frequently accessed or temporary telemetry snapshots may be cached in Redis.

## 4.6 Workspace Presentation

The Quality Engineer should see:

Parameter timeline
Relevant machine
Batch
Timestamp
Measured value
Unit
Detected deviation
Source system
Query timestamp
# 5. Maintenance Data Flow
## 5.1 Purpose

Maintenance information allows ForgeSight to determine whether equipment condition or maintenance history could contribute to a defect.

## 5.2 Flow
CMMS / ERP
    │
    ▼
Maintenance Records
    │
    ▼
MCP Data Access
    │
    ▼
Source Validation
    │
    ▼
MaintenanceRecord
    │
    ▼
Maintenance History Analysis
    │
    ▼
Evidence Correlation
    │
    ▼
Investigation Workspace
    │
    ▼
Quality Engineer
    │
    ▼
Maintenance Engineer
(if machine-related investigation is required)
## 5.3 Data Format

Maintenance information may include:

Field	Description
machine_id	Machine receiving maintenance
nozzle_id	Nozzle involved, when applicable
action_type	Cleaning, replacement, calibration, inspection, etc.
performed_by	Person who performed the maintenance
performed_at	Maintenance timestamp
notes	Maintenance details
source_system	CMMS/ERP source
## 5.4 Processing

ForgeSight can analyze:

time since last maintenance
recurring machine faults
nozzle cleaning intervals
feeder calibration history
previous maintenance events
maintenance events occurring near the incident

AI may identify a machine-related hypothesis, but the hypothesis does not automatically become a confirmed root cause.

## 5.5 Workspace Presentation

The Quality Engineer sees:

Machine
Component/nozzle where applicable
Maintenance history
Last maintenance date
Maintenance action
Relevant machine events
Source/provenance

If the investigation indicates a machine-related issue, a Maintenance Engineer can review the evidence and recommend corrective maintenance.

# Component and Lot Data Flow
## 6.1 Purpose

Component and supplier data allows ForgeSight to investigate whether a particular component lot is associated with an elevated defect rate.

A statistical correlation is not treated as proof that the supplier caused the defect.

## 6.2 Flow
ERP
 │
 ▼
Component / Lot Records
 │
 ▼
MCP Data Access
 │
 ▼
Validation
 │
 ├───────────────┐
 ▼               ▼
ComponentLot   Supplier
 │               │
 └───────┬───────┘
         ▼
Lot / Supplier Analysis
         │
         ▼
Evidence Correlation
         │
         ▼
Investigation Workspace
         │
         ▼
Quality Engineer
         │
         ▼
Supplier Quality Engineer
(if supplier investigation is required)
## 6.3 Data Format

Component lot information includes:

Field	Description
part_number	Component manufacturer/part identifier
lot_number	Supplier lot identifier
supplier_id	Supplier associated with the lot
quantity_received	Quantity received
received_at	Receiving timestamp
defect_rate_history	Historical quality information where available

Supplier information includes:

supplier name
contact information
country
historical quality information
## 6.4 Processing

ForgeSight can compare:

defect occurrence by lot
historical defect rates
lot usage dates
batches using the lot
component type
supplier history

The system must clearly distinguish:

Correlation
     ↓
Evidence Review
     ↓
Root-Cause Hypothesis
     ↓
Human SQE Validation
     ↓
Potential SCAR

ForgeSight must never automatically accuse a supplier based only on statistical correlation.

## 6.5 Workspace Presentation

The Quality Engineer sees:

Part number
Lot number
Supplier
Quantity
Receipt date
Defect-rate history
Batches using the lot
Evidence supporting or contradicting the supplier hypothesis
# 7. Technical Document Knowledge Flow
## 7.1 Purpose

Technical documents such as SOPs, machine manuals, work instructions, and quality procedures provide authoritative manufacturing knowledge for an investigation.

## 7.2 Flow
Technical Document
      │
      ▼
Document Upload
      │
      ▼
Document Validation
      │
      ▼
Document Chunking
      │
      ▼
Text Chunks
      │
      ▼
Embedding Generation
      │
      ▼
pgvector
      │
      ▼
RAG Retrieval
      │
      ▼
Relevant Passages
      │
      ▼
Investigation Workspace
      │
      ▼
Quality Engineer
## 7.3 Data Format

Documents should preserve:

Field	Description
document_title	Document name
document_version	Revision/version
document_date	Document publication/effective date
section_reference	Section or heading
chunk_text	Retrieved document content
source_reference	Original document reference
retrieval_query	Query used for retrieval
retrieval_score	Similarity/relevance score
retrieval_timestamp	Time of retrieval
7.4 Processing

Documents are:

Uploaded.
Validated.
Divided into meaningful text chunks.
Converted into embeddings.
Stored in the pgvector-backed document retrieval structure.
Retrieved using semantic similarity.
Presented to the engineer with provenance.

The final embedding model is TBD.

## 7.5 Workspace Presentation

The Quality Engineer sees:

Document title
Version
Date
Relevant passage
Section
Retrieval score
Query
Source reference

The engineer should be able to distinguish authoritative source material from AI-generated interpretation.

# 8. Historical Incident Data Flow
## 8.1 Purpose

Historical incidents help ForgeSight identify similar previous manufacturing problems.

## 8.2 Flow
Historical Incident Records
          │
          ▼
Incident Summary Preparation
          │
          ▼
Embedding Generation
          │
          ▼
pgvector
          │
          ▼
Similarity Search
          │
          ▼
Similar Historical Incidents
          │
          ▼
Evidence Correlation
          │
          ▼
Investigation Workspace
          │
          ▼
Quality Engineer
## 8.3 Data Format

Historical incident embeddings may include:

Field	Description
source_id	Original incident identifier
source_type	Historical incident
chunk_text	Incident summary or searchable description
embedding	Vector representation
model_name	Embedding model used
metadata_json	Additional incident metadata
created_at	Embedding creation timestamp
## 8.4 Processing

The current incident can be compared semantically against historical incidents.

Potentially useful similarity attributes include:

defect type
component
machine
line
batch characteristics
symptom description
previous root cause
corrective action

Similarity is evidence for investigation, not automatic proof of the same root cause.

# 9. Evidence Correlation Flow

Evidence correlation is the central process that combines information from multiple sources.

                 ┌───────────────┐
                 │ Inspection    │
                 │ Images / CV   │
                 └───────┬───────┘
                         │
                         ▼
┌───────────────┐   ┌───────────────────┐   ┌───────────────┐
│ Production    │──►│                   │◄──│ Maintenance   │
│ Telemetry     │   │ Evidence          │   │ History       │
└───────────────┘   │ Correlation       │   └───────────────┘
                    │                   │
┌───────────────┐   │                   │   ┌───────────────┐
│ Component /   │──►│                   │◄──│ Supplier      │
│ Lot Data      │   └─────────┬─────────┘   │ History       │
└───────────────┘             │             └───────────────┘
                              │
                    ┌─────────▼─────────┐
                    │ Technical Docs /  │
                    │ Historical Cases  │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ Correlated        │
                    │ Evidence View     │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ Hypothesis        │
                    │ Generation        │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ QE Review         │
                    └───────────────────┘

The correlation layer should preserve the difference between:

raw evidence
derived analysis
statistical correlation
AI-generated hypothesis
human-confirmed root cause
# Complete End-to-End Investigation Data Flow

The following diagram connects the major data flows to the investigation workflow.

                    MANUFACTURING ENVIRONMENT
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   AOI Hardware         MES / Sensors          CMMS / ERP
        │                     │                     │
        ▼                     ▼                     ▼
 Inspection Images        Telemetry          Maintenance Data
        │                     │                     │
        │                     │                     │
        ▼                     ▼                     ▼
    CV Pipeline            MCP Access          MCP Access
        │                     │                     │
        ▼                     ▼                     ▼
    CV Findings          Telemetry DB       Maintenance DB
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │ Evidence Correlation│
                   └──────────┬──────────┘
                              │
        ┌─────────────────────┼──────────────────────┐
        │                     │                      │
        ▼                     ▼                      ▼
 Component / Lot        Technical Documents    Historical Incidents
        │                     │                      │
        ▼                     ▼                      ▼
   ERP + MCP              RAG + pgvector       pgvector Search
        │                     │                      │
        └─────────────────────┼──────────────────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │ Investigation       │
                   │ Evidence View       │
                   └──────────┬──────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │ Root-Cause          │
                   │ Hypotheses          │
                   └──────────┬──────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │ Corrective Action   │
                   │ Recommendations     │
                   └──────────┬──────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │ Human QE Review     │
                   └──────────┬──────────┘
                              │
                         Approval Gate
                              │
                              ▼
                   ┌─────────────────────┐
                   │ Incident Report +   │
                   │ Audit Trail         │
                   └─────────────────────┘
# 11. Data Provenance Preservation

ForgeSight must preserve provenance as data moves through the platform.

The conceptual provenance chain is:

Original Source
      │
      ▼
Ingestion
      │
      ▼
Validation
      │
      ▼
Stored Evidence
      │
      ▼
Analysis
      │
      ▼
Derived Finding
      │
      ▼
Correlation
      │
      ▼
AI Hypothesis / Recommendation
      │
      ▼
Human Review
      │
      ▼
Approved Decision

At each stage, the system should retain enough information to answer:

Where did this data originate?
When was it captured?
Which source system produced it?
What transformation occurred?
Which AI model or capability processed it?
Which evidence supports the conclusion?
Did a human modify the result?
Who approved the final decision?
# 12. Data Quality and Validation Rules

ForgeSight should validate incoming data before it becomes trusted investigation evidence.

### 12.1 Inspection Image Validation

An AOI image should have:

valid image reference
board serial
inspection station
capture timestamp
source system

An image without a board identity should not automatically be linked to an incident.

### 12.2 Telemetry Validation

Telemetry should contain:

machine ID
timestamp
parameter name
parameter value
unit where applicable
source system

Invalid or incomplete telemetry should be flagged rather than silently accepted.

### 12.3 Maintenance Validation

Maintenance records should contain:

machine ID
maintenance action
performed-by identity
performed timestamp
source system

If a nozzle is involved, the nozzle identity should be validated against the associated machine.

### 12.4 Component Lot Validation

Component lot records should contain:

part number
lot number
supplier
quantity received
receiving timestamp

Supplier references should resolve to known supplier records.

### 12.5 Incident Validation

An incident should maintain valid relationships to relevant:

board
batch
defect
creator

Where information is unavailable, the absence should be explicitly recorded rather than replaced with fabricated values.

### 12.6 Document Validation

Technical documents should preserve:

title
version
date
source reference
section information

Documents with unknown versions should be clearly marked as having incomplete provenance.

# 13. PostgreSQL vs Redis Data Boundary

ForgeSight uses PostgreSQL for permanent manufacturing and investigation records and Redis only for temporary or performance-oriented state.

### 13.1 PostgreSQL

PostgreSQL is the durable source of truth for:

Users
Products
Batches
Boards
Machines
Nozzles
Maintenance records
Component lots
Suppliers
Defects
Inspection image metadata
CV findings
Incidents
Production telemetry
Root-cause hypotheses
Corrective actions
Audit events
Reports

PostgreSQL data must survive application restarts and must support historical investigation reconstruction.

### 13.2 Redis

Redis is intended for temporary or rapidly changing information such as:

user/session cache
temporary investigation workspace state
short-lived telemetry snapshots
frequently accessed investigation data
temporary processing state

Redis should not become the authoritative source for permanent quality records.

### 13.3 Boundary Principle
Temporary / Fast-changing
          │
          ▼
        Redis
          │
          │
          │  NOT authoritative
          │
          ▼
Permanent / Auditable
          │
          ▼
      PostgreSQL

A permanent manufacturing decision, approved investigation result, or audit event must ultimately be persisted in PostgreSQL.

# 14. Investigation Workspace Data Assembly

The Quality Engineer's workspace is assembled from multiple persistent and derived sources.

PostgreSQL
   │
   ├── Incident
   ├── Board
   ├── Batch
   ├── Defect
   ├── Machine
   ├── Maintenance
   ├── Component Lot
   ├── Supplier
   ├── Telemetry
   ├── CV Findings
   └── Audit Events
        │
        ▼
   Investigation Context
        │
        ├───────────────┐
        │               │
        ▼               ▼
    pgvector           CV Results
        │               │
        ▼               ▼
  RAG / Similarity   Visual Evidence
        │               │
        └───────┬───────┘
                ▼
       Evidence Correlation
                │
                ▼
       Investigation Workspace
                │
                ▼
        Quality Engineer

The workspace should distinguish clearly between:

Original source data
Derived machine/CV analysis
Retrieved knowledge
Correlated evidence
AI-generated hypotheses
AI-generated recommendations
Human decisions
# 15. Relationship to the 12-Stage Investigation Workflow

The data architecture supports all 12 investigation stages.

Workflow Stage	Main Data Used
Stage 1 — Defect Detection & Threshold Trigger	AOI defect flags, CV findings
Stage 2 — Incident Creation & Context Setup	Incident, board, batch, product
Stage 3 — Visual Evidence Extraction	Inspection images, CV findings
Stage 4 — Production & Telemetry Investigation	Production telemetry
Stage 5 — Machine & Maintenance Check	Machines, nozzles, maintenance records
Stage 6 — Component Lot & Supplier Correlation	Components, lots, suppliers
Stage 7 — Technical SOP & Manual Retrieval	Technical documents, document chunks, pgvector
Stage 8 — Evidence Correlation & Synthesis	All relevant evidence sources
Stage 9 — Root-Cause Hypothesis Ranking	Correlated evidence, historical incidents
Stage 10 — Corrective Action Recommendation	Root-cause hypotheses, risk classification
Stage 11 — Human Engineer Review & Sign-Off	Hypotheses, corrective actions, approval records
Stage 12 — Report Generation & Audit Trail	Report, audit events, evidence references
# 16. Data Architecture Principles

The ForgeSight data architecture follows these principles:

### 16.1 PostgreSQL is the system of record

Permanent investigation and manufacturing records are stored in PostgreSQL.

### 16.2 Redis is not the system of record

Redis supports performance and temporary state but does not replace durable storage.

### 16.3 Evidence must remain traceable

Every important conclusion must be traceable to source evidence.

### 16.4 Derived data must remain distinguishable from source data

A CV finding, AI hypothesis, or recommendation must not be confused with the original manufacturing evidence.

### 16.5 Correlation is not causation

Statistical association, especially in supplier investigations, must not automatically become a confirmed root cause.

### 16.6 Human approval remains authoritative

High-impact manufacturing decisions require human approval.

### 16.7 Data relationships must remain internally consistent

For example:

Board
  ↓
Batch
  ↓
Line
  ↓
Machine
  ↓
Nozzle
  ↓
Maintenance Record
  ↓
Component
  ↓
Component Lot
  ↓
Supplier

References between these entities must resolve to valid records.

### 16.8 Model versions must be traceable

AI-generated findings should retain the relevant model/version information so that historical investigations can be reconstructed.

### 16.9 No final AI model is selected in Phase 2

CV and embedding model selections remain TBD and will be determined in later phases.

# 17. Summary

ForgeSight's data architecture connects manufacturing evidence from multiple systems into one investigation context.

The core flow is:

Manufacturing Sources
        ↓
Data Validation
        ↓
Ingestion / MCP Access
        ↓
PostgreSQL / pgvector
        ↓
CV / RAG / Data Analysis
        ↓
Evidence Correlation
        ↓
Root-Cause Hypotheses
        ↓
Corrective Action Recommendations
        ↓
Human QE Review
        ↓
Approval
        ↓
Report + Immutable Audit Trail

The architecture is intentionally designed around the investigation workflow rather than around individual AI agents or human job titles.

The system assists the Quality Engineer with evidence retrieval, analysis, correlation, and recommendation generation while preserving human authority over quality decisions and high-impact manufacturing actions.