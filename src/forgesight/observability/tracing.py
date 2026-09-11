"""
Distributed tracing setup (OpenTelemetry) — Phase 11 Step 11.2.

Two systems are deliberately kept separate in this codebase:
- LangGraph checkpointing (agents/orchestrator.py): durable state that lets
  a paused/crashed investigation RESUME.
- This module: span-level tracing that lets you OBSERVE an investigation's
  execution (including ones already finished), independent of whether it's
  still resumable.

configure_tracing() is idempotent and safe to call multiple times (e.g. once
from the FastAPI process's lifespan, once from the standalone agent-runner
entry point) — only the first call actually installs a TracerProvider.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Iterator, Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
from opentelemetry.trace import Span, Status, StatusCode

from forgesight.config.logging import get_logger
from forgesight.config.settings import settings

logger = get_logger(__name__)

_TRACING_CONFIGURED = False


def configure_tracing() -> None:
    """Install the OTel TracerProvider once per process. No-op if tracing is
    disabled in config, or if already configured."""
    global _TRACING_CONFIGURED
    if _TRACING_CONFIGURED:
        return

    if not settings.tracing_enabled:
        logger.info("tracing_disabled_by_config")
        _TRACING_CONFIGURED = True
        return

    resource = Resource.create({SERVICE_NAME: settings.tracing_service_name})
    sampler = TraceIdRatioBased(settings.tracing_sample_rate)
    provider = TracerProvider(resource=resource, sampler=sampler)

    exporter = OTLPSpanExporter(endpoint=settings.tracing_otlp_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)
    _TRACING_CONFIGURED = True
    logger.info(
        "tracing_configured",
        extra={
            "service_name": settings.tracing_service_name,
            "otlp_endpoint": settings.tracing_otlp_endpoint,
            "sample_rate": settings.tracing_sample_rate,
        },
    )


def instrument_fastapi_app(app) -> None:
    """Auto-instrument a FastAPI app instance for HTTP request tracing."""
    if not settings.tracing_enabled:
        return
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    FastAPIInstrumentor.instrument_app(app)


def instrument_httpx() -> None:
    """Auto-instrument outbound httpx calls (e.g. Groq API calls if made via httpx)."""
    if not settings.tracing_enabled:
        return
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

    HTTPXClientInstrumentor().instrument()


def instrument_sqlalchemy(engine) -> None:
    """Auto-instrument SQLAlchemy for DB query tracing."""
    if not settings.tracing_enabled:
        return
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)


def get_tracer(name: str) -> trace.Tracer:
    """Return a named tracer, mirroring the get_logger(name) pattern."""
    configure_tracing()
    return trace.get_tracer(name)


_tracer = get_tracer(__name__)


@contextmanager
def agent_span(agent_name: str, incident_id: str, stage: int, span_kind: str) -> Iterator[Span]:
    """
    Open a span for an agent node's execution or a tool call it makes.

    span_kind is one of: "agent_node" | "tool_call" | "llm_call" (Mandatory
    Rule 11). The span is marked errored — not just logged — if the wrapped
    block raises, and the exception is re-raised unchanged.
    """
    tracer = get_tracer("forgesight.agents")
    with tracer.start_as_current_span(f"{agent_name}.{span_kind}") as span:
        span.set_attribute("agent.name", agent_name)
        span.set_attribute("incident_id", incident_id)
        span.set_attribute("investigation_stage", stage)
        span.set_attribute("span.kind", span_kind)
        start_time = time.monotonic()
        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as exc:
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            span.record_exception(exc)
            raise
        finally:
            span.set_attribute("duration_ms", int((time.monotonic() - start_time) * 1000))


@contextmanager
def llm_call_span(agent_name: str, model_name: str, incident_id: str, stage: int) -> Iterator[Span]:
    """
    Open a span specifically for an LLM call. Callers should populate
    prompt_tokens/completion_tokens on the yielded span after the call
    completes via span.set_attribute(...) — never the raw prompt/completion
    text (Mandatory Rule 11).
    """
    tracer = get_tracer("forgesight.agents.llm")
    with tracer.start_as_current_span(f"{agent_name}.llm_call") as span:
        span.set_attribute("agent.name", agent_name)
        span.set_attribute("incident_id", incident_id)
        span.set_attribute("investigation_stage", stage)
        span.set_attribute("span.kind", "llm_call")
        span.set_attribute("model_name", model_name)
        start_time = time.monotonic()
        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as exc:
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            span.record_exception(exc)
            raise
        finally:
            span.set_attribute("duration_ms", int((time.monotonic() - start_time) * 1000))


def current_trace_context() -> Optional[dict[str, str]]:
    """Return {"trace_id": ..., "span_id": ...} for the active span, or None
    if there is no active span. Used by the logging bridge."""
    span = trace.get_current_span()
    context = span.get_span_context()
    if context is None or not context.is_valid:
        return None
    return {
        "trace_id": format(context.trace_id, "032x"),
        "span_id": format(context.span_id, "016x"),
    }