import base64
import hashlib
import hmac

from fastapi import HTTPException

from app.core.database import db_connection
from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, LoginResponse


class AuthService:
    def login(self, payload: LoginRequest) -> LoginResponse:
        with db_connection() as connection:
            row = connection.execute(
                """
                SELECT id, username, password_hash, display_name, status
                FROM users
                WHERE username = %s OR email = %s
                """,
                (payload.username, payload.username),
            ).fetchone()
            if row is None or row["status"] != "active":
                raise HTTPException(status_code=401, detail="账号或密码错误")
            if not self._verify_password(payload.password, row["password_hash"]):
                raise HTTPException(status_code=401, detail="账号或密码错误")

            member = connection.execute(
                """
                SELECT workspace_id
                FROM workspace_members
                WHERE user_id = %s
                ORDER BY joined_at ASC
                LIMIT 1
                """,
                (row["id"],),
            ).fetchone()
            connection.execute(
                "UPDATE users SET last_login_at = now() WHERE id = %s",
                (row["id"],),
            )
            workspace_id = member["workspace_id"] if member else "default"
            return LoginResponse(
                access_token=create_access_token(row["id"], workspace_id),
                user_id=row["id"],
                username=row["username"],
                display_name=row["display_name"],
                workspace_id=workspace_id,
            )

    def _verify_password(self, password: str, password_hash: str) -> bool:
        parts = password_hash.split("$")
        if len(parts) == 4 and parts[0] == "pbkdf2_sha256":
            iterations = int(parts[1])
            salt = parts[2]
            expected = parts[3]
            digest = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt.encode("utf-8"),
                iterations,
            )
            actual = base64.b64encode(digest).decode("ascii")
            return hmac.compare_digest(actual, expected)
        return False


auth_service = AuthService()
