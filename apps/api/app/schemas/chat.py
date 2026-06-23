from datetime import datetime

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    id: str | None = None
    role: str
    content: str
    created_at: datetime | None = None


class ChatRequest(BaseModel):
    agent_id: str = "default-agent"
    conversation_id: str | None = None
    messages: list[ChatMessage] = Field(default_factory=list)
    input: str | None = None
    stream: bool = False


class ChatResponse(BaseModel):
    agent_id: str
    conversation_id: str
    content: str
    messages: list[ChatMessage] = Field(default_factory=list)


class ConversationCreate(BaseModel):
    agent_id: str = "default-agent"
    title: str | None = None


class ConversationRead(BaseModel):
    id: str
    agent_id: str
    title: str
    messages: list[ChatMessage] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class AgentRunRead(BaseModel):
    id: str
    agent_id: str
    conversation_id: str | None = None
    status: str
    input: str
    output: str
    model_name: str | None = None
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None

