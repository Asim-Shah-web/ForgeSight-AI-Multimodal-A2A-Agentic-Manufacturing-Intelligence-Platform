"""Request/response schemas for the vision/CV endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import ConfigDict
from sqlmodel import SQLModel


class CvFindingResponse(SQLModel):
    cv_finding_id: uuid.UUID
    image_id: uuid.UUID
    board_id: str
    defect_type: str
    component_designator: Optional[str] = None
    confidence: float
    bounding_box: list[int]
    raw_image_reference: str
    model_name: str
    model_version: str
    inference_timestamp: datetime
    dataset_used_for_training: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class InspectionImageResponse(SQLModel):
    image_id: uuid.UUID
    board_id: str
    image_reference: str
    station_id: Optional[str] = None
    captured_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InspectionResultResponse(SQLModel):
    inspection_image: InspectionImageResponse
    cv_findings: list[CvFindingResponse]
    findings_count: int