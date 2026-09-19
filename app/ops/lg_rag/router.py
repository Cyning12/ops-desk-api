"""LangGraph 旁路 HTTP：invoke · stream · replay。

freeze：
- invoke · lg-rag-http-v1
- stream / replay · lg-rag-sse-v1（T2/T4 · 默认 mode=supervisor · updates 帧 · 可选 cursor）

薄包装 lg_rag 三个 ainvoke / astream 入口；
{ok,data} 外壳、cookie 鉴权、异常 500 外壳、flush_traces 体例对齐
lc_evidence_chain/router.py 先例。

Checkpointer：默认不传（入口默认 InMemorySaver，进程内同 thread_id 续写）；
env LG_RAG_HTTP_CHECKPOINTER=postgres 时走 apostgres_saver(setup=True)
（每请求构建，幂等建表；生产默认不开）。stream 本波不挂 PG（与 invoke 可后续对齐）。
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from collections.abc import AsyncIterator
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse, StreamingResponse
from langchain_core.messages import AIMessage
from pydantic import BaseModel, Field

from app.db.models import OpsUser
from app.ops.deps import CurrentUser
from app.ops.lg_rag import (
    ainvoke_basic_agent,
    ainvoke_router_agent,
    ainvoke_supervisor_agent,
)
from app.ops.lg_rag.checkpointer import apostgres_saver
from app.ops.lg_rag.event_store import LgRagRunNotFoundError, load_events_after
from app.ops.lg_rag.sse_replay import InvalidCursorError, resolve_replay_target
from app.ops.lg_rag.sse_stream import iter_lg_rag_sse
from app.ops.lg_rag.thread_store import (
    LgRagThreadForbiddenError,
    load_thread_turns,
    persist_thread_turns,
    resolve_thread_for_user,
)
from app.ops.tenant_context import (
    TENANT_A,
    TENANT_HEADER,
    reset_current_tenant,
    resolve_header_against_session,
    set_current_tenant,
)
from app.ops.tracing import flush_traces, tracing_enabled

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lg-rag", tags=["lg-rag"])

QUERY_MAX_LENGTH = 8000
THREAD_ID_MAX_LENGTH = 255
_FAIL_CODE = "lg_rag_failed"
_FAIL_MESSAGE = "旁路调用失败"

Mode = Literal["router", "basic", "supervisor"]


class InvokeRequest(BaseModel):
    """旁路 invoke 请求体（freeze lg-rag-http-v1）。"""

    query: str = Field(..., min_length=1, max_length=QUERY_MAX_LENGTH)
    mode: Mode = "router"
    thread_id: str | None = Field(default=None, max_length=THREAD_ID_MAX_LENGTH)


class StreamRequest(BaseModel):
    """旁路 SSE 请求体（freeze lg-rag-sse-v1）。默认 supervisor 主线。"""

    query: str = Field(..., min_length=1, max_length=QUERY_MAX_LENGTH)
    mode: Mode = "supervisor"
    thread_id: str | None = Field(default=None, max_length=THREAD_ID_MAX_LENGTH)


class ReplayRequest(BaseModel):
    """断联续看：``{run_id, after_seq}`` 或 ``{cursor}``（freeze lg-rag-sse-v1）。"""

    run_id: str | None = Field(default=None, max_length=64)
    after_seq: int | None = Field(default=None, ge=0)
    cursor: str | None = Field(default=None, max_length=96)


class ChainMetaOut(BaseModel):
    """rag 路径质量信号子集（对齐 lc 的 MetaOut 风格，缺省 0/""）。"""

    gate_action: str = ""
    hit_count: int = 0
    kept_count: int = 0
    best_relevance: str = ""
    grade_count: int = 0


class DataOut(BaseModel):
    """freeze 响应 data（lg-rag-http-v1）。"""

    answer: str
    mode: str
    thread_id: str
    route: str = ""
    retry_count: int = 0
    chain_meta: ChainMetaOut
    subtasks: list[dict[str, Any]] = []
    subtask_results: list[dict[str, Any]] = []


def _extract_answer(messages: Any) -> str:
    """取末条 AIMessage content；无则空串。"""
    for msg in reversed(messages or []):
        if isinstance(msg, AIMessage):
            content = msg.content
            return content if isinstance(content, str) else str(content)
    return ""


def _chain_meta_out(meta: Any) -> ChainMetaOut:
    meta = meta or {}
    return ChainMetaOut(
        gate_action=str(meta.get("gate_action") or ""),
        hit_count=int(meta.get("hit_count") or 0),
        kept_count=int(meta.get("kept_count") or 0),
        best_relevance=str(meta.get("best_relevance") or ""),
        grade_count=int(meta.get("grade_count") or 0),
    )


def serialize_state(state: dict[str, Any], *, mode: str, thread_id: str) -> DataOut:
    """把图返回 state 转成 freeze 响应 data。"""
    return DataOut(
        answer=_extract_answer(state.get("messages")),
        mode=mode,
        thread_id=thread_id,
        route=str(state.get("route") or ""),
        retry_count=int(state.get("retry_count") or 0),
        chain_meta=_chain_meta_out(state.get("chain_meta")),
        subtasks=list(state.get("subtasks") or []),
        subtask_results=list(state.get("subtask_results") or []),
    )


def _use_postgres_checkpointer() -> bool:
    return os.getenv("LG_RAG_HTTP_CHECKPOINTER", "").strip().lower() == "postgres"


async def _dispatch(
    mode: Mode,
    query: str,
    thread_id: str,
    history_turns: list[dict] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """mode → 对应 ainvoke 入口；env 开关决定是否包 PG checkpointer。"""
    if mode == "basic":
        entry = ainvoke_basic_agent
    elif mode == "supervisor":
        entry = ainvoke_supervisor_agent
    else:
        entry = ainvoke_router_agent
    kwargs: dict[str, Any] = {
        "thread_id": thread_id,
        "history_turns": history_turns or [],
    }
    if mode == "supervisor" and run_id:
        kwargs["run_id"] = run_id
    if _use_postgres_checkpointer():
        async with apostgres_saver(setup=True) as saver:
            return await entry(query, checkpointer=saver, **kwargs)
    return await entry(query, **kwargs)


async def _prepare_thread(thread_id: str, user_id: str) -> list[dict]:
    """归属校验 + 加载历史；跨用户 404；加载失败按无历史。"""
    try:
        owned = await resolve_thread_for_user(thread_id, user_id)
    except LgRagThreadForbiddenError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found",
        ) from None
    if not owned:
        return []
    try:
        return await load_thread_turns(thread_id)
    except Exception:
        logger.exception("lg-rag load turns failed thread_id=%s", thread_id)
        return []


def _resolve_request_tenant(request: Request) -> str:
    """F1=C：session 真源；头不一致 → 403；未知租户 → 422。"""
    session_tenant = getattr(request.state, "ops_tenant_id", TENANT_A)
    try:
        return resolve_header_against_session(
            session_tenant, request.headers.get(TENANT_HEADER)
        )
    except ValueError as exc:
        detail = str(exc)
        code = 403 if "mismatch" in detail else 422
        raise HTTPException(status_code=code, detail=detail) from exc


@router.post("/invoke")
async def invoke_lg_rag(
    body: InvokeRequest,
    request: Request,
    user: OpsUser = CurrentUser,
) -> JSONResponse:
    """同步调用 lg_rag 旁路图；须登录。"""
    tenant_id = _resolve_request_tenant(request)
    thread_id = (body.thread_id or uuid.uuid4().hex)[:THREAD_ID_MAX_LENGTH]
    history_turns = await _prepare_thread(thread_id, str(user.id))
    run_id = uuid.uuid4().hex
    token = set_current_tenant(tenant_id)
    try:
        try:
            state = await _dispatch(
                body.mode,
                body.query,
                thread_id,
                history_turns=history_turns,
                run_id=run_id,
            )
        except HTTPException:
            raise
        except Exception:
            logger.exception("lg-rag invoke failed")
            if tracing_enabled():
                flush_traces()
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "ok": False,
                    "error": {"code": _FAIL_CODE, "message": _FAIL_MESSAGE},
                },
            )
        try:
            await persist_thread_turns(
                thread_id, str(user.id), body.query, _extract_answer(state.get("messages"))
            )
        except Exception:
            logger.exception("lg-rag invoke persist failed thread_id=%s", thread_id)
        if tracing_enabled():
            flush_traces()
        return JSONResponse(
            content={
                "ok": True,
                "data": serialize_state(
                    state, mode=body.mode, thread_id=thread_id
                ).model_dump(),
            }
        )
    finally:
        reset_current_tenant(token)


@router.post("/stream")
async def stream_lg_rag(
    body: StreamRequest,
    request: Request,
    user: OpsUser = CurrentUser,
) -> StreamingResponse:
    """SSE 流式旁路（freeze lg-rag-sse-v1）；须登录。默认 mode=supervisor。"""
    tenant_id = _resolve_request_tenant(request)

    thread_id = (body.thread_id or uuid.uuid4().hex)[:THREAD_ID_MAX_LENGTH]
    history_turns = await _prepare_thread(thread_id, str(user.id))
    run_id = uuid.uuid4().hex

    async def event_gen() -> AsyncIterator[str]:
        token = set_current_tenant(tenant_id)
        try:
            async for chunk in iter_lg_rag_sse(
                query=body.query,
                mode=body.mode,
                thread_id=thread_id,
                run_id=run_id,
                history_turns=history_turns,
                user_id=str(user.id),
            ):
                yield chunk
        finally:
            reset_current_tenant(token)

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "X-Ops-Lg-Rag-Thread-Id": thread_id,
            "X-Ops-Lg-Rag-Run-Id": run_id,
        },
    )


@router.post("/replay")
async def replay_lg_rag(
    body: ReplayRequest,
    user: OpsUser = CurrentUser,
) -> StreamingResponse:
    """SSE 重放已落盘帧（seq > after_seq）；须登录。未知/跨用户 run_id → 404。"""
    try:
        run_id, after_seq = resolve_replay_target(
            run_id=body.run_id,
            after_seq=body.after_seq,
            cursor=body.cursor,
        )
    except InvalidCursorError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc) or "invalid cursor",
        ) from None

    try:
        events = await load_events_after(run_id, str(user.id), after_seq)
    except LgRagRunNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        ) from None

    async def event_gen() -> AsyncIterator[str]:
        for ev in events:
            yield (
                f"event: {ev['event_type']}\n"
                f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
            )

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "X-Ops-Lg-Rag-Run-Id": run_id,
        },
    )
