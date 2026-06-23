from fastapi import APIRouter

from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth_service import auth_service

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest) -> LoginResponse:
    return auth_service.login(payload)
