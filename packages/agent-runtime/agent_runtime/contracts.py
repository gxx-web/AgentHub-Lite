from dataclasses import dataclass, field


@dataclass(slots=True)
class ModelConfig:
    provider_id: str
    model_name: str
    temperature: float = 0.7
    max_tokens: int | None = None


@dataclass(slots=True)
class AgentConfig:
    id: str
    name: str
    system_prompt: str
    model: ModelConfig
    skill_ids: list[str] = field(default_factory=list)
    knowledge_base_ids: list[str] = field(default_factory=list)
    mcp_tool_ids: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ChatMessage:
    role: str
    content: str


@dataclass(slots=True)
class ChatResult:
    content: str
    tool_calls: list[dict] = field(default_factory=list)
    retrieved_chunks: list[dict] = field(default_factory=list)

