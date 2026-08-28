---
document_id: SOP-MAINT-017
title: SMT Placer Nozzle Inspection & Replacement
category: sop
version: v1.0
date: 2026-01-15
author: Maintenance Engineering
approved_by: Maintenance Engineer; Quality Manager
status: active
language: en
---

# SOP-MAINT-017: SMT Placer Nozzle Inspection & Replacement

## 1. Purpose

Defines the inspection interval, wear thresholds, and replacement procedure for pick-and-place nozzles, to prevent placement defects (misalignment, tombstoning, dropped components) caused by nozzle degradation.

## 2. Scope

Applies to all nozzles installed on PLACER-05, PLACER-06, and PLACER-07 across SMT-LINE-01 through SMT-LINE-04.

## 3. Referenced Standards

- Machine OEM maintenance manual (Placer series, nozzle subsystem)
- SOP-QUAL-042 (Component Placement Alignment Inspection)

## 4. Nozzle Wear Thresholds

| Condition | Threshold | Action |
| --- | --- | --- |
| Nozzle tip wear (visual/optical measurement) | > 0.05 mm deviation from OEM spec | Schedule replacement within 24 hours |
| Vacuum pressure drop | > 15% below nominal at pickup | Immediate inspection, replace if wear confirmed |
| Days since last cleaning | > 30 days | Schedule cleaning; > 45 days without cleaning is a maintenance non-compliance flag |
| Placement defect correlation | Nozzle associated with > 1.5% component misalignment rate over trailing 500 placements | Immediate inspection and likely replacement |

## 5. Inspection Procedure

1. Remove nozzle from the placer head per OEM-specified release procedure.
2. Inspect tip under magnification for chipping, deformation, or debris buildup.
3. Measure tip diameter and compare against OEM tolerance.
4. Test vacuum seal integrity using the station's built-in pressure test cycle.
5. Record inspection result in the maintenance log: `nozzle_id`, `machine_id`, `inspection_date`, `wear_measurement`, `vacuum_test_result`, `disposition` (pass / clean / replace).

## 6. Replacement Procedure

1. Power down the placement head per machine safety lockout procedure.
2. Remove worn nozzle; install OEM-approved replacement nozzle of matching size class.
3. Run calibration cycle for the new nozzle.
4. Perform 20-board verification run; confirm placement accuracy is within SOP-QUAL-042 Section 4.2 tolerances before returning the machine to full production.
5. Log the replacement as a completed Work Order, referencing prior maintenance record and machine ID (e.g. PLACER-07).

## 7. Correlation with Investigation Workflow

When an incident (e.g. cluster of `component_misalignment` defects around a specific component designator such as C17) is under investigation at Stage 5 (Machine & Maintenance Check), the investigating Quality Engineer should retrieve the most recent maintenance record for the implicated machine and nozzle position. A nozzle overdue for cleaning or replacement per Section 4 thresholds is a relevant, but not sufficient, contributing factor — it must be considered alongside production telemetry and component lot evidence before ranking as a root-cause hypothesis.

## 8. Related Records

- MaintenanceRecord entries per nozzle/machine
- WorkOrder entries for replacement events
- SOP-QUAL-042 (verification tolerance reference)

## 9. Revision History

| Version | Date | Change |
|---|---|---|
| v1.0 | 2026-01-15 | Initial release |
