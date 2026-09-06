"""
Orchestration layer: upload -> inference -> persistence.

This module produces evidence rows only (InspectionImage, CvFinding). It
never creates or modifies an Incident — linking evidence to an incident
remains a human/operator action via the existing
POST /incidents/{incident_id}/evidence endpoint (Phase 7), referencing the
cv_finding_id values returned here.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from forgesight.config.logging import get_logger
from forgesight.config.settings import settings
from forgesight.domain.models.inspection import CvFinding, InspectionImage
from forgesight.domain.models.manufacturing import Board
from forgesight.vision.inference import run_inference
from forgesight.vision.storage import save_uploaded_image

logger = get_logger(__name__)


class BoardNotFoundError(Exception):
    """Raised when the referenced board_id does not exist."""


async def process_inspection_image(
    session: AsyncSession,
    board_id: str,
    file_bytes: bytes,
    content_type: str,
    station_id: Optional[str] = None,
) -> tuple[InspectionImage, list[CvFinding]]:
    """
    Full Stage 3 (Visual Evidence Extraction) pipeline for a single image:
    validate board -> save image -> run inference -> persist CvFinding rows.

    Every CvFinding is created with full provenance and the exact
    dataset_used_for_training disclosure from configuration, so no consumer
    of this evidence can mistake it for a production-validated detector
    unless config/vision/vision.yaml has actually been updated to reflect one.
    """
    board_result = await session.execute(select(Board).where(Board.board_id == board_id))
    if board_result.scalar_one_or_none() is None:
        raise BoardNotFoundError(f"Board '{board_id}' not found.")

    image_reference = await save_uploaded_image(board_id, file_bytes, content_type)

    inspection_image = InspectionImage(
        board_id=board_id,
        image_reference=image_reference,
        station_id=station_id,
    )
    session.add(inspection_image)
    await session.flush()
    await session.refresh(inspection_image)

    detections = await run_inference(image_reference)
    inference_timestamp = datetime.now(timezone.utc)

    cv_findings: list[CvFinding] = []
    for detection in detections:
        cv_finding = CvFinding(
            image_id=inspection_image.image_id,
            board_id=board_id,
            defect_type=detection.defect_type,
            confidence=detection.confidence,
            bounding_box=detection.bounding_box,
            raw_image_reference=image_reference,
            model_name=settings.cv_model_name,
            model_version=settings.cv_model_version,
            inference_timestamp=inference_timestamp,
            dataset_used_for_training=settings.cv_dataset_used_for_training,
        )
        session.add(cv_finding)
        cv_findings.append(cv_finding)

    if cv_findings:
        await session.flush()
        for finding in cv_findings:
            await session.refresh(finding)

    logger.info(
        "inspection_image_processed",
        extra={
            "board_id": board_id,
            "image_id": str(inspection_image.image_id),
            "findings_count": len(cv_findings),
            "model_version": settings.cv_model_version,
        },
    )
    return inspection_image, cv_findings