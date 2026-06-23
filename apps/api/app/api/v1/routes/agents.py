from fastapi import APIRouter, Depends

from app.core.deps import CurrentUser, get_current_user
from app.schemas.agent import AgentCreate, AgentRead, AgentUpdate
from app.services.agent_service import agent_service

router = APIRouter()


@router.get("", response_model=list[AgentRead])
async def list_agents(current_user: CurrentUser = Depends(get_current_user)) -> list[AgentRead]:
    return agent_service.list_agents(current_user.workspace_id)


@router.post("", response_model=AgentRead, status_code=201)
async def create_agent(
    payload: AgentCreate,
    current_user: CurrentUser = Depends(get_current_user),
) -> AgentRead:
    return agent_service.create_agent(payload, current_user.workspace_id, current_user.user_id)


@router.get("/{agent_id}", response_model=AgentRead)
async def get_agent(
    agent_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> AgentRead:
    return agent_service.get_agent(agent_id, current_user.workspace_id)


@router.patch("/{agent_id}", response_model=AgentRead)
async def update_agent(
    agent_id: str,
    payload: AgentUpdate,
    current_user: CurrentUser = Depends(get_current_user),
) -> AgentRead:
    return agent_service.update_agent(agent_id, payload, current_user.workspace_id)


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> None:
    agent_service.delete_agent(agent_id, current_user.workspace_id)

