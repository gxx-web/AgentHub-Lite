import asyncio
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.chat import (
    AgentRunRead,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ConversationCreate,
    ConversationRead,
)
from app.services.agent_service import agent_service
from app.services.model_provider_service import model_provider_service


class ChatService:
    def __init__(self) -> None:
        now = self._now()
        self._conversations: dict[str, ConversationRead] = {
            "default-conversation": ConversationRead(
                id="default-conversation",
                agent_id="default-agent",
                title="Default conversation",
                messages=[
                    ChatMessage(
                        id="welcome-message",
                        role="assistant",
                        content="Hi, I am the default assistant. Ask me anything.",
                        created_at=now,
                    )
                ],
                created_at=now,
                updated_at=now,
            )
        }
        self._runs: list[AgentRunRead] = []

    def list_conversations(self, agent_id: str | None = None) -> list[ConversationRead]:
        conversations = list(self._conversations.values())
        if agent_id:
            conversations = [
                conversation
                for conversation in conversations
                if conversation.agent_id == agent_id
            ]
        return sorted(conversations, key=lambda item: item.updated_at, reverse=True)

    def create_conversation(self, payload: ConversationCreate) -> ConversationRead:
        agent = agent_service.get_agent(payload.agent_id)
        now = self._now()
        conversation_id = f"conv-{uuid4().hex[:12]}"
        conversation = ConversationRead(
            id=conversation_id,
            agent_id=agent.id,
            title=payload.title or f"{agent.name} chat",
            messages=[
                ChatMessage(
                    id=f"msg-{uuid4().hex[:12]}",
                    role="assistant",
                    content=agent.opening_message,
                    created_at=now,
                )
            ],
            created_at=now,
            updated_at=now,
        )
        self._conversations[conversation_id] = conversation
        return conversation

    def get_conversation(self, conversation_id: str) -> ConversationRead:
        conversation = self._conversations.get(conversation_id)
        if conversation is None:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation

    def list_runs(self) -> list[AgentRunRead]:
        return list(reversed(self._runs[-50:]))

    async def invoke(self, payload: ChatRequest) -> ChatResponse:
        agent = agent_service.get_agent(payload.agent_id)
        conversation = self._resolve_conversation(payload)
        user_input = payload.input or self._last_user_message(payload)
        if user_input:
            conversation = self._append_message(conversation, "user", user_input)
        content = await self._generate_response(
            agent_name=agent.name,
            provider_id=agent.model_provider_id,
            system_prompt=agent.system_prompt,
            model_name=agent.model_name,
            temperature=agent.temperature,
            max_tokens=agent.max_tokens,
            messages=conversation.messages,
            user_input=user_input,
        )
        conversation = self._append_message(conversation, "assistant", content)
        self._runs.append(
            AgentRunRead(
                id=f"run-{uuid4().hex[:12]}",
                agent_id=agent.id,
                conversation_id=conversation.id,
                status="succeeded",
                input=user_input or "",
                output=content,
                created_at=self._now(),
            )
        )
        return ChatResponse(
            agent_id=agent.id,
            conversation_id=conversation.id,
            content=content,
            messages=conversation.messages,
        )

    async def stream(self, payload: ChatRequest) -> AsyncIterator[str]:
        response = await self.invoke(payload)
        yield f"event: conversation\ndata: {response.conversation_id}\n\n"
        for token in response.content.split(" "):
            await asyncio.sleep(0.02)
            yield f"event: message\ndata: {token} \n\n"
        yield "event: done\ndata: [DONE]\n\n"

    def _last_user_message(self, payload: ChatRequest) -> str | None:
        for message in reversed(payload.messages):
            if message.role == "user":
                return message.content
        return None

    def _resolve_conversation(self, payload: ChatRequest) -> ConversationRead:
        if payload.conversation_id:
            return self.get_conversation(payload.conversation_id)
        if payload.messages:
            now = self._now()
            conversation_id = f"conv-{uuid4().hex[:12]}"
            conversation = ConversationRead(
                id=conversation_id,
                agent_id=payload.agent_id,
                title="Ad hoc chat",
                messages=[
                    message.model_copy(
                        update={
                            "id": message.id or f"msg-{uuid4().hex[:12]}",
                            "created_at": message.created_at or now,
                        }
                    )
                    for message in payload.messages
                ],
                created_at=now,
                updated_at=now,
            )
            self._conversations[conversation_id] = conversation
            return conversation
        return self.create_conversation(ConversationCreate(agent_id=payload.agent_id))

    def _append_message(
        self,
        conversation: ConversationRead,
        role: str,
        content: str,
    ) -> ConversationRead:
        now = self._now()
        messages = [
            *conversation.messages,
            ChatMessage(
                id=f"msg-{uuid4().hex[:12]}",
                role=role,
                content=content,
                created_at=now,
            ),
        ]
        updated = conversation.model_copy(update={"messages": messages, "updated_at": now})
        self._conversations[conversation.id] = updated
        return updated

    async def _generate_response(
        self,
        agent_name: str,
        provider_id: str,
        system_prompt: str,
        model_name: str,
        temperature: float,
        max_tokens: int | None,
        messages: list[ChatMessage],
        user_input: str | None,
    ) -> str:
        provider = model_provider_service.get_provider(provider_id)
        if provider.api_key:
            return await asyncio.to_thread(
                model_provider_service.call_chat_completion,
                provider,
                model_name,
                system_prompt,
                temperature,
                max_tokens,
                messages,
            )
        return self._build_fallback_response(agent_name, system_prompt, user_input)

    def _build_fallback_response(
        self,
        agent_name: str,
        system_prompt: str,
        user_input: str | None,
    ) -> str:
        prompt_hint = system_prompt.strip().splitlines()[0][:120] if system_prompt else ""
        if not user_input:
            return f"{agent_name} 已就绪。发送一条消息开始会话。"
        return (
            f"{agent_name} 收到了你的消息：{user_input}。"
            f"当前使用的系统提示词：{prompt_hint}"
        )

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)


chat_service = ChatService()
