from fastapi import APIRouter

from app.schemas.model_provider import (
    ModelProviderRead,
    ModelProviderTestRequest,
    ModelProviderTestResponse,
    ModelProviderUpdate,
)
from app.services.model_provider_service import model_provider_service

router = APIRouter()


@router.get("", response_model=list[ModelProviderRead])
async def list_model_providers() -> list[ModelProviderRead]:
    return [provider.to_read() for provider in model_provider_service.list_providers()]


@router.get("/{provider_id}", response_model=ModelProviderRead)
async def get_model_provider(provider_id: str) -> ModelProviderRead:
    return model_provider_service.get_provider(provider_id).to_read()


@router.patch("/{provider_id}", response_model=ModelProviderRead)
async def update_model_provider(
    provider_id: str,
    payload: ModelProviderUpdate,
) -> ModelProviderRead:
    return model_provider_service.update_provider(provider_id, payload).to_read()


@router.post("/{provider_id}/test", response_model=ModelProviderTestResponse)
async def test_model_provider(
    provider_id: str,
    payload: ModelProviderTestRequest,
) -> ModelProviderTestResponse:
    return model_provider_service.test_provider(provider_id, payload)
