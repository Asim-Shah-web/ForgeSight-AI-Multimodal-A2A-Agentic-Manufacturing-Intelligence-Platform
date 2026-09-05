"""
Application settings loaded from environment variables, .env file, and
declarative YAML configuration under config/ (Phase 8 Step 8.0).

Precedence, highest to lowest:
    1. Environment variable (e.g. EMBEDDING_MODEL_NAME=...)
    2. YAML file under config/ (e.g. config/models/models.yaml)
    3. Hardcoded fallback default on the Pydantic model

This is the single source of truth for configuration. No hardcoded secrets
are permitted anywhere else in the codebase — every piece of configuration
(DB URL, Redis URL, JWT secret, MCP endpoints, model names, RAG parameters)
must flow through this module.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import TypeVar

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic_settings import BaseSettings

T = TypeVar("T", bound=BaseModel)

# src/forgesight/config/settings.py -> repo root is 3 parents up.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_CONFIG_DIR = _REPO_ROOT / "config"


def load_yaml_config(path: Path, model: type[T]) -> T:
    """
    Load a YAML file into the given Pydantic model. If the file does not
    exist, returns the model's own defaults rather than raising — this
    keeps the application bootable (e.g. in a pip-installed package or a
    test environment) even when the config/ tree isn't present alongside
    the code, falling back to the hardcoded defaults on each config model.
    """
    if not path.exists():
        return model()
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    return model.model_validate(raw)


# ---------------------------------------------------------------------------
# Declarative config models (config/models/models.yaml, config/rag/rag.yaml)
# ---------------------------------------------------------------------------

class EmbeddingConfig(BaseModel):
    model_name: str = "BAAI/bge-large-en-v1.5"
    dimension: int = 1024  # vector(1024) per Phase 4 ADR-005
    device: str = "cpu"
    batch_size: int = 32


class RerankerConfig(BaseModel):
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    device: str = "cpu"


class ModelsConfig(BaseModel):
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    reranker: RerankerConfig = Field(default_factory=RerankerConfig)


class ChunkingConfig(BaseModel):
    max_tokens: int = 400
    overlap_tokens: int = 40


class RetrievalConfig(BaseModel):
    top_k: int = 20
    rerank_top_k: int = 5
    min_relevance_score: float = 0.5
    hybrid_fusion_enabled: bool = True


class RagConfig(BaseModel):
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)


_MODELS_YAML_PATH = Path(
    os.environ.get("FORGESIGHT_MODELS_CONFIG_PATH", str(_DEFAULT_CONFIG_DIR / "models" / "models.yaml"))
)
_RAG_YAML_PATH = Path(
    os.environ.get("FORGESIGHT_RAG_CONFIG_PATH", str(_DEFAULT_CONFIG_DIR / "rag" / "rag.yaml"))
)

_yaml_models = load_yaml_config(_MODELS_YAML_PATH, ModelsConfig)
_yaml_rag = load_yaml_config(_RAG_YAML_PATH, RagConfig)


class Settings(BaseSettings):
    """Central application configuration, loaded from environment/.env/YAML."""

    # Application
    app_name: str = "ForgeSight AI"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = Field(
        ..., description="postgresql+psycopg://user:pass@host:port/db"
    )
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Redis
    redis_url: str = Field(..., description="redis://host:port/db")

    # Security
    secret_key: str = Field(..., min_length=32, description="JWT signing secret")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480  # 8 hours, per SEC-005

    # CV Model (Phase 3)
    cv_model_path: str = "models/vision/checkpoints/yolov8-forgesight.pt"
    cv_confidence_threshold: float = 0.5

    # RAG / Embeddings (Phase 4 ADR-005, Phase 8 Step 8.0)
    # These flat fields remain the primary, backward-compatible, env-overridable
    # interface established in Phase 7. Their defaults are now sourced from the
    # declarative YAML config rather than being hardcoded literals.
    embedding_model_name: str = _yaml_models.embedding.model_name
    embedding_dimension: int = _yaml_models.embedding.dimension
    embedding_device: str = _yaml_models.embedding.device
    embedding_batch_size: int = _yaml_models.embedding.batch_size

    reranker_model_name: str = _yaml_models.reranker.model_name
    reranker_device: str = _yaml_models.reranker.device

    rag_chunk_max_tokens: int = _yaml_rag.chunking.max_tokens
    rag_chunk_overlap_tokens: int = _yaml_rag.chunking.overlap_tokens
    rag_retrieval_top_k: int = _yaml_rag.retrieval.top_k
    rag_rerank_top_k: int = _yaml_rag.retrieval.rerank_top_k
    rag_min_relevance_score: float = _yaml_rag.retrieval.min_relevance_score
    rag_hybrid_fusion_enabled: bool = _yaml_rag.retrieval.hybrid_fusion_enabled

    # Structured, nested access to the same configuration (mirrors the flat
    # fields above after validation — see _sync_nested_config_from_flat_fields).
    rag: RagConfig = Field(default_factory=lambda: _yaml_rag.model_copy(deep=True))
    models: ModelsConfig = Field(default_factory=lambda: _yaml_models.model_copy(deep=True))

    # MCP (Phase 5)
    mcp_manufacturing_server_url: str = Field(...)
    mcp_documents_server_url: str = Field(...)

    # CORS
    cors_allowed_origins: str = "http://localhost:3000"

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key_strength(cls, value: str) -> str:
        if len(value.strip()) < 32:
            raise ValueError("secret_key must be at least 32 characters long")
        return value

    @model_validator(mode="after")
    def _sync_nested_config_from_flat_fields(self) -> "Settings":
        """
        The flat fields above are the authoritative, env-overridable values
        (Phase 7 backward compatibility). After validation, mirror them into
        the nested RagConfig/ModelsConfig objects so callers that prefer
        structured access (settings.models.embedding.dimension,
        settings.rag.retrieval.top_k, ...) always see the same, single
        resolved configuration — never a stale YAML-only value.
        """
        self.models.embedding.model_name = self.embedding_model_name
        self.models.embedding.dimension = self.embedding_dimension
        self.models.embedding.device = self.embedding_device
        self.models.embedding.batch_size = self.embedding_batch_size
        self.models.reranker.model_name = self.reranker_model_name
        self.models.reranker.device = self.reranker_device

        self.rag.chunking.max_tokens = self.rag_chunk_max_tokens
        self.rag.chunking.overlap_tokens = self.rag_chunk_overlap_tokens
        self.rag.retrieval.top_k = self.rag_retrieval_top_k
        self.rag.retrieval.rerank_top_k = self.rag_rerank_top_k
        self.rag.retrieval.min_relevance_score = self.rag_min_relevance_score
        self.rag.retrieval.hybrid_fusion_enabled = self.rag_hybrid_fusion_enabled
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (loaded once per process)."""
    return Settings()  # type: ignore[call-arg]


settings = get_settings()