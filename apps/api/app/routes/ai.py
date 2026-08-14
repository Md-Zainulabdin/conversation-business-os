from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.ai import (
    AICommandRequest,
    AIExecuteRequest,
    AIExecuteResponse,
    AIProposalResponse,
    AIResolveRequest,
)
from app.services import ai as ai_service

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/commands", response_model=AIProposalResponse)
async def propose_command(
    data: AICommandRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ai_service.propose(
        db, current_user, data.message, conversation_id=data.conversation_id
    )


@router.post("/commands/resolve", response_model=AIProposalResponse)
async def resolve_command(
    data: AIResolveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ai_service.resolve(db, current_user, data.command, data.product_id)


@router.post("/commands/execute", response_model=AIExecuteResponse)
async def execute_command(
    data: AIExecuteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ai_service.execute(
        db, current_user, data.command, idempotency_key=data.idempotency_key
    )