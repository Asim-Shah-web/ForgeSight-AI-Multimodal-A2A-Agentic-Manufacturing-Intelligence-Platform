---
document_id: SOP-QUAL-042
title: Component Placement Alignment Inspection
category: sop
version: v1.0
date: 2026-01-15
author: Quality Engineering
approved_by: Quality Manager
status: active
language: en
---

# SOP-QUAL-042: Component Placement Alignment Inspection

## 1. Purpose

This procedure defines the inspection criteria and method for verifying component placement alignment on SMT assemblies following the Pick & Place and Reflow stages, in accordance with IPC-A-610 Class 3 requirements for high-reliability electronic assemblies.

## 2. Scope

Applies to all surface-mount components inspected via Automated Optical Inspection (AOI) on SMT-LINE-01 through SMT-LINE-04, including placement performed by PLACER-05, PLACER-06, and PLACER-07.

## 3. Referenced Standards

- IPC-A-610, Class 3 — Acceptability of Electronic Assemblies, Section 8 (Component Placement)
- Internal Document: SOP-PROC-031 (Reflow Oven Thermal Profile Verification)

## 4. Procedure

### 4.1 Pre-Inspection Setup

1. Confirm AOI station calibration is current (calibration record checked within the last 30 days).
2. Load the correct board program corresponding to the product/batch under inspection.
3. Confirm lighting and camera focus settings match the standard AOI profile for the board type.

### 4.2 Acceptance Criteria — Placement Alignment (IPC-A-610 Class 3)

| Component Type | Maximum Lateral Offset | Maximum Rotational Offset | Notes |
| --- | --- | --- | --- |
| Chip capacitors/resistors (0402–1210) | 25% of component width or 0.2 mm, whichever is smaller | 5° | Applies to components such as C17 (10µF capacitor) |
| SOIC/QFP packages | 20% of lead width | 5° | Measured lead-to-pad overlap |
| BGA packages | No visible solder ball bridging; ≤ 0.1 mm centroid offset | N/A | Requires X-ray verification if AOI flags an anomaly |

A component exceeding these thresholds is classified as a **placement misalignment defect** and must be logged in ForgeSight with defect type `component_misalignment`, referencing the affected component designator (e.g. C17), board serial, and batch ID.

### 4.3 Inspection Steps

1. Run AOI scan across the full board.
2. Review all flagged components exceeding the thresholds in Section 4.2.
3. For each flagged component, capture the AOI image, bounding box, and confidence score as `CvFinding` evidence.
4. Cross-reference the batch and machine (e.g. PLACER-07) associated with the flagged board.
5. If misalignment frequency for a single component designator exceeds 2% of boards in a batch, escalate to Stage 2 (Incident Creation) per the incident workflow.

## 5. Disposition

- **Pass**: within tolerance, no further action.
- **Reject/Rework**: exceeds tolerance — board is routed to rework per SOP-QUAL-055 (Defect Containment & Batch Hold Procedure) if the defect rate crosses the batch hold threshold.

## 6. Related Records

- CvFinding records (AOI evidence)
- Incident records referencing `defect_type = component_misalignment`
- SOP-QUAL-055 (Defect Containment & Batch Hold Procedure)
- SOP-MAINT-017 (if misalignment is suspected to originate from placer nozzle wear)

## 7. Revision History

| Version | Date | Change |
|---|---|---|
| v1.0 | 2026-01-15 | Initial release |
