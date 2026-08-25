# ForgeSight AI — Domain Model & Data Architecture

**Project:** ForgeSight AI  
**Phase:** Phase 2 — Domain Model & Data Architecture  
**Status:** Conceptual architecture  
**Scope:** Domain entities, relationships, PostgreSQL conceptual schema, pgvector/embedding design, and data-flow summary

---

# 1. Entity Catalog

## 1.1 Purpose

This document defines the conceptual domain model and data architecture for ForgeSight AI.

The model is derived from:

- The 12-stage manufacturing incident investigation workflow
- The seven established human personas
- SMT/PCB manufacturing processes
- The human-in-the-loop decision boundary
- The requirement for evidence provenance and auditability

The domain model intentionally distinguishes between:

1. **Manufacturing entities** — physical or operational objects such as boards, batches, machines, components, and lots.
2. **Investigation entities** — objects created or used during an investigation such as incidents, defects, hypotheses, corrective actions, and reports.
3. **Evidence entities** — inspection images, CV findings, telemetry, maintenance records, and technical documents.
4. **Governance entities** — users and audit events.
5. **Reference entities** — products, suppliers, lines, and historical records.

The model is conceptual. It does not represent the final production database schema.

---

## 1.2 Entity Catalog

| Entity | Description | Persona Owner | Investigation Stage Used | Priority |
|:---|:---|:---|:---|:---|
| `Incident` | Formal quality investigation record representing a manufacturing quality event requiring investigation. | Quality Engineer | 2–12 | Core |
| `Defect` | Observed or detected manufacturing defect associated with a board and inspection source. | Quality Engineer | 1–3 | Core |
| `Board` | Individual PCB assembly identified by a unique serial number. | Production Operator / Quality Engineer | 2–12 | Core |
| `Batch` | Production group containing boards manufactured under common production conditions. | Quality Engineer / Manufacturing Engineer | 2–12 | Core |
| `Product` | PCB product definition, including product name and revision. | Manufacturing Engineer / Quality Manager | 2–12 | Supporting |
| `Line` | SMT production line on which a batch is manufactured. | Manufacturing Engineer | 2–6 | Core |
| `Machine` | Manufacturing equipment such as placer, printer, or reflow oven. | Manufacturing Engineer / Maintenance Engineer | 4–6 | Core |
| `Nozzle` | Pick-and-place nozzle used to place components on boards. | Maintenance Engineer | 5 | Supporting |
| `Feeder` | Pick-and-place component feeder supplying parts to the placement machine. | Maintenance Engineer / Manufacturing Engineer | 4–6 | Supporting |
| `MaintenanceRecord` | Historical maintenance activity performed on equipment or equipment components. | Maintenance Engineer | 5 | Core |
| `WorkOrder` | Planned or corrective maintenance task resulting from an engineering recommendation or maintenance process. | Maintenance Engineer | 5, 10 | Supporting |
| `Component` | Physical component type used on a PCB, identified by part number and position/use context. | Manufacturing Engineer / SQE | 6 | Core |
| `ComponentLot` | Supplier/manufacturing lot associated with a component population used in production. | Supplier Quality Engineer | 6 | Core |
| `Supplier` | External organization providing components or materials. | Supplier Quality Engineer | 6 | Core |
| `InspectionImage` | Raw image captured by an AOI or other inspection station and associated with a board/defect. | Quality Engineer | 3 | Core |
| `CvFinding` | Structured result produced by computer vision analysis of an inspection image. | Quality Engineer | 3 | Core |
| `ProductionTelemetry` | Time-series manufacturing machine or process measurements. | Manufacturing Engineer | 4 | Core |
| `ReflowProfile` | Thermal profile information representing reflow oven behavior across zones/time. | Manufacturing Engineer | 4 | Supporting |
| `SolderPasteRecord` | Record of solder paste material, usage, lot, age, storage, or printing-related information. | Manufacturing Engineer / Quality Engineer | 4, 6 | Supporting |
| `TechnicalDocument` | Controlled technical source such as an SOP, work instruction, machine manual, or process specification. | Quality Engineer / Manufacturing Engineer | 7 | Core |
| `HistoricalIncident` | Previously closed or historical quality incident used for comparison and pattern discovery. | Quality Engineer / Quality Manager | 8–9 | Supporting |
| `RootCauseHypothesis` | Ranked explanation proposed from available evidence but not yet necessarily confirmed. | Quality Engineer | 9 | Core |
| `CorrectiveAction` | Recommended action intended to address an identified or suspected root cause. | Quality Engineer / Manufacturing Engineer / Maintenance Engineer / SQE | 10 | Core |
| `AuditEvent` | Immutable record of an important system, user, AI, approval, or manufacturing-impacting action. | System Administrator / Quality Manager | 12 | Core |
| `User` | Authenticated human user with a business role and corresponding permissions. | System Administrator | All | Core |
| `Report` | Formal investigation output containing findings, evidence, conclusions, approvals, and audit references. | Quality Engineer | 12 | Core |

