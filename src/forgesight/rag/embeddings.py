"""
Embedding service — wraps BAAI/bge-large-en-v1.5 (Phase 4 ADR-005).

The model is loaded once as a module-level singleton. All encode() calls are
synchronous under the hood (sentence-transformers), so every public function
here offloads to a worker thread via asyncio.to_thread to avoid blocking the
event loop.
"""

from __future__ import annotations

import asyncio
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from forgesight.config.logging import get_logger
from forgesight.config.settings import settings

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def _get_embedding_model() -> SentenceTransformer:
    """Load and cache the embedding model as a process-wide singleton."""
    logger.info(
        "embedding_model_loading",
        extra={"model_name": settings.embedding_model_name, "device": settings.embedding_device},
    )
    model = SentenceTransformer(settings.embedding_model_name, device=settings.embedding_device)
    logger.info("embedding_model_loaded", extra={"model_name": settings.embedding_model_name})
    return model


def _encode_sync(texts: list[str]) -> list[list[float]]:
    model = _get_embedding_model()
    vectors = model.encode(
        texts,
        batch_size=settings.embedding_batch_size,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return [vector.tolist() for vector in vectors]


def _validate_dimension(vectors: list[list[float]]) -> None:
    for vector in vectors:
        if len(vector) != settings.embedding_dimension:
            raise ValueError(
                f"Embedding dimension mismatch: expected {settings.embedding_dimension}, "
                f"got {len(vector)}. This likely means the configured embedding model "
                f"({settings.embedding_model_name}) does not match the pgvector column "
                f"dimension. Re-embedding all chunks is required before proceeding "
                f"(see rag-architecture.md Section 4.7)."
            )


async def embed_text(text: str) -> list[float]:
    """Embed a single string. Returns a vector of length settings.embedding_dimension."""
    vectors = await asyncio.to_thread(_encode_sync, [text])
    _validate_dimension(vectors)
    return vectors[0]


async def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed a batch of strings in one model call."""
    if not texts:
        return []
    vectors = await asyncio.to_thread(_encode_sync, texts)
    _validate_dimension(vectors)
    return vectors