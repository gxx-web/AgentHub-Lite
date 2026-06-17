from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AgentHub-Lite"
    app_version: str = "0.1.0"
    app_env: str = "local"

    database_url: str = "sqlite:///./agenthub.db"
    redis_url: str = "redis://localhost:6379/0"

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    openai_compatible_base_url: str = "https://api.openai.com/v1"
    openai_compatible_api_key: str | None = None
    openai_compatible_model: str = "gpt-4.1-mini"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

