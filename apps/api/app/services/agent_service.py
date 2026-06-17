from fastapi import HTTPException

from app.schemas.agent import AgentCreate, AgentRead


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
            )
        }

    def list_agents(self) -> list[AgentRead]:
        return list(self._agents.values())

    def create_agent(self, payload: AgentCreate) -> AgentRead:
        agent_id = payload.name.lower().strip().replace(" ", "-")
        if not agent_id:
            raise HTTPException(status_code=400, detail="Agent name is required")
        if agent_id in self._agents:
            raise HTTPException(status_code=409, detail="Agent already exists")

        agent = AgentRead(id=agent_id, **payload.model_dump())
        self._agents[agent_id] = agent
        return agent

    def get_agent(self, agent_id: str) -> AgentRead:
        agent = self._agents.get(agent_id)
        if agent is None:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent


agent_service = AgentService()

