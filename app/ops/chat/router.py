"""Chat SSE endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import OpsSessionChat, OpsUser
from app.db.session import get_db
from app.llm.model_catalog import get_default_model, get_models_for_provider
from app.ops.chat.schema import ChatModelsResponse, ChatSessionOut
from app.ops.deps import get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])

# T6 (2026-08-31): chat SSE 传输下线。chat 代码/图/表保留，仅本端点 410。
_CHAT_STREAM_GONE_DETAIL = {
    "error": "chat_stream_deprecated",
    "migrate_to": "/api/ops/lg-rag/stream",
    "message": (
        "POST /api/ops/chat/stream 已于 2026-08-31 下线（lg-rag T6）。"
        "请迁移到 POST /api/ops/lg-rag/stream（lg-rag SSE · freeze lg-rag-sse-v1）。"
    ),
}

_CHAT_STREAM_GONE_HEADERS = {
    "Deprecation": "true",
    "Link": '</api/ops/lg-rag/stream>; rel="successor-version"',
}


@router.post("/stream")
async def chat_stream(
    user: OpsUser = Depends(get_current_user),
) -> None:
    """Deprecated chat SSE stream (T6): always 410 Gone with a migration pointer.

    Auth stays in front of the 410 so anonymous probes still get 401 and never
    see the migration pointer.
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail=_CHAT_STREAM_GONE_DETAIL,
        headers=_CHAT_STREAM_GONE_HEADERS,
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
