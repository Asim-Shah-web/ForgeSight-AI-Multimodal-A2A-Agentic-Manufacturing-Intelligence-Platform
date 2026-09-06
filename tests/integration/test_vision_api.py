"""
Integration tests for the /api/v1/vision routes.

These require a real trained checkpoint at settings.cv_model_path (produced
by notebooks/finetune_yolov8_forgesight.ipynb) to exercise the full
pipeline — they skip cleanly with a clear message if it isn't present.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from httpx import AsyncClient
from PIL import Image
from sqlmodel import select

from forgesight.config import database as db_module
from forgesight.config.settings import settings
from forgesight.domain.models.audit import AuditEvent, AuditEventType
from forgesight.domain.models.manufacturing import Batch, Board, Line, Product
from forgesight.domain.models.users import UserRole


@pytest.fixture(scope="module", autouse=True)
def _skip_if_no_checkpoint():
    if not Path(settings.cv_model_path).exists():
        pytest.skip(
            f"No CV checkpoint at '{settings.cv_model_path}'. Run "
            f"notebooks/finetune_yolov8_forgesight.ipynb to produce one."
        )


def _make_test_jpeg_bytes() -> bytes:
    image = Image.new("RGB", (640, 640), color=(40, 90, 50))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


async def _seed_board(board_id: str) -> None:
    async with db_module.AsyncSessionFactory() as session:
        session.add(Product(product_id="VISION-TEST-PRODUCT", name="Vision Test Product"))
        session.add(Line(line_id="VISION-TEST-LINE", name="Vision Test Line"))
        await session.flush()
        session.add(
            Batch(
                batch_id="VISION-TEST-BATCH",
                product_id="VISION-TEST-PRODUCT",
                line_id="VISION-TEST-LINE",
                board_count=1,
                started_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
            )
        )
        await session.flush()
        session.add(Board(board_id=board_id, batch_id="VISION-TEST-BATCH", serial_number=f"SN-{board_id}"))
        await session.commit()


@pytest.mark.asyncio
async def test_inspect_board_as_production_operator_returns_201(
    client: AsyncClient, users_per_role, make_auth_headers
) -> None:
    board_id = "BRD-VISION-TEST-001"
    await _seed_board(board_id)

    operator = users_per_role[UserRole.PRODUCTION_OPERATOR]
    response = await client.post(
        f"/api/v1/vision/boards/{board_id}/inspect",
        headers=make_auth_headers(operator),
        files={"file": ("test.jpg", _make_test_jpeg_bytes(), "image/jpeg")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["inspection_image"]["board_id"] == board_id
    assert "cv_findings" in body
    assert body["findings_count"] == len(body["cv_findings"])
    for finding in body["cv_findings"]:
        assert finding["confidence"] >= settings.cv_confidence_threshold
        assert finding["dataset_used_for_training"] == settings.cv_dataset_used_for_training


@pytest.mark.asyncio
async def test_inspect_board_as_quality_manager_returns_403(
    client: AsyncClient, users_per_role, make_auth_headers
) -> None:
    board_id = "BRD-VISION-TEST-002"
    await _seed_board(board_id)

    quality_manager = users_per_role[UserRole.QUALITY_MANAGER]
    response = await client.post(
        f"/api/v1/vision/boards/{board_id}/inspect",
        headers=make_auth_headers(quality_manager),
        files={"file": ("test.jpg", _make_test_jpeg_bytes(), "image/jpeg")},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_inspect_board_unauthenticated_returns_401(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/vision/boards/BRD-IRRELEVANT/inspect",
        files={"file": ("test.jpg", _make_test_jpeg_bytes(), "image/jpeg")},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_board_findings_returns_created_findings(
    client: AsyncClient, users_per_role, make_auth_headers
) -> None:
    board_id = "BRD-VISION-TEST-003"
    await _seed_board(board_id)

    operator = users_per_role[UserRole.PRODUCTION_OPERATOR]
    qe = users_per_role[UserRole.QUALITY_ENGINEER]

    await client.post(
        f"/api/v1/vision/boards/{board_id}/inspect",
        headers=make_auth_headers(operator),
        files={"file": ("test.jpg", _make_test_jpeg_bytes(), "image/jpeg")},
    )

    response = await client.get(
        f"/api/v1/vision/boards/{board_id}/findings", headers=make_auth_headers(qe)
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_nonexistent_finding_returns_404(
    client: AsyncClient, users_per_role, make_auth_headers
) -> None:
    qe = users_per_role[UserRole.QUALITY_ENGINEER]
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/api/v1/vision/findings/{fake_id}", headers=make_auth_headers(qe))
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_inspect_creates_cv_execution_and_evidence_audit_events(
    client: AsyncClient, users_per_role, make_auth_headers
) -> None:
    board_id = "BRD-VISION-TEST-004"
    await _seed_board(board_id)

    operator = users_per_role[UserRole.PRODUCTION_OPERATOR]
    await client.post(
        f"/api/v1/vision/boards/{board_id}/inspect",
        headers=make_auth_headers(operator),
        files={"file": ("test.jpg", _make_test_jpeg_bytes(), "image/jpeg")},
    )

    async with db_module.AsyncSessionFactory() as session:
        cv_result = await session.execute(
            select(AuditEvent).where(
                AuditEvent.who == operator.user_id,
                AuditEvent.what == AuditEventType.CV_EXECUTION,
            )
        )
        evidence_result = await session.execute(
            select(AuditEvent).where(
                AuditEvent.who == operator.user_id,
                AuditEvent.what == AuditEventType.EVIDENCE_SUBMITTED,
            )
        )
        assert len(cv_result.scalars().all()) >= 1
        assert len(evidence_result.scalars().all()) >= 1