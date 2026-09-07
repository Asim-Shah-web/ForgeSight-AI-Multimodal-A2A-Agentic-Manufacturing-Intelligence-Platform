"""Unit tests for the embedding service.

Note: test_embed_text_returns_correct_dimension and
test_embed_batch_empty_list_returns_empty exercise the real
BAAI/bge-large-en-v1.5 model and will download/load it on first run.
"""

from __future__ import annotations

import pytest

from forgesight.config.settings import settings
from forgesight.rag import embeddings


@pytest.mark.asyncio
async def test_embed_text_returns_correct_dimension() -> None:
    vector = await embeddings.embed_text(
        "Placement tolerance for chip capacitors under IPC-A-610 Class 3."
    )
    assert len(vector) == settings.embedding_dimension
    assert all(isinstance(v, float) for v in vector)


@pytest.mark.asyncio
async def test_embed_batch_empty_list_returns_empty() -> None:
    result = await embeddings.embed_batch([])
    assert result == []


@pytest.mark.asyncio
async def test_mismatched_dimension_raises_value_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_encode_sync(texts: list[str]) -> list[list[float]]:
        return [[0.0] * (settings.embedding_dimension - 1) for _ in texts]

    monkeypatch.setattr(embeddings, "_encode_sync", _fake_encode_sync)

    with pytest.raises(ValueError, match="Embedding dimension mismatch"):
        await embeddings.embed_text("this will produce a wrong-length vector")