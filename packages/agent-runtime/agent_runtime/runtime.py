from agent_runtime.contracts import AgentConfig, ChatMessage, ChatResult


class AgentRuntime:
    """Minimal runtime boundary before LangChain / LangGraph integration."""

    def __init__(self, agent: AgentConfig) -> None:
        self.agent = agent

    async def invoke(self, messages: list[ChatMessage]) -> ChatResult:
        last_user_message = next(
            (message.content for message in reversed(messages) if message.role == "user"),
            "",
        )
        return ChatResult(
            content=(
                f"{self.agent.name} is ready. "
                f"Runtime received: {last_user_message or 'empty message'}"
            )
        )

