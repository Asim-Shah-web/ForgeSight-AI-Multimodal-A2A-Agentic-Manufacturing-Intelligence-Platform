"""
Manufacturing MCP Server — implements the 5 tools specified in
docs/architecture/mcp-architecture.md Section 2 and
mcp_servers/manufacturing/README.md, exactly.

Each tool: resolves the caller from caller_token, checks RBAC, executes
against the real database via forgesight's existing domain models, records
an audit event, and returns the exact JSON shape documented in Phase 5.

High-risk tools (execute_batch_hold, modify_machine_parameters) are
deliberately NOT registered here — see Phase 5 Section 5.2.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from mcp.server import Server
import mcp.types as types
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from forgesight.config.database import AsyncSessionFactory
from forgesight.config.logging import get_logger
from forgesight.domain.models.inspection import CvFinding, InspectionImage
from forgesight.domain.models.maintenance import MaintenanceRecord
from forgesight.domain.models.manufacturing import Board, Machine, Nozzle
from forgesight.domain.models.supply_chain import Component, ComponentLot, Supplier
from forgesight.domain.models.telemetry import ProductionTelemetry
from forgesight.domain.models.users import User

from mcp_servers.shared.audit import compute_result_hash, record_tool_invocation
from mcp_servers.shared.auth import McpAuthenticationError, McpPermissionError, check_tool_permission, resolve_caller

logger = get_logger(__name__)

server = Server("forgesight-manufacturing")


# ---------------------------------------------------------------------------
# Tool definitions (list_tools) — Phase 5 Section 2 input schemas
# ---------------------------------------------------------------------------

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_board_inspection_data",
            description="Retrieve raw board-level AOI inspection detail (Stage 2/3 evidence).",
            inputSchema={
                "type": "object",
                "properties": {
                    "caller_token": {"type": "string"},
                    "board_id": {"type": "string"},
                },
                "required": ["caller_token", "board_id"],
            },
        ),
        types.Tool(
            name="get_production_telemetry",
            description="Retrieve time-series sensor/process data for a machine/batch window (Stage 4).",
            inputSchema={
                "type": "object",
                "properties": {
                    "caller_token": {"type": "string"},
                    "machine_id": {"type": "string"},
                    "batch_id": {"type": "string"},
                    "start_time": {"type": "string", "description": "ISO 8601 UTC"},
                    "end_time": {"type": "string", "description": "ISO 8601 UTC"},
                },
                "required": ["caller_token", "machine_id", "batch_id", "start_time", "end_time"],
            },
        ),
        types.Tool(
            name="get_machine_maintenance_history",
            description="Retrieve maintenance/nozzle wear history for a machine (Stage 5).",
            inputSchema={
                "type": "object",
                "properties": {
                    "caller_token": {"type": "string"},
                    "machine_id": {"type": "string"},
                    "nozzle_id": {"type": ["string", "null"], "default": None},
                },
                "required": ["caller_token", "machine_id"],
            },
        ),
        types.Tool(
            name="get_component_lot_history",
            description="Retrieve lot genealogy, supplier linkage, and incoming inspection stats (Stage 6). "
                        "Never returns a fault/root-cause field.",
            inputSchema={
                "type": "object",
                "properties": {
                    "caller_token": {"type": "string"},
                    "lot_number": {"type": "string"},
                    "part_number": {"type": "string"},
                },
                "required": ["caller_token", "lot_number", "part_number"],
            },
        ),
        types.Tool(
            name="recommend_preventative_maintenance",
            description="Generate a pending maintenance recommendation from investigation evidence. "
                        "Always returns a PendingApprovalRequest; never creates a WorkOrder directly.",
            inputSchema={
                "type": "object",
                "properties": {
                    "caller_token": {"type": "string"},
                    "machine_id": {"type": "string"},
                    "nozzle_id": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["caller_token", "machine_id", "nozzle_id", "reason"],
            },
        ),
    ]


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    async with AsyncSessionFactory() as session:
        try:
            result = await _dispatch(session, name, arguments)
            await session.commit()
            return [types.TextContent(type="text", text=json.dumps(result))]
        except McpAuthenticationError as exc:
            await session.rollback()
            await _record(session, None, name, arguments, "error:AUTHENTICATION_FAILED")
            return [_error_response("AUTHENTICATION_FAILED", str(exc))]
        except McpPermissionError as exc:
            await session.rollback()
            user = await _try_resolve(session, arguments)
            await _record(session, user, name, arguments, "error:PERMISSION_DENIED")
            return [_error_response("PERMISSION_DENIED", str(exc))]
        except _ToolError as exc:
            await session.rollback()
            user = await _try_resolve(session, arguments)
            await _record(session, user, name, arguments, f"error:{exc.code}")
            return [_error_response(exc.code, str(exc))]


class _ToolError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


def _error_response(code: str, message: str) -> types.TextContent:
    return types.TextContent(type="text", text=json.dumps({"error_code": code, "detail": message}))


async def _try_resolve(session: AsyncSession, arguments: dict) -> Optional[User]:
    token = arguments.get("caller_token")
    if not token:
        return None
    try:
        return await resolve_caller(token, session)
    except McpAuthenticationError:
        return None


async def _record(
    session: AsyncSession, user: Optional[User], tool_name: str, arguments: dict, result: str, output: Any = None
) -> None:
    result_hash = compute_result_hash(output) if output is not None else None
    await record_tool_invocation(session, user, tool_name, arguments, result, result_hash=result_hash)
    await session.commit()


async def _dispatch(session: AsyncSession, name: str, arguments: dict) -> dict:
    caller_token = arguments.get("caller_token", "")
    user = await resolve_caller(caller_token, session)

    if name == "get_board_inspection_data":
        check_tool_permission(user.role, "evidence:read")
        result = await _get_board_inspection_data(session, arguments["board_id"])
    elif name == "get_production_telemetry":
        check_tool_permission(user.role, "evidence:read")
        result = await _get_production_telemetry(
            session, arguments["machine_id"], arguments["batch_id"], arguments["start_time"], arguments["end_time"]
        )
    elif name == "get_machine_maintenance_history":
        check_tool_permission(user.role, "maintenance:read")
        result = await _get_machine_maintenance_history(
            session, arguments["machine_id"], arguments.get("nozzle_id")
        )
    elif name == "get_component_lot_history":
        check_tool_permission(user.role, "component_lot:read")
        result = await _get_component_lot_history(session, arguments["lot_number"], arguments["part_number"])
    elif name == "recommend_preventative_maintenance":
        check_tool_permission(user.role, "maintenance:recommend")
        result = await _recommend_preventative_maintenance(
            session, arguments["machine_id"], arguments["nozzle_id"], arguments["reason"]
        )
    else:
        raise _ToolError("UNKNOWN_TOOL", f"Tool '{name}' is not registered on this server.")

    await _record(session, user, name, arguments, "success" if name != "recommend_preventative_maintenance" else "pending_approval", output=result)
    return result


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

async def _get_board_inspection_data(session: AsyncSession, board_id: str) -> dict:
    board_result = await session.execute(select(Board).where(Board.board_id == board_id))
    board = board_result.scalar_one_or_none()
    if board is None:
        raise _ToolError("BOARD_NOT_FOUND", f"No record for board_id '{board_id}'.")

    images_result = await session.execute(select(InspectionImage).where(InspectionImage.board_id == board_id))
    images = images_result.scalars().all()

    findings_result = await session.execute(select(CvFinding).where(CvFinding.board_id == board_id))
    findings = findings_result.scalars().all()

    aoi_flags = [
        {
            "component_designator": f.component_designator,
            "defect_type": f.defect_type,
            "confidence": f.confidence,
            "bounding_box": f.bounding_box,
            "image_reference": f.raw_image_reference,
            "cv_finding_id": str(f.cv_finding_id),
        }
        for f in findings
    ]

    return {
        "board_id": board.board_id,
        "batch_id": board.batch_id,
        "aoi_flags": aoi_flags,
        "inspection_timestamp": images[0].captured_at.isoformat() if images else None,
        "source_system": "InspectionDB",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }


async def _get_production_telemetry(
    session: AsyncSession, machine_id: str, batch_id: str, start_time: str, end_time: str
) -> dict:
    machine_result = await session.execute(select(Machine).where(Machine.machine_id == machine_id))
    if machine_result.scalar_one_or_none() is None:
        raise _ToolError("MACHINE_NOT_FOUND", f"No machine '{machine_id}'.")

    try:
        start_dt = datetime.fromisoformat(start_time)
        end_dt = datetime.fromisoformat(end_time)
    except ValueError as exc:
        raise _ToolError("INVALID_TIME_RANGE", f"Could not parse start_time/end_time: {exc}") from exc

    if start_dt >= end_dt:
        raise _ToolError("INVALID_TIME_RANGE", "start_time must be before end_time.")

    telemetry_result = await session.execute(
        select(ProductionTelemetry).where(
            ProductionTelemetry.machine_id == machine_id,
            ProductionTelemetry.batch_id == batch_id,
            ProductionTelemetry.recorded_at >= start_dt,
            ProductionTelemetry.recorded_at <= end_dt,
        )
    )
    readings = telemetry_result.scalars().all()

    if not readings:
        raise _ToolError("NO_TELEMETRY_IN_WINDOW", "No telemetry found in the given range.")

    return {
        "machine_id": machine_id,
        "batch_id": batch_id,
        "telemetry": [
            {"timestamp": r.recorded_at.isoformat(), "parameter": r.parameter, "value": r.value, "unit": r.unit}
            for r in readings
        ],
        "source_system": "MES",
        "data_snapshot_timestamp": datetime.now(timezone.utc).isoformat(),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }


async def _get_machine_maintenance_history(
    session: AsyncSession, machine_id: str, nozzle_id: Optional[str]
) -> dict:
    machine_result = await session.execute(select(Machine).where(Machine.machine_id == machine_id))
    if machine_result.scalar_one_or_none() is None:
        raise _ToolError("MACHINE_NOT_FOUND", f"No machine '{machine_id}'.")

    if nozzle_id is not None:
        nozzle_result = await session.execute(select(Nozzle).where(Nozzle.nozzle_id == nozzle_id))
        if nozzle_result.scalar_one_or_none() is None:
            raise _ToolError("NOZZLE_NOT_FOUND", f"No nozzle '{nozzle_id}' on machine '{machine_id}'.")

    query = select(MaintenanceRecord).where(MaintenanceRecord.machine_id == machine_id)
    if nozzle_id is not None:
        query = query.where(MaintenanceRecord.nozzle_id == nozzle_id)
    records_result = await session.execute(query)
    records = records_result.scalars().all()

    return {
        "machine_id": machine_id,
        "maintenance_records": [
            {
                "record_id": str(r.record_id),
                "nozzle_id": r.nozzle_id,
                "last_cleaned": r.last_cleaned.isoformat() if r.last_cleaned else None,
                "days_since_cleaning": r.days_since_cleaning,
                "wear_measurement_mm": r.wear_measurement_mm,
                "vacuum_test_result": r.vacuum_test_result,
                "disposition": r.disposition,
            }
            for r in records
        ],
        "source_system": "CMMS",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }


async def _get_component_lot_history(session: AsyncSession, lot_number: str, part_number: str) -> dict:
    lot_result = await session.execute(
        select(ComponentLot).where(
            ComponentLot.lot_number == lot_number, ComponentLot.part_number == part_number
        )
    )
    lot = lot_result.scalar_one_or_none()
    if lot is None:
        raise _ToolError("LOT_NOT_FOUND", f"No lot '{lot_number}' for part '{part_number}'.")

    supplier_result = await session.execute(select(Supplier).where(Supplier.supplier_id == lot.supplier_id))
    supplier = supplier_result.scalar_one_or_none()

    # Deliberately no root_cause / supplier_fault field anywhere below —
    # only observed statistics, per SOP-SUPP-008 / ADR-003.
    return {
        "lot_number": lot.lot_number,
        "part_number": lot.part_number,
        "supplier_id": lot.supplier_id,
        "supplier_name": supplier.name if supplier else None,
        "incoming_inspection": {
            "sample_size": lot.sample_size,
            "defect_count": lot.defect_count,
            "rejection_threshold": lot.rejection_threshold,
            "disposition": lot.disposition,
        },
        "historical_defect_rate_pct": lot.historical_defect_rate_pct,
        "source_system": "ERP",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }


async def _recommend_preventative_maintenance(
    session: AsyncSession, machine_id: str, nozzle_id: str, reason: str
) -> dict:
    machine_result = await session.execute(select(Machine).where(Machine.machine_id == machine_id))
    if machine_result.scalar_one_or_none() is None:
        raise _ToolError("MACHINE_NOT_FOUND", f"No machine '{machine_id}'.")

    nozzle_result = await session.execute(select(Nozzle).where(Nozzle.nozzle_id == nozzle_id))
    if nozzle_result.scalar_one_or_none() is None:
        raise _ToolError("NOZZLE_NOT_FOUND", f"No nozzle '{nozzle_id}' on machine '{machine_id}'.")

    # Deliberately does NOT create a WorkOrder row. WorkOrder creation stays
    # a separate, human-approved action (WorkOrder.approved_by), per Phase 5
    # Section 5.2's HITL approval gate pattern.
    return {
        "recommendation_id": str(uuid.uuid4()),
        "status": "pending_approval",
        "machine_id": machine_id,
        "nozzle_id": nozzle_id,
        "reason": reason,
        "recommended_action": "clean_and_inspect",
        "requires_approval_by": "Maintenance Engineer",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }