"""Pytest test configuration fixtures."""

import pytest
from fastapi.testclient import TestClient
from forgesight.api.main import app


@pytest.fixture
def client():
    return TestClient(app)
