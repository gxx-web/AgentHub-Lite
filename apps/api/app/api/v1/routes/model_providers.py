from fastapi import APIRouter, Depends

from app.core.deps import CurrentUser, get_current_user
from app.schemas.model_provider import (
    ModelProviderCreate,
    ModelProviderRead,
    ModelProviderTestRequest,
    ModelProviderTestResponse,
    ModelProviderUpdate,
)
from app.services.model_provider_service import model_provider_service

router = APIRouter()


@router.get("", response_model=list[ModelProviderRead])
async def list_model_providers(
    current_user: CurrentUser = Depends(get_current_user),
) -> list[ModelProviderRead]:
    return [
        provider.to_read()
        for provider in model_provider_service.list_providers(current_user.workspace_id)
    ]


@router.post("", response_model=ModelProviderRead, status_code=201)
async def create_model_provider(
    payload: ModelProviderCreate,
    current_user: CurrentUser = Depends(get_current_user),
) -> ModelProviderRead:
    return model_provider_service.create_provider(payload, current_user.workspace_id).to_read()


@router.get("/{provider_id}", response_model=ModelProviderRead)
async def get_model_provider(
    provider_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> ModelProviderRead:
    return model_provider_service.get_provider(provider_id, current_user.workspace_id).to_read()


@router.patch("/{provider_id}", response_model=ModelProviderRead)
async def update_model_provider(
    provider_id: str,
    payload: ModelProviderUpdate,
    current_user: CurrentUser = Depends(get_current_user),
) -> ModelProviderRead:
    return model_provider_service.update_provider(
        provider_id,
        payload,
        current_user.workspace_id,
    ).to_read()


@router.post("/{provider_id}/test", response_model=ModelProviderTestResponse)
async def test_model_provider(
    provider_id: str,
    payload: ModelProviderTestRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> ModelProviderTestResponse:
    return model_provider_service.test_provider(provider_id, payload, current_user.workspace_id)


@router.delete("/{provider_id}", status_code=204)
async def delete_model_provider(
    provider_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> None:
    model_provider_service.delete_provider(provider_id, current_user.workspace_id)
