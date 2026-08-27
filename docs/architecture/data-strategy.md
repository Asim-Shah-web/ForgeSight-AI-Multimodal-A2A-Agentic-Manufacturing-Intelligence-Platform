
# ForgeSight AI — Synthetic Data Strategy

## Document Status

- **Project:** ForgeSight AI
- **Phase:** Phase 2 — Domain Model & Data Architecture
- **Purpose:** Define a coherent synthetic manufacturing world for development, testing, investigation demonstrations, and future integration validation.
- **Data Type:** Synthetic
- **Implementation Status:** Documentation only
- **Important Boundary:** This document defines data requirements and relationships, not Python generators, SQL seed scripts, or production database implementation.

---

# 1. Purpose of Synthetic Data

ForgeSight requires synthetic data because publicly available PCB datasets generally provide useful inspection images but do not provide the complete enterprise manufacturing context required for realistic quality investigations.

A realistic ForgeSight investigation needs to connect visual evidence to:

- board identity
- production batch
- SMT line
- machine
- machine subcomponents
- production telemetry
- maintenance history
- component
- component lot
- supplier
- technical documentation
- previous incidents

A single PCB image is therefore insufficient to demonstrate the complete investigation workflow.

The synthetic data strategy creates a connected manufacturing world in which every important record can be traced backward and forward through the manufacturing process.

---

# 2. Connected Manufacturing World

The central traceability chain is:

```text
PCB Inspection Image
        │
        ▼
     Board ID
        │
        ▼
      Batch
        │
        ▼
      SMT Line
        │
        ▼
     Machine
        │
        ├──────────────► Nozzle
        │                   │
        │                   ▼
        │             Maintenance Record
        │
        ▼
 Production Telemetry


Board
  │
  ▼
Component
  │
  ▼
Component Lot
  │
  ▼
Supplier



|  #  | Dataset                              | Purpose                                                       |
| :-: | :----------------------------------- | :------------------------------------------------------------ |
|  1  | `synthetic_suppliers.csv`            | Supplier master data and quality context.                     |
|  2  | `synthetic_component_lots.csv`       | Incoming component lot traceability and quality history.      |
|  3  | `synthetic_machines.csv`             | SMT equipment master data.                                    |
|  4  | `synthetic_nozzles.csv`              | Placer nozzle state and maintenance context.                  |
|  5  | `synthetic_maintenance.csv`          | Machine and nozzle maintenance events.                        |
|  6  | `synthetic_batches.csv`              | Manufacturing batch context.                                  |
|  7  | `synthetic_boards.csv`               | Individual board traceability.                                |
|  8  | `synthetic_production_telemetry.csv` | Time-series manufacturing conditions.                         |
|  9  | `synthetic_defects.csv`              | Defect observations linked to boards and inspection evidence. |
|  10 | `synthetic_incidents.csv`            | Formal quality investigation records.                         |



# Dataset 1 — synthetic_suppliers.csv

Purpose:
Represents supplier master data used by Supplier Quality Engineers during component-lot investigations


| Column           | Description                            |
| :--------------- | :------------------------------------- |
| `supplier_id`    | Unique synthetic supplier identifier.  |
| `supplier_name`  | Supplier organization name.            |
| `country`        | Supplier country.                      |
| `contact_name`   | Synthetic supplier-quality contact.    |
| `quality_rating` | Synthetic quality performance rating.  |
| `status`         | Approved, conditional, suspended, etc. |
| `created_at`     | Supplier record creation timestamp.    |

# Examples

| supplier_id | supplier_name               | country  | contact_name | quality_rating | status   | created_at           |
| :---------- | :-------------------------- | :------- | :----------- | -------------: | :------- | :------------------- |
| SUP-001     | Apex Passive Components     | Japan    | Hiro Tanaka  |           96.2 | Approved | 2025-03-12T08:00:00Z |
| SUP-002     | Meridian Electronics Supply | Malaysia | Nur Aisyah   |           91.8 | Approved | 2025-05-21T09:30:00Z |
| SUP-003     | NorthStar Components        | Taiwan   | Wei Chen     |           94.6 | Approved | 2025-01-18T07:45:00Z |


# Synthetic Component Lots — synthetic_component_lots.csv
| Column                       | Description                                 |
| :--------------------------- | :------------------------------------------ |
| `component_lot_id`           | Unique lot identity.                        |
| `part_number`                | Component part number.                      |
| `component_description`      | Component description.                      |
| `lot_number`                 | Supplier lot number.                        |
| `supplier_id`                | Supplier reference.                         |
| `quantity_received`          | Quantity received.                          |
| `received_at`                | Receipt timestamp.                          |
| `historical_defect_rate`     | Historical defect rate for the lot/context. |
| `incoming_inspection_result` | Incoming inspection outcome.                |
| `status`                     | Released, quarantine, consumed, etc.        |

## Examples
| component_lot_id | part_number | component_description | lot_number | supplier_id | quantity_received | received_at          | historical_defect_rate | incoming_inspection_result | status   |
| :--------------- | :---------- | :-------------------- | :--------- | :---------- | ----------------: | :------------------- | ---------------------: | :------------------------- | :------- |
| LOT-9918         | C-10UF-0603 | 10µF 0603 capacitor   | LOT-9918   | SUP-001     |             50000 | 2026-06-02T10:00:00Z |                  0.18% | Pass                       | Consumed |
| LOT-9921         | C-10UF-0603 | 10µF 0603 capacitor   | LOT-9921   | SUP-001     |             48000 | 2026-07-10T11:15:00Z |                  1.74% | Pass                       | Consumed |
| LOT-9925         | R-10K-0603  | 10kΩ 0603 resistor    | LOT-9925   | SUP-002     |             60000 | 2026-07-15T08:40:00Z |                  0.12% | Pass                       | Consumed |


