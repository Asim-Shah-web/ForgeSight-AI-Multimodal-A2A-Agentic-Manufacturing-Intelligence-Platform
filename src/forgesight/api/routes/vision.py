"""
Vision / CV routes — Stage 3 (Visual Evidence Extraction) API surface.

POST /inspect never creates or modifies an Incident, and never authorizes
any manufacturing action by itself — it only produces evidence rows that a
human later attaches to an incident via the existing
POST /incidents/{incident_id}/evidence endpoint.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from forgesight.api.schemas.vision import (
    CvFindingResponse,
    InspectionImageResponse,
    InspectionResultResponse,
)
from forgesight.api.security import get_current_user, require_roles
from forgesight.config.database import get_session
from forgesight.config.logging import get_logger
from forgesight.config.settings import settings
from forgesight.domain.models.audit import AuditEvent, AuditEventType
from forgesight.domain.models.inspection import CvFinding
from forgesight.domain.models.users import User, UserRole
from forgesight.vision.service import BoardNotFoundError, process_inspection_image
from forgesight.vision.storage import InvalidUploadError
from forgesight.vision.inference import InvalidImageError

logger = get_logger(__name__)

router = APIRouter()

_EVIDENCE_SUBMIT_ROLES = (UserRole.PRODUCTION_OPERATOR, UserRole.QUALITY_ENGINEER)
_QUALITY_ROLES = (
    UserRole.QUALITY_ENGINEER,
    UserRole.MANUFACTURING_ENGINEER,
    UserRole.MAINTENANCE_ENGINEER,
    UserRole.QUALITY_MANAGER,
    UserRole.SUPPLIER_QUALITY_ENGINEER,
)


@router.post(
    "/boards/{board_id}/inspect",
    response_model=InspectionResultResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(*_EVIDENCE_SUBMIT_ROLES))],
)
async def inspect_board_image(
    board_id: str,
    request: Request,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> InspectionResultResponse:
    """
    Upload an AOI inspection image for a board and run CV inference on it.

    Returns the created InspectionImage and every CvFinding above
    settings.cv_confidence_threshold. An empty findings list is a valid,
    expected outcome (no defect detected above threshold) — never treated
    as an error.
    """
    file_bytes = await file.read()
    content_type = file.content_type or "application/octet-stream"

    try:
        inspection_image, cv_findings = await process_inspection_image(
            session, board_id=board_id, file_bytes=file_bytes, content_type=content_type
        )
    except BoardNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidUploadError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except InvalidImageError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    evidence_audit_event = AuditEvent(
        who=current_user.user_id,
        what=AuditEventType.EVIDENCE_SUBMITTED,
        target_id=str(inspection_image.image_id),
        target_type="inspection_image",
        action="upload_inspection_image",
        result="success",
        new_state={"board_id": board_id, "image_reference": inspection_image.image_reference},
        ip_address=request.client.host if request.client else None,
    )
    session.add(evidence_audit_event)

    cv_execution_audit_event = AuditEvent(
        who=current_user.user_id,
        what=AuditEventType.CV_EXECUTION,
        target_id=",".join(str(f.cv_finding_id) for f in cv_findings) or None,
        target_type="cv_finding",
        action="run_cv_inference",
        result="success",
        new_state={
            "board_id": board_id,
            "image_id": str(inspection_image.image_id),
            "findings_count": len(cv_findings),
        },
        ai_version=settings.cv_model_version,
        evidence_version=settings.cv_dataset_used_for_training,
        ip_address=request.client.host if request.client else None,
    )
    session.add(cv_execution_audit_event)
    await session.flush()

    logger.info(
        "inspection_completed",
        extra={"board_id": board_id, "findings_count": len(cv_findings), "by": str(current_user.user_id)},
    )

    return InspectionResultResponse(
        inspection_image=InspectionImageResponse.model_validate(inspection_image),
        cv_findings=[CvFindingResponse.model_validate(f) for f in cv_findings],
        findings_count=len(cv_findings),
    )


@router.get(
    "/boards/{board_id}/findings",
    response_model=list[CvFindingResponse],
    dependencies=[Depends(require_roles(*_QUALITY_ROLES))],
)
async def get_board_findings(
    board_id: str, session: AsyncSession = Depends(get_session)
) -> list[CvFindingResponse]:
    """Returns all CvFinding rows for a board (satisfies the Phase 5
    get_board_inspection_data MCP tool's data shape)."""
    result = await session.execute(select(CvFinding).where(CvFinding.board_id == board_id))
    findings = result.scalars().all()
    return [CvFindingResponse.model_validate(f) for f in findings]


@router.get(
    "/findings/{cv_finding_id}",
    response_model=CvFindingResponse,
    dependencies=[Depends(require_roles(*_QUALITY_ROLES))],
)
async def get_finding(
    cv_finding_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> CvFindingResponse:
    """Returns a single CvFinding with full provenance. 404 if not found."""
    result = await session.execute(select(CvFinding).where(CvFinding.cv_finding_id == cv_finding_id))
    finding = result.scalar_one_or_none()
    if finding is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"CvFinding '{cv_finding_id}' not found."
        )
    return CvFindingResponse.model_validate(finding)