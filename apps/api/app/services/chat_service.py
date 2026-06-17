import asyncio
from collections.abc import AsyncIterator

from app.schemas.chat import ChatRequest, ChatResponse


class ChatService:
    async def invoke(self, payload: ChatRequest) -> ChatResponse:
        user_input = payload.input or self._last_user_message(payload)
        content = (
            "AgentHub-Lite runtime is ready. "
            f"Received: {user_input or 'empty message'}"
        )
        return ChatResponse(agent_id=payload.agent_id, content=content)

    async def stream(self, payload: ChatRequest) -> AsyncIterator[str]:
        response = await self.invoke(payload)
        for token in response.content.split(" "):
            await asyncio.sleep(0.02)
            yield f"event: message\ndata: {token} \n\n"
        yield "event: done\ndata: [DONE]\n\n"

    def _last_user_message(self, payload: ChatRequest) -> str | None:
        for message in reversed(payload.messages):
            if message.role == "user":
                return message.content
        return None


chat_service = ChatService()
