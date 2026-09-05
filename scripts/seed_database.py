"""
Idempotent synthetic data seeder for ForgeSight AI.

Seeds users, products, lines, machines, nozzles, suppliers, component lots,
batches, boards, maintenance records, one complete incident
(INCIDENT-2026-00421), and production telemetry, per Phase 2's synthetic
data strategy and dependency order.

Usage:
    python scripts/seed_database.py

Idempotency: every insert checks for an existing row (by primary/natural
key) before inserting, so running this script multiple times never creates
duplicates.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from sqlmodel import select

from forgesight.api.security import hash_password
from forgesight.config.database import session_scope, create_db_and_tables
from forgesight.config.logging import get_logger
from forgesight.domain.models.investigation import Incident, IncidentStatus
from forgesight.domain.models.maintenance import MaintenanceRecord
from forgesight.domain.models.manufacturing import (
    Batch,
    Board,
    Feeder,
    Line,
    Machine,
    Nozzle,
    Product,
)
from forgesight.domain.models.supply_chain import Component, ComponentLot, Supplier
from forgesight.domain.models.telemetry import ProductionTelemetry
from forgesight.domain.models.users import User, UserRole

logger = get_logger(__name__)

TEST_PASSWORD = "ForgeSight!Test123"


async def seed_users(session) -> dict[UserRole, User]:
    """Seed one user per non-SysAdmin persona, plus one SysAdmin."""
    users_spec = [
        ("operator1", "operator1@forgesight.example", "Alex Operator", UserRole.PRODUCTION_OPERATOR),
        ("qe1", "qe1@forgesight.example", "Jordan QualityEngineer", UserRole.QUALITY_ENGINEER),
        ("mfgeng1", "mfgeng1@forgesight.example", "Sam ManufacturingEngineer", UserRole.MANUFACTURING_ENGINEER),
        ("mainteng1", "mainteng1@forgesight.example", "Riley MaintenanceEngineer", UserRole.MAINTENANCE_ENGINEER),
        ("qmgr1", "qmgr1@forgesight.example", "Casey QualityManager", UserRole.QUALITY_MANAGER),
        ("sqe1", "sqe1@forgesight.example", "Morgan SupplierQualityEngineer", UserRole.SUPPLIER_QUALITY_ENGINEER),
        ("sysadmin1", "sysadmin1@forgesight.example", "Taylor SysAdmin", UserRole.SYSTEM_ADMINISTRATOR),
    ]

    created: dict[UserRole, User] = {}
    for username, email, full_name, role in users_spec:
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(
                username=username,
                email=email,
                full_name=full_name,
                hashed_password=hash_password(TEST_PASSWORD),
                role=role,
            )
            session.add(user)
            await session.flush()
            logger.info("seed_user_created", extra={"username": username, "role": role.value})
        created[role] = user
    return created


async def seed_products(session) -> None:
    products = [
        ("ECU-2026", "ECU Controller Board"),
        ("BCM-2025", "Body Control Module"),
        ("ADAS-2026", "ADAS Sensor Board"),
    ]
    for product_id, name in products:
        result = await session.execute(select(Product).where(Product.product_id == product_id))
        if result.scalar_one_or_none() is None:
            session.add(Product(product_id=product_id, name=name))
            await session.flush()


async def seed_lines_and_machines(session) -> None:
    lines = ["SMT-LINE-03", "SMT-LINE-04"]
    for line_id in lines:
        result = await session.execute(select(Line).where(Line.line_id == line_id))
        if result.scalar_one_or_none() is None:
            session.add(Line(line_id=line_id, name=f"{line_id} Assembly Line"))
            await session.flush()

        for machine_suffix, machine_type in [
            (line_id.split("-")[-1], "placer"),
            ("PRINTER", "printer"),
            ("OVEN", "reflow_oven"),
        ]:
            machine_id = f"{machine_type.upper().split('_')[0]}-{line_id.split('-')[-1]}"
            result = await session.execute(select(Machine).where(Machine.machine_id == machine_id))
            if result.scalar_one_or_none() is None:
                session.add(Machine(machine_id=machine_id, line_id=line_id, machine_type=machine_type))
                await session.flush()

    # Ensure PLACER-07 exists explicitly (referenced by INCIDENT-2026-00421).
    result = await session.execute(select(Machine).where(Machine.machine_id == "PLACER-07"))
    if result.scalar_one_or_none() is None:
        session.add(Machine(machine_id="PLACER-07", line_id="SMT-LINE-03", machine_type="placer"))
        await session.flush()

    # Nozzles 1-5 on PLACER-07.
    for position in range(1, 6):
        nozzle_id = f"NZ-07-{position:02d}"
        result = await session.execute(select(Nozzle).where(Nozzle.nozzle_id == nozzle_id))
        if result.scalar_one_or_none() is None:
            session.add(Nozzle(nozzle_id=nozzle_id, machine_id="PLACER-07", position=position))
            await session.flush()


async def seed_suppliers_and_lots(session) -> None:
    suppliers = [("SUP-0042", "Acme Micro"), ("SUP-0091", "Delta Passive Components")]
    for supplier_id, name in suppliers:
        result = await session.execute(select(Supplier).where(Supplier.supplier_id == supplier_id))
        if result.scalar_one_or_none() is None:
            session.add(Supplier(supplier_id=supplier_id, name=name))
            await session.flush()

    components = [
        ("CAP-10UF-0603", "10uF Ceramic Capacitor, 0603"),
        ("RES-1K-0402", "1k Ohm Resistor, 0402"),
        ("IC-MCU-32PIN", "32-pin Microcontroller"),
    ]
    for part_number, description in components:
        result = await session.execute(select(Component).where(Component.part_number == part_number))
        if result.scalar_one_or_none() is None:
            session.add(Component(part_number=part_number, description=description))
            await session.flush()

    lots = [
        ("LOT-9921", "CAP-10UF-0603", "SUP-0042", 50, 2, 3, 1.8),
        ("LOT-8814", "RES-1K-0402", "SUP-0091", 50, 0, 3, 0.3),
        ("LOT-7702", "IC-MCU-32PIN", "SUP-0042", 32, 1, 2, 0.9),
    ]
    for lot_number, part_number, supplier_id, sample_size, defect_count, threshold, hist_rate in lots:
        result = await session.execute(select(ComponentLot).where(ComponentLot.lot_number == lot_number))
        if result.scalar_one_or_none() is None:
            session.add(
                ComponentLot(
                    lot_number=lot_number,
                    part_number=part_number,
                    supplier_id=supplier_id,
                    sample_size=sample_size,
                    defect_count=defect_count,
                    rejection_threshold=threshold,
                    disposition="accepted",
                    historical_defect_rate_pct=hist_rate,
                )
            )
            await session.flush()


async def seed_batches_and_boards(session) -> str:
    """Seed 10 batches with 50 boards distributed across them. Returns the
    board_id used for the seeded incident."""
    base_time = datetime.now(timezone.utc) - timedelta(days=30)
    target_board_id = "BRD-24017-00432"
    target_batch_id = "B-24017"

    batch_specs = [(f"B-2401{i}", "ECU-2026" if i % 2 == 0 else "BCM-2025", "SMT-LINE-03" if i % 2 == 0 else "SMT-LINE-04") for i in range(10)]
    # Force the batch referenced by the seeded incident to exist explicitly.
    batch_specs[7] = (target_batch_id, "ECU-2026", "SMT-LINE-03")

    board_counter = 0
    for idx, (batch_id, product_id, line_id) in enumerate(batch_specs):
        result = await session.execute(select(Batch).where(Batch.batch_id == batch_id))
        if result.scalar_one_or_none() is None:
            session.add(
                Batch(
                    batch_id=batch_id,
                    product_id=product_id,
                    line_id=line_id,
                    board_count=5,
                    started_at=base_time + timedelta(hours=idx * 4),
                    completed_at=base_time + timedelta(hours=idx * 4 + 3),
                )
            )
            await session.flush()

        for board_pos in range(1, 6):
            board_counter += 1
            if board_counter > 50:
                break
            if batch_id == target_batch_id and board_pos == 1:
                board_id = target_board_id
            else:
                board_id = f"BRD-{batch_id.split('-')[-1]}-{board_pos:05d}"
            serial_number = f"SN-{board_id}"

            result = await session.execute(select(Board).where(Board.board_id == board_id))
            if result.scalar_one_or_none() is None:
                session.add(
                    Board(
                        board_id=board_id,
                        batch_id=batch_id,
                        serial_number=serial_number,
                        position_in_batch=board_pos,
                    )
                )
                await session.flush()

    return target_board_id


async def seed_maintenance_records(session) -> None:
    now = datetime.now(timezone.utc)
    records = [
        ("PLACER-07", "NZ-07-01", now - timedelta(days=10), 0.02, "pass", "pass"),
        ("PLACER-07", "NZ-07-02", now - timedelta(days=20), 0.03, "pass", "pass"),
        ("PLACER-07", "NZ-07-03", now - timedelta(days=47), 0.06, "pass", "clean_recommended"),
    ]
    for machine_id, nozzle_id, last_cleaned, wear_mm, vacuum_result, disposition in records:
        # Idempotency check: skip if an identical record already exists for
        # this machine/nozzle/last_cleaned combination.
        result = await session.execute(
            select(MaintenanceRecord).where(
                MaintenanceRecord.machine_id == machine_id,
                MaintenanceRecord.nozzle_id == nozzle_id,
                MaintenanceRecord.last_cleaned == last_cleaned,
            )
        )
        if result.scalar_one_or_none() is None:
            session.add(
                MaintenanceRecord(
                    machine_id=machine_id,
                    nozzle_id=nozzle_id,
                    last_cleaned=last_cleaned,
                    wear_measurement_mm=wear_mm,
                    vacuum_test_result=vacuum_result,
                    disposition=disposition,
                )
            )
            await session.flush()


async def seed_incident(session, board_id: str, created_by_user: User) -> None:
    incident_id = "INCIDENT-2026-00421"
    result = await session.execute(select(Incident).where(Incident.incident_id == incident_id))
    if result.scalar_one_or_none() is None:
        session.add(
            Incident(
                incident_id=incident_id,
                board_id=board_id,
                batch_id="B-24017",
                line_id="SMT-LINE-03",
                product_id="ECU-2026",
                defect_type="component_misalignment",
                component_designator="C17",
                description=(
                    "Several boards from this batch appear to have a misaligned "
                    "component around C17 and the solder joint looks abnormal."
                ),
                status=IncidentStatus.IN_PROGRESS,
                current_stage=5,
                created_by=created_by_user.user_id,
            )
        )
        await session.flush()
        logger.info("seed_incident_created", extra={"incident_id": incident_id})


async def seed_telemetry(session) -> None:
    base_time = datetime.now(timezone.utc) - timedelta(hours=6)
    for i in range(10):
        recorded_at = base_time + timedelta(minutes=i * 5)
        result = await session.execute(
            select(ProductionTelemetry).where(
                ProductionTelemetry.machine_id == "PLACER-07",
                ProductionTelemetry.batch_id == "B-24017",
                ProductionTelemetry.recorded_at == recorded_at,
            )
        )
        if result.scalar_one_or_none() is None:
            session.add(
                ProductionTelemetry(
                    machine_id="PLACER-07",
                    batch_id="B-24017",
                    parameter="placement_head_pressure",
                    value=4.8 + (i * 0.01),
                    unit="bar",
                    recorded_at=recorded_at,
                )
            )
            await session.flush()


async def main() -> None:
    logger.info("seed_database_starting")
    await create_db_and_tables()

    async with session_scope() as session:
        users = await seed_users(session)
        await seed_products(session)
        await seed_lines_and_machines(session)
        await seed_suppliers_and_lots(session)
        target_board_id = await seed_batches_and_boards(session)
        await seed_maintenance_records(session)
        await seed_incident(session, target_board_id, users[UserRole.PRODUCTION_OPERATOR])
        await seed_telemetry(session)

    logger.info("seed_database_complete")


if __name__ == "__main__":
    asyncio.run(main())