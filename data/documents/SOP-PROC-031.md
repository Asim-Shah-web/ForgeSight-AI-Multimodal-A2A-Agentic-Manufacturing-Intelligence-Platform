---
document_id: SOP-PROC-031
title: Reflow Oven Thermal Profile Verification
category: sop
version: v1.0
date: 2026-01-15
author: Manufacturing Engineering
approved_by: Manufacturing Engineer; Quality Manager
status: active
language: en
---

# SOP-PROC-031: Reflow Oven Thermal Profile Verification

## 1. Purpose

Defines the procedure for verifying reflow oven zone temperature profiles against the qualified process window, to prevent solder-related defects (cold solder joints, Head-in-Pillow, tombstoning, voids).

## 2. Scope

Applies to OVEN-01 and OVEN-02 servicing SMT-LINE-01 through SMT-LINE-04.

## 3. Referenced Standards

- J-STD-020 solder reflow profile guidelines (reference)
- SOP-QUAL-042 (Component Placement Alignment Inspection) — thermal-related placement effects

## 4. Qualified Profile Parameters (Lead-Free SAC305 Paste)

| Zone | Target Temperature | Acceptable Range | Notes |
| --- | --- | --- | --- |
| Zone 1 (Preheat) | 150°C | 140–160°C | Ramp rate ≤ 3°C/sec |
| Zone 2 (Soak) | 180°C | 170–190°C | Duration 60–120 sec |
| Zone 3 (Reflow) | 245°C | 235–255°C | Peak temperature, duration above liquidus 45–75 sec |
| Zone 4 (Cooling) | 100°C | 90–110°C | Controlled cooling rate ≤ 4°C/sec to prevent thermal shock |

A deviation of any zone beyond its acceptable range for more than 2 consecutive production hours is classified as a **reflow temperature deviation** and must be logged as a process anomaly.

## 5. Verification Procedure

1. Attach thermocouple profiling board at the start of shift and after any oven parameter change.
2. Run profiling board through the oven at production belt speed.
3. Record actual zone temperatures against the targets in Section 4.
4. If any zone falls outside its acceptable range, halt production on the affected line and notify the Manufacturing Engineer.
5. Log verification results: `oven_id`, `zone`, `measured_temp`, `target_temp`, `timestamp`, `disposition`.

## 6. Correlation with Investigation Workflow

At Stage 4 (Production & Telemetry Investigation), a Quality Engineer investigating solder-related defects (e.g. cold solder joints, Head-in-Pillow) should retrieve the most recent thermal profile verification for the oven associated with the affected batch. A documented Zone 4 cooling-rate deviation, for example, is relevant supporting evidence for a solder-joint-integrity hypothesis, but confirmation still requires cross-correlation with SPI/AOI evidence per Stage 8 (Evidence Correlation & Synthesis).

## 7. Related Records

- ReflowProfile records per production run
- ProductionTelemetry (zone temperature time series)
- Incident records referencing solder-related defect types

## 8. Revision History

| Version | Date | Change |
|---|---|---|
| v1.0 | 2026-01-15 | Initial release |
