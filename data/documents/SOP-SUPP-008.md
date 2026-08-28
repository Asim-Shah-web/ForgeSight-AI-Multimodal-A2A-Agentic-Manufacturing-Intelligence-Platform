---
document_id: SOP-SUPP-008
title: Incoming Component Lot Inspection
category: sop
version: v1.0
date: 2026-01-15
author: Supplier Quality Engineering
approved_by: Quality Manager
status: active
language: en
---

# SOP-SUPP-008: Incoming Component Lot Inspection

## 1. Purpose

Defines the incoming inspection sampling plan and rejection criteria for component lots received from approved suppliers, to prevent defective components from entering production.

## 2. Scope

Applies to all passive and active components received under a `ComponentLot` record, prior to release for use on SMT-LINE-01 through SMT-LINE-04.

## 3. Referenced Standards

- ANSI/ASQ Z1.4 sampling plan (reference, General Inspection Level II)
- IPC-A-610 Class 3 component acceptance criteria

## 4. Sampling Plan

| Lot Size | Sample Size | Acceptance Number | Rejection Number |
| --- | --- | --- | --- |
| 501–1,200 units | 32 | 1 | 2 |
| 1,201–3,200 units | 50 | 2 | 3 |
| 3,201–10,000 units | 80 | 3 | 4 |

Sample units are inspected for: dimensional conformance, marking/polarity correctness, visible damage, and moisture-sensitive-level (MSL) packaging integrity.

## 5. Rejection Criteria

A component lot is **rejected** if:

- Defect count in the sample meets or exceeds the rejection number in Section 4, or
- Any single unit shows evidence of counterfeit markings, or
- MSL packaging is compromised (broken seal, missing desiccant/humidity indicator card showing exposure).

A rejected lot is quarantined and a Supplier Corrective Action Request (SCAR) may be initiated **only after SQE review**, per the supplier safety rule below.

## 6. Supplier Attribution Rule (Mandatory)

Statistical correlation between a `ComponentLot` and an elevated defect rate on the production line is **not**, by itself, sufficient grounds to attribute root cause to the supplier or the lot. Before a SCAR is initiated:

1. Internal SMT process variables (placement, reflow, nozzle condition) must be evaluated and reasonably excluded per Stages 4–7 of the investigation workflow.
2. Physical verification of the suspect component (e.g. cross-section, X-ray, or electrical test) should be performed where feasible.
3. Historical defect delta for the same lot/supplier across other batches should be reviewed.

Only a human Supplier Quality Engineer may confirm supplier root cause and approve a SCAR.

## 7. Correlation with Investigation Workflow

At Stage 6 (Component Lot & Supplier Correlation), retrieved lot inspection records for the implicated `ComponentLot` (e.g. lot 9921) should be attached as evidence. Any elevated defect frequency for that lot is reported as a correlation, using the mandated wording: *"the available evidence indicates a correlation... additional evidence is required before attributing root cause to the supplier."*

## 8. Related Records

- ComponentLot records
- Supplier records
- Incoming inspection results
- SCAR records (created only after SQE approval)

## 9. Revision History

| Version | Date | Change |
|---|---|---|
| v1.0 | 2026-01-15 | Initial release |