---

## 1.3 Entity Classification

### Core Entities

Core entities are necessary to represent an end-to-end ForgeSight investigation:

- Incident
- Defect
- Board
- Batch
- Line
- Machine
- MaintenanceRecord
- Component
- ComponentLot
- Supplier
- InspectionImage
- CvFinding
- ProductionTelemetry
- TechnicalDocument
- RootCauseHypothesis
- CorrectiveAction
- AuditEvent
- User
- Report

### Supporting Entities

Supporting entities improve investigation depth but are not necessarily required for the minimum incident lifecycle:

- Product
- Nozzle
- Feeder
- WorkOrder
- ReflowProfile
- SolderPasteRecord
- HistoricalIncident

### Reference Entities

Some entities act primarily as contextual references:

- Product
- Supplier
- Line
- TechnicalDocument

A reference entity may still be a first-class database entity when it has its own lifecycle, relationships, provenance, or authorization requirements.

---

# 2. Relationships & ERD

## 2.1 Relationship Catalog

| Entity A | Relationship | Entity B | Type | Explanation |
|:---|:---|:---|:---|:---|
| `Product` | has | `Batch` | One-to-many | A product revision can be manufactured in many production batches. |
| `Batch` | contains | `Board` | One-to-many | A production batch contains many individual boards. |
| `Board` | belongs to | `Batch` | Many-to-one | Every board is produced as part of a batch. |
| `Batch` | runs on | `Line` | Many-to-one | A batch is associated with the SMT line used for production. |
| `Line` | contains/uses | `Machine` | One-to-many | A production line contains multiple manufacturing machines. |
| `Incident` | concerns | `Board` | Many-to-one | An incident can be associated with one primary affected board while also referencing a batch. |
| `Incident` | concerns | `Batch` | Many-to-one | An incident can apply to a production batch containing multiple affected boards. |
| `Incident` | triggered by | `Defect` | Many-to-one | A detected defect can trigger the creation of a formal investigation. |
| `Defect` | found on | `Board` | Many-to-one | A defect is observed on a particular PCB board. |
| `Defect` | detected at | `InspectionImage` / inspection station context | Many-to-one | The defect originates from an inspection context, usually AOI/SPI/AXI. |
| `InspectionImage` | belongs to | `Board` | Many-to-one | Images provide visual evidence for a particular board. |
| `InspectionImage` | may document | `Defect` | Many-to-one | An image may be captured because a specific defect was detected. |
| `CvFinding` | analyzes | `InspectionImage` | Many-to-one | A CV finding is generated from an inspection image. |
| `Machine` | produces | `ProductionTelemetry` | One-to-many | Machines generate many time-series telemetry records. |
| `Machine` | has | `Nozzle` | One-to-many | A placement machine may have multiple installed or tracked nozzles. |
| `Machine` | has | `Feeder` | One-to-many | A placement machine may have multiple feeders. |
| `Nozzle` | has history | `MaintenanceRecord` | One-to-many | Nozzle cleaning, replacement, inspection, and maintenance events are tracked over time. |
| `Machine` | has history | `MaintenanceRecord` | One-to-many | Machine maintenance is recorded against equipment. |
| `Machine` | has | `WorkOrder` | One-to-many | A machine may have multiple maintenance work orders. |
| `Component` | is supplied as | `ComponentLot` | One-to-many | A component part number may appear in many supplier lots. |
| `ComponentLot` | supplied by | `Supplier` | Many-to-one | Each component lot is associated with a supplier. |
| `ComponentLot` | used in | `Batch` | Many-to-many | A batch can use multiple lots and a lot can be consumed across multiple batches. |
| `Board` | contains | `Component` | Many-to-many | A board contains multiple component types and a component type appears on many boards. |
| `Incident` | generates | `RootCauseHypothesis` | One-to-many | An investigation may contain multiple ranked hypotheses. |
| `RootCauseHypothesis` | supports | `CorrectiveAction` | One-to-many | A hypothesis may lead to one or more recommended corrective actions. |
| `Incident` | generates | `CorrectiveAction` | One-to-many | Corrective actions belong to the investigation context. |
| `Incident` | produces | `Report` | One-to-many | An incident may generate draft and final report versions. |
| `Incident` | has | `AuditEvent` | One-to-many | Investigation activity is captured in the audit trail. |
| `User` | performs | `AuditEvent` | One-to-many | Human actions are attributed to authenticated users. |
| `User` | creates/modifies | `Incident` | One-to-many | Authorized users create or modify incidents. |
| `User` | approves | `RootCauseHypothesis` | One-to-many | Human approval is required before a hypothesis is treated as confirmed. |
| `User` | approves | `CorrectiveAction` | One-to-many | High-impact corrective actions require authorized human approval. |
| `TechnicalDocument` | contains | document chunks | One-to-many | Technical documents are divided into retrieval units for RAG. |
| `HistoricalIncident` | resembles | `Incident` | Many-to-many | Historical incidents can be semantically similar to an active incident. |
| `HistoricalIncident` | has | embeddings | One-to-many | Historical incident summaries can be embedded for semantic search. |
| `TechnicalDocument` | has | embeddings | One-to-many | Document chunks are embedded for RAG retrieval. |
| `Defect` | has | semantic representation | One-to-many | Defect descriptions may be embedded for pattern matching. |
| `All significant actions` | produce | `AuditEvent` | One-to-many | Important system and human actions must be auditable. |

