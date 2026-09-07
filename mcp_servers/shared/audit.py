"""
MCP tool invocation audit logging (Phase 5 Section 4.3).

Every tool call — success, permission denial, or error — must produce
exactly one AuditEvent. This is called even when authentication itself
fails, using a sentinel "unresolved caller" UUID so the audit trail never
silently omits a call just because the caller couldn't be identified.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any, Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from forgesight.config.logging import get_logger
from forgesight.domain.models.audit import AuditEvent, AuditEventType
from forgesight.domain.models.users import User

logger = get_logger(__name__)

# Sentinel UUID used as `who` when the caller could not be authenticated at
# all (e.g. missing/invalid token) — the audit event still must exist.
UNRESOLVED_CALLER_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")


def compute_result_hash(output: Any) -> str:
    """Compute a tamper-evidence hash of a tool's JSON output, per the
    result_hash field in Phase 5's AuditEvent schema."""
    serialized = json.dumps(output, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


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
    Write one AuditEvent for an MCP tool call.

    `result` is one of: "success", "error:<CODE>", or "pending_approval",
    matching Phase 5 Section 4.3's documented values.
    """
    # arguments may legitimately contain a caller_token; never persist raw
    # tokens into the audit trail.
    safe_arguments = {k: v for k, v in arguments.items() if k != "caller_token"}

    audit_event = AuditEvent(
        who=user.user_id if user is not None else UNRESOLVED_CALLER_ID,
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
        extra={
            "tool_name": tool_name,
            "result": result,
            "who": str(user.user_id) if user is not None else "unresolved",
        },
    )