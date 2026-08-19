import logging
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.rate_limit import get_rate_limiter
from app.models.user import User
from app.schemas.ai import (
    AICommandRequest,
    AIExecuteRequest,
    AIExecuteResponse,
    AIProposalResponse,
    AIResolveRequest,
    VoiceProposalResponse,
)
from app.services import ai as ai_service

router = APIRouter(prefix="/ai", tags=["ai"])

logger = logging.getLogger(__name__)


def _server_conversation_id(client_id: str | None) -> str:
    return client_id or uuid.uuid4().hex


async def _check_ai_rate_limit(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
) -> None:
    limiter = get_rate_limiter()
    key = f"ai:{current_user.id}"
    allowed, headers = limiter.check(key)
    for k, v in headers.items():
        response.headers[k] = v
    if not allowed:
        logger.warning("AI rate limit exceeded: user=%s", current_user.id)
        raise HTTPException(
            status_code=429,
            detail="Too many AI requests. Please wait before sending more.",
        )


@router.post("/commands", response_model=AIProposalResponse)
async def propose_command(
    data: AICommandRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rate_limit: None = Depends(_check_ai_rate_limit),
):
    conversation_id = _server_conversation_id(data.conversation_id)
    logger.info(
        "AI propose request: user=%s conversation_id=%s message_len=%d",
        current_user.id,
        conversation_id,
        len(data.message),
    )
    proposal = await ai_service.propose(
        db, current_user, data.message, conversation_id=conversation_id
    )
    proposal.command.conversation_id = conversation_id
    logger.info(
        "AI propose response: user=%s conversation_id=%s intent=%s requires_confirmation=%s",
        current_user.id,
        conversation_id,
        proposal.command.intent,
        proposal.requires_confirmation,
    )
    return proposal


MAX_VOICE_UPLOAD_BYTES = 25 * 1024 * 1024


@router.post("/voice", response_model=VoiceProposalResponse)
async def propose_voice_command(
    file: UploadFile = File(..., description="Audio file (max 25MB)"),
    conversation_id: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rate_limit: None = Depends(_check_ai_rate_limit),
):
    file_bytes = await file.read()
    if len(file_bytes) > MAX_VOICE_UPLOAD_BYTES:
        logger.warning(
            "Voice upload too large: user=%s size=%d max=%d",
            current_user.id,
            len(file_bytes),
            MAX_VOICE_UPLOAD_BYTES,
        )
        raise HTTPException(
            status_code=413,
            detail="Audio file is too large (maximum 25MB)",
        )
    server_conversation_id = _server_conversation_id(conversation_id)
    logger.info(
        "Voice propose request: user=%s conversation_id=%s filename=%s content_type=%s size=%d",
        current_user.id,
        server_conversation_id,
        file.filename,
        file.content_type,
        len(file_bytes),
    )
    transcript, proposal = await ai_service.transcribe_and_propose(
        db,
        current_user,
        file_bytes,
        file.filename or "recording.mp3",
        conversation_id=server_conversation_id,
        content_type=file.content_type,
    )
    proposal.command.conversation_id = server_conversation_id
    logger.info(
        "Voice propose response: user=%s conversation_id=%s transcript_len=%d intent=%s requires_confirmation=%s",
        current_user.id,
        server_conversation_id,
        len(transcript),
        proposal.command.intent,
        proposal.requires_confirmation,
    )
    return VoiceProposalResponse(
        **proposal.model_dump(),
        transcript=transcript,
    )


@router.post("/commands/resolve", response_model=AIProposalResponse)
async def resolve_command(
    data: AIResolveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rate_limit: None = Depends(_check_ai_rate_limit),
):
    logger.info(
        "AI resolve request: user=%s product_id=%s",
        current_user.id,
        data.product_id,
    )
    return await ai_service.resolve(db, current_user, data.command, data.product_id)


@router.post("/commands/execute", response_model=AIExecuteResponse)
async def execute_command(
    data: AIExecuteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rate_limit: None = Depends(_check_ai_rate_limit),
):
    logger.info(
        "AI execute request: user=%s intent=%s idempotency_key=%s",
        current_user.id,
        data.command.intent,
        data.idempotency_key,
    )
    return await ai_service.execute(
        db, current_user, data.command, idempotency_key=data.idempotency_key
    )