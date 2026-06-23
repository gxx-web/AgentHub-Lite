from fastapi import APIRouter, Depends
from starlette.responses import StreamingResponse

from app.core.deps import CurrentUser, get_current_user
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
async def list_conversations(
    agent_id: str | None = None,
    current_user: CurrentUser = Depends(get_current_user),
) -> list[ConversationRead]:
    return chat_service.list_conversations(agent_id, current_user.workspace_id)


@router.post("/conversations", response_model=ConversationRead, status_code=201)
async def create_conversation(
    payload: ConversationCreate,
    current_user: CurrentUser = Depends(get_current_user),
) -> ConversationRead:
    return chat_service.create_conversation(payload, current_user.workspace_id, current_user.user_id)


@router.get("/conversations/{conversation_id}", response_model=ConversationRead)
async def get_conversation(
    conversation_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> ConversationRead:
    return chat_service.get_conversation(conversation_id, current_user.workspace_id)


@router.get("/runs", response_model=list[AgentRunRead])
async def list_runs(current_user: CurrentUser = Depends(get_current_user)) -> list[AgentRunRead]:
    return chat_service.list_runs(current_user.workspace_id)


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> ChatResponse:
    return await chat_service.invoke(payload, current_user.workspace_id, current_user.user_id)


@router.post("/stream")
async def stream_chat(
    payload: ChatRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> StreamingResponse:
    return StreamingResponse(
        chat_service.stream(payload, current_user.workspace_id, current_user.user_id),
        media_type="text/event-stream",
    )
