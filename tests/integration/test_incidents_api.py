"""Integration tests for the incidents API, including RBAC and audit-event assertions."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlmodel import select

from forgesight.config import database as db_module
from forgesight.domain.models.audit import AuditEvent, AuditEventType
from forgesight.domain.models.manufacturing import Batch, Board, Line, Product
from forgesight.domain.models.users import UserRole


async def _seed_incident_context(board_id: str, batch_id: str, line_id: str, product_id: str) -> None:
    async with db_module.AsyncSessionFactory() as session:
        session.add(Product(product_id=product_id, name="Test Product"))
        session.add(Line(line_id=line_id, name="Test Line"))
        await session.flush()
        session.add(
            Batch(
                batch_id=batch_id,
                product_id=product_id,
                line_id=line_id,
                board_count=1,
                started_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
            )
        )
        await session.flush()
        session.add(Board(board_id=board_id, batch_id=batch_id, serial_number=f"SN-{board_id}"))
        await session.commit()


@pytest.mark.asyncio
async def test_create_incident_as_production_operator_returns_201(
    client: AsyncClient, users_per_role, make_auth_headers
) -> None:
    board_id, batch_id, line_id, product_id = (
        f"BRD-TEST-{uuid.uuid4().hex[:6]}",
        f"BATCH-TEST-{uuid.uuid4().hex[:6]}",
        f"LINE-TEST-{uuid.uuid4().hex[:6]}",
        f"PROD-TEST-{uuid.uuid4().hex[:6]}",
    )
    await _seed_incident_context(board_id, batch_id, line_id, product_id)

    operator = users_per_role[UserRole.PRODUCTION_OPERATOR]
    headers = make_auth_headers(operator)

    response = await client.post(
        "/api/v1/incidents",
        headers=headers,
        json={
            "board_id": board_id,
            "batch_id": batch_id,
            "line_id": line_id,
            "product_id": product_id,
            "defect_type": "component_misalignment",
            "component_designator": "C17",
            "description": "Test incident creation via integration test.",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["board_id"] == board_id
    assert body["status"] == "open"
    return body["incident_id"]


@pytest.mark.asyncio
async def test_create_incident_unauthenticated_returns_401(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/incidents",
        json={
            "board_id": "irrelevant",
            "batch_id": "irrelevant",
            "line_id": "irrelevant",
            "product_id": "irrelevant",
            "defect_type": "component_misalignment",
            "description": "Should not be created.",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_incident_as_quality_engineer_returns_200(
    client: AsyncClient, users_per_role, make_auth_headers
) -> None:
    board_id, batch_id, line_id, product_id = (
        f"BRD-TEST-{uuid.uuid4().hex[:6]}",
        f"BATCH-TEST-{uuid.uuid4().hex[:6]}",
        f"LINE-TEST-{uuid.uuid4().hex[:6]}",
        f"PROD-TEST-{uuid.uuid4().hex[:6]}",
    )
    await _seed_incident_context(board_id, batch_id, line_id, product_id)

    operator = users_per_role[UserRole.PRODUCTION_OPERATOR]
    qe = users_per_role[UserRole.QUALITY_ENGINEER]

    create_response = await client.post(
        "/api/v1/incidents",
        headers=make_auth_headers(operator),
        json={
            "board_id": board_id,
            "batch_id": batch_id,
            "line_id": line_id,
            "product_id": product_id,
            "defect_type": "component_misalignment",
            "description": "Test incident for GET.",
        },
    )
    incident_id = create_response.json()["incident_id"]

    get_response = await client.get(
        f"/api/v1/incidents/{incident_id}", headers=make_auth_headers(qe)
    )
    assert get_response.status_code == 200
    body = get_response.json()
    assert body["incident_id"] == incident_id
    assert body["board_id"] == board_id


@pytest.mark.asyncio
async def test_update_status_as_system_administrator_returns_403(
    client: AsyncClient, users_per_role, make_auth_headers
) -> None:
    board_id, batch_id, line_id, product_id = (
        f"BRD-TEST-{uuid.uuid4().hex[:6]}",
        f"BATCH-TEST-{uuid.uuid4().hex[:6]}",
        f"LINE-TEST-{uuid.uuid4().hex[:6]}",
        f"PROD-TEST-{uuid.uuid4().hex[:6]}",
    )
    await _seed_incident_context(board_id, batch_id, line_id, product_id)

    operator = users_per_role[UserRole.PRODUCTION_OPERATOR]
    sysadmin = users_per_role[UserRole.SYSTEM_ADMINISTRATOR]

    create_response = await client.post(
        "/api/v1/incidents",
        headers=make_auth_headers(operator),
        json={
            "board_id": board_id,
            "batch_id": batch_id,
            "line_id": line_id,
            "product_id": product_id,
            "defect_type": "component_misalignment",
            "description": "Test incident for SysAdmin 403 check.",
        },
    )
    incident_id = create_response.json()["incident_id"]

    response = await client.patch(
        f"/api/v1/incidents/{incident_id}/status",
        headers=make_auth_headers(sysadmin),
        json={"status": "in_progress", "reason": "SysAdmin should not be able to do this."},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_approve_incident_as_quality_engineer_creates_audit_event(
    client: AsyncClient, users_per_role, make_auth_headers
) -> None:
    board_id, batch_id, line_id, product_id = (
        f"BRD-TEST-{uuid.uuid4().hex[:6]}",
        f"BATCH-TEST-{uuid.uuid4().hex[:6]}",
        f"LINE-TEST-{uuid.uuid4().hex[:6]}",
        f"PROD-TEST-{uuid.uuid4().hex[:6]}",
    )
    await _seed_incident_context(board_id, batch_id, line_id, product_id)

    operator = users_per_role[UserRole.PRODUCTION_OPERATOR]
    qe = users_per_role[UserRole.QUALITY_ENGINEER]

    create_response = await client.post(
        "/api/v1/incidents",
        headers=make_auth_headers(operator),
        json={
            "board_id": board_id,
            "batch_id": batch_id,
            "line_id": line_id,
            "product_id": product_id,
            "defect_type": "component_misalignment",
            "description": "Test incident for approval flow.",
        },
    )
    incident_id = create_response.json()["incident_id"]

    approve_response = await client.post(
        f"/api/v1/incidents/{incident_id}/approve",
        headers=make_auth_headers(qe),
        json={"approval_statement": "Root cause confirmed via evidence review; closing incident."},
    )
    assert approve_response.status_code == 200
    body = approve_response.json()
    assert body["status"] == "closed"
    assert body["signed_off_by"] == str(qe.user_id)

    async with db_module.AsyncSessionFactory() as session:
        result = await session.execute(
            select(AuditEvent).where(
                AuditEvent.target_id == incident_id,
                AuditEvent.what == AuditEventType.HUMAN_APPROVAL,
            )
        )
        audit_rows = result.scalars().all()
        assert len(audit_rows) == 1
        assert audit_rows[0].approval_by == qe.user_id
        assert audit_rows[0].who == qe.user_id