from fastapi import APIRouter

from app.schemas.agent import AgentCreate, AgentRead
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

