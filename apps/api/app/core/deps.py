from dataclasses import dataclass

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.database import db_connection
from app.core.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    username: str
    display_name: str
    workspace_id: str


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    workspace_id = payload.get("workspace_id")
    if not user_id or not workspace_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    with db_connection() as connection:
        row = connection.execute(
            """
            SELECT u.id, u.username, u.display_name
            FROM users u
            JOIN workspace_members wm ON wm.user_id = u.id
            WHERE u.id = %s
              AND u.status = 'active'
              AND wm.workspace_id = %s
            """,
            (user_id, workspace_id),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return CurrentUser(
            user_id=row["id"],
            username=row["username"],
            display_name=row["display_name"],
            workspace_id=workspace_id,
        )
