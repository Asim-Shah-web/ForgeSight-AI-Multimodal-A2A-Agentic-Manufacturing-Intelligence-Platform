---
document_id: SOP-QUAL-055
title: Defect Containment & Batch Hold Procedure
category: sop
version: v1.0
date: 2026-01-15
author: Quality Engineering
approved_by: Quality Manager
status: active
language: en
---

# SOP-QUAL-055: Defect Containment & Batch Hold Procedure

## 1. Purpose

Defines the triggers and steps for placing a batch on quality hold when defect rates exceed acceptable thresholds, to contain nonconforming product before it advances further in the production flow.

## 2. Scope

Applies to all batches in-process or awaiting shipment on SMT-LINE-01 through SMT-LINE-04.

## 3. Referenced Standards

- Internal traceability requirements (ISO 9001, Clause 8.5.2 — Identification and Traceability, reference)
- SOP-QUAL-042 (Component Placement Alignment Inspection)

## 4. Batch Hold Triggers

| Condition | Threshold |
|---|---|
| Single defect type frequency in batch | > 2% of boards inspected |
| Cluster of defects around a single component designator | > 3 boards affected within the same batch |
| Supplier lot correlation (pending SQE review) | Elevated defect rate coincides with a single ComponentLot across ≥ 2 batches |
| Reflow/process deviation confirmed | Any Zone deviation per SOP-PROC-031 lasting > 2 hours during the batch's production window |

Any one trigger is sufficient to initiate a **quality hold recommendation**; final hold approval authority sits with the Quality Engineer (standard hold) or Quality Manager (high-risk/high-volume hold), per the persona authorization model.

## 5. Containment Procedure

1. Flag the batch as `on_hold` in the MES and ForgeSight incident record.
2. Segregate physically-identifiable affected boards from unaffected inventory.
3. Notify Production Operator(s) on the affected line to pause further processing of the batch pending disposition.
4. Open (or update) the corresponding Incident record, referencing Stage 2 (Incident Creation & Context Setup) of the investigation workflow.
5. Proceed through Stages 3–9 of the investigation workflow to establish and rank root-cause hypotheses before disposition.

## 6. Disposition Options

- **Release**: root cause identified and confirmed contained; hold lifted with Quality Engineer sign-off.
- **Rework**: affected boards routed to rework per applicable process SOP.
- **Scrap**: nonconforming boards beyond economical rework, disposed per scrap procedure (out of scope for this SOP).
- **Escalate**: high-risk or high-volume holds are escalated to the Quality Manager for `APPROVE_HIGH_RISK_HOLD`.

## 7. Correlation with Investigation Workflow

This SOP governs the containment action that typically follows Stage 9 (Root-Cause Hypothesis Ranking) and precedes or accompanies Stage 10 (Corrective Action Recommendation). It is retrieved as evidence whenever an investigation confirms a hold-triggering condition, so the QE can reference the exact threshold that justified containment.

## 8. Related Records

- Incident records
- Batch/Board hold status
- AuditEvent for hold placement/lift actions

## 9. Revision History

| Version | Date | Change |
|---|---|---|
| v1.0 | 2026-01-15 | Initial release |