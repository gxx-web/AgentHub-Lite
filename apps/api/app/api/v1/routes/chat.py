from fastapi import APIRouter
from starlette.responses import StreamingResponse

from app.schemas.chat import (
    AgentRunRead,
    ChatRequest,
    ChatResponse,
    ConversationCreate,
    ConversationRead,
)
from app.services.chat_service import chat_service

router = APIRouter()


@router.get("/conversations", response_model=list[ConversationRead])
async def list_conversations(agent_id: str | None = None) -> list[ConversationRead]:
    return chat_service.list_conversations(agent_id)


@router.post("/conversations", response_model=ConversationRead, status_code=201)
async def create_conversation(payload: ConversationCreate) -> ConversationRead:
    return chat_service.create_conversation(payload)


@router.get("/conversations/{conversation_id}", response_model=ConversationRead)
async def get_conversation(conversation_id: str) -> ConversationRead:
    return chat_service.get_conversation(conversation_id)


@router.get("/runs", response_model=list[AgentRunRead])
async def list_runs() -> list[AgentRunRead]:
    return chat_service.list_runs()


@router.post("", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    return await chat_service.invoke(payload)


@router.post("/stream")
async def stream_chat(payload: ChatRequest) -> StreamingResponse:
    return StreamingResponse(chat_service.stream(payload), media_type="text/event-stream")
