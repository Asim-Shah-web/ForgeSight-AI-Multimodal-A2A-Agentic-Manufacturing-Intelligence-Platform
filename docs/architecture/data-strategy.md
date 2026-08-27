
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
```

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


# Dataset 2 Synthetic Component Lots — synthetic_component_lots.csv
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

# Dataset 3 — synthetic_machines.csv

| Column         | Description                          |
| :------------- | :----------------------------------- |
| `machine_id`   | Unique machine identifier.           |
| `machine_name` | Human-readable machine name.         |
| `machine_type` | Printer, placer, oven, AOI, etc.     |
| `line_id`      | SMT line identifier.                 |
| `manufacturer` | Synthetic equipment manufacturer.    |
| `model`        | Machine model.                       |
| `status`       | Running, idle, maintenance, offline. |
| `installed_at` | Installation date.                   |

## Examples

| machine_id      | machine_name   | machine_type         | line_id     | manufacturer | model   | status  | installed_at |
| :-------------- | :------------- | :------------------- | :---------- | :----------- | :------ | :------ | :----------- |
| MACH-PLACER-07  | PLACER-07      | Pick-and-Place       | SMT-LINE-03 | SynthMount   | PX-5000 | Running | 2024-02-10   |
| MACH-PRINTER-03 | PRINTER-03     | Solder Paste Printer | SMT-LINE-03 | PrintTech    | SP-800  | Running | 2024-02-10   |
| MACH-OVEN-03    | REFLOW-OVEN-03 | Reflow Oven          | SMT-LINE-03 | ThermoForge  | RF-12   | Running | 2024-02-11   |

# Dataset 4 — synthetic_nozzles.csv
| Column              | Description                |
| :------------------ | :------------------------- |
| `nozzle_id`         | Unique nozzle identity.    |
| `machine_id`        | Parent placer machine.     |
| `position`          | Machine nozzle position.   |
| `nozzle_type`       | Nozzle type.               |
| `last_cleaned_at`   | Last cleaning timestamp.   |
| `wear_level`        | Estimated wear percentage. |
| `inspection_status` | Normal, inspect, replace.  |
| `anomaly_flag`      | Synthetic scenario flag.   |


## Examples

| nozzle_id | machine_id     | position | nozzle_type | last_cleaned_at      | wear_level | inspection_status | anomaly_flag |
| :-------- | :------------- | :------- | :---------- | :------------------- | ---------: | :---------------- | :----------- |
| NOZ-07-01 | MACH-PLACER-07 | N01      | CN-040      | 2026-08-01T08:00:00Z |       12.0 | Normal            | No           |
| NOZ-07-02 | MACH-PLACER-07 | N02      | CN-040      | 2026-07-18T08:00:00Z |       24.0 | Normal            | No           |
| NOZ-07-03 | MACH-PLACER-07 | N03      | CN-040      | 2026-06-19T08:00:00Z |       67.0 | Inspect           | Yes          |

# Dataset 5 — synthetic_maintenance.csv

| Column                 | Description                                          |
| :--------------------- | :--------------------------------------------------- |
| `maintenance_id`       | Unique maintenance event.                            |
| `machine_id`           | Machine involved.                                    |
| `nozzle_id`            | Optional nozzle involved.                            |
| `action_type`          | Cleaning, inspection, replacement, calibration, etc. |
| `performed_by`         | Synthetic maintenance user.                          |
| `performed_at`         | Maintenance timestamp.                               |
| `notes`                | Technician observation.                              |
| `result`               | Maintenance result.                                  |
| `work_order_reference` | Associated work order if applicable.                 |

## Examples

| maintenance_id | machine_id     | nozzle_id | action_type | performed_by | performed_at         | notes                          | result  | work_order_reference |
| :------------- | :------------- | :-------- | :---------- | :----------- | :------------------- | :----------------------------- | :------ | :------------------- |
| MNT-1001       | MACH-PLACER-07 | NOZ-07-01 | Cleaning    | MECH-014     | 2026-08-01T08:00:00Z | Routine cleaning               | Pass    | WO-5001              |
| MNT-1002       | MACH-PLACER-07 | NOZ-07-02 | Inspection  | MECH-014     | 2026-07-18T08:00:00Z | Minor residue observed         | Pass    | WO-4977              |
| MNT-1003       | MACH-PLACER-07 | NOZ-07-03 | Inspection  | MECH-021     | 2026-06-19T08:00:00Z | Pickup force trending abnormal | Monitor | WO-4888              |



# Dataset 6 — synthetic_batches.csv
| Column             | Description                         |
| :----------------- | :---------------------------------- |
| `batch_id`         | Unique production batch identifier. |
| `product_id`       | Product being manufactured.         |
| `product_name`     | Product description.                |
| `product_revision` | Product revision.                   |
| `line_id`          | SMT production line.                |
| `started_at`       | Batch start time.                   |
| `completed_at`     | Batch completion time.              |
| `planned_quantity` | Planned production quantity.        |
| `actual_quantity`  | Actual boards produced.             |

## Examples

| batch_id | product_id | product_name         | product_revision | line_id     | started_at           | completed_at         | planned_quantity | actual_quantity |
| :------- | :--------- | :------------------- | :--------------- | :---------- | :------------------- | :------------------- | ---------------: | --------------: |
| B-24015  | ECU-2026   | ECU Controller Board | Rev-C            | SMT-LINE-03 | 2026-08-20T06:00:00Z | 2026-08-20T14:30:00Z |              800 |             796 |
| B-24016  | ECU-2026   | ECU Controller Board | Rev-C            | SMT-LINE-03 | 2026-08-21T06:10:00Z | 2026-08-21T14:40:00Z |              800 |             793 |
| B-24017  | ECU-2026   | ECU Controller Board | Rev-C            | SMT-LINE-03 | 2026-08-22T06:00:00Z | 2026-08-22T15:00:00Z |              800 |             789 |

# Dataset 7 — synthetic_boards.csv

| Column              | Description                     |
| :------------------ | :------------------------------ |
| `board_id`          | Unique internal board identity. |
| `serial`            | Physical PCB serial number.     |
| `batch_id`          | Manufacturing batch.            |
| `product_id`        | Product identity.               |
| `line_id`           | Production line.                |
| `manufactured_at`   | Board manufacturing timestamp.  |
| `inspection_status` | Pass, fail, review.             |

## Examples

| board_id      | serial        | batch_id | product_id | line_id     | manufactured_at      | inspection_status |
| :------------ | :------------ | :------- | :--------- | :---------- | :------------------- | :---------------- |
| BRD-24017-001 | ECU2608220001 | B-24017  | ECU-2026   | SMT-LINE-03 | 2026-08-22T08:14:20Z | Pass              |
| BRD-24017-002 | ECU2608220002 | B-24017  | ECU-2026   | SMT-LINE-03 | 2026-08-22T08:16:02Z | Review            |
| BRD-24017-003 | ECU2608220003 | B-24017  | ECU-2026   | SMT-LINE-03 | 2026-08-22T08:17:44Z | Review  

## Dataset 8 — synthetic_Production_telemetry.csv
| Column            | Description                             |
| :---------------- | :-------------------------------------- |
| `telemetry_id`    | Unique reading identity.                |
| `machine_id`      | Machine producing the reading.          |
| `batch_id`        | Batch being processed.                  |
| `timestamp`       | Reading time.                           |
| `parameter_name`  | Sensor/process parameter.               |
| `parameter_value` | Numeric measurement.                    |
| `unit`            | Measurement unit.                       |
| `nominal_min`     | Expected lower boundary.                |
| `nominal_max`     | Expected upper boundary.                |
| `anomaly_flag`    | Indicates intentionally seeded anomaly. |

## Examples

| telemetry_id | machine_id     | batch_id | timestamp            | parameter_name  | parameter_value | unit | nominal_min | nominal_max | anomaly_flag |
| :----------- | :------------- | :------- | :------------------- | :-------------- | --------------: | :--- | ----------: | ----------: | :----------- |
| TEL-7001     | MACH-PLACER-07 | B-24017  | 2026-08-22T08:10:00Z | placement_speed |            8200 | cph  |        7800 |        8500 | No           |
| TEL-7002     | MACH-PLACER-07 | B-24017  | 2026-08-22T08:16:00Z | placement_force |            2.91 | N    |        2.50 |        3.10 | No           |
| TEL-7003     | MACH-PLACER-07 | B-24017  | 2026-08-22T08:17:00Z | placement_force |            2.31 | N    |        2.50 |        3.10 | Yes          |

#  Dataset 9 — synthetic_defects.csv
| Column                       | Description                            |
| :--------------------------- | :------------------------------------- |
| `defect_id`                  | Unique defect identity.                |
| `board_id`                   | Affected board.                        |
| `inspection_image_reference` | Reference to inspection image.         |
| `defect_type`                | SMT defect category.                   |
| `source_system`              | AOI, SPI, ICT, manual inspection, etc. |
| `confidence`                 | Detection confidence.                  |
| `severity`                   | Defect severity.                       |
| `detected_at`                | Detection time.                        |
| `component_reference`        | PCB reference designator such as C17.  |
| `description`                | Human-readable defect description.     |

## Examples

| defect_id   | board_id      | inspection_image_reference | defect_type            | source_system | confidence | severity | detected_at          | component_reference | description                                      |
| :---------- | :------------ | :------------------------- | :--------------------- | :------------ | ---------: | :------- | :------------------- | :------------------ | :----------------------------------------------- |
| DEF-421-001 | BRD-24017-002 | IMG-24017-002-C17          | Component Misalignment | AOI           |       0.96 | Major    | 2026-08-22T08:18:10Z | C17                 | 10µF capacitor shifted toward board edge.        |
| DEF-421-002 | BRD-24017-003 | IMG-24017-003-C17          | Abnormal Solder Joint  | AOI           |       0.91 | Major    | 2026-08-22T08:19:55Z | C17                 | Solder fillet geometry outside expected profile. |
| DEF-421-003 | BRD-24017-005 | IMG-24017-005-C17          | Component Misalignment | AOI           |       0.89 | Major    | 2026-08-22T08:23:12Z | C17                 | Repeated lateral shift near C17.                 |

# Dataset 10 — synthetic_incidents.csv

| Column                 | Description                              |
| :--------------------- | :--------------------------------------- |
| `incident_id`          | Formal incident identifier.              |
| `title`                | Incident title.                          |
| `batch_id`             | Affected batch.                          |
| `primary_board_id`     | Main affected board.                     |
| `triggering_defect_id` | Defect that triggered the investigation. |
| `line_id`              | Production line.                         |
| `machine_id`           | Machine initially suspected or involved. |
| `status`               | Incident state.                          |
| `created_by`           | User creating the incident.              |
| `created_at`           | Incident creation time.                  |
| `description`          | Operator/engineer description.           |

## Examples

| incident_id         | title                    | batch_id | primary_board_id | triggering_defect_id | line_id     | machine_id     | status | created_by | created_at           | description                                                      |
| :------------------ | :----------------------- | :------- | :--------------- | :------------------- | :---------- | :------------- | :----- | :--------- | :------------------- | :--------------------------------------------------------------- |
| INCIDENT-2026-00419 | C17 placement deviation  | B-24015  | BRD-24015-014    | DEF-419-001          | SMT-LINE-03 | MACH-PLACER-07 | Closed | QE-001     | 2026-08-20T14:50:00Z | C17 placement shifted on isolated boards.                        |
| INCIDENT-2026-00420 | Reflow solder anomaly    | B-24016  | BRD-24016-027    | DEF-420-001          | SMT-LINE-03 | MACH-OVEN-03   | Closed | QE-001     | 2026-08-21T15:05:00Z | Abnormal solder formation detected after reflow.                 |
| INCIDENT-2026-00421 | C17 misalignment cluster | B-24017  | BRD-24017-002    | DEF-421-001          | SMT-LINE-03 | MACH-PLACER-07 | Open   | OP-014     | 2026-08-22T08:25:00Z | Several boards show C17 misalignment and abnormal solder joints. |





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



