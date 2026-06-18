import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import HTTPException

from app.core.config import settings
from app.schemas.chat import ChatMessage
from app.schemas.model_provider import (
    ModelProviderConfig,
    ModelProviderTestRequest,
    ModelProviderTestResponse,
    ModelProviderUpdate,
)


class ModelProviderService:
    def __init__(self) -> None:
        default_models = self._split_models(settings.openai_compatible_model)
        self._providers: dict[str, ModelProviderConfig] = {
            "openai-compatible": ModelProviderConfig(
                id="openai-compatible",
                name="OpenAI Compatible",
                provider_type="openai-compatible",
                base_url=settings.openai_compatible_base_url,
                api_key=settings.openai_compatible_api_key,
                default_model=default_models[0],
                available_models=default_models,
                supports_streaming=True,
                supports_tool_calling=True,
            )
        }

    def list_providers(self) -> list[ModelProviderConfig]:
        return list(self._providers.values())

    def get_provider(self, provider_id: str) -> ModelProviderConfig:
        provider = self._providers.get(provider_id)
        if provider is None:
            raise HTTPException(status_code=404, detail="Model provider not found")
        return provider

    def update_provider(
        self,
        provider_id: str,
        payload: ModelProviderUpdate,
    ) -> ModelProviderConfig:
        provider = self.get_provider(provider_id)
        updates = payload.model_dump(exclude_unset=True)
        if "available_models" in updates and updates["available_models"] is not None:
            updates["available_models"] = [
                model.strip()
                for model in updates["available_models"]
                if model and model.strip()
            ]
        if updates.get("api_key") == "":
            updates.pop("api_key")
        updated = provider.model_copy(update=updates)
        if not updated.available_models:
            updated = updated.model_copy(update={"available_models": [updated.default_model]})
        if updated.default_model not in updated.available_models:
            updated = updated.model_copy(
                update={"available_models": [updated.default_model, *updated.available_models]}
            )
        self._providers[provider_id] = updated
        return updated

    def test_provider(
        self,
        provider_id: str,
        payload: ModelProviderTestRequest,
    ) -> ModelProviderTestResponse:
        provider = self.get_provider(provider_id)
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

    def _split_models(self, value: str) -> list[str]:
        models = [model.strip() for model in value.replace("\n", ",").split(",") if model.strip()]
        return models or ["gpt-4.1-mini"]


model_provider_service = ModelProviderService()
