import asyncio
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException

from app.core.database import db_connection
from app.schemas.chat import (
    AgentRunRead,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ConversationCreate,
    ConversationRead,
)
from app.schemas.agent import AgentRead
from app.schemas.model_provider import ModelProviderConfig
from app.services.agent_service import agent_service
from app.services.model_provider_service import model_provider_service


class ChatService:
    def list_conversations(self, agent_id: str | None = None, workspace_id: str = "default") -> list[ConversationRead]:
        with db_connection() as connection:
            if agent_id:
                rows = connection.execute(
                    """
                    SELECT
                      c.id,
                      c.agent_id,
                      c.title,
                      c.created_at,
                      c.updated_at,
                      latest.id AS latest_message_id,
                      latest.role AS latest_message_role,
                      latest.content AS latest_message_content,
                      latest.created_at AS latest_message_created_at
                    FROM conversations c
                    LEFT JOIN LATERAL (
                      SELECT id, role, content, created_at
                      FROM messages
                      WHERE conversation_id = c.id
                      ORDER BY created_at DESC, id DESC
                      LIMIT 1
                    ) latest ON true
                    WHERE c.workspace_id = %s AND c.agent_id = %s AND c.status <> 'deleted'
                    ORDER BY c.updated_at DESC
                    """,
                    (workspace_id, agent_id),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT
                      c.id,
                      c.agent_id,
                      c.title,
                      c.created_at,
                      c.updated_at,
                      latest.id AS latest_message_id,
                      latest.role AS latest_message_role,
                      latest.content AS latest_message_content,
                      latest.created_at AS latest_message_created_at
                    FROM conversations c
                    LEFT JOIN LATERAL (
                      SELECT id, role, content, created_at
                      FROM messages
                      WHERE conversation_id = c.id
                      ORDER BY created_at DESC, id DESC
                      LIMIT 1
                    ) latest ON true
                    WHERE c.workspace_id = %s AND c.status <> 'deleted'
                    ORDER BY c.updated_at DESC
                    """,
                    (workspace_id,),
                ).fetchall()
            return [self._row_to_conversation_summary(connection, row) for row in rows]

    def create_conversation(
        self,
        payload: ConversationCreate,
        workspace_id: str = "default",
        user_id: str | None = None,
    ) -> ConversationRead:
        agent = agent_service.get_agent(payload.agent_id, workspace_id)
        now = self._now()
        conversation_id = f"conv-{uuid4().hex[:12]}"
        with db_connection() as connection:
            row = connection.execute(
                """
                INSERT INTO conversations (
                  id,
                  workspace_id,
                  agent_id,
                  user_id,
                  title,
                  channel,
                  created_at,
                  updated_at
                )
                VALUES (%s, %s, %s, %s, %s, 'web', %s, %s)
                RETURNING id, agent_id, title, created_at, updated_at
                """,
                (
                    conversation_id,
                    workspace_id,
                    agent.id,
                    user_id,
                    payload.title or f"{agent.name} chat",
                    now,
                    now,
                ),
            ).fetchone()
            connection.execute(
                """
                INSERT INTO messages (id, conversation_id, agent_id, role, content, created_at)
                VALUES (%s, %s, %s, 'assistant', %s, %s)
                """,
                (
                    f"msg-{uuid4().hex[:12]}",
                    conversation_id,
                    agent.id,
                    agent.opening_message,
                    now,
                ),
            )
            assert row is not None
            return self._row_to_conversation(connection, row)

    def get_conversation(self, conversation_id: str, workspace_id: str = "default") -> ConversationRead:
        with db_connection() as connection:
            row = self._get_conversation_row(connection, conversation_id, workspace_id)
            return self._row_to_conversation(connection, row)

    def list_runs(self, workspace_id: str) -> list[AgentRunRead]:
        with db_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                  id,
                  agent_id,
                  conversation_id,
                  status,
                  input,
                  output,
                  model_name,
                  error_message,
                  created_at,
                  completed_at
                FROM agent_runs
                WHERE workspace_id = %s
                ORDER BY created_at DESC
                LIMIT 50
                """,
                (workspace_id,),
            ).fetchall()
            return [
                AgentRunRead(
                    id=row["id"],
                    agent_id=row["agent_id"],
                    conversation_id=row["conversation_id"],
                    status=row["status"],
                    input=row["input"],
                    output=row["output"],
                    model_name=row["model_name"],
                    error_message=row["error_message"],
                    created_at=row["created_at"],
                    completed_at=row["completed_at"],
                )
                for row in rows
            ]

    async def invoke(self, payload: ChatRequest, workspace_id: str, user_id: str) -> ChatResponse:
        user_input = payload.input or self._last_user_message(payload)
        with db_connection() as connection:
            agent = self._get_agent(connection, payload.agent_id, workspace_id)
            conversation = self._resolve_conversation(
                connection,
                payload,
                agent,
                workspace_id,
                user_id,
            )
            if user_input:
                conversation = self._append_message(
                    connection,
                    conversation.id,
                    agent.id,
                    "user",
                    user_input,
                    workspace_id,
                    user_id,
                )
            provider = self._get_provider(connection, agent.model_provider_id, workspace_id)

        try:
            content = await self._generate_response(
                agent_name=agent.name,
                provider=provider,
                system_prompt=agent.system_prompt,
                model_name=agent.model_name,
                temperature=agent.temperature,
                max_tokens=agent.max_tokens,
                messages=conversation.messages,
                user_input=user_input,
            )
        except Exception as exc:
            with db_connection() as connection:
                self._record_run(
                    connection,
                    agent,
                    conversation.id,
                    user_id,
                    user_input or "",
                    "",
                    "failed",
                    str(exc),
                )
            raise
        with db_connection() as connection:
            conversation = self._append_message(
                connection,
                conversation.id,
                agent.id,
                "assistant",
                content,
                workspace_id,
                None,
            )
            self._record_run(connection, agent, conversation.id, user_id, user_input or "", content, "succeeded")
        return ChatResponse(
            agent_id=agent.id,
            conversation_id=conversation.id,
            content=content,
            messages=conversation.messages,
        )

    async def stream(self, payload: ChatRequest, workspace_id: str, user_id: str) -> AsyncIterator[str]:
        user_input = payload.input or self._last_user_message(payload)
        with db_connection() as connection:
            agent = self._get_agent(connection, payload.agent_id, workspace_id)
            conversation = self._resolve_conversation(
                connection,
                payload,
                agent,
                workspace_id,
                user_id,
            )
            if user_input:
                conversation = self._append_message(
                    connection,
                    conversation.id,
                    agent.id,
                    "user",
                    user_input,
                    workspace_id,
                    user_id,
                )
            provider = self._get_provider(connection, agent.model_provider_id, workspace_id)

        yield self._sse("conversation", conversation.id)

        content = ""
        try:
            content = await self._generate_response(
                agent_name=agent.name,
                provider=provider,
                system_prompt=agent.system_prompt,
                model_name=agent.model_name,
                temperature=agent.temperature,
                max_tokens=agent.max_tokens,
                messages=conversation.messages,
                user_input=user_input,
            )
            for token in self._chunk_content(content):
                await asyncio.sleep(0.02)
                yield self._sse("message", token)
            with db_connection() as connection:
                conversation = self._append_message(
                    connection,
                    conversation.id,
                    agent.id,
                    "assistant",
                    content,
                    workspace_id,
                    None,
                )
                self._record_run(
                    connection,
                    agent,
                    conversation.id,
                    user_id,
                    user_input or "",
                    content,
                    "succeeded",
                )
            yield self._sse("done", "[DONE]")
        except Exception as exc:
            error_message = str(exc)
            with db_connection() as connection:
                self._record_run(
                    connection,
                    agent,
                    conversation.id,
                    user_id,
                    user_input or "",
                    content,
                    "failed",
                    error_message,
                )
            yield self._sse("error", error_message)

    def _resolve_conversation(
        self,
        connection,
        payload: ChatRequest,
        agent: AgentRead,
        workspace_id: str,
        user_id: str,
    ) -> ConversationRead:
        if payload.conversation_id:
            row = self._get_conversation_row(connection, payload.conversation_id, workspace_id)
            return self._row_to_conversation(connection, row)
        if payload.messages:
            return self._create_ad_hoc_conversation(connection, payload, agent, workspace_id, user_id)
        return self._create_conversation(connection, ConversationCreate(agent_id=agent.id), agent, workspace_id, user_id)

    def _create_conversation(
        self,
        connection,
        payload: ConversationCreate,
        agent: AgentRead,
        workspace_id: str,
        user_id: str | None,
    ) -> ConversationRead:
        now = self._now()
        conversation_id = f"conv-{uuid4().hex[:12]}"
        row = connection.execute(
            """
            INSERT INTO conversations (
              id,
              workspace_id,
              agent_id,
              user_id,
              title,
              channel,
              created_at,
              updated_at
            )
            VALUES (%s, %s, %s, %s, %s, 'web', %s, %s)
            RETURNING id, agent_id, title, created_at, updated_at
            """,
            (
                conversation_id,
                workspace_id,
                agent.id,
                user_id,
                payload.title or f"{agent.name} chat",
                now,
                now,
            ),
        ).fetchone()
        connection.execute(
            """
            INSERT INTO messages (id, conversation_id, agent_id, role, content, created_at)
            VALUES (%s, %s, %s, 'assistant', %s, %s)
            """,
            (
                f"msg-{uuid4().hex[:12]}",
                conversation_id,
                agent.id,
                agent.opening_message,
                now,
            ),
        )
        assert row is not None
        return self._row_to_conversation(connection, row)

    def _create_ad_hoc_conversation(
        self,
        connection,
        payload: ChatRequest,
        agent: AgentRead,
        workspace_id: str,
        user_id: str,
    ) -> ConversationRead:
        now = self._now()
        conversation_id = f"conv-{uuid4().hex[:12]}"
        row = connection.execute(
            """
            INSERT INTO conversations (
              id,
              workspace_id,
              agent_id,
              user_id,
              title,
              channel,
              created_at,
              updated_at
            )
            VALUES (%s, %s, %s, %s, 'Ad hoc chat', 'web', %s, %s)
            RETURNING id, agent_id, title, created_at, updated_at
            """,
            (conversation_id, workspace_id, agent.id, user_id, now, now),
        ).fetchone()
        for message in payload.messages:
            connection.execute(
                """
                INSERT INTO messages (id, conversation_id, agent_id, role, content, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    message.id or f"msg-{uuid4().hex[:12]}",
                    conversation_id,
                    agent.id,
                    message.role,
                    message.content,
                    message.created_at or now,
                ),
            )
        assert row is not None
        return self._row_to_conversation(connection, row)

    def _append_message(
        self,
        connection,
        conversation_id: str,
        agent_id: str,
        role: str,
        content: str,
        workspace_id: str,
        user_id: str | None,
    ) -> ConversationRead:
        now = self._now()
        connection.execute(
            """
            INSERT INTO messages (id, conversation_id, agent_id, user_id, role, content, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (f"msg-{uuid4().hex[:12]}", conversation_id, agent_id, user_id, role, content, now),
        )
        connection.execute(
            "UPDATE conversations SET updated_at = %s WHERE id = %s",
            (now, conversation_id),
        )
        row = self._get_conversation_row(connection, conversation_id, workspace_id)
        return self._row_to_conversation(connection, row)

    def _record_run(
        self,
        connection,
        agent: AgentRead,
        conversation_id: str,
        user_id: str,
        user_input: str,
        output: str,
        status: str,
        error_message: str | None = None,
    ) -> None:
        connection.execute(
            """
            INSERT INTO agent_runs (
              id,
              workspace_id,
              agent_id,
              conversation_id,
              user_id,
              status,
              input,
              output,
              model_provider_id,
              model_name,
              error_message,
              created_at,
              completed_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                f"run-{uuid4().hex[:12]}",
                agent.workspace_id,
                agent.id,
                conversation_id,
                user_id,
                status,
                user_input,
                output,
                agent.model_provider_id,
                agent.model_name,
                error_message,
                self._now(),
                self._now(),
            ),
        )

    async def _generate_response(
        self,
        agent_name: str,
        provider: ModelProviderConfig,
        system_prompt: str,
        model_name: str,
        temperature: float,
        max_tokens: int | None,
        messages: list[ChatMessage],
        user_input: str | None,
    ) -> str:
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

    def _get_agent(self, connection, agent_id: str, workspace_id: str) -> AgentRead:
        row = connection.execute(
            """
            SELECT
              id,
              workspace_id,
              name,
              description,
              system_prompt,
              model_provider_id,
              model_name,
              temperature,
              max_tokens,
              opening_message,
              example_questions
            FROM agents
            WHERE id = %s AND workspace_id = %s
            """,
            (agent_id, workspace_id),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Agent not found")
        return AgentRead(
            id=row["id"],
            workspace_id=row["workspace_id"],
            name=row["name"],
            description=row["description"],
            system_prompt=row["system_prompt"],
            model_provider_id=row["model_provider_id"],
            model_name=row["model_name"],
            temperature=float(row["temperature"]),
            max_tokens=row["max_tokens"],
            knowledge_base_ids=[],
            skill_ids=[],
            mcp_tool_ids=[],
            opening_message=row["opening_message"],
            example_questions=list(row["example_questions"] or []),
        )

    def _get_provider(
        self,
        connection,
        provider_id: str,
        workspace_id: str,
    ) -> ModelProviderConfig:
        row = connection.execute(
            """
            SELECT
              mp.id,
              mp.name,
              mp.provider_type,
              mp.base_url,
              mp.default_model,
              mp.available_models,
              mp.supports_streaming,
              mp.supports_tool_calling,
              mc.encrypted_api_key
            FROM model_providers mp
            LEFT JOIN model_credentials mc ON mc.model_provider_id = mp.id
            WHERE mp.id = %s AND mp.workspace_id = %s
            """,
            (provider_id, workspace_id),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Model provider not found")
        return ModelProviderConfig(
            id=row["id"],
            name=row["name"],
            provider_type=row["provider_type"],
            base_url=row["base_url"],
            api_key=row["encrypted_api_key"],
            default_model=row["default_model"],
            available_models=list(row["available_models"] or []),
            supports_streaming=row["supports_streaming"],
            supports_tool_calling=row["supports_tool_calling"],
        )

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

    def _chunk_content(self, content: str) -> list[str]:
        if " " in content:
            return [part + " " for part in content.split(" ") if part]
        return [content[index : index + 12] for index in range(0, len(content), 12)]

    def _sse(self, event: str, data: str) -> str:
        lines = str(data).splitlines() or [""]
        payload = "\n".join(f"data: {line}" for line in lines)
        return f"event: {event}\n{payload}\n\n"

    def _row_to_conversation(self, connection, row) -> ConversationRead:
        return ConversationRead(
            id=row["id"],
            agent_id=row["agent_id"],
            title=row["title"],
            messages=self._list_messages(connection, row["id"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _row_to_conversation_summary(self, connection, row) -> ConversationRead:
        latest_message_id = row.get("latest_message_id")
        return ConversationRead(
            id=row["id"],
            agent_id=row["agent_id"],
            title=row["title"],
            messages=[
                ChatMessage(
                    id=latest_message_id,
                    role=row["latest_message_role"],
                    content=row["latest_message_content"],
                    created_at=row["latest_message_created_at"],
                )
            ]
            if latest_message_id
            else [],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _list_messages(self, connection, conversation_id: str) -> list[ChatMessage]:
        rows = connection.execute(
            """
            SELECT id, role, content, created_at
            FROM messages
            WHERE conversation_id = %s
            ORDER BY created_at ASC, id ASC
            """,
            (conversation_id,),
        ).fetchall()
        return [
            ChatMessage(
                id=row["id"],
                role=row["role"],
                content=row["content"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def _get_conversation_row(self, connection, conversation_id: str, workspace_id: str):
        row = connection.execute(
            """
            SELECT id, agent_id, title, created_at, updated_at
            FROM conversations
            WHERE id = %s AND workspace_id = %s AND status <> 'deleted'
            """,
            (conversation_id, workspace_id),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return row

    def _last_user_message(self, payload: ChatRequest) -> str | None:
        for message in reversed(payload.messages):
            if message.role == "user":
                return message.content
        return None

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)


chat_service = ChatService()
