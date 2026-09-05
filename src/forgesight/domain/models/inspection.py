"""Inspection domain models: InspectionImage, CvFinding.

CvFinding carries the full CV provenance schema required by Phase 3
(vision-architecture.md) — every field here is mandatory for evidence trust.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class InspectionImage(SQLModel, table=True):
    """A raw AOI/AXI inspection image captured for a board."""

    __tablename__ = "inspection_images"

    image_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    board_id: str = Field(foreign_key="boards.board_id", index=True)
    image_reference: str  # storage URI, e.g. s3://forgesight-images/...
    station_id: Optional[str] = None
    captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CvFinding(SQLModel, table=True):
    """A single CV-model-detected defect finding on an inspection image.

    Full provenance fields (Phase 3 requirement) are mandatory, not optional,
    so that every finding shown to a QE is independently verifiable.
    """

    __tablename__ = "cv_findings"

    cv_finding_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    image_id: uuid.UUID = Field(foreign_key="inspection_images.image_id", index=True)
    board_id: str = Field(foreign_key="boards.board_id", index=True)

    defect_type: str  # e.g. "component_misalignment"
    component_designator: Optional[str] = None  # e.g. "C17"
    confidence: float
    bounding_box: list[int] = Field(sa_column=Column(JSON))  # [x, y, w, h]

    raw_image_reference: str
    model_name: str
    model_version: str
    inference_timestamp: datetime
    dataset_used_for_training: Optional[str] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))