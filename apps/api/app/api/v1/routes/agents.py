from fastapi import APIRouter

from app.schemas.agent import AgentCreate, AgentRead, AgentUpdate
from app.services.agent_service import agent_service

router = APIRouter()


@router.get("", response_model=list[AgentRead])
async def list_agents() -> list[AgentRead]:
    return agent_service.list_agents()


@router.post("", response_model=AgentRead, status_code=201)
async def create_agent(payload: AgentCreate) -> AgentRead:
    return agent_service.create_agent(payload)


@router.get("/{agent_id}", response_model=AgentRead)
async def get_agent(agent_id: str) -> AgentRead:
    return agent_service.get_agent(agent_id)


@router.patch("/{agent_id}", response_model=AgentRead)
async def update_agent(agent_id: str, payload: AgentUpdate) -> AgentRead:
    return agent_service.update_agent(agent_id, payload)


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(agent_id: str) -> None:
    agent_service.delete_agent(agent_id)

