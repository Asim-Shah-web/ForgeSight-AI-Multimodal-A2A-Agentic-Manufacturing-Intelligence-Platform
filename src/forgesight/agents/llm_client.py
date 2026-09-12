"""
Groq LLM client wrapper — Phase 11 Step 11.3.

Every call is wrapped in llm_call_span (Step 11.2) and strips any
provider-emitted reasoning/thinking content before returning, so no
downstream code can accidentally persist or trace raw chain-of-thought
(Mandatory Rule 10) even if a future model starts emitting it inline.
"""

from __future__ import annotations

import re

from groq import AsyncGroq
from pydantic import BaseModel

from forgesight.config.logging import get_logger
from forgesight.config.settings import settings
from forgesight.observability.tracing import llm_call_span

logger = get_logger(__name__)

_THINKING_BLOCK_PATTERN = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)

_client: AsyncGroq | None = None


def _get_client() -> AsyncGroq:
    global _client
    if _client is None:
        if not settings.groq_api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not configured. Set it in .env before making any LLM call."
            )
        _client = AsyncGroq(api_key=settings.groq_api_key)
    return _client


class LlmResponse(BaseModel):
    """The only shape that leaves this module — no raw provider response
    object, no reasoning/thinking content."""

    content: str
    model_name: str
    prompt_tokens: int
    completion_tokens: int


def _strip_reasoning_content(text: str) -> str:
    """Remove any <think>...</think>-style block some models emit inline.
    This is a structural guard, not just a UI-layer hiding step."""
    return _THINKING_BLOCK_PATTERN.sub("", text).strip()


async def call_llm(
    agent_name: str,
    incident_id: str,
    stage: int,
    system_prompt: str,
    user_prompt: str,
    model_name: str | None = None,
) -> LlmResponse:
    """
    Call the Groq API on behalf of `agent_name`, resolving the model from
    settings.agent_models (per-agent override) falling back to
    settings.llm_default_model, wrapped in an llm_call_span.
    """
    resolved_model = model_name or settings.agent_models.get(agent_name, settings.llm_default_model)

    with llm_call_span(agent_name, resolved_model, incident_id, stage) as span:
        client = _get_client()
        response = await client.chat.completions.create(
            model=resolved_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        raw_content = response.choices[0].message.content or ""
        cleaned_content = _strip_reasoning_content(raw_content)

        prompt_tokens = response.usage.prompt_tokens if response.usage else 0
        completion_tokens = response.usage.completion_tokens if response.usage else 0

        # Token counts are safe telemetry; the prompt/completion text itself
        # is deliberately never attached as a span attribute.
        span.set_attribute("prompt_tokens", prompt_tokens)
        span.set_attribute("completion_tokens", completion_tokens)

        logger.info(
            "llm_call_completed",
            extra={
                "agent_name": agent_name,
                "model_name": resolved_model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
            },
        )

        return LlmResponse(
            content=cleaned_content,
            model_name=resolved_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )