from fastapi import APIRouter

from app.core.config import settings
from app.schemas.model_provider import ModelProviderRead

router = APIRouter()


@router.get("", response_model=list[ModelProviderRead])
async def list_model_providers() -> list[ModelProviderRead]:
    return [
        ModelProviderRead(
            id="openai-compatible",
            name="OpenAI Compatible",
            provider_type="openai-compatible",
            base_url=settings.openai_compatible_base_url,
            default_model=settings.openai_compatible_model,
            supports_streaming=True,
            supports_tool_calling=True,
        )
    ]

