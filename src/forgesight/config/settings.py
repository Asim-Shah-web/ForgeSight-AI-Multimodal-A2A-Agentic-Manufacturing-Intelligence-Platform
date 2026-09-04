
"""
Application settings loaded from environment variables / .env file.

This is the single source of truth for configuration. No hardcoded secrets
are permitted anywhere else in the codebase — every piece of configuration
(DB URL, Redis URL, JWT secret, MCP endpoints) must flow through this module.
"""

from functools import lru_cache

from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central application configuration, loaded from environment/.env."""

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

    # RAG / Embeddings (Phase 4, ADR-005)
    embedding_model_name: str = "BAAI/bge-large-en-v1.5"
    embedding_dimension: int = 1024  # vector(1024) per ADR-005
    rag_retrieval_top_k: int = 20
    rag_rerank_top_k: int = 5

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

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (loaded once per process)."""
    return Settings()  # type: ignore[call-arg]


settings = get_settings()