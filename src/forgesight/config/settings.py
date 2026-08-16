"""Application settings using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ForgeSight AI"
    environment: str = "development"
    log_level: str = "INFO"
    secret_key: str = "default_secret_key"

    # API
    host: str = "0.0.0.0"
    port: int = 8000

    # LLM API Keys
    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    groq_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
