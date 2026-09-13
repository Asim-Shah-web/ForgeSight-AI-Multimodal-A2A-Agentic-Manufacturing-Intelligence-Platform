"""Unit tests for the LLM client wrapper — chain-of-thought stripping and
token accounting, with the Groq client mocked."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from forgesight.agents.llm_client import LlmResponse, call_llm, _strip_reasoning_content


def test_strip_reasoning_content_removes_think_block() -> None:
    raw = "<think>internal reasoning that must never be persisted</think>The final answer is X."
    cleaned = _strip_reasoning_content(raw)
    assert "internal reasoning" not in cleaned
    assert cleaned == "The final answer is X."


def test_strip_reasoning_content_passthrough_when_no_think_block() -> None:
    raw = "Just a normal response."
    assert _strip_reasoning_content(raw) == raw


@pytest.mark.asyncio
async def test_call_llm_returns_clean_response_and_token_counts() -> None:
    fake_message = MagicMock()
    fake_message.content = "<think>hidden</think>Visible answer only."
    fake_choice = MagicMock()
    fake_choice.message = fake_message
    fake_usage = MagicMock()
    fake_usage.prompt_tokens = 42
    fake_usage.completion_tokens = 17
    fake_response = MagicMock()
    fake_response.choices = [fake_choice]
    fake_response.usage = fake_usage

    fake_client = MagicMock()
    fake_client.chat.completions.create = AsyncMock(return_value=fake_response)

    with patch("forgesight.agents.llm_client._get_client", return_value=fake_client):
        result = await call_llm(
            agent_name="HypothesisRankingAgent",
            incident_id="INCIDENT-TEST-001",
            stage=9,
            system_prompt="test system prompt",
            user_prompt="test user prompt",
        )

    assert isinstance(result, LlmResponse)
    assert result.content == "Visible answer only."
    assert "hidden" not in result.content
    assert result.prompt_tokens == 42
    assert result.completion_tokens == 17