import os
from pathlib import Path

from pydantic import BaseModel, Field


class Settings(BaseModel):
    app_name: str = "AgentHub-Lite"
    app_version: str = "0.1.0"
    app_env: str = "local"

    database_url: str = "sqlite:///./agenthub.db"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret_key: str = "agenthub-lite-dev-secret-change-me"
    jwt_expires_minutes: int = 60 * 24

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    openai_compatible_base_url: str = "https://api.openai.com/v1"
    openai_compatible_api_key: str | None = None
    openai_compatible_model: str = "gpt-4.1-mini"


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _env(name: str, default: str | None = None) -> str | None:
    return os.environ.get(name, default)


_load_dotenv(Path.cwd() / ".env")

settings = Settings(
    app_env=_env("APP_ENV", "local") or "local",
    database_url=_env("DATABASE_URL", "sqlite:///./agenthub.db") or "sqlite:///./agenthub.db",
    redis_url=_env("REDIS_URL", "redis://localhost:6379/0") or "redis://localhost:6379/0",
    jwt_secret_key=_env("JWT_SECRET_KEY", "agenthub-lite-dev-secret-change-me")
    or "agenthub-lite-dev-secret-change-me",
    jwt_expires_minutes=int(_env("JWT_EXPIRES_MINUTES", str(60 * 24)) or str(60 * 24)),
    openai_compatible_base_url=(
        _env("OPENAI_COMPATIBLE_BASE_URL", "https://api.openai.com/v1")
        or "https://api.openai.com/v1"
    ),
    openai_compatible_api_key=_env("OPENAI_COMPATIBLE_API_KEY"),
    openai_compatible_model=_env("OPENAI_COMPATIBLE_MODEL", "gpt-4.1-mini") or "gpt-4.1-mini",
)
