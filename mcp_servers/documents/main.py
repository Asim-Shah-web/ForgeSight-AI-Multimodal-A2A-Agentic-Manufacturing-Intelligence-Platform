"""
Entry point for the Documents MCP Server.

Usage:
    python -m mcp_servers.documents
"""

from __future__ import annotations

import asyncio

from mcp.server.stdio import stdio_server

from forgesight.config.logging import configure_logging, get_logger
from forgesight.config.settings import settings

import forgesight.domain.models  # noqa: F401

from mcp_servers.documents.server import server

configure_logging()
logger = get_logger(__name__)


async def _run_stdio() -> None:
    logger.info("documents_mcp_server_starting", extra={"transport": "stdio"})
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


async def _run_http() -> None:
    # See the note in mcp_servers/manufacturing/__main__.py regarding the
    # mcp SDK's Streamable HTTP transport API surface.
    from mcp.server.streamable_http import StreamableHTTPServerTransport
    import uvicorn
    from starlette.applications import Starlette
    from starlette.routing import Mount

    logger.info(
        "documents_mcp_server_starting",
        extra={
            "transport": "http",
            "host": settings.mcp_documents_http_host,
            "port": settings.mcp_documents_http_port,
        },
    )

    transport = StreamableHTTPServerTransport(server)
    app = Starlette(routes=[Mount("/mcp", app=transport.asgi_app)])

    config = uvicorn.Config(
        app,
        host=settings.mcp_documents_http_host,
        port=settings.mcp_documents_http_port,
        log_level="info",
    )
    await uvicorn.Server(config).serve()


def main() -> None:
    if settings.mcp_documents_transport == "http":
        asyncio.run(_run_http())
    else:
        asyncio.run(_run_stdio())


if __name__ == "__main__":
    main()