from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    agent_id: str = "default-agent"
    messages: list[ChatMessage] = Field(default_factory=list)
    input: str | None = None
    stream: bool = False


class ChatResponse(BaseModel):
    agent_id: str
    content: str

