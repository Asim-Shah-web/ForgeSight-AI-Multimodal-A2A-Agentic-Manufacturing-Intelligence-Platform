"""
Documents MCP Server — implements the 3 tools specified in
docs/architecture/mcp-architecture.md Section 3 and
mcp_servers/documents/README.md, exactly.

Each tool wraps an already-implemented async function from
forgesight.rag.retrieval (Phase 8) — this file adds only the MCP protocol
adapter, RBAC, and audit layer around them.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from mcp.server import Server
import mcp.types as types
from sqlmodel.ext.asyncio.session import AsyncSession

from forgesight.config.database import AsyncSessionFactory
from forgesight.config.logging import get_logger
from forgesight.domain.models.users import User
from forgesight.rag.retrieval import (
    DocumentNotFoundError,
    get_document_by_id,
    search_historical_incidents,
    search_technical_sops,
)

from mcp_servers.shared.audit import compute_result_hash, record_tool_invocation
from mcp_servers.shared.auth import McpAuthenticationError, McpPermissionError, check_tool_permission, resolve_caller

logger = get_logger(__name__)

server = Server("forgesight-documents")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="search_technical_sops",
            description="Semantic/hybrid retrieval of SOP and machine manual passages (Stage 7).",
            inputSchema={
                "type": "object",
                "properties": {
                    "caller_token": {"type": "string"},
                    "query": {"type": "string"},
                    "category": {"type": ["string", "null"], "default": None},
                    "machine_id": {"type": ["string", "null"], "default": None},
                },
                "required": ["caller_token", "query"],
            },
        ),
        types.Tool(
            name="get_document_by_id",
            description="Retrieve the full text and metadata of a specific document version.",
            inputSchema={
                "type": "object",
                "properties": {
                    "caller_token": {"type": "string"},
                    "document_id": {"type": "string"},
                    "version": {"type": ["string", "null"], "default": None},
                },
                "required": ["caller_token", "document_id"],
            },
        ),
        types.Tool(
            name="search_historical_incidents",
            description="Semantic retrieval of similar closed incidents (Stage 9).",
            inputSchema={
                "type": "object",
                "properties": {
                    "caller_token": {"type": "string"},
                    "defect_type": {"type": "string"},
                    "component_id": {"type": ["string", "null"], "default": None},
                    "top_k": {"type": "integer", "default": 5},
                },
                "required": ["caller_token", "defect_type"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    async with AsyncSessionFactory() as session:
        try:
            result = await _dispatch(session, name, arguments)
            await session.commit()
            return [types.TextContent(type="text", text=json.dumps(result))]
        except McpAuthenticationError as exc:
            await session.rollback()
            await _record(session, None, name, arguments, "error:AUTHENTICATION_FAILED")
            return [_error_response("AUTHENTICATION_FAILED", str(exc))]
        except McpPermissionError as exc:
            await session.rollback()
            user = await _try_resolve(session, arguments)
            await _record(session, user, name, arguments, "error:PERMISSION_DENIED")
            return [_error_response("PERMISSION_DENIED", str(exc))]
        except _ToolError as exc:
            await session.rollback()
            user = await _try_resolve(session, arguments)
            await _record(session, user, name, arguments, f"error:{exc.code}")
            return [_error_response(exc.code, str(exc))]


class _ToolError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


def _error_response(code: str, message: str) -> types.TextContent:
    return types.TextContent(type="text", text=json.dumps({"error_code": code, "detail": message}))


async def _try_resolve(session: AsyncSession, arguments: dict) -> Optional[User]:
    token = arguments.get("caller_token")
    if not token:
        return None
    try:
        return await resolve_caller(token, session)
    except McpAuthenticationError:
        return None


async def _record(
    session: AsyncSession, user: Optional[User], tool_name: str, arguments: dict, result: str, output: Any = None
) -> None:
    result_hash = compute_result_hash(output) if output is not None else None
    await record_tool_invocation(session, user, tool_name, arguments, result, result_hash=result_hash)
    await session.commit()


async def _dispatch(session: AsyncSession, name: str, arguments: dict) -> dict:
    caller_token = arguments.get("caller_token", "")
    user = await resolve_caller(caller_token, session)
    check_tool_permission(user.role, "evidence:read")

    if name == "search_technical_sops":
        result = await _search_technical_sops(
            session, arguments["query"], arguments.get("category"), arguments.get("machine_id")
        )
    elif name == "get_document_by_id":
        result = await _get_document_by_id(session, arguments["document_id"], arguments.get("version"))
    elif name == "search_historical_incidents":
        result = await _search_historical_incidents(
            session, arguments["defect_type"], arguments.get("component_id"), arguments.get("top_k", 5)
        )
    else:
        raise _ToolError("UNKNOWN_TOOL", f"Tool '{name}' is not registered on this server.")

    await _record(session, user, name, arguments, "success", output=result)
    return result


async def _search_technical_sops(
    session: AsyncSession, query: str, category: Optional[str], machine_id: Optional[str]
) -> dict:
    passages = await search_technical_sops(
        session, query=query, category=category, machine_id=machine_id, retrieved_by="agent"
    )
    if not passages:
        raise _ToolError("NO_RELEVANT_DOCUMENT_FOUND", "No passage cleared the minimum relevance threshold.")

    return {
        "results": [
            {
                "passage_id": str(p.passage_id),
                "document_id": p.document_id,
                "document_title": p.document_title,
                "document_version": p.document_version,
                "section_title": p.section_title,
                "section_reference": p.section_reference,
                "chunk_text": p.chunk_text,
                "retrieval_score": p.retrieval_score,
                "rerank_score": p.rerank_score,
                "retrieval_query": p.retrieval_query,
                "retrieval_timestamp": p.retrieval_timestamp.isoformat(),
                "embedding_model": p.embedding_model,
                "retrieved_by": p.retrieved_by,
            }
            for p in passages
        ],
        "result_count": len(passages),
    }


async def _get_document_by_id(session: AsyncSession, document_id: str, version: Optional[str]) -> dict:
    try:
        document = await get_document_by_id(session, document_id=document_id, version=version)
    except DocumentNotFoundError as exc:
        code = "VERSION_NOT_FOUND" if version is not None else "DOCUMENT_NOT_FOUND"
        raise _ToolError(code, str(exc)) from exc

    return {
        "document_id": document.document_id,
        "title": document.title,
        "version": document.version,
        "status": document.status,
        "category": document.category,
        "full_text": None,  # full text served via the REST API (Phase 8); not duplicated here
        "approved_by": document.approved_by,
        "date": document.document_date.isoformat(),
    }


async def _search_historical_incidents(
    session: AsyncSession, defect_type: str, component_id: Optional[str], top_k: int
) -> dict:
    matches = await search_historical_incidents(
        session, defect_type=defect_type, component_id=component_id, top_k=top_k
    )
    if not matches:
        raise _ToolError("NO_SIMILAR_INCIDENTS_FOUND", "No historical incident above similarity threshold.")

    return {
        "results": [
            {
                "incident_id": m.incident_id,
                "title": m.title,
                "defect_type": m.defect_type,
                "root_cause_confirmed": m.root_cause_confirmed,
                "corrective_action_taken": m.corrective_action_taken,
                "similarity_score": m.similarity_score,
                "retrieval_timestamp": m.retrieval_timestamp.isoformat(),
            }
            for m in matches
        ],
        "result_count": len(matches),
    }