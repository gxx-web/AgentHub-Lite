from fastapi import HTTPException

from app.schemas.agent import AgentCreate, AgentRead, AgentUpdate


class AgentService:
    def __init__(self) -> None:
        self._agents: dict[str, AgentRead] = {
            "default-agent": AgentRead(
                id="default-agent",
                name="Default Assistant",
                description="MVP sample Agent.",
                system_prompt="You are a helpful AI agent for AgentHub-Lite.",
                model_provider_id="openai-compatible",
                model_name="gpt-4.1-mini",
                opening_message="Hi, I am the default assistant. Ask me anything.",
                example_questions=[
                    "Summarize today's project plan.",
                    "Draft a simple task checklist.",
                ],
            )
        }

    def list_agents(self) -> list[AgentRead]:
        return list(self._agents.values())

    def create_agent(self, payload: AgentCreate) -> AgentRead:
        agent_id = self._slugify(payload.name)
        if not agent_id:
            raise HTTPException(status_code=400, detail="Agent name is required")
        if agent_id in self._agents:
            raise HTTPException(status_code=409, detail="Agent already exists")

        agent = AgentRead(id=agent_id, **payload.model_dump())
        self._agents[agent_id] = agent
        return agent

    def update_agent(self, agent_id: str, payload: AgentUpdate) -> AgentRead:
        agent = self.get_agent(agent_id)
        updates = payload.model_dump(exclude_unset=True)
        if "name" in updates:
            updates["name"] = updates["name"].strip()
        updated_agent = agent.model_copy(update=updates)
        self._agents[agent_id] = updated_agent
        return updated_agent

    def delete_agent(self, agent_id: str) -> None:
        if agent_id == "default-agent":
            raise HTTPException(status_code=400, detail="Default agent cannot be deleted")
        if agent_id not in self._agents:
            raise HTTPException(status_code=404, detail="Agent not found")
        del self._agents[agent_id]

    def get_agent(self, agent_id: str) -> AgentRead:
        agent = self._agents.get(agent_id)
        if agent is None:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent

    def _slugify(self, value: str) -> str:
        slug = "".join(char.lower() if char.isalnum() else "-" for char in value.strip())
        return "-".join(part for part in slug.split("-") if part)


agent_service = AgentService()

