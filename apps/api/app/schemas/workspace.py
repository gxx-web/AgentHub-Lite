from pydantic import BaseModel


class WorkspaceRead(BaseModel):
    id: str
    name: str
    description: str | None = None

