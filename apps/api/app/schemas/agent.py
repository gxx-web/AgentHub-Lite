from pydantic import BaseModel, Field


class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: str | None = None
    system_prompt: str = "You are a helpful AI agent."
    model_provider_id: str = "openai-compatible"
    model_name: str = "gpt-4.1-mini"


class AgentRead(AgentCreate):
    id: str
    workspace_id: str = "default"

