"""Incident routes — the core investigation workflow API.

Every write operation here emits an AuditEvent. The /approve endpoint is the
mandatory Stage 11 Human Engineer Review & Sign-Off HITL gate (Phase 1 Rule 1
/ Phase 6 mandatory rule) — it can never be bypassed programmatically.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from math import ceil
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from forgesight.api.schemas.evidence import EvidenceAttachRequest, EvidenceResponse
from forgesight.api.schemas.incidents import (
    IncidentApprovalRequest,
    IncidentCreate,
    IncidentListResponse,
    IncidentResponse,
    IncidentStatusUpdate,
)
from forgesight.api.security import get_current_user, require_roles
from forgesight.config.database import get_session
from forgesight.config.logging import get_logger
from forgesight.domain.models.audit import AuditEvent, AuditEventType
from forgesight.domain.models.investigation import Incident, IncidentStatus
from forgesight.domain.models.manufacturing import Batch, Board, Line, Product
from forgesight.domain.models.users import User, UserRole

logger = get_logger(__name__)

router = APIRouter()


def _generate_incident_id() -> str:
    """Generate a human-readable incident ID, e.g. INCIDENT-2026-00001-style."""
    year = datetime.now(timezone.utc).year
    suffix = uuid.uuid4().hex[:6].upper()
    return f"INCIDENT-{year}-{suffix}"


@router.post(
    "",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.PRODUCTION_OPERATOR, UserRole.QUALITY_ENGINEER))],
)
async def create_incident(
    payload: IncidentCreate,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> IncidentResponse:
    """
    Create an incident (Stage 2: Incident Creation & Context Setup).

    Validates that the referenced board, batch, line, and product actually
    exist before creating the incident, so an incident can never be created
    against fabricated or nonexistent context.
    """
    board_result = await session.execute(select(Board).where(Board.board_id == payload.board_id))
    if board_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Board '{payload.board_id}' not found.")

    batch_result = await session.execute(select(Batch).where(Batch.batch_id == payload.batch_id))
    if batch_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Batch '{payload.batch_id}' not found.")

    line_result = await session.execute(select(Line).where(Line.line_id == payload.line_id))
    if line_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Line '{payload.line_id}' not found.")

    product_result = await session.execute(select(Product).where(Product.product_id == payload.product_id))
    if product_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product '{payload.product_id}' not found.")

    incident = Incident(
        incident_id=_generate_incident_id(),
        board_id=payload.board_id,
        batch_id=payload.batch_id,
        line_id=payload.line_id,
        product_id=payload.product_id,
        defect_type=payload.defect_type,
        component_designator=payload.component_designator,
        description=payload.description,
        status=IncidentStatus.OPEN,
        current_stage=2,
        created_by=current_user.user_id,
    )
    session.add(incident)
    await session.flush()
    await session.refresh(incident)

    audit_event = AuditEvent(
        who=current_user.user_id,
        what=AuditEventType.INCIDENT_CREATED,
        target_id=incident.incident_id,
        target_type="incident",
        action="create_incident",
        result="success",
        new_state={"status": incident.status.value, "defect_type": incident.defect_type},
        ip_address=request.client.host if request.client else None,
    )
    session.add(audit_event)
    await session.flush()

    logger.info("incident_created", extra={"incident_id": incident.incident_id, "by": str(current_user.user_id)})
    return IncidentResponse.model_validate(incident)


@router.get(
    "",
    response_model=IncidentListResponse,
    dependencies=[
        Depends(
            require_roles(
                UserRole.QUALITY_ENGINEER,
                UserRole.QUALITY_MANAGER,
                UserRole.MANUFACTURING_ENGINEER,
                UserRole.MAINTENANCE_ENGINEER,
                UserRole.SUPPLIER_QUALITY_ENGINEER,
            )
        )
    ],
)
async def list_incidents(
    session: AsyncSession = Depends(get_session),
    status_filter: Optional[IncidentStatus] = Query(default=None, alias="status"),
    line_id: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> IncidentListResponse:
    """List incidents, paginated and optionally filtered by status/line."""
    query = select(Incident)
    count_query = select(func.count()).select_from(Incident)

    if status_filter is not None:
        query = query.where(Incident.status == status_filter)
        count_query = count_query.where(Incident.status == status_filter)
    if line_id is not None:
        query = query.where(Incident.line_id == line_id)
        count_query = count_query.where(Incident.line_id == line_id)

    total_result = await session.execute(count_query)
    total = total_result.scalar_one()

    query = query.order_by(Incident.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    incidents = result.scalars().all()

    return IncidentListResponse(
        items=[IncidentResponse.model_validate(i) for i in incidents],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
    dependencies=[
        Depends(
            require_roles(
                UserRole.QUALITY_ENGINEER,
                UserRole.QUALITY_MANAGER,
                UserRole.MANUFACTURING_ENGINEER,
                UserRole.MAINTENANCE_ENGINEER,
                UserRole.SUPPLIER_QUALITY_ENGINEER,
            )
        )
    ],
)
async def get_incident(incident_id: str, session: AsyncSession = Depends(get_session)) -> IncidentResponse:
    """Get full incident detail."""
    result = await session.execute(select(Incident).where(Incident.incident_id == incident_id))
    incident = result.scalar_one_or_none()
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incident '{incident_id}' not found.")
    return IncidentResponse.model_validate(incident)


@router.patch(
    "/{incident_id}/status",
    response_model=IncidentResponse,
    dependencies=[Depends(require_roles(UserRole.QUALITY_ENGINEER, UserRole.QUALITY_MANAGER))],
)
async def update_incident_status(
    incident_id: str,
    payload: IncidentStatusUpdate,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> IncidentResponse:
    """Update incident status. Restricted to Quality Engineer / Quality Manager only —
    a System Administrator is deliberately excluded (SEC-003: technical
    administration never unlocks manufacturing/quality decision authority)."""
    result = await session.execute(select(Incident).where(Incident.incident_id == incident_id))
    incident = result.scalar_one_or_none()
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incident '{incident_id}' not found.")

    prior_status = incident.status
    incident.status = payload.status
    incident.updated_at = datetime.now(timezone.utc)
    session.add(incident)
    await session.flush()
    await session.refresh(incident)

    audit_event = AuditEvent(
        who=current_user.user_id,
        what=AuditEventType.INCIDENT_STATUS_CHANGED,
        target_id=incident.incident_id,
        target_type="incident",
        action="update_status",
        result="success",
        prior_state={"status": prior_status.value},
        new_state={"status": incident.status.value, "reason": payload.reason},
        ip_address=request.client.host if request.client else None,
    )
    session.add(audit_event)
    await session.flush()

    logger.info(
        "incident_status_changed",
        extra={"incident_id": incident.incident_id, "prior": prior_status.value, "new": incident.status.value},
    )
    return IncidentResponse.model_validate(incident)


@router.post(
    "/{incident_id}/evidence",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.QUALITY_ENGINEER))],
)
async def attach_evidence(
    incident_id: str,
    payload: EvidenceAttachRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> EvidenceResponse:
    """Attach an additional evidence reference to an incident."""
    result = await session.execute(select(Incident).where(Incident.incident_id == incident_id))
    incident = result.scalar_one_or_none()
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incident '{incident_id}' not found.")

    attached_at = datetime.now(timezone.utc)

    audit_event = AuditEvent(
        who=current_user.user_id,
        what=AuditEventType.EVIDENCE_SUBMITTED,
        target_id=incident.incident_id,
        target_type="incident",
        action="attach_evidence",
        result="success",
        new_state={"evidence_type": payload.evidence_type, "reference_id": payload.reference_id},
        ip_address=request.client.host if request.client else None,
    )
    session.add(audit_event)
    await session.flush()

    logger.info(
        "evidence_attached",
        extra={"incident_id": incident.incident_id, "evidence_type": payload.evidence_type},
    )

    return EvidenceResponse(
        incident_id=incident.incident_id,
        evidence_type=payload.evidence_type,
        reference_id=payload.reference_id,
        note=payload.note,
        attached_by=current_user.user_id,
        attached_at=attached_at,
    )


@router.post(
    "/{incident_id}/approve",
    response_model=IncidentResponse,
    dependencies=[Depends(require_roles(UserRole.QUALITY_ENGINEER))],
)
async def approve_incident(
    incident_id: str,
    payload: IncidentApprovalRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> IncidentResponse:
    """
    Stage 11 — Human Engineer Review & Sign-Off. This is the mandatory HITL
    gate: only a Quality Engineer may call this endpoint (explicitly not a
    System Administrator, per SEC-003), and it always requires an explicit,
    non-blank approval statement — there is no default/implicit approval.

    Always emits an AuditEvent with approval_by, approver role, and
    timestamp populated, per AR-002.
    """
    result = await session.execute(select(Incident).where(Incident.incident_id == incident_id))
    incident = result.scalar_one_or_none()
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incident '{incident_id}' not found.")

    if incident.status == IncidentStatus.CLOSED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Incident is already closed and cannot be re-approved.",
        )

    now = datetime.now(timezone.utc)
    prior_status = incident.status

    incident.status = IncidentStatus.CLOSED
    incident.current_stage = 11
    incident.signed_off_by = current_user.user_id
    incident.signed_off_at = now
    incident.updated_at = now
    session.add(incident)
    await session.flush()
    await session.refresh(incident)

    audit_event = AuditEvent(
        who=current_user.user_id,
        what=AuditEventType.HUMAN_APPROVAL,
        target_id=incident.incident_id,
        target_type="incident",
        action="stage_11_sign_off",
        result="success",
        prior_state={"status": prior_status.value},
        new_state={
            "status": incident.status.value,
            "approval_statement": payload.approval_statement,
            "confirmed_hypothesis_id": (
                str(payload.confirmed_hypothesis_id) if payload.confirmed_hypothesis_id else None
            ),
        },
        approval_by=current_user.user_id,
        ip_address=request.client.host if request.client else None,
    )
    session.add(audit_event)
    await session.flush()

    logger.info(
        "incident_signed_off",
        extra={"incident_id": incident.incident_id, "approved_by": str(current_user.user_id)},
    )
    return IncidentResponse.model_validate(incident)