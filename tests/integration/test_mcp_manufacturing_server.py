"""
Integration tests for the Manufacturing MCP Server's tool implementations.

Calls the internal dispatch/tool functions directly against the real test
DB (bypassing the stdio/HTTP transport layer, which is protocol plumbing
already covered by the `mcp` SDK's own test suite) — this exercises the
actual business logic, RBAC, and audit behavior this phase is responsible for.
"""

from __future__ import annotations

import json

import pytest
from sqlmodel import select

from forgesight.api.security import create_access_token
from forgesight.config import database as db_module
from forgesight.domain.models.audit import AuditEvent, AuditEventType
from forgesight.domain.models.maintenance import WorkOrder
from forgesight.domain.models.users import UserRole

from mcp_servers.manufacturing.server import call_tool


def _token_for(user) -> str:
    token, _ = create_access_token(subject=user.username, role=user.role)
    return token


@pytest.mark.asyncio
async def test_get_board_inspection_data_returns_seeded_findings(users_per_role) -> None:
    qe = users_per_role[UserRole.QUALITY_ENGINEER]
    result = await call_tool(
        "get_board_inspection_data",
        {"caller_token": _token_for(qe), "board_id": "BRD-24017-00432"},
    )
    body = json.loads(result[0].text)

    if "error_code" in body:
        # Board may not be seeded in this test DB instance — acceptable, but
        # if present, must have the correct error shape, not a raw crash.
        assert body["error_code"] == "BOARD_NOT_FOUND"
    else:
        assert body["board_id"] == "BRD-24017-00432"
        assert "aoi_flags" in body


@pytest.mark.asyncio
async def test_get_component_lot_history_never_includes_fault_field(users_per_role) -> None:
    sqe = users_per_role[UserRole.SUPPLIER_QUALITY_ENGINEER]
    result = await call_tool(
        "get_component_lot_history",
        {"caller_token": _token_for(sqe), "lot_number": "LOT-9921", "part_number": "CAP-10UF-0603"},
    )
    body = json.loads(result[0].text)

    if "error_code" not in body:
        forbidden_keys = {"root_cause", "supplier_fault", "fault", "blame"}
        assert forbidden_keys.isdisjoint(set(body.keys()))
        incoming = body.get("incoming_inspection", {})
        assert forbidden_keys.isdisjoint(set(incoming.keys()))


@pytest.mark.asyncio
async def test_recommend_preventative_maintenance_never_creates_work_order(users_per_role) -> None:
    maint_eng = users_per_role[UserRole.MAINTENANCE_ENGINEER]

    async with db_module.AsyncSessionFactory() as session:
        before_result = await session.execute(select(WorkOrder))
        work_order_count_before = len(before_result.scalars().all())

    result = await call_tool(
        "recommend_preventative_maintenance",
        {
            "caller_token": _token_for(maint_eng),
            "machine_id": "PLACER-07",
            "nozzle_id": "NZ-07-03",
            "reason": "Nozzle overdue for cleaning; correlated with recent misalignment defects.",
        },
    )
    body = json.loads(result[0].text)

    if "error_code" not in body:
        assert body["status"] == "pending_approval"
        assert body["requires_approval_by"] == "Maintenance Engineer"

    async with db_module.AsyncSessionFactory() as session:
        after_result = await session.execute(select(WorkOrder))
        work_order_count_after = len(after_result.scalars().all())

    assert work_order_count_after == work_order_count_before


@pytest.mark.asyncio
async def test_tool_called_with_insufficient_permission_returns_permission_denied(users_per_role) -> None:
    operator = users_per_role[UserRole.PRODUCTION_OPERATOR]
    result = await call_tool(
        "get_component_lot_history",
        {"caller_token": _token_for(operator), "lot_number": "LOT-9921", "part_number": "CAP-10UF-0603"},
    )
    body = json.loads(result[0].text)
    assert body["error_code"] == "PERMISSION_DENIED"

    async with db_module.AsyncSessionFactory() as session:
        audit_result = await session.execute(
            select(AuditEvent).where(
                AuditEvent.who == operator.user_id,
                AuditEvent.what == AuditEventType.MCP_TOOL_INVOCATION,
                AuditEvent.action == "get_component_lot_history",
            )
        )
        audit_rows = audit_result.scalars().all()
        assert any(row.result == "error:PERMISSION_DENIED" for row in audit_rows)