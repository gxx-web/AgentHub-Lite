from typing import Any

from fastapi import HTTPException

from app.core.database import db_connection
from app.schemas.agent import AgentCreate, AgentRead, AgentUpdate


class AgentService:
    def list_agents(self, workspace_id: str) -> list[AgentRead]:
        with db_connection() as connection:
            rows = connection.execute(
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
                WHERE workspace_id = %s AND status <> 'archived'
                ORDER BY updated_at DESC, created_at DESC
                """,
                (workspace_id,),
            ).fetchall()
            return [self._row_to_read(connection, row) for row in rows]

    def create_agent(self, payload: AgentCreate, workspace_id: str, user_id: str) -> AgentRead:
        agent_id = self._slugify(payload.name)
        if not agent_id:
            raise HTTPException(status_code=400, detail="Agent name is required")

        with db_connection() as connection:
            self._ensure_model_provider(connection, payload.model_provider_id, workspace_id)
            exists = connection.execute(
                "SELECT 1 FROM agents WHERE id = %s AND workspace_id = %s",
                (agent_id, workspace_id),
            ).fetchone()
            if exists:
                raise HTTPException(status_code=409, detail="Agent already exists")

            row = connection.execute(
                """
                INSERT INTO agents (
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
                  example_questions,
                  visibility,
                  status,
                  created_by
                )
                VALUES (
                  %(id)s,
                  %(workspace_id)s,
                  %(name)s,
                  %(description)s,
                  %(system_prompt)s,
                  %(model_provider_id)s,
                  %(model_name)s,
                  %(temperature)s,
                  %(max_tokens)s,
                  %(opening_message)s,
                  %(example_questions)s,
                  'workspace',
                  'published',
                  %(created_by)s
                )
                RETURNING
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
                """,
                {
                    "id": agent_id,
                    "workspace_id": workspace_id,
                    "created_by": user_id,
                    **payload.model_dump(),
                },
            ).fetchone()
            assert row is not None
            self._replace_bindings(connection, agent_id, payload)
            return self._row_to_read(connection, row)

    def update_agent(self, agent_id: str, payload: AgentUpdate, workspace_id: str) -> AgentRead:
        with db_connection() as connection:
            current = self._get_agent_row(connection, agent_id, workspace_id)
            updates = payload.model_dump(exclude_unset=True)
            if "name" in updates and updates["name"] is not None:
                updates["name"] = updates["name"].strip()
            if "model_provider_id" in updates and updates["model_provider_id"]:
                self._ensure_model_provider(connection, updates["model_provider_id"], workspace_id)

            merged = {
                **dict(current),
                **{
                    key: value
                    for key, value in updates.items()
                    if key
                    not in {
                        "knowledge_base_ids",
                        "skill_ids",
                        "mcp_tool_ids",
                    }
                },
            }
            row = connection.execute(
                """
                UPDATE agents
                SET
                  name = %(name)s,
                  description = %(description)s,
                  system_prompt = %(system_prompt)s,
                  model_provider_id = %(model_provider_id)s,
                  model_name = %(model_name)s,
                  temperature = %(temperature)s,
                  max_tokens = %(max_tokens)s,
                  opening_message = %(opening_message)s,
                  example_questions = %(example_questions)s
                WHERE id = %(id)s AND workspace_id = %(workspace_id)s
                RETURNING
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
                """,
                merged,
            ).fetchone()
            assert row is not None
            self._replace_bindings(connection, agent_id, payload)
            return self._row_to_read(connection, row)

    def delete_agent(self, agent_id: str, workspace_id: str) -> None:
        if agent_id == "default-agent":
            raise HTTPException(status_code=400, detail="Default agent cannot be deleted")
        with db_connection() as connection:
            result = connection.execute(
                "DELETE FROM agents WHERE id = %s AND workspace_id = %s",
                (agent_id, workspace_id),
            )
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Agent not found")

    def get_agent(self, agent_id: str, workspace_id: str) -> AgentRead:
        with db_connection() as connection:
            return self._row_to_read(connection, self._get_agent_row(connection, agent_id, workspace_id))

    def _get_agent_row(self, connection: Any, agent_id: str, workspace_id: str) -> dict[str, Any]:
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
        return row

    def _row_to_read(self, connection: Any, row: dict[str, Any]) -> AgentRead:
        agent_id = row["id"]
        return AgentRead(
            id=agent_id,
            workspace_id=row["workspace_id"],
            name=row["name"],
            description=row["description"],
            system_prompt=row["system_prompt"],
            model_provider_id=row["model_provider_id"],
            model_name=row["model_name"],
            temperature=float(row["temperature"]),
            max_tokens=row["max_tokens"],
            knowledge_base_ids=self._list_bindings(
                connection,
                "agent_knowledge_bases",
                "knowledge_base_id",
                agent_id,
            ),
            skill_ids=self._list_bindings(connection, "agent_skills", "skill_id", agent_id),
            mcp_tool_ids=self._list_bindings(connection, "agent_mcp_tools", "mcp_tool_id", agent_id),
            opening_message=row["opening_message"],
            example_questions=list(row["example_questions"] or []),
        )

    def _replace_bindings(self, connection: Any, agent_id: str, payload: AgentCreate | AgentUpdate) -> None:
        data = payload.model_dump(exclude_unset=True)
        binding_specs = [
            ("knowledge_base_ids", "agent_knowledge_bases", "knowledge_base_id", "knowledge_bases"),
            ("skill_ids", "agent_skills", "skill_id", "skills"),
            ("mcp_tool_ids", "agent_mcp_tools", "mcp_tool_id", "mcp_tools"),
        ]
        for field_name, join_table, join_column, target_table in binding_specs:
            if field_name not in data or data[field_name] is None:
                continue
            connection.execute(f"DELETE FROM {join_table} WHERE agent_id = %s", (agent_id,))
            for item_id in data[field_name]:
                if self._row_exists(connection, target_table, item_id):
                    connection.execute(
                        f"INSERT INTO {join_table} (agent_id, {join_column}) VALUES (%s, %s)",
                        (agent_id, item_id),
                    )

    def _list_bindings(
        self,
        connection: Any,
        table_name: str,
        column_name: str,
        agent_id: str,
    ) -> list[str]:
        rows = connection.execute(
            f"SELECT {column_name} FROM {table_name} WHERE agent_id = %s ORDER BY created_at",
            (agent_id,),
        ).fetchall()
        return [row[column_name] for row in rows]

    def _row_exists(self, connection: Any, table_name: str, row_id: str) -> bool:
        return (
            connection.execute(f"SELECT 1 FROM {table_name} WHERE id = %s", (row_id,)).fetchone()
            is not None
        )

    def _ensure_model_provider(self, connection: Any, provider_id: str, workspace_id: str) -> None:
        exists = connection.execute(
            "SELECT 1 FROM model_providers WHERE id = %s AND workspace_id = %s",
            (provider_id, workspace_id),
        ).fetchone()
        if not exists:
            raise HTTPException(status_code=400, detail="Model provider does not exist")

    def _slugify(self, value: str) -> str:
        slug = "".join(char.lower() if char.isalnum() else "-" for char in value.strip())
        return "-".join(part for part in slug.split("-") if part)


agent_service = AgentService()
