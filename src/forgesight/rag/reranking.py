"""Cross-encoder reranking service (Phase 4 Section 5.3, Option B selected)."""

from __future__ import annotations

import asyncio
from functools import lru_cache

from sentence_transformers import CrossEncoder

from forgesight.config.logging import get_logger
from forgesight.config.settings import settings

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def _get_reranker_model() -> CrossEncoder:
    logger.info("reranker_model_loading", extra={"model_name": settings.reranker_model_name})
    model = CrossEncoder(settings.reranker_model_name, device=settings.reranker_device)
    logger.info("reranker_model_loaded", extra={"model_name": settings.reranker_model_name})
    return model


def _rerank_sync(query: str, candidates: list[tuple[str, str]]) -> list[tuple[str, float]]:
    model = _get_reranker_model()
    pairs = [[query, chunk_text] for _chunk_id, chunk_text in candidates]
    scores = model.predict(pairs)
    scored = [(candidates[i][0], float(scores[i])) for i in range(len(candidates))]
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored


async def rerank(query: str, candidates: list[tuple[str, str]]) -> list[tuple[str, float]]:
    """
    Rerank (chunk_id, chunk_text) candidates against a query.

    Returns (chunk_id, rerank_score) tuples sorted descending by score.
    An empty candidate list returns an empty list without invoking the model.
    """
    if not candidates:
        return []
    return await asyncio.to_thread(_rerank_sync, query, candidates)