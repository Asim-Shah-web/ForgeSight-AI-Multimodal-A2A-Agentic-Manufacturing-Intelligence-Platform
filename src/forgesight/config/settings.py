"""
Application settings loaded from environment variables, .env file, and
declarative YAML configuration under config/.

Precedence, highest to lowest:
    1. Environment variable
    2. YAML file under config/
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

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_CONFIG_DIR = _REPO_ROOT / "config"


def load_yaml_config(path: Path, model: type[T]) -> T:
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
    dimension: int = 1024
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
            "insufficient_solder_paste", "excessive_solder_paste", "solder_paste_bridging",
            "component_misalignment", "missing_component", "tombstoning", "polarity_inversion",
            "wrong_component", "cold_solder_joint", "solder_bridging", "solder_balling",
            "solder_voids", "head_in_pillow",
        ]
    )


# ---------------------------------------------------------------------------
# config/mcp/mcp.yaml (Phase 10)
# ---------------------------------------------------------------------------

class McpServerConfig(BaseModel):
    name: str = "forgesight-mcp-server"
    transport: str = "stdio"
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


# ---------------------------------------------------------------------------
# config/agents/agents.yaml, config/a2a/a2a.yaml (Phase 11)
# ---------------------------------------------------------------------------

class LlmConfig(BaseModel):
    provider: str = "groq"
    default_model: str = "llama-3.3-70b-versatile"
    temperature: float = 0.1
    max_tokens: int = 2048


class OrchestratorSettingsConfig(BaseModel):
    system_role_username: str = "forgesight-orchestrator-system"
    max_stage_retries: int = 2
    stage_timeout_seconds: int = 60


class CheckpointingConfig(BaseModel):
    backend: str = "postgres"


class AgentsConfig(BaseModel):
    llm: LlmConfig = Field(default_factory=LlmConfig)
    agent_models: dict[str, str] = Field(default_factory=dict)
    orchestrator: OrchestratorSettingsConfig = Field(default_factory=OrchestratorSettingsConfig)
    checkpointing: CheckpointingConfig = Field(default_factory=CheckpointingConfig)


class MessageBusConfig(BaseModel):
    transport: str = "in_process"


class RetryPolicyConfig(BaseModel):
    transient_error_max_retries: int = 2
    transient_error_backoff_seconds: int = 2
    escalate_after_consecutive_errors: int = 3


class TracingConfig(BaseModel):
    enabled: bool = True
    otlp_endpoint: str = "http://localhost:4317"
    service_name: str = "forgesight-agents"
    sample_rate: float = 1.0


class A2aConfig(BaseModel):
    message_bus: MessageBusConfig = Field(default_factory=MessageBusConfig)
    retry_policy: RetryPolicyConfig = Field(default_factory=RetryPolicyConfig)
    tracing: TracingConfig = Field(default_factory=TracingConfig)


_MODELS_YAML_PATH = Path(os.environ.get("FORGESIGHT_MODELS_CONFIG_PATH", str(_DEFAULT_CONFIG_DIR / "models" / "models.yaml")))
_RAG_YAML_PATH = Path(os.environ.get("FORGESIGHT_RAG_CONFIG_PATH", str(_DEFAULT_CONFIG_DIR / "rag" / "rag.yaml")))
_VISION_YAML_PATH = Path(os.environ.get("FORGESIGHT_VISION_CONFIG_PATH", str(_DEFAULT_CONFIG_DIR / "vision" / "vision.yaml")))
_MCP_YAML_PATH = Path(os.environ.get("FORGESIGHT_MCP_CONFIG_PATH", str(_DEFAULT_CONFIG_DIR / "mcp" / "mcp.yaml")))
_AGENTS_YAML_PATH = Path(os.environ.get("FORGESIGHT_AGENTS_CONFIG_PATH", str(_DEFAULT_CONFIG_DIR / "agents" / "agents.yaml")))
_A2A_YAML_PATH = Path(os.environ.get("FORGESIGHT_A2A_CONFIG_PATH", str(_DEFAULT_CONFIG_DIR / "a2a" / "a2a.yaml")))

_yaml_models = load_yaml_config(_MODELS_YAML_PATH, ModelsConfig)
_yaml_rag = load_yaml_config(_RAG_YAML_PATH, RagConfig)
_yaml_vision = load_yaml_config(_VISION_YAML_PATH, VisionConfig)
_yaml_mcp = load_yaml_config(_MCP_YAML_PATH, McpConfig)
_yaml_agents = load_yaml_config(_AGENTS_YAML_PATH, AgentsConfig)
_yaml_a2a = load_yaml_config(_A2A_YAML_PATH, A2aConfig)


class Settings(BaseSettings):
    """Central application configuration, loaded from environment/.env/YAML."""

    # Application
    app_name: str = "ForgeSight AI"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = Field(...)
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Redis
    redis_url: str = Field(...)

    # Security
    secret_key: str = Field(..., min_length=32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

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
    cv_upload_allowed_mime_types: list[str] = Field(default_factory=lambda: list(_yaml_vision.upload.allowed_mime_types))
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

    # Agents / LLM (Phase 11)
    groq_api_key: str = Field(default="", description="Groq API key; required at runtime for real LLM calls, never in YAML")
    llm_provider: str = _yaml_agents.llm.provider
    llm_default_model: str = _yaml_agents.llm.default_model
    llm_temperature: float = _yaml_agents.llm.temperature
    llm_max_tokens: int = _yaml_agents.llm.max_tokens
    agent_models: dict[str, str] = Field(default_factory=lambda: dict(_yaml_agents.agent_models))
    orchestrator_system_role_username: str = _yaml_agents.orchestrator.system_role_username
    orchestrator_max_stage_retries: int = _yaml_agents.orchestrator.max_stage_retries
    orchestrator_stage_timeout_seconds: int = _yaml_agents.orchestrator.stage_timeout_seconds
    checkpointing_backend: str = _yaml_agents.checkpointing.backend

    # A2A / Tracing (Phase 11)
    a2a_message_bus_transport: str = _yaml_a2a.message_bus.transport
    a2a_transient_error_max_retries: int = _yaml_a2a.retry_policy.transient_error_max_retries
    a2a_transient_error_backoff_seconds: int = _yaml_a2a.retry_policy.transient_error_backoff_seconds
    a2a_escalate_after_consecutive_errors: int = _yaml_a2a.retry_policy.escalate_after_consecutive_errors
    tracing_enabled: bool = _yaml_a2a.tracing.enabled
    tracing_otlp_endpoint: str = _yaml_a2a.tracing.otlp_endpoint
    tracing_service_name: str = _yaml_a2a.tracing.service_name
    tracing_sample_rate: float = _yaml_a2a.tracing.sample_rate

    # Structured, nested access to the same configuration.
    rag: RagConfig = Field(default_factory=lambda: _yaml_rag.model_copy(deep=True))
    models: ModelsConfig = Field(default_factory=lambda: _yaml_models.model_copy(deep=True))
    vision: VisionConfig = Field(default_factory=lambda: _yaml_vision.model_copy(deep=True))
    mcp: McpConfig = Field(default_factory=lambda: _yaml_mcp.model_copy(deep=True))
    agents: AgentsConfig = Field(default_factory=lambda: _yaml_agents.model_copy(deep=True))
    a2a: A2aConfig = Field(default_factory=lambda: _yaml_a2a.model_copy(deep=True))

    # CORS
    cors_allowed_origins: str = "http://localhost:3000"

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore")

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key_strength(cls, value: str) -> str:
        if len(value.strip()) < 32:
            raise ValueError("secret_key must be at least 32 characters long")
        return value

    @model_validator(mode="after")
    def _sync_nested_config_from_flat_fields(self) -> "Settings":
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

        self.agents.llm.provider = self.llm_provider
        self.agents.llm.default_model = self.llm_default_model
        self.agents.llm.temperature = self.llm_temperature
        self.agents.llm.max_tokens = self.llm_max_tokens
        self.agents.agent_models = dict(self.agent_models)
        self.agents.orchestrator.system_role_username = self.orchestrator_system_role_username
        self.agents.orchestrator.max_stage_retries = self.orchestrator_max_stage_retries
        self.agents.orchestrator.stage_timeout_seconds = self.orchestrator_stage_timeout_seconds
        self.agents.checkpointing.backend = self.checkpointing_backend

        self.a2a.message_bus.transport = self.a2a_message_bus_transport
        self.a2a.retry_policy.transient_error_max_retries = self.a2a_transient_error_max_retries
        self.a2a.retry_policy.transient_error_backoff_seconds = self.a2a_transient_error_backoff_seconds
        self.a2a.retry_policy.escalate_after_consecutive_errors = self.a2a_escalate_after_consecutive_errors
        self.a2a.tracing.enabled = self.tracing_enabled
        self.a2a.tracing.otlp_endpoint = self.tracing_otlp_endpoint
        self.a2a.tracing.service_name = self.tracing_service_name
        self.a2a.tracing.sample_rate = self.tracing_sample_rate
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()