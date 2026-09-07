"""
Application settings loaded from environment variables, .env file, and
declarative YAML configuration under config/.

Precedence, highest to lowest:
    1. Environment variable (e.g. EMBEDDING_MODEL_NAME=...)
    2. YAML file under config/ (e.g. config/models/models.yaml)
    3. Hardcoded fallback default on the Pydantic model

This is the single source of truth for configuration. No hardcoded secrets
are permitted anywhere else in the codebase.
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
    exist, returns the model's own defaults rather than raising.
    """
    if not path.exists():
        return model()
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    return model.model_validate(raw)


# ---------------------------------------------------------------------------
# config/models/models.yaml, config/rag/rag.yaml (Phase 8)
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


# ---------------------------------------------------------------------------
# config/vision/vision.yaml (Phase 9)
# ---------------------------------------------------------------------------

class VisionModelConfig(BaseModel):
    checkpoint_path: str = "models/vision/checkpoints/yolov8-forgesight-synthetic-v1.pt"
    model_name: str = "yolov8-forgesight"
    model_version: str = "synthetic-v1"
    dataset_used_for_training: str = "synthetic-placeholder-v1 (not for production use)"
    device: str = "cpu"
    image_size: int = 640


class VisionInferenceConfig(BaseModel):
    confidence_threshold: float = 0.5
    iou_threshold: float = 0.45
    max_detections_per_image: int = 50


class VisionUploadConfig(BaseModel):
    max_file_size_mb: int = 10
    allowed_mime_types: list[str] = Field(default_factory=lambda: ["image/jpeg", "image/png"])
    storage_dir: str = "data/images/uploaded"


class VisionConfig(BaseModel):
    model: VisionModelConfig = Field(default_factory=VisionModelConfig)
    inference: VisionInferenceConfig = Field(default_factory=VisionInferenceConfig)
    upload: VisionUploadConfig = Field(default_factory=VisionUploadConfig)
    defect_classes: list[str] = Field(
        default_factory=lambda: [
            "insufficient_solder_paste",
            "excessive_solder_paste",
            "solder_paste_bridging",
            "component_misalignment",
            "missing_component",
            "tombstoning",
            "polarity_inversion",
            "wrong_component",
            "cold_solder_joint",
            "solder_bridging",
            "solder_balling",
            "solder_voids",
            "head_in_pillow",
        ]
    )


# ---------------------------------------------------------------------------
# config/mcp/mcp.yaml (Phase 10)
# ---------------------------------------------------------------------------

class McpServerConfig(BaseModel):
    name: str = "forgesight-mcp-server"
    transport: str = "stdio"  # "stdio" | "http"
    http_host: str = "0.0.0.0"
    http_port: int = 9000


class McpToolExecutionConfig(BaseModel):
    timeout_seconds: int = 30
    max_retries: int = 2


class McpConfig(BaseModel):
    manufacturing_server: McpServerConfig = Field(
        default_factory=lambda: McpServerConfig(name="forgesight-manufacturing", http_port=9001)
    )
    documents_server: McpServerConfig = Field(
        default_factory=lambda: McpServerConfig(name="forgesight-documents", http_port=9002)
    )
    tool_execution: McpToolExecutionConfig = Field(default_factory=McpToolExecutionConfig)


_MODELS_YAML_PATH = Path(
    os.environ.get("FORGESIGHT_MODELS_CONFIG_PATH", str(_DEFAULT_CONFIG_DIR / "models" / "models.yaml"))
)
_RAG_YAML_PATH = Path(
    os.environ.get("FORGESIGHT_RAG_CONFIG_PATH", str(_DEFAULT_CONFIG_DIR / "rag" / "rag.yaml"))
)
_VISION_YAML_PATH = Path(
    os.environ.get("FORGESIGHT_VISION_CONFIG_PATH", str(_DEFAULT_CONFIG_DIR / "vision" / "vision.yaml"))
)
_MCP_YAML_PATH = Path(
    os.environ.get("FORGESIGHT_MCP_CONFIG_PATH", str(_DEFAULT_CONFIG_DIR / "mcp" / "mcp.yaml"))
)

