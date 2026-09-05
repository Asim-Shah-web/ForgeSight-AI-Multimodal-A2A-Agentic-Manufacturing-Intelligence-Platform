"""Document / RAG search routes."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from forgesight.api.schemas.documents import (
    DocumentDetailResponse,
    DocumentSearchResponse,
    HistoricalIncidentMatchResponse,
    HistoricalIncidentSearchResponse,
    RetrievedPassageResponse,
)
from forgesight.api.security import get_current_user, require_roles
from forgesight.config.database import get_session
from forgesight.config.logging import get_logger
from forgesight.domain.models.audit import AuditEvent, AuditEventType
from forgesight.domain.models.users import User, UserRole
from forgesight.rag.retrieval import (
    DocumentNotFoundError,
    get_document_by_id,
    search_historical_incidents,
    search_technical_sops,
)

logger = get_logger(__name__)

router = APIRouter()

_QUALITY_ROLES = (
    UserRole.QUALITY_ENGINEER,
    UserRole.MANUFACTURING_ENGINEER,
    UserRole.MAINTENANCE_ENGINEER,
    UserRole.QUALITY_MANAGER,
    UserRole.SUPPLIER_QUALITY_ENGINEER,
)


@router.get(
    "/search",
    response_model=DocumentSearchResponse,
    dependencies=[Depends(require_roles(*_QUALITY_ROLES))],
)
async def search_documents(
    request: Request,
    query: str = Query(min_length=1),
    category: Optional[str] = Query(default=None),
    machine_id: Optional[str] = Query(default=None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> DocumentSearchResponse:
    """
    Search technical SOPs/manuals (Phase 4/5 search_technical_sops contract).

    Never returns 404 for "nothing relevant found" — that's a valid outcome,
    surfaced as no_relevant_document_found=True with an empty passage list,
    per the mandatory hallucination mitigation policy.
    """
    passages = await search_technical_sops(
        session, query=query, category=category, machine_id=machine_id, retrieved_by="direct_search"
    )

    audit_event = AuditEvent(
        who=current_user.user_id,
        what=AuditEventType.RAG_RETRIEVAL,
        target_type="document_chunk",
        action="search_technical_sops",
        result="success",
        new_state={"query": query, "category": category, "result_count": len(passages)},
        ip_address=request.client.host if request.client else None,
    )
    session.add(audit_event)
    await session.flush()

    logger.info("rag_search_executed", extra={"query": query, "result_count": len(passages)})

    return DocumentSearchResponse(
        passages=[RetrievedPassageResponse.model_validate(p.model_dump()) for p in passages],
        no_relevant_document_found=len(passages) == 0,
        result_count=len(passages),
    )


@router.get(
    "/historical-incidents",
    response_model=HistoricalIncidentSearchResponse,
    dependencies=[Depends(require_roles(*_QUALITY_ROLES))],
)
async def search_historical_incidents_route(
    request: Request,
    defect_type: str = Query(min_length=1),
    component_id: Optional[str] = Query(default=None),
    top_k: int = Query(default=5, ge=1, le=20),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> HistoricalIncidentSearchResponse:
    """Search semantically similar closed incidents (Phase 4/5 search_historical_incidents)."""
    matches = await search_historical_incidents(
        session, defect_type=defect_type, component_id=component_id, top_k=top_k
    )

    audit_event = AuditEvent(
        who=current_user.user_id,
        what=AuditEventType.RAG_RETRIEVAL,
        target_type="incident_embedding",
        action="search_historical_incidents",
        result="success",
        new_state={"defect_type": defect_type, "component_id": component_id, "result_count": len(matches)},
        ip_address=request.client.host if request.client else None,
    )
    session.add(audit_event)
    await session.flush()

    return HistoricalIncidentSearchResponse(
        matches=[HistoricalIncidentMatchResponse.model_validate(m.model_dump()) for m in matches],
        result_count=len(matches),
    )


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    dependencies=[Depends(require_roles(*_QUALITY_ROLES))],
)
async def get_document(
    document_id: str,
    version: Optional[str] = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> DocumentDetailResponse:
    """Get full document metadata + raw text. 404 if the document/version does not exist."""
    try:
        document = await get_document_by_id(session, document_id=document_id, version=version)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    full_text: Optional[str] = None
    file_path = Path(document.file_path)
    if file_path.exists():
        full_text = file_path.read_text(encoding="utf-8")

    return DocumentDetailResponse(
        document_id=document.document_id,
        title=document.title,
        category=document.category,
        version=document.version,
        document_date=document.document_date.isoformat(),
        author=document.author,
        approved_by=document.approved_by,
        status=document.status,
        language=document.language,
        full_text=full_text,
    )