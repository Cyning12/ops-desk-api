"""Chat SSE endpoint."""
from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import OpsSessionChat, OpsUser
from app.db.session import AsyncSessionLocal, get_db
from app.llm.model_catalog import get_default_model, get_models_for_provider
from app.ops.chat.schema import ChatModelsResponse, ChatSessionOut, ChatStreamRequest
from app.ops.chat.sse import make_sse_event
from app.ops.chat.state import ChatState
from app.ops.chat.streaming import (
    ChatEventStreamer,
)
from app.ops.chat.streaming import (
    create_run_record as _create_run_record,
)
from app.ops.chat.streaming import (
    resolve_chat_session as _resolve_chat_session,
)
from app.ops.deps import get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/stream")
async def chat_stream(
    request: Request,
    user: OpsUser = Depends(get_current_user),
) -> StreamingResponse:
    """Stream chat response via Server-Sent Events."""
    body = await request.json()
    req = ChatStreamRequest(**body)
    run_id = str(uuid.uuid4())

    run_model = req.model or settings.ops_llm_model

    # Setup chat session and run record outside the SSE generator.
    async with AsyncSessionLocal() as setup_session:
        chat_session_id = await _resolve_chat_session(
            setup_session,
            req.session_id,
            user.id,
            req.message,
        )
        await setup_session.commit()

    await _create_run_record(
        run_id,
        chat_session_id,
        req.message,
        run_model,
    )

    state = ChatState(
        query=req.message,
        session_id=chat_session_id,
        run_id=run_id,
        model=req.model,
        issue_context=[],
        pr_context=[],
        graph_context=None,
        intent="",
        answer="",
        events=[],
    )

    streamer = ChatEventStreamer(state, run_id, run_model)

    async def event_generator() -> AsyncGenerator[str, None]:
        async for event in streamer.events():
            yield make_sse_event(event)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/models", response_model=ChatModelsResponse)
async def list_models() -> ChatModelsResponse:
    """Return available chat models."""
    provider = settings.ops_llm_provider
    return ChatModelsResponse(
        provider=provider,
        default_model=get_default_model(provider),
        models=get_models_for_provider(provider),
    )


@router.get("/sessions/latest", response_model=ChatSessionOut)
async def get_latest_chat_session(
    user: OpsUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatSessionOut:
    """Return the current user's most recent chat session, creating one if needed.

    This endpoint is optimized for iOS v1, which only supports a single Chat
    screen and should always land on the latest session.
    """
    result = await db.execute(
        select(OpsSessionChat)
        .where(OpsSessionChat.user_id == user.id)
        .order_by(OpsSessionChat.updated_at.desc())
        .limit(1)
    )
    chat_session = result.scalar_one_or_none()

    if chat_session is None:
        chat_session = OpsSessionChat(user_id=user.id, title="New Chat")
        db.add(chat_session)
        await db.commit()
        await db.refresh(chat_session)

    return ChatSessionOut(
        id=str(chat_session.id),
        user_id=str(chat_session.user_id),
        title=chat_session.title,
        created_at=chat_session.created_at,
        updated_at=chat_session.updated_at,
    )
