"""Unit tests for the declarative agents/a2a config loading layer (Step 11.0)."""

from __future__ import annotations

import pytest

from forgesight.config.settings import get_settings


def test_agents_yaml_loads_into_nested_settings() -> None:
    get_settings.cache_clear()
    settings = get_settings()

    assert settings.agents.llm.default_model == settings.llm_default_model
    assert settings.agents.orchestrator.system_role_username == settings.orchestrator_system_role_username
    assert settings.agents.agent_models == settings.agent_models


def test_a2a_yaml_loads_into_nested_settings() -> None:
    get_settings.cache_clear()
    settings = get_settings()

    assert settings.a2a.retry_policy.transient_error_max_retries == settings.a2a_transient_error_max_retries
    assert settings.a2a.tracing.otlp_endpoint == settings.tracing_otlp_endpoint


def test_env_var_overrides_agent_yaml_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_DEFAULT_MODEL", "test-override-model")
    monkeypatch.setenv("TRACING_SAMPLE_RATE", "0.5")
    get_settings.cache_clear()

    overridden = get_settings()
    assert overridden.llm_default_model == "test-override-model"
    assert overridden.agents.llm.default_model == "test-override-model"
    assert overridden.tracing_sample_rate == 0.5
    assert overridden.a2a.tracing.sample_rate == 0.5

    get_settings.cache_clear()


def test_per_agent_model_overrides_are_present() -> None:
    get_settings.cache_clear()
    settings = get_settings()
    assert "HypothesisRankingAgent" in settings.agent_models
    assert "ReportGenerationAgent" in settings.agent_models