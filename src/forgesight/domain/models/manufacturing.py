"""Core manufacturing domain models: Product, Line, Batch, Board, Machine, Nozzle, Feeder.

Derived from docs/architecture/domain-model.md (Phase 2 conceptual schema).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class Product(SQLModel, table=True):
    """A manufactured product definition, e.g. ECU-2026."""

    __tablename__ = "products"

    product_id: str = Field(primary_key=True)  # e.g. "ECU-2026"
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Line(SQLModel, table=True):
    """A physical SMT production line, e.g. SMT-LINE-03."""

    __tablename__ = "lines"

    line_id: str = Field(primary_key=True)  # e.g. "SMT-LINE-03"
    name: str
    facility: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Machine(SQLModel, table=True):
    """A machine on a production line (placer, printer, reflow oven, etc.)."""

    __tablename__ = "machines"

    machine_id: str = Field(primary_key=True)  # e.g. "PLACER-07"
    line_id: str = Field(foreign_key="lines.line_id", index=True)
    machine_type: str  # "placer" | "printer" | "reflow_oven" | "aoi_station"
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    installed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Nozzle(SQLModel, table=True):
    """A pick-and-place nozzle installed on a placer machine."""

    __tablename__ = "nozzles"

    nozzle_id: str = Field(primary_key=True)  # e.g. "NZ-07-03"
    machine_id: str = Field(foreign_key="machines.machine_id", index=True)
    position: int
    size_class: Optional[str] = None
    installed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Feeder(SQLModel, table=True):
    """A component feeder installed on a placer machine."""

    __tablename__ = "feeders"

    feeder_id: str = Field(primary_key=True)
    machine_id: str = Field(foreign_key="machines.machine_id", index=True)
    slot_number: int
    part_number: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Batch(SQLModel, table=True):
    """A production batch of boards for a given product on a given line."""

    __tablename__ = "batches"

    batch_id: str = Field(primary_key=True)  # e.g. "B-24017"
    product_id: str = Field(foreign_key="products.product_id", index=True)
    line_id: str = Field(foreign_key="lines.line_id", index=True)
    board_count: int = Field(default=0)
    started_at: datetime
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Board(SQLModel, table=True):
    """An individual PCB board within a batch."""

    __tablename__ = "boards"

    board_id: str = Field(primary_key=True)  # e.g. "BRD-24017-00432"
    batch_id: str = Field(foreign_key="batches.batch_id", index=True)
    serial_number: str = Field(index=True, unique=True)
    position_in_batch: Optional[int] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))