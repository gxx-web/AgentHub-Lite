from fastapi import APIRouter

from app.api.v1.routes import agents, chat, model_providers, workspaces

api_router = APIRouter()
api_router.include_router(workspaces.router, prefix="/workspaces", tags=["workspaces"])
api_router.include_router(model_providers.router, prefix="/model-providers", tags=["model-providers"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])

