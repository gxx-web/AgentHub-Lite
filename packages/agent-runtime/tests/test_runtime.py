import asyncio

from agent_runtime import AgentConfig, AgentRuntime, ChatMessage, ModelConfig


def test_runtime_echoes_user_message() -> None:
    runtime = AgentRuntime(
        AgentConfig(
            id="default-agent",
            name="Default Assistant",
            system_prompt="You are helpful.",
            model=ModelConfig(provider_id="openai-compatible", model_name="gpt-4.1-mini"),
        )
    )

    result = asyncio.run(runtime.invoke([ChatMessage(role="user", content="hello")]))

    assert "hello" in result.content
