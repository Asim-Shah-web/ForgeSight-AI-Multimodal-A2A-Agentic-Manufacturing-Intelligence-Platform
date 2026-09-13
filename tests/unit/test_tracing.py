"""Unit tests for the tracing helpers using OTel's in-memory span exporter."""

from __future__ import annotations

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from forgesight.observability.tracing import agent_span, llm_call_span


@pytest.fixture
def in_memory_exporter():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    previous_provider = trace.get_tracer_provider()
    trace.set_tracer_provider(provider)
    yield exporter
    trace.set_tracer_provider(previous_provider)


def test_agent_span_records_required_attributes(in_memory_exporter) -> None:
    with agent_span("VisionAnalysisAgent", "INCIDENT-TEST-001", 3, "agent_node"):
        pass

    spans = in_memory_exporter.get_finished_spans()
    assert len(spans) == 1
    span = spans[0]
    attrs = span.attributes
    assert attrs["agent.name"] == "VisionAnalysisAgent"
    assert attrs["incident_id"] == "INCIDENT-TEST-001"
    assert attrs["investigation_stage"] == 3
    assert attrs["span.kind"] == "agent_node"
    assert "duration_ms" in attrs


def test_agent_span_marks_error_on_exception(in_memory_exporter) -> None:
    with pytest.raises(ValueError):
        with agent_span("TelemetryAnalysisAgent", "INCIDENT-TEST-001", 4, "tool_call"):
            raise ValueError("simulated failure")

    spans = in_memory_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].status.status_code.name == "ERROR"


def test_llm_call_span_records_model_name(in_memory_exporter) -> None:
    with llm_call_span("HypothesisRankingAgent", "llama-3.3-70b-versatile", "INCIDENT-TEST-001", 9) as span:
        span.set_attribute("prompt_tokens", 100)
        span.set_attribute("completion_tokens", 50)

    spans = in_memory_exporter.get_finished_spans()
    assert len(spans) == 1
    attrs = spans[0].attributes
    assert attrs["model_name"] == "llama-3.3-70b-versatile"
    assert attrs["span.kind"] == "llm_call"
    assert attrs["prompt_tokens"] == 100
    # No prompt/completion text attribute should ever be present.
    assert not any("prompt" in k and k != "prompt_tokens" for k in attrs.keys())