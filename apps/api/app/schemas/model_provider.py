from pydantic import BaseModel


class ModelProviderRead(BaseModel):
    id: str
    name: str
    provider_type: str
    base_url: str
    default_model: str
    supports_streaming: bool
    supports_tool_calling: bool