---

## 2.2 Component and Lot Relationship

The component relationship requires particular care.

A `Component` represents a part definition, for example:

- Part number: `CAP-10UF-0603`
- Board reference: `C17`
- Component type: `10µF capacitor`

A `ComponentLot` represents a specific material lot, for example:

- Part number: `CAP-10UF-0603`
- Lot number: `LOT-9921`
- Supplier: `SUP-003`

The distinction is important because an investigation may determine:

> "C17 is the affected component position."

while separately finding:

> "Lot LOT-9921 was used during the affected production period."

The second statement is a lot-level correlation and must not automatically become a supplier root-cause conclusion.

---

## 2.3 Text-Based ERD

```text
                           ┌──────────────────┐
                           │     Product      │
                           └────────┬─────────┘
                                    │ 1
                                    │
                                    │ N
                           ┌────────▼─────────┐
                           │      Batch       │
                           └───────┬───┬──────┘
                                   │   │
                            N      │   │ N
                                   │   │
                    ┌──────────────▼┐  └───────────────┐
                    │     Board     │                  │
                    └──────┬────────┘                  │
                           │                           │
                           │ N                         │ N
                           ▼                           ▼
                    ┌──────────────┐            ┌──────────────┐
                    │    Defect    │            │ Production   │
                    │              │            │  Telemetry   │
                    └──────┬───────┘            └──────▲───────┘
                           │                            │
                           │                            │ N
                           │                            │
                           │                      ┌─────┴──────┐
                           │                      │   Machine  │
                           │                      └──┬─────┬───┘
                           │                         │     │
                           │                         │     ├─────────────┐
                           │                         │                   │
                           │                         ▼                   ▼
                           │                     ┌────────┐        ┌────────┐
                           │                     │ Nozzle │        │ Feeder │
                           │                     └───┬────┘        └────────┘
                           │                         │
                           │                         ▼
                           │                 ┌──────────────────┐
                           │                 │ MaintenanceRecord│
                           │                 └──────────────────┘
                           │
                           ▼
                    ┌──────────────────┐
                    │ InspectionImage  │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │    CvFinding     │
                    └──────────────────┘


       ┌──────────────┐             ┌────────────────┐
       │  Component   │────────────▶│ ComponentLot   │
       └──────────────┘             └───────┬────────┘
                                           │
                                           ▼
                                    ┌──────────────┐
                                    │   Supplier   │
                                    └──────────────┘


                    ┌────────────────────────────┐
                    │          Incident          │
                    └──────┬─────┬──────┬────────┘
                           │     │      │
                           │     │      │
                           ▼     ▼      ▼
                    ┌────────┐ ┌─────┐ ┌─────────────────────┐
                    │Hypotheses│ │Actions│ │      Report       │
                    └────┬─────┘ └──┬──┘ └─────────────────────┘
                         │           │
                         └─────┬─────┘
                               │
                               ▼
                         Human Approval


       ┌───────────────────┐
       │ TechnicalDocument │
       └─────────┬─────────┘
                 │
                 ▼
          ┌───────────────┐
          │Document Chunks│
          └───────┬───────┘
                  │
                  ▼
              pgvector
                  │
                  ▼
          RAG Retrieval


                    All significant activities
                               │
                               ▼
                       ┌─────────────┐
                       │ AuditEvent  │
                       └─────────────┘