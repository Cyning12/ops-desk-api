"""lg-rag 会话历史只读 API（chat-history-api B1 · 裁定 B1 落点）。

路由挂 ``APIRouter(prefix="/chat")``，由 ``app/ops/router.py`` 注册进
``/api/ops`` → 实际路径：

- ``GET /api/ops/chat/threads``（H1：当前用户 thread 列表）
- ``GET /api/ops/chat/threads/{thread_id}/history``（H2：单 thread 完整历史）

真源 = 事件表 ``ops_lg_rag_run_events``（SPEC Q1 · 每帧独立 commit）；
聚合在 ``history.py`` 纯函数层（H3），本层只管鉴权 / 归属 / 分页 / 超时。

**import 纪律（task N1 钉）**：鉴权 ``CurrentUser`` 与 ORM ``OpsUser``
经同族 ``app.ops.lg_rag.router`` 间接取——直连 ``app.ops.deps`` /
``app.db.models`` 会破 import-linter ``lg-rag-outbound`` 契约。
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Path, Query, status

from app.ops.lg_rag import event_store, history
from app.ops.lg_rag.router import CurrentUser, OpsUser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat-history"])

# FP-2/N3：聚合超时阈值（秒）。模块常量，测试可注入小阈值断言 504。
HISTORY_AGGREGATE_TIMEOUT_S = 10.0

_THREAD_ID_MAX = 255
_CURSOR_MAX = 512


def _map_cursor_error(exc: history.HistoryCursorError) -> HTTPException:
    return HTTPException(
        status_code=422,
        detail=str(exc) or "invalid cursor",
    )


async def _load_threads_page(
    user_id: str, *, limit: int, cursor: str | None
) -> dict[str, Any]:
    """H1 数据装配：thread 活动页 + 事件拉取 + 纯函数摘要。"""
    after = None
    if cursor is not None:
        try:
            after = history.threads_cursor_after(cursor)
        except history.HistoryCursorError as exc:
            raise _map_cursor_error(exc) from None
    page = await event_store.list_thread_activity_page(
        user_id, limit=limit, after=after
    )
    grouped = await event_store.fetch_events_for_threads(
        user_id, [row["thread_id"] for row in page]
    )
    threads = [
        history.build_thread_summary(
            row["thread_id"],
            grouped.get(row["thread_id"], []),
            last_activity_at=row["last_activity_at"],
            run_count=row["run_count"],
        )
        for row in page
    ]
    next_cursor = None
    if len(page) == limit and page:
        last = page[-1]
        next_cursor = history.make_threads_cursor(
            last["last_activity_at"], last["thread_id"]
        )
    return {"threads": threads, "next_cursor": next_cursor}


async def _load_thread_history(
    user_id: str, thread_id: str, *, limit: int, cursor: str | None
) -> dict[str, Any]:
    """H2 数据装配：归属 404 + 事件拉取 + run 消息视图分页。"""
    owner = await event_store.thread_owner(thread_id)
    if owner is None or str(owner) != str(user_id):
        # FP-1：跨用户/未知一律 404，不泄露存在性（不 403）
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found",
        )
    grouped = await event_store.fetch_events_for_threads(user_id, [thread_id])
    try:
        views, next_cursor = history.paginate_run_views(
            grouped.get(thread_id, []), limit=limit, cursor=cursor
        )
    except history.HistoryCursorError as exc:
        raise _map_cursor_error(exc) from None
    return {"thread_id": thread_id, "runs": views, "next_cursor": next_cursor}


@router.get("/threads")
async def list_chat_threads(
    user: OpsUser = CurrentUser,
    limit: int = Query(
        default=history.DEFAULT_LIMIT,
        ge=1,
        le=history.MAX_LIMIT,
        description="每页条数（默认 20 · 上限 100 · 超限 422）",
    ),
    cursor: str | None = Query(default=None, max_length=_CURSOR_MAX),
) -> dict[str, Any]:
    """当前用户 thread 列表（H1）；按 ``last_activity_at`` 倒序 keyset 分页。"""
    try:
        data = await asyncio.wait_for(
            _load_threads_page(str(user.id), limit=limit, cursor=cursor),
            timeout=HISTORY_AGGREGATE_TIMEOUT_S,
        )
    except TimeoutError:
        # FP-2：聚合超时 → 504（可重试：缩小 limit 后重试）
        logger.warning("chat history threads aggregate timeout")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="History aggregation timeout",
        ) from None
    return {"ok": True, "data": data}


@router.get("/threads/{thread_id}/history")
async def get_chat_thread_history(
    thread_id: str = Path(..., max_length=_THREAD_ID_MAX),
    user: OpsUser = CurrentUser,
    limit: int = Query(
        default=history.DEFAULT_LIMIT,
        ge=1,
        le=history.MAX_LIMIT,
        description="每页 run 数（默认 20 · 上限 100 · 超限 422）",
    ),
    cursor: str | None = Query(default=None, max_length=_CURSOR_MAX),
) -> dict[str, Any]:
    """单 thread 完整历史（H2）；跨用户/未知 → 404（H4 · 不泄露存在性）。"""
    try:
        data = await asyncio.wait_for(
            _load_thread_history(str(user.id), thread_id, limit=limit, cursor=cursor),
            timeout=HISTORY_AGGREGATE_TIMEOUT_S,
        )
    except TimeoutError:
        logger.warning(
            "chat history thread aggregate timeout thread_id=%s", thread_id
        )
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="History aggregation timeout",
        ) from None
    return {"ok": True, "data": data}
