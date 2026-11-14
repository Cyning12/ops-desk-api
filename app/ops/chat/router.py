"""Chat 端点墓碑（P0' T2a/T2b）。

计算栈已于 T2a 清除；/chat/stream 于 lg-rag T6（2026-08-31）410；
/chat/models 与 /chat/sessions/latest 于 T2b（2026-11-14）410。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.db.models import OpsUser
from app.ops.deps import get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])

# lg-rag T6 (2026-08-31): chat SSE 传输下线，410 墓碑。
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

# P0' T2b (2026-11-14): chat 兼容端点下线，410 墓碑。
_CHAT_MODELS_GONE_DETAIL = {
    "error": "chat_models_deprecated",
    "migrate_to": "/api/ops/lg-rag/models",
    "message": (
        "GET /api/ops/chat/models 已于 2026-11-14 下线（P0' T2b）。"
        "模型目录请走 GET /api/ops/lg-rag/models。"
    ),
}

_CHAT_SESSIONS_GONE_DETAIL = {
    "error": "chat_sessions_deprecated",
    "migrate_to": "/api/ops/chat/threads",
    "message": (
        "GET /api/ops/chat/sessions/latest 已于 2026-11-14 下线（P0' T2b）。"
        "会话列表请走 GET /api/ops/chat/threads（lg-rag history · SoT=thread_id）。"
    ),
}

_CHAT_GONE_HEADERS = {
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


@router.get("/models")
async def list_models(
    user: OpsUser = Depends(get_current_user),
) -> None:
    """Deprecated chat models endpoint (T2b): always 410 Gone.

    Auth stays in front of the 410 so anonymous probes still get 401.
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail=_CHAT_MODELS_GONE_DETAIL,
        headers=_CHAT_GONE_HEADERS,
    )


@router.get("/sessions/latest")
async def get_latest_chat_session(
    user: OpsUser = Depends(get_current_user),
) -> None:
    """Deprecated latest-session endpoint (T2b): always 410 Gone.

    Auth stays in front of the 410 so anonymous probes still get 401.
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail=_CHAT_SESSIONS_GONE_DETAIL,
        headers=_CHAT_GONE_HEADERS,
    )
