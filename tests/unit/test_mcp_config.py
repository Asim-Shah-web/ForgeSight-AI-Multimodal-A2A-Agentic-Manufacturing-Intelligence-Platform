"""Unit tests for the declarative MCP config loading layer (Step 10.0)."""

from __future__ import annotations

import pytest

from forgesight.config.settings import get_settings


def test_mcp_yaml_loads_into_nested_settings() -> None:
    get_settings.cache_clear()
    settings = get_settings()

    assert settings.mcp.manufacturing_server.transport == settings.mcp_manufacturing_transport
    assert settings.mcp.manufacturing_server.http_port == settings.mcp_manufacturing_http_port
    assert settings.mcp.documents_server.http_port == settings.mcp_documents_http_port
    assert settings.mcp.tool_execution.timeout_seconds == settings.mcp_tool_timeout_seconds


def test_mcp_env_var_overrides_yaml_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCP_MANUFACTURING_TRANSPORT", "http")
    monkeypatch.setenv("MCP_TOOL_MAX_RETRIES", "5")
    get_settings.cache_clear()

    overridden = get_settings()

    assert overridden.mcp_manufacturing_transport == "http"
    assert overridden.mcp.manufacturing_server.transport == "http"
    assert overridden.mcp_tool_max_retries == 5
    assert overridden.mcp.tool_execution.max_retries == 5

    get_settings.cache_clear()


def test_manufacturing_and_documents_ports_differ_by_default() -> None:
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.mcp_manufacturing_http_port != settings.mcp_documents_http_port