"""Integration test for GET /api/v1/health."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_returns_ok_with_db_and_redis(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["db"] == "ok"
    assert body["redis"] == "ok"
    assert "version" in body