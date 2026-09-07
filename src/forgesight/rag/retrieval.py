"""
Retrieval service — implements the pipeline from Phase 4 Section 5.1 and the
search_technical_sops / get_document_by_id / search_historical_incidents
contracts from mcp_servers/documents/README.md.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel
from rank_bm25 import BM25Okapi
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from forgesight.config.logging import get_logger
from forgesight.config.settings import settings
from forgesight.domain.models.investigation import CorrectiveAction, Incident, RootCauseHypothesis
from forgesight.domain.models.knowledge import DocumentChunk, IncidentEmbedding, TechnicalDocument
from forgesight.rag.embeddings import embed_text
from forgesight.rag.reranking import rerank

logger = get_logger(__name__)


class DocumentNotFoundError(Exception):
    """Raised when a requested document_id/version does not exist."""


class RetrievedPassage(BaseModel):
    """Full provenance schema per Phase 4 Section 6.1 / Phase 5 Section 3.1."""

    passage_id: uuid.UUID
    incident_id: Optional[str] = None
    document_id: str
    document_title: str
    document_version: str
    document_date: Optional[str] = None
    section_title: Optional[str] = None
    section_reference: Optional[str] = None
    chunk_text: str
    retrieval_score: float
    rerank_score: Optional[float] = None
    retrieval_query: str
    retrieval_timestamp: datetime
    embedding_model: str
    retrieved_by: str = "direct_search"


class HistoricalIncidentMatch(BaseModel):
    incident_id: str
    title: str
    defect_type: str
    root_cause_confirmed: Optional[str] = None
    corrective_action_taken: Optional[str] = None
    similarity_score: float
    retrieval_timestamp: datetime


def _tokenize(text: str) -> list[str]:
    return text.lower().split()


async def _dense_candidates(
    session: AsyncSession,
    query_vector: list[float],
    category: Optional[str],
    limit: int,
) -> list[tuple[DocumentChunk, float]]:
    query = select(
        DocumentChunk,
        DocumentChunk.embedding.cosine_distance(query_vector).label("distance"),
    ).where(DocumentChunk.status == "active")

    if category is not None:
        query = query.join(
            TechnicalDocument, TechnicalDocument.document_id == DocumentChunk.document_id
        ).where(TechnicalDocument.category == category)

    query = query.order_by("distance").limit(limit)
    result = await session.execute(query)
    rows = result.all()
    return [(row[0], 1.0 - float(row[1])) for row in rows]


def _hybrid_fuse(
    dense_ranked: list[tuple[DocumentChunk, float]],
    query: str,
) -> list[tuple[DocumentChunk, float]]:
    """Reciprocal Rank Fusion between dense similarity order and BM25 keyword
    order over the same dense candidate pool (Phase 4 Section 5.1 steps 3-4)."""
    if not dense_ranked:
        return []

    corpus = [_tokenize(chunk.chunk_text) for chunk, _score in dense_ranked]
    bm25 = BM25Okapi(corpus)
    bm25_scores = bm25.get_scores(_tokenize(query))

    dense_rank = {chunk.chunk_id: rank for rank, (chunk, _score) in enumerate(dense_ranked)}
    bm25_order = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)
    bm25_rank = {dense_ranked[i][0].chunk_id: rank for rank, i in enumerate(bm25_order)}

    k = 60  # standard RRF constant
    fused_scores: dict[uuid.UUID, float] = {}
    chunk_lookup: dict[uuid.UUID, DocumentChunk] = {}
    dense_score_lookup: dict[uuid.UUID, float] = {}
    for chunk, dense_score in dense_ranked:
        chunk_lookup[chunk.chunk_id] = chunk
        dense_score_lookup[chunk.chunk_id] = dense_score
        fused_scores[chunk.chunk_id] = (
            1.0 / (k + dense_rank[chunk.chunk_id] + 1) + 1.0 / (k + bm25_rank[chunk.chunk_id] + 1)
        )

    ranked_ids = sorted(fused_scores.keys(), key=lambda cid: fused_scores[cid], reverse=True)
    return [(chunk_lookup[cid], dense_score_lookup[cid]) for cid in ranked_ids]


async def search_technical_sops(
    session: AsyncSession,
    query: str,
    category: Optional[str] = None,
    machine_id: Optional[str] = None,
    retrieved_by: str = "direct_search",
) -> list[RetrievedPassage]:
    """
    Full retrieval pipeline: dense retrieval -> optional hybrid fusion ->
    cross-encoder rerank -> relevance filtering -> top-k RetrievedPassage list.

    Returns an empty list if nothing clears the minimum relevance threshold —
    callers must surface this as an explicit "no relevant document found"
    result, never substitute a low-confidence match.
    """
    effective_query = query
    if machine_id:
        effective_query = f"{query} Machine: {machine_id}."

    query_vector = await embed_text(effective_query)

    dense_candidates = await _dense_candidates(
        session, query_vector, category, limit=settings.rag_retrieval_top_k
    )
    if not dense_candidates:
        return []

    fused_candidates = (
        _hybrid_fuse(dense_candidates, effective_query)
        if settings.rag_hybrid_fusion_enabled
        else dense_candidates
    )

    rerank_pairs = [(str(chunk.chunk_id), chunk.chunk_text) for chunk, _score in fused_candidates]
    rerank_results = await rerank(effective_query, rerank_pairs)

    chunk_lookup = {str(chunk.chunk_id): chunk for chunk, _score in fused_candidates}
    dense_score_lookup = {str(chunk.chunk_id): score for chunk, score in fused_candidates}

    now = datetime.now(timezone.utc)
    passages: list[RetrievedPassage] = []
    for chunk_id, rerank_score in rerank_results:
        if rerank_score < settings.rag_min_relevance_score:
            continue
        chunk = chunk_lookup[chunk_id]
        document_result = await session.execute(
            select(TechnicalDocument).where(TechnicalDocument.document_id == chunk.document_id)
        )
        document = document_result.scalar_one_or_none()

        passages.append(
            RetrievedPassage(
                passage_id=uuid.uuid4(),
                document_id=chunk.document_id,
                document_title=chunk.document_title,
                document_version=chunk.document_version,
                document_date=document.document_date.isoformat() if document else None,
                section_title=chunk.section_title,
                section_reference=chunk.section_reference,
                chunk_text=chunk.chunk_text,
                retrieval_score=dense_score_lookup[chunk_id],
                rerank_score=rerank_score,
                retrieval_query=effective_query,
                retrieval_timestamp=now,
                embedding_model=chunk.embedding_model or settings.embedding_model_name,
                retrieved_by=retrieved_by,
            )
        )
        if len(passages) >= settings.rag_rerank_top_k:
            break

    return passages


async def get_document_by_id(
    session: AsyncSession, document_id: str, version: Optional[str] = None
) -> TechnicalDocument:
    """Retrieve full document metadata. Raises DocumentNotFoundError if missing."""
    query = select(TechnicalDocument).where(TechnicalDocument.document_id == document_id)
    if version is not None:
        query = query.where(TechnicalDocument.version == version)
    else:
        query = query.where(TechnicalDocument.status == "active")

    result = await session.execute(query)
    document = result.scalar_one_or_none()
    if document is None:
        raise DocumentNotFoundError(
            f"Document '{document_id}'" + (f" version '{version}'" if version else "") + " not found."
        )
    return document


async def search_historical_incidents(
    session: AsyncSession,
    defect_type: str,
    component_id: Optional[str] = None,
    top_k: int = 5,
) -> list[HistoricalIncidentMatch]:
    """
    Semantic search over closed-incident embeddings. Returns an empty list
    (not an error) when no incident embeddings exist yet, e.g. in a fresh system.
    """
    query_text = defect_type + (f" component {component_id}" if component_id else "")
    query_vector = await embed_text(query_text)

    query = (
        select(
            IncidentEmbedding,
            IncidentEmbedding.embedding.cosine_distance(query_vector).label("distance"),
        )
        .order_by("distance")
        .limit(top_k)
    )
    result = await session.execute(query)
    rows = result.all()

    now = datetime.now(timezone.utc)
    matches: list[HistoricalIncidentMatch] = []

    for incident_embedding, distance in rows:
        similarity = 1.0 - float(distance)
        if similarity < settings.rag_min_relevance_score:
            continue

        incident_result = await session.execute(
            select(Incident).where(Incident.incident_id == incident_embedding.incident_id)
        )
        incident = incident_result.scalar_one_or_none()
        if incident is None:
            continue  # embedding orphaned from a deleted incident; skip rather than fabricate

        hypothesis_result = await session.execute(
            select(RootCauseHypothesis).where(
                RootCauseHypothesis.incident_id == incident.incident_id,
                RootCauseHypothesis.is_confirmed == True,  # noqa: E712
            )
        )
        confirmed_hypothesis = hypothesis_result.scalars().first()

        corrective_action_text: Optional[str] = None
        if confirmed_hypothesis is not None:
            action_result = await session.execute(
                select(CorrectiveAction).where(
                    CorrectiveAction.hypothesis_id == confirmed_hypothesis.hypothesis_id,
                    CorrectiveAction.status == "approved",
                )
            )
            approved_action = action_result.scalars().first()
            if approved_action is not None:
                corrective_action_text = approved_action.proposed_action

        matches.append(
            HistoricalIncidentMatch(
                incident_id=incident.incident_id,
                title=incident.description[:120],
                defect_type=incident.defect_type,
                root_cause_confirmed=confirmed_hypothesis.conclusion if confirmed_hypothesis else None,
                corrective_action_taken=corrective_action_text,
                similarity_score=similarity,
                retrieval_timestamp=now,
            )
        )
    return matches