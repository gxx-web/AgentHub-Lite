from fastapi import APIRouter

from app.schemas.workspace import WorkspaceRead

router = APIRouter()


@router.get("", response_model=list[WorkspaceRead])
async def list_workspaces() -> list[WorkspaceRead]:
    return [
        WorkspaceRead(
            id="default",
            name="Default Workspace",
            description="Personal workspace for local development.",
        )
    ]

