"""
MCP tool invocation audit logging (Phase 5 Section 4.3).

Every tool call — success, permission denial, or error — must produce an
auditable record. When the caller could not be authenticated at all (no
valid user to attribute the event to), we cannot satisfy AuditEvent.who's
NOT NULL foreign-key constraint against a real user row, so that case is
recorded as a structured, equally-searchable log event instead of a DB row.
Every other outcome (permission denial for an authenticated user, tool
success, tool error) always produces exactly one AuditEvent DB row.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from forgesight.config.logging import get_logger
from forgesight.domain.models.audit import AuditEvent, AuditEventType
from forgesight.domain.models.users import User

logger = get_logger(__name__)


def compute_result_hash(output: Any) -> str:
    """Compute a tamper-evidence hash of a tool's JSON output, per the
    result_hash field in Phase 5's AuditEvent schema."""
    serialized = json.dumps(output, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _redact(arguments: dict) -> dict:
    """arguments may legitimately contain a caller_token; never persist raw
    tokens into the audit trail."""
    return {k: v for k, v in arguments.items() if k != "caller_token"}


async def record_tool_invocation(
    session: AsyncSession,
    user: Optional[User],
    tool_name: str,
    arguments: dict,
    result: str,
    incident_id: Optional[str] = None,
    result_hash: Optional[str] = None,
) -> None:
    """
    Record one MCP tool invocation.

    `result` is one of: "success", "error:<CODE>", or "pending_approval",
    matching Phase 5 Section 4.3's documented values.

    If `user` is None (authentication itself failed before a caller could be
    resolved), this is logged structurally rather than written as an
    AuditEvent row, since AuditEvent.who is a NOT NULL foreign key to a real
    user and there is no user to attribute an unauthenticated call to.
    """
    safe_arguments = _redact(arguments)

    if user is None:
        logger.warning(
            "mcp_tool_invocation_unauthenticated",
            extra={
                "tool_name": tool_name,
                "result": result,
                "arguments": safe_arguments,
                "incident_id": incident_id,
            },
        )
        return

    audit_event = AuditEvent(
        who=user.user_id,
        what=AuditEventType.MCP_TOOL_INVOCATION,
        target_id=incident_id,
        target_type="mcp_tool",
        action=tool_name,
        result=result,
        new_state={"arguments": safe_arguments},
        evidence_version=result_hash,
        ip_address=None,
    )
    session.add(audit_event)
    await session.flush()

    logger.info(
        "mcp_tool_invocation_audited",
        extra={"tool_name": tool_name, "result": result, "who": str(user.user_id)},
    )