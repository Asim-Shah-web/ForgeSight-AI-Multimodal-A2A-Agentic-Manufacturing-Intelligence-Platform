"""
Bridges active OpenTelemetry span context into structured log records.

Extends (does not replace) the Phase 7 JsonFormatter — every log record
emitted while inside an active OTel span automatically carries trace_id/
span_id fields, letting you pivot from "an error appeared in the logs" to
"show me the full trace" without a separate correlation ID scheme.
"""

from __future__ import annotations

import logging

from forgesight.observability.tracing import current_trace_context


class TraceContextFilter(logging.Filter):
    """A logging.Filter that stamps trace_id/span_id onto every record when
    an OTel span is active. Attach to the root logger's handler."""

    def filter(self, record: logging.LogRecord) -> bool:
        context = current_trace_context()
        if context is not None:
            record.trace_id = context["trace_id"]
            record.span_id = context["span_id"]
        return True