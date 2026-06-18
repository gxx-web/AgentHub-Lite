from pydantic import BaseModel, Field


class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: str | None = None
    system_prompt: str = "You are a helpful AI agent."
    model_provider_id: str = "openai-compatible"
    model_name: str = "gpt-4.1-mini"
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int | None = Field(default=1024, ge=1, le=128000)
    knowledge_base_ids: list[str] = Field(default_factory=list)
    skill_ids: list[str] = Field(default_factory=list)
    mcp_tool_ids: list[str] = Field(default_factory=list)
    opening_message: str = "Hi, I am ready to help."
    example_questions: list[str] = Field(default_factory=list)


class AgentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    description: str | None = None
    system_prompt: str | None = None
    model_provider_id: str | None = None
    model_name: str | None = None
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1, le=128000)
    knowledge_base_ids: list[str] | None = None
    skill_ids: list[str] | None = None
    mcp_tool_ids: list[str] | None = None
    opening_message: str | None = None
    example_questions: list[str] | None = None


class AgentRead(AgentCreate):
    id: str
    workspace_id: str = "default"

