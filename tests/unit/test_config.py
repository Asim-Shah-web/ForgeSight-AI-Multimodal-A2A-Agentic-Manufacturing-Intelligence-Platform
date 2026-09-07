"""Unit tests for the declarative config loading layer (Step 8.0).

Note: these tests exercise get_settings() directly (the cached factory
function), not the module-level `settings` singleton other modules import —
that singleton is resolved once at first import, consistent with the
lru_cache pattern already established in Phase 7.
"""

from __future__ import annotations

import pytest

from forgesight.config.settings import get_settings


def test_yaml_config_loads_into_nested_settings() -> None:
    get_settings.cache_clear()
    settings = get_settings()

    assert settings.models.embedding.model_name == settings.embedding_model_name
    assert settings.models.embedding.dimension == settings.embedding_dimension
    assert settings.rag.retrieval.top_k == settings.rag_retrieval_top_k
    assert settings.rag.retrieval.rerank_top_k == settings.rag_rerank_top_k


def test_env_var_overrides_yaml_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EMBEDDING_MODEL_NAME", "test-override-model")
    monkeypatch.setenv("RAG_RETRIEVAL_TOP_K", "42")
    get_settings.cache_clear()

    overridden_settings = get_settings()

    assert overridden_settings.embedding_model_name == "test-override-model"
    assert overridden_settings.models.embedding.model_name == "test-override-model"
    assert overridden_settings.rag_retrieval_top_k == 42
    assert overridden_settings.rag.retrieval.top_k == 42

    get_settings.cache_clear()


def test_flat_fields_match_nested_config_objects() -> None:
    get_settings.cache_clear()
    settings = get_settings()

    assert settings.rag_chunk_max_tokens == settings.rag.chunking.max_tokens
    assert settings.rag_chunk_overlap_tokens == settings.rag.chunking.overlap_tokens
    assert settings.rag_min_relevance_score == settings.rag.retrieval.min_relevance_score
    assert settings.reranker_model_name == settings.models.reranker.model_name