"""
MCP client wrapper for agent nodes — Phase 11 Step 11.5.

Connects to the Manufacturing/Documents MCP servers over stdio, spawning
them as subprocesses (matching Phase 10's stdio entry points). Wraps every
call in a tool_call span and implements the retry policy from
config/a2a/a2a.yaml — retrying only transient (connection-level) failures,
never business errors like PERMISSION_DENIED or *_NOT_FOUND, per Phase 6
Section 1.3's transient-vs-terminal error distinction.
"""

from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from forgesight.config.logging import get_logger
from forgesight.config.settings import settings
from forgesight.observability.tracing import agent_span

logger = get_logger(__name__)

# Business error codes that must never be retried — retrying them cannot
# change the outcome and would only mask a real problem behind latency.
_TERMINAL_ERROR_CODES = {
    "BOARD_NOT_FOUND",
    "MACHINE_NOT_FOUND",
    "NOZZLE_NOT_FOUND",
    "LOT_NOT_FOUND",
    "DOCUMENT_NOT_FOUND",
    "VERSION_NOT_FOUND",
    "NO_TELEMETRY_IN_WINDOW",
    "NO_RELEVANT_DOCUMENT_FOUND",
    "NO_SIMILAR_INCIDENTS_FOUND",
    "INVALID_TIME_RANGE",
    "PERMISSION_DENIED",
    "AUTHENTICATION_FAILED",
    "UNKNOWN_TOOL",
}


class McpToolError(Exception):
    """Raised when an MCP tool call returns an error_code, so agent node
    code can `try/except McpToolError` cleanly."""

    def __init__(self, error_code: str, detail: str) -> None:
        self.error_code = error_code
        self.detail = detail
        super().__init__(f"{error_code}: {detail}")


@asynccontextmanager
async def _mcp_session(module_name: str) -> AsyncIterator[ClientSession]:
    """Spawn the given MCP server module as a subprocess over stdio and
    yield an initialized ClientSession."""
    server_params = StdioServerParameters(command="python", args=["-m", module_name])
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            yield session


async def _call_with_retry(
    module_name: str, tool_name: str, arguments: dict[str, Any], agent_name: str, incident_id: str, stage: int
) -> dict:
    """Call an MCP tool with the configured transient-error retry policy."""
    max_retries = settings.a2a_transient_error_max_retries
    backoff_seconds = settings.a2a_transient_error_backoff_seconds

    last_exception: Exception | None = None
    for attempt in range(max_retries + 1):
        with agent_span(agent_name, incident_id, stage, "tool_call") as span:
            span.set_attribute("tool_name", tool_name)
            span.set_attribute("attempt", attempt)
            try:
                async with _mcp_session(module_name) as session:
                    result = await session.call_tool(tool_name, arguments=arguments)

                text_content = result.content[0].text if result.content else "{}"
                body = json.loads(text_content)

                if "error_code" in body:
                    error_code = body["error_code"]
                    if error_code in _TERMINAL_ERROR_CODES:
                        raise McpToolError(error_code, body.get("detail", ""))
                    # Non-terminal error code from the tool itself: treat as
                    # retryable business-transient (rare, but handled).
                    raise RuntimeError(f"Retryable tool error: {error_code}")

                return body

            except McpToolError:
                raise  # never retry terminal business errors
            except Exception as exc:  # connection/protocol-level failure
                last_exception = exc
                if attempt < max_retries:
                    logger.warning(
                        "mcp_tool_call_transient_failure_retrying",
                        extra={"tool_name": tool_name, "attempt": attempt, "error": str(exc)},
                    )
                    await asyncio.sleep(backoff_seconds)
                    continue
                raise

    # Unreachable in practice (loop either returns or raises), but keeps
    # type checkers satisfied and gives a clear error if it ever is reached.
    raise last_exception or RuntimeError(f"MCP tool call to '{tool_name}' failed with no captured exception.")


async def call_manufacturing_tool(
    tool_name: str, orchestrator_token: str, agent_name: str, incident_id: str, stage: int, **kwargs: Any
) -> dict:
    """Call a tool on the Manufacturing MCP Server."""
    arguments = {"caller_token": orchestrator_token, **kwargs}
    return await _call_with_retry(
        "mcp_servers.manufacturing", tool_name, arguments, agent_name, incident_id, stage
    )


async def call_documents_tool(
    tool_name: str, orchestrator_token: str, agent_name: str, incident_id: str, stage: int, **kwargs: Any
) -> dict:
    """Call a tool on the Documents MCP Server."""
    arguments = {"caller_token": orchestrator_token, **kwargs}
    return await _call_with_retry(
        "mcp_servers.documents", tool_name, arguments, agent_name, incident_id, stage
    )