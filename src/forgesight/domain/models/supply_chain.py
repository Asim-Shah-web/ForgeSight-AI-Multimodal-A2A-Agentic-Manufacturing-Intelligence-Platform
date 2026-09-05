"""Supply chain domain models: Supplier, Component, ComponentLot.

CRITICAL: no field on these models may express or imply supplier fault.
Only observed statistics are stored here. Root-cause/SCAR attribution is a
human SQE decision recorded on RootCauseHypothesis / CorrectiveAction, never
on ComponentLot itself. See SOP-SUPP-008 Section 6.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class Supplier(SQLModel, table=True):
    """An approved component supplier."""

    __tablename__ = "suppliers"

    supplier_id: str = Field(primary_key=True)  # e.g. "SUP-0042"
    name: str
    approved: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Component(SQLModel, table=True):
    """A component part definition (not lot-specific)."""

    __tablename__ = "components"

    part_number: str = Field(primary_key=True)  # e.g. "CAP-10UF-0603"
    description: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ComponentLot(SQLModel, table=True):
    """A specific incoming lot of a component from a supplier.

    Only observed statistics are stored — never a fault/conclusion field.
    """

    __tablename__ = "component_lots"

    lot_number: str = Field(primary_key=True)  # e.g. "LOT-9921"
    part_number: str = Field(foreign_key="components.part_number", index=True)
    supplier_id: str = Field(foreign_key="suppliers.supplier_id", index=True)
    sample_size: Optional[int] = None
    defect_count: Optional[int] = None
    rejection_threshold: Optional[int] = None
    disposition: str = Field(default="accepted")  # "accepted" | "rejected" | "quarantined"
    historical_defect_rate_pct: Optional[float] = None
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))