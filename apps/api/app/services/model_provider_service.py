import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import HTTPException

from app.core.database import db_connection
from app.schemas.chat import ChatMessage
from app.schemas.model_provider import (
    ModelProviderCreate,
    ModelProviderConfig,
    ModelProviderTestRequest,
    ModelProviderTestResponse,
    ModelProviderUpdate,
)


class ModelProviderService:
    def list_providers(self, workspace_id: str) -> list[ModelProviderConfig]:
        with db_connection() as connection:
            rows = connection.execute(
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
                WHERE mp.workspace_id = %s
                ORDER BY mp.is_default DESC, mp.updated_at DESC
                """,
                (workspace_id,),
            ).fetchall()
            return [self._row_to_config(row) for row in rows]

    def get_provider(self, provider_id: str, workspace_id: str) -> ModelProviderConfig:
        with db_connection() as connection:
            return self._get_provider(connection, provider_id, workspace_id)

    def create_provider(self, payload: ModelProviderCreate, workspace_id: str) -> ModelProviderConfig:
        provider_id = self._slugify(payload.name)
        if not provider_id:
            raise HTTPException(status_code=400, detail="Model provider name is required")
        available_models = [
            model.strip()
            for model in payload.available_models
            if model and model.strip()
        ]
        if not available_models:
            available_models = [payload.default_model]
        if payload.default_model not in available_models:
            available_models = [payload.default_model, *available_models]

        with db_connection() as connection:
            exists = connection.execute(
                "SELECT 1 FROM model_providers WHERE id = %s AND workspace_id = %s",
                (provider_id, workspace_id),
            ).fetchone()
            if exists:
                raise HTTPException(status_code=409, detail="Model provider already exists")

            connection.execute(
                """
                INSERT INTO model_providers (
                  id,
                  workspace_id,
                  name,
                  provider_type,
                  base_url,
                  default_model,
                  available_models,
                  supports_streaming,
                  supports_tool_calling
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    provider_id,
                    workspace_id,
                    payload.name.strip(),
                    payload.provider_type,
                    payload.base_url,
                    payload.default_model,
                    available_models,
                    payload.supports_streaming,
                    payload.supports_tool_calling,
                ),
            )
            if payload.api_key:
                connection.execute(
                    """
                    INSERT INTO model_credentials (model_provider_id, encrypted_api_key)
                    VALUES (%s, %s)
                    """,
                    (provider_id, payload.api_key),
                )
            return self._get_provider(connection, provider_id, workspace_id)

    def update_provider(
        self,
        provider_id: str,
        payload: ModelProviderUpdate,
        workspace_id: str,
    ) -> ModelProviderConfig:
        updates = payload.model_dump(exclude_unset=True)
        with db_connection() as connection:
            provider = self._get_provider(connection, provider_id, workspace_id)
            available_models = updates.get("available_models", provider.available_models)
            if available_models is not None:
                available_models = [
                    model.strip()
                    for model in available_models
                    if model and model.strip()
                ]
            default_model = updates.get("default_model", provider.default_model)
            if not available_models:
                available_models = [default_model]
            if default_model not in available_models:
                available_models = [default_model, *available_models]

            merged = {
                "id": provider_id,
                "name": updates.get("name", provider.name),
                "provider_type": updates.get("provider_type", provider.provider_type),
                "base_url": updates.get("base_url", provider.base_url),
                "default_model": default_model,
                "available_models": available_models,
                "supports_streaming": updates.get("supports_streaming", provider.supports_streaming),
                "supports_tool_calling": updates.get(
                    "supports_tool_calling",
                    provider.supports_tool_calling,
                ),
            }
            connection.execute(
                """
                UPDATE model_providers
                SET
                  name = %(name)s,
                  provider_type = %(provider_type)s,
                  base_url = %(base_url)s,
                  default_model = %(default_model)s,
                  available_models = %(available_models)s,
                  supports_streaming = %(supports_streaming)s,
                  supports_tool_calling = %(supports_tool_calling)s
                WHERE id = %(id)s AND workspace_id = %(workspace_id)s
                """,
                {**merged, "workspace_id": workspace_id},
            )

            api_key = updates.get("api_key")
            if api_key:
                connection.execute(
                    """
                    INSERT INTO model_credentials (model_provider_id, encrypted_api_key)
                    VALUES (%s, %s)
                    ON CONFLICT (model_provider_id)
                    DO UPDATE SET encrypted_api_key = EXCLUDED.encrypted_api_key
                    """,
                    (provider_id, api_key),
                )
            return self._get_provider(connection, provider_id, workspace_id)

    def delete_provider(self, provider_id: str, workspace_id: str) -> None:
        if provider_id == "openai-compatible":
            raise HTTPException(status_code=400, detail="Default model provider cannot be deleted")
        with db_connection() as connection:
            in_use = connection.execute(
                "SELECT 1 FROM agents WHERE model_provider_id = %s AND workspace_id = %s LIMIT 1",
                (provider_id, workspace_id),
            ).fetchone()
            if in_use:
                raise HTTPException(status_code=409, detail="Model provider is used by agents")
            result = connection.execute(
                "DELETE FROM model_providers WHERE id = %s AND workspace_id = %s",
                (provider_id, workspace_id),
            )
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Model provider not found")

    def test_provider(
        self,
        provider_id: str,
        payload: ModelProviderTestRequest,
        workspace_id: str,
    ) -> ModelProviderTestResponse:
        provider = self.get_provider(provider_id, workspace_id)
        model_name = payload.model or provider.default_model
        content = self.call_chat_completion(
            provider=provider,
            model_name=model_name,
            system_prompt="你是一个用于测试模型连通性的助手。",
            temperature=0.2,
            max_tokens=100,
            messages=[ChatMessage(role="user", content=payload.message)],
        )
        return ModelProviderTestResponse(ok=True, message=content)

    def call_chat_completion(
        self,
        provider: ModelProviderConfig,
        model_name: str,
        system_prompt: str,
        temperature: float,
        max_tokens: int | None,
        messages: list[ChatMessage],
    ) -> str:
        if not provider.api_key:
            raise HTTPException(status_code=400, detail="当前模型供应商未配置 API Key")

        endpoint = provider.base_url.rstrip("/") + "/chat/completions"
        payload: dict[str, object] = {
            "model": model_name or provider.default_model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                *[
                    {"role": message.role, "content": message.content}
                    for message in messages
                    if message.role in {"user", "assistant", "system"} and message.content
                ],
            ],
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        request = Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {provider.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=60) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise HTTPException(
                status_code=502,
                detail={
                    "message": "模型供应商返回错误",
                    "provider": provider.name,
                    "endpoint": endpoint,
                    "model": model_name,
                    "status_code": exc.code,
                    "response": detail,
                },
            ) from exc
        except URLError as exc:
            raise HTTPException(
                status_code=502,
                detail={
                    "message": "无法连接模型供应商",
                    "provider": provider.name,
                    "endpoint": endpoint,
                    "model": model_name,
                    "error": str(exc),
                },
            ) from exc
        except TimeoutError as exc:
            raise HTTPException(status_code=504, detail="模型供应商请求超时") from exc

        try:
            return body["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as exc:
            raise HTTPException(
                status_code=502,
                detail={
                    "message": "模型供应商返回格式不符合 OpenAI Compatible Chat Completions",
                    "provider": provider.name,
                    "model": model_name,
                    "response": body,
                },
            ) from exc

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
        return self._row_to_config(row)

    def _row_to_config(self, row) -> ModelProviderConfig:
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

    def _slugify(self, value: str) -> str:
        slug = "".join(char.lower() if char.isalnum() else "-" for char in value.strip())
        return "-".join(part for part in slug.split("-") if part)


model_provider_service = ModelProviderService()
