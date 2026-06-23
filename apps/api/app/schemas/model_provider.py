from pydantic import BaseModel, Field


class ModelProviderRead(BaseModel):
    id: str
    name: str
    provider_type: str
    base_url: str
    default_model: str
    available_models: list[str] = Field(default_factory=list)
    has_api_key: bool = False
    supports_streaming: bool
    supports_tool_calling: bool


class ModelProviderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    provider_type: str = "openai-compatible"
    base_url: str
    api_key: str | None = None
    default_model: str
    available_models: list[str] = Field(default_factory=list)
    supports_streaming: bool = True
    supports_tool_calling: bool = True


class ModelProviderUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    provider_type: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    default_model: str | None = None
    available_models: list[str] | None = None
    supports_streaming: bool | None = None
    supports_tool_calling: bool | None = None


class ModelProviderConfig(BaseModel):
    id: str
    name: str
    provider_type: str
    base_url: str
    api_key: str | None = None
    default_model: str
    available_models: list[str] = Field(default_factory=list)
    supports_streaming: bool = True
    supports_tool_calling: bool = True

    def to_read(self) -> ModelProviderRead:
        return ModelProviderRead(
            id=self.id,
            name=self.name,
            provider_type=self.provider_type,
            base_url=self.base_url,
            default_model=self.default_model,
            available_models=self.available_models,
            has_api_key=bool(self.api_key),
            supports_streaming=self.supports_streaming,
            supports_tool_calling=self.supports_tool_calling,
        )


class ModelProviderTestRequest(BaseModel):
    model: str | None = None
    message: str = "你好，请用一句话回复模型连接正常。"


class ModelProviderTestResponse(BaseModel):
    ok: bool
    message: str

