from fastapi import APIRouter
from starlette.responses import StreamingResponse

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import chat_service

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    return await chat_service.invoke(payload)


@router.post("/stream")
async def stream_chat(payload: ChatRequest) -> StreamingResponse:
    return StreamingResponse(chat_service.stream(payload), media_type="text/event-stream")
