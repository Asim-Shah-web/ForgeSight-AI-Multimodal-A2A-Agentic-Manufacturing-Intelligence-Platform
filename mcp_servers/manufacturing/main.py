"""
Entry point for the Manufacturing MCP Server.

Usage:
    python -m mcp_servers.manufacturing

Transport (stdio vs. http) is read from settings.mcp.manufacturing_server.transport.
"""

from __future__ import annotations

import asyncio

from mcp.server.stdio import stdio_server

from forgesight.config.logging import configure_logging, get_logger
from forgesight.config.settings import settings

# Import domain models so any code path that touches SQLModel.metadata sees
# every table, consistent with how main.py/scripts do this in Phases 7-9.
import forgesight.domain.models  # noqa: F401

from mcp_servers.manufacturing.server import server

configure_logging()
logger = get_logger(__name__)


async def _run_stdio() -> None:
    logger.info("manufacturing_mcp_server_starting", extra={"transport": "stdio"})
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


async def _run_http() -> None:
    # NOTE: the exact Streamable HTTP transport API surface in the `mcp`
    # Python SDK has evolved across versions. This uses the SDK's
    # streamable_http module as of mcp>=1.2.0; if your installed version's
    # API differs, adapt this function to that version's transport setup
    # call rather than silently falling back to stdio.
    from mcp.server.streamable_http import StreamableHTTPServerTransport
    import uvicorn
    from starlette.applications import Starlette
    from starlette.routing import Mount

    logger.info(
        "manufacturing_mcp_server_starting",
        extra={
            "transport": "http",
            "host": settings.mcp_manufacturing_http_host,
            "port": settings.mcp_manufacturing_http_port,
        },
    )

    transport = StreamableHTTPServerTransport(server)
    app = Starlette(routes=[Mount("/mcp", app=transport.asgi_app)])

    config = uvicorn.Config(
        app,
        host=settings.mcp_manufacturing_http_host,
        port=settings.mcp_manufacturing_http_port,
        log_level="info",
    )
    await uvicorn.Server(config).serve()


def main() -> None:
    if settings.mcp_manufacturing_transport == "http":
        asyncio.run(_run_http())
    else:
        asyncio.run(_run_stdio())


if __name__ == "__main__":
    main()