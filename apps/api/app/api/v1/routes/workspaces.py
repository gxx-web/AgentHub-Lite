from fastapi import APIRouter, Depends

from app.core.deps import CurrentUser, get_current_user
from app.core.database import db_connection
from app.schemas.workspace import WorkspaceRead

router = APIRouter()


@router.get("", response_model=list[WorkspaceRead])
async def list_workspaces(current_user: CurrentUser = Depends(get_current_user)) -> list[WorkspaceRead]:
    with db_connection() as connection:
        rows = connection.execute(
            """
            SELECT w.id, w.name, w.description
            FROM workspaces w
            JOIN workspace_members wm ON wm.workspace_id = w.id
            WHERE wm.user_id = %s
            ORDER BY w.created_at ASC
            """,
            (current_user.user_id,),
        ).fetchall()
        return [
            WorkspaceRead(
                id=row["id"],
                name=row["name"],
                description=row["description"],
            )
            for row in rows
        ]

