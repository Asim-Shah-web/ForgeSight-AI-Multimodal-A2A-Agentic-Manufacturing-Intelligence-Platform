"""Telemetry domain models: ProductionTelemetry, ReflowProfile."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class ProductionTelemetry(SQLModel, table=True):
    """A single sensor/process-parameter reading tied to a machine and batch."""

    __tablename__ = "production_telemetry"

    telemetry_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    machine_id: str = Field(foreign_key="machines.machine_id", index=True)
    batch_id: str = Field(foreign_key="batches.batch_id", index=True)
    parameter: str  # e.g. "placement_head_pressure"
    value: float
    unit: str
    recorded_at: datetime = Field(index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReflowProfile(SQLModel, table=True):
    """A verified reflow oven thermal profile run, per SOP-PROC-031."""

    __tablename__ = "reflow_profiles"

    profile_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    machine_id: str = Field(foreign_key="machines.machine_id", index=True)
    batch_id: Optional[str] = Field(default=None, foreign_key="batches.batch_id")
    zone: str  # e.g. "Zone 3 - Reflow"
    measured_temp_c: float
    target_temp_c: float
    acceptable_range_low_c: float
    acceptable_range_high_c: float
    disposition: str = Field(default="pass")  # "pass" | "deviation"
    verified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))