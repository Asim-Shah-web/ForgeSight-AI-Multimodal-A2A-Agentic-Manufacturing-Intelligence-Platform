"""Maintenance domain models: MaintenanceRecord, WorkOrder.

Per SOP-MAINT-017 (nozzle wear thresholds) and the Phase 2 domain model.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class WorkOrderStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MaintenanceRecord(SQLModel, table=True):
    """A maintenance/inspection record for a machine or nozzle."""

    __tablename__ = "maintenance_records"

    record_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    machine_id: str = Field(foreign_key="machines.machine_id", index=True)
    nozzle_id: Optional[str] = Field(default=None, foreign_key="nozzles.nozzle_id", index=True)
    last_cleaned: Optional[datetime] = None
    wear_measurement_mm: Optional[float] = None
    vacuum_test_result: Optional[str] = None  # "pass" | "fail"
    disposition: str  # "pass" | "clean_recommended" | "replace_recommended"
    inspected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def days_since_cleaning(self) -> Optional[int]:
        if self.last_cleaned is None:
            return None
        now = datetime.now(timezone.utc)
        last = self.last_cleaned
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        return (now - last).days


class WorkOrder(SQLModel, table=True):
    """A maintenance work order, created only after human approval of a
    MaintenanceRecord-derived recommendation (never auto-executed)."""

    __tablename__ = "work_orders"

    work_order_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    machine_id: str = Field(foreign_key="machines.machine_id", index=True)
    nozzle_id: Optional[str] = Field(default=None, foreign_key="nozzles.nozzle_id")
    source_record_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="maintenance_records.record_id"
    )
    description: str
    status: WorkOrderStatus = Field(default=WorkOrderStatus.OPEN)
    approved_by: Optional[uuid.UUID] = Field(default=None, foreign_key="users.user_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None