_yaml_models = load_yaml_config(_MODELS_YAML_PATH, ModelsConfig)
_yaml_rag = load_yaml_config(_RAG_YAML_PATH, RagConfig)
_yaml_vision = load_yaml_config(_VISION_YAML_PATH, VisionConfig)
_yaml_mcp = load_yaml_config(_MCP_YAML_PATH, McpConfig)


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

    # CV Model (Phase 3/7/9)
    cv_model_path: str = _yaml_vision.model.checkpoint_path
    cv_model_name: str = _yaml_vision.model.model_name
    cv_model_version: str = _yaml_vision.model.model_version
    cv_dataset_used_for_training: str = _yaml_vision.model.dataset_used_for_training
    cv_device: str = _yaml_vision.model.device
    cv_image_size: int = _yaml_vision.model.image_size

    cv_confidence_threshold: float = _yaml_vision.inference.confidence_threshold
    cv_iou_threshold: float = _yaml_vision.inference.iou_threshold
    cv_max_detections_per_image: int = _yaml_vision.inference.max_detections_per_image

    cv_upload_max_size_mb: int = _yaml_vision.upload.max_file_size_mb
    cv_upload_allowed_mime_types: list[str] = Field(
        default_factory=lambda: list(_yaml_vision.upload.allowed_mime_types)
    )
    cv_upload_storage_dir: str = _yaml_vision.upload.storage_dir
    cv_defect_classes: list[str] = Field(default_factory=lambda: list(_yaml_vision.defect_classes))

    # RAG / Embeddings (Phase 4/8)
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

    # MCP (Phase 5/10)
    mcp_manufacturing_server_url: str = Field(...)
    mcp_documents_server_url: str = Field(...)

    mcp_manufacturing_transport: str = _yaml_mcp.manufacturing_server.transport
    mcp_manufacturing_http_host: str = _yaml_mcp.manufacturing_server.http_host
    mcp_manufacturing_http_port: int = _yaml_mcp.manufacturing_server.http_port

    mcp_documents_transport: str = _yaml_mcp.documents_server.transport
    mcp_documents_http_host: str = _yaml_mcp.documents_server.http_host
    mcp_documents_http_port: int = _yaml_mcp.documents_server.http_port

    mcp_tool_timeout_seconds: int = _yaml_mcp.tool_execution.timeout_seconds
    mcp_tool_max_retries: int = _yaml_mcp.tool_execution.max_retries

    # Structured, nested access to the same configuration.
    rag: RagConfig = Field(default_factory=lambda: _yaml_rag.model_copy(deep=True))
    models: ModelsConfig = Field(default_factory=lambda: _yaml_models.model_copy(deep=True))
    vision: VisionConfig = Field(default_factory=lambda: _yaml_vision.model_copy(deep=True))
    mcp: McpConfig = Field(default_factory=lambda: _yaml_mcp.model_copy(deep=True))

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
        The flat fields above are the authoritative, env-overridable values.
        After validation, mirror them into the nested config objects so
        callers that prefer structured access always see the same, single
        resolved configuration.
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

        self.vision.model.checkpoint_path = self.cv_model_path
        self.vision.model.model_name = self.cv_model_name
        self.vision.model.model_version = self.cv_model_version
        self.vision.model.dataset_used_for_training = self.cv_dataset_used_for_training
        self.vision.model.device = self.cv_device
        self.vision.model.image_size = self.cv_image_size
        self.vision.inference.confidence_threshold = self.cv_confidence_threshold
        self.vision.inference.iou_threshold = self.cv_iou_threshold
        self.vision.inference.max_detections_per_image = self.cv_max_detections_per_image
        self.vision.upload.max_file_size_mb = self.cv_upload_max_size_mb
        self.vision.upload.allowed_mime_types = list(self.cv_upload_allowed_mime_types)
        self.vision.upload.storage_dir = self.cv_upload_storage_dir
        self.vision.defect_classes = list(self.cv_defect_classes)

        self.mcp.manufacturing_server.transport = self.mcp_manufacturing_transport
        self.mcp.manufacturing_server.http_host = self.mcp_manufacturing_http_host
        self.mcp.manufacturing_server.http_port = self.mcp_manufacturing_http_port
        self.mcp.documents_server.transport = self.mcp_documents_transport
        self.mcp.documents_server.http_host = self.mcp_documents_http_host
        self.mcp.documents_server.http_port = self.mcp_documents_http_port
        self.mcp.tool_execution.timeout_seconds = self.mcp_tool_timeout_seconds
        self.mcp.tool_execution.max_retries = self.mcp_tool_max_retries
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (loaded once per process)."""
    return Settings()  # type: ignore[call-arg]


settings = get_settings()