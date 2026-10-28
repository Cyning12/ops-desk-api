"""LangGraph 旁路 HTTP：invoke · stream · replay。

freeze：
- invoke · lg-rag-http-v1
- stream / replay · lg-rag-sse-v1（T2/T4 · 默认 mode=supervisor · updates 帧 · 可选 cursor）

薄包装 lg_rag 三个 ainvoke / astream 入口；
{ok,data} 外壳、cookie 鉴权、异常 500 外壳、flush_traces 体例对齐
lc_evidence_chain/router.py 先例。

Checkpointer：默认不传（入口默认 InMemorySaver，进程内同 thread_id 续写）；
env LG_RAG_HTTP_CHECKPOINTER=postgres 时走 apostgres_saver(setup=True)
（每请求构建，幂等建表；生产默认不开）。
**stream 与 invoke 读同一把闸**（checkpointer.use_postgres_checkpointer）：
supervisor 图会在 observe 里被 interrupt() 挂起等人审批，那一刻进程内什么都不
推进了，"这次 run 停在哪个 checkpoint"必须已落盘，否则下一个请求（人点批准）
找不到恢复点。SSE 侧的 saver 由 sse_stream 在整个流期间持有。
"""

from __future__ import annotations

import asyncio
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
from app.llm.usage import reset_run_context, set_run_context
from app.ops.deps import CurrentUser
from app.ops.lg_rag import (
    ainvoke_basic_agent,
    ainvoke_router_agent,
    ainvoke_supervisor_agent,
)
from app.ops.lg_rag.checkpointer import apostgres_saver, use_postgres_checkpointer
from app.ops.lg_rag.event_store import (
    LgRagRunInFlightError,
    LgRagRunNotFoundError,
    LgRagRunResumeInProgressError,
    load_events_after,
)
from app.ops.lg_rag.run_worker import start_run_worker
from app.ops.lg_rag.sse_replay import InvalidCursorError, resolve_replay_target
from app.ops.lg_rag.sse_subscribe import subscribe_run_sse
from app.ops.lg_rag.thread_store import (
    LgRagThreadForbiddenError,
    load_thread_turns,
    persist_thread_turns,
    resolve_thread_for_user,
)
from app.ops.memory.extract import schedule_memory_extraction
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
    # Wave B：失败后「继续回复」= 同 thread 新 run；读旧 run partial 注入草稿（禁 HITL resume）
    continue_from_run_id: str | None = Field(default=None, max_length=64)


class ReplayRequest(BaseModel):
    """断联续看：``{run_id, after_seq}`` 或 ``{cursor}``（freeze lg-rag-sse-v1）。"""

    run_id: str | None = Field(default=None, max_length=64)
    after_seq: int | None = Field(default=None, ge=0)
    cursor: str | None = Field(default=None, max_length=96)
    # task_lg_rag_replay_resume_ux_opt D2：follow=true = live-tail
    # （推存量 → 事件表轮询按 seq 推增量 → 见新收尾帧收尾）；缺省 false = 存量重放字面零 diff。
    follow: bool = False


# ---------------------------------------------------------------------------
# replay follow live-tail 环境面（task_lg_rag_replay_resume_ux_opt D2 · 承 run_worker env 体例）
# ---------------------------------------------------------------------------

_REPLAY_FOLLOW_MAX_DEFAULT_SECONDS = 900.0
# 定稿理由（30 实证裁定 · FP-3）：恢复段实测 68–289s（2026-10-28 PG 实证
# run 38cb1138… latency_ms=289607 / 1039c1a9… ≈68s · 仅两数据点），总时长上限取
# max 实测约 3 倍余量定默认 900s（≥600s 建议线）；到点流自然结束、禁伪造帧，
# 客户端同请求重连即可续 tail。
_REPLAY_FOLLOW_POLL_DEFAULT_SECONDS = 2.0
_REPLAY_FOLLOW_POLL_MIN_SECONDS = 1.0


def _replay_follow_max_seconds() -> float:
    """读 env LG_RAG_REPLAY_FOLLOW_MAX_SECONDS；缺省/非法/≤0 回退默认。"""
    raw = os.environ.get("LG_RAG_REPLAY_FOLLOW_MAX_SECONDS", "").strip()
    if not raw:
        return _REPLAY_FOLLOW_MAX_DEFAULT_SECONDS
    try:
        value = float(raw)
    except ValueError:
        logger.warning("LG_RAG_REPLAY_FOLLOW_MAX_SECONDS 非法值 %r，回退默认 %.0fs", raw, _REPLAY_FOLLOW_MAX_DEFAULT_SECONDS)
        return _REPLAY_FOLLOW_MAX_DEFAULT_SECONDS
    if value <= 0:
        logger.warning("LG_RAG_REPLAY_FOLLOW_MAX_SECONDS 须 >0（%r），回退默认 %.0fs", raw, _REPLAY_FOLLOW_MAX_DEFAULT_SECONDS)
        return _REPLAY_FOLLOW_MAX_DEFAULT_SECONDS
    return value


def _replay_follow_poll_seconds() -> float:
    """读 env LG_RAG_REPLAY_FOLLOW_POLL_SECONDS；缺省/非法/≤0 回退默认；环境面 floor 1.0s（FP-6 防锤库）。"""
    raw = os.environ.get("LG_RAG_REPLAY_FOLLOW_POLL_SECONDS", "").strip()
    if not raw:
        return _REPLAY_FOLLOW_POLL_DEFAULT_SECONDS
    try:
        value = float(raw)
    except ValueError:
        logger.warning("LG_RAG_REPLAY_FOLLOW_POLL_SECONDS 非法值 %r，回退默认 %.0fs", raw, _REPLAY_FOLLOW_POLL_DEFAULT_SECONDS)
        return _REPLAY_FOLLOW_POLL_DEFAULT_SECONDS
    if value <= 0:
        logger.warning("LG_RAG_REPLAY_FOLLOW_POLL_SECONDS 须 >0（%r），回退默认 %.0fs", raw, _REPLAY_FOLLOW_POLL_DEFAULT_SECONDS)
        return _REPLAY_FOLLOW_POLL_DEFAULT_SECONDS
    return max(value, _REPLAY_FOLLOW_POLL_MIN_SECONDS)


def _replay_follow_keepalive_interval_s() -> float:
    """复用 sse_stream keepalive 体例（延迟 import · 模块属性运行时读，承 sse_subscribe 可 patch 先例）。"""
    from app.ops.lg_rag import sse_stream

    return float(sse_stream._KEEPALIVE_INTERVAL_S)


def _format_replay_sse_frame(ev: dict[str, Any]) -> str:
    """replay 面 SSE 帧体例（freeze lg-rag-sse-v1 · 存量重放与 follow 共用，逐字节一致）。"""
    return f"event: {ev['event_type']}\ndata: {json.dumps(ev, ensure_ascii=False)}\n\n"


async def _iter_replay_follow_sse(
    *,
    run_id: str,
    user_id: str,
    after_seq: int,
    initial_events: list[dict[str, Any]],
    poll_seconds: float,
    keepalive_interval_s: float,
    max_seconds: float,
) -> AsyncIterator[str]:
    """follow=true live-tail：推存量 → 事件表轮询按 seq 推增量 → 见新收尾帧收尾。

    契约（task_lg_rag_replay_resume_ux_opt D2）：
    - 轮询真源 = load_events_after（refuse_in_flight=False · follow=等待语义不写闸，
      故在飞/恢复段在写窗 follow 不返 409）；
    - 收尾条件 = 推出 seq > after_seq 的 done/error（含再挂起 done{waiting_approval} ·
      FP-7）；初始批已含收尾帧 ⇒ 推完即结束、零轮询；
    - keepalive = SSE comment（``: keepalive`` · 延迟 import 复用 sse_stream 体例）
      不进 data · 防 idle 掐断（FP-2）；
    - 总时长上限到点流自然结束，禁伪造 done/error/任何帧（FP-3 · 末帧永远来自事件表）；
    - 帧字节与存量重放逐字节同构（freeze lg-rag-sse-v1 零新 event_type）；
    - 无后台任务：客户端断连（aclose/CancelledError）即取消本循环，零残留。
    """
    from app.ops.lg_rag.sse_stream import _KEEPALIVE_FRAME

    loop = asyncio.get_running_loop()
    deadline = loop.time() + max_seconds
    cursor = after_seq
    for ev in initial_events:
        cursor = max(cursor, int(ev["seq"]))
        yield _format_replay_sse_frame(ev)
        if ev["event_type"] in ("done", "error"):
            return
    last_data = loop.time()
    next_poll = last_data  # 立即首 poll 追已落增量
    next_keepalive = last_data + keepalive_interval_s
    while True:
        now = loop.time()
        if now >= deadline:
            return
        if now >= next_poll:
            events = await load_events_after(
                run_id,
                user_id,
                cursor,
                refuse_in_flight=False,
            )
            now = loop.time()
            next_poll = now + poll_seconds
            if events:
                for ev in events:
                    cursor = max(cursor, int(ev["seq"]))
                    yield _format_replay_sse_frame(ev)
                    if ev["event_type"] in ("done", "error"):
                        return
                last_data = loop.time()
                next_keepalive = last_data + keepalive_interval_s
                continue
        if now >= next_keepalive:
            yield _KEEPALIVE_FRAME
            next_keepalive = now + keepalive_interval_s
            continue
        wake_at = min(next_poll, next_keepalive, deadline)
        delay = wake_at - loop.time()
        if delay > 0:
            await asyncio.sleep(delay)


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
    """委托给 checkpointer 模块的唯一真源（SSE 与恢复入口读同一把闸）。"""
    return use_postgres_checkpointer()


async def _dispatch(
    mode: Mode,
    query: str,
    thread_id: str,
    history_turns: list[dict] | None = None,
    run_id: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    """mode → 对应 ainvoke 入口；env 开关决定是否包 PG checkpointer。

    `user_id` = session 用户（阶段 T 身份链路的产物），仅供图内记忆注入
    （memory-facts-p0）；`MEMORY_FACTS_ENABLED` 默认关，关闭时零 diff。
    """
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
    if user_id:
        kwargs["user_id"] = user_id
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


async def _partial_answer_from_run(run_id: str, user_id: str) -> str:
    """从已落盘 run 聚合 partial answer（delta/content）；失败/未知 → 空串。"""
    from app.ops.lg_rag.event_store import LgRagRunNotFoundError, load_events_after

    try:
        events = await load_events_after(run_id, user_id, 0, refuse_in_flight=False)
    except LgRagRunNotFoundError:
        return ""
    except Exception:
        logger.exception("lg-rag continue_from_run_id load failed run_id=%s", run_id)
        return ""
    parts: list[str] = []
    final = ""
    for ev in events:
        if ev.get("event_type") != "answer":
            continue
        payload = ev.get("payload") or {}
        delta = payload.get("delta")
        if isinstance(delta, str) and delta:
            parts.append(delta)
        content = payload.get("content")
        if isinstance(content, str) and content:
            final = content
    if final:
        return final
    return "".join(parts)


def _resolve_request_tenant(request: Request) -> str:
    """F1=C：session 真源；头不一致 → 403；未知租户 → 422。"""
    session_tenant = getattr(request.state, "ops_tenant_id", TENANT_A)
    try:
        return resolve_header_against_session(session_tenant, request.headers.get(TENANT_HEADER))
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
    # D4：usage 落表 run 上下文（lg_rag 面 · hex run_id；与 chat UUID 口径区分）
    llm_ctx_token = set_run_context(run_id=run_id, surface="lg_rag")
    try:
        try:
            state = await _dispatch(
                body.mode,
                body.query,
                thread_id,
                history_turns=history_turns,
                run_id=run_id,
                user_id=str(user.id),
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
        answer = _extract_answer(state.get("messages"))
        try:
            await persist_thread_turns(thread_id, str(user.id), body.query, answer)
        except Exception:
            logger.exception("lg-rag invoke persist failed thread_id=%s", thread_id)
        # memory-facts-p1：run 完成后离线抽取（默认关；create_task 点火不 await，
        # 热路径零抽取调用零额外延迟；对齐 T5.1 后台 persist 模式）
        schedule_memory_extraction(
            tenant_id=tenant_id,
            user_id=str(user.id),
            run_id=run_id,
            source_turn=len(history_turns) + 1,
            query=body.query,
            answer=answer,
        )
        if tracing_enabled():
            flush_traces()
        return JSONResponse(
            content={
                "ok": True,
                "data": serialize_state(state, mode=body.mode, thread_id=thread_id).model_dump(),
            }
        )
    finally:
        reset_run_context(llm_ctx_token)
        reset_current_tenant(token)


@router.post("/stream")
async def stream_lg_rag(
    body: StreamRequest,
    request: Request,
    user: OpsUser = CurrentUser,
) -> StreamingResponse:
    """SSE 流式旁路（freeze lg-rag-sse-v1）；须登录。默认 mode=supervisor。

    Wave B：先 start RunWorker（持有 astream→event_store），再 subscribe fanout。
    客户端断连只取消 subscriber，worker 继续至普通 done / worker_failed。
    """
    tenant_id = _resolve_request_tenant(request)

    thread_id = (body.thread_id or uuid.uuid4().hex)[:THREAD_ID_MAX_LENGTH]
    history_turns = await _prepare_thread(thread_id, str(user.id))
    run_id = uuid.uuid4().hex
    query = body.query
    # B2 薄：可选 continue_from_run_id → 把旧 run partial 拼进 query 草稿（新 run_id）
    if body.continue_from_run_id:
        partial = await _partial_answer_from_run(body.continue_from_run_id, str(user.id))
        if partial:
            query = f"{body.query}\n\n[继续回复·既有草稿]\n{partial}"

    # 先启动 worker（与 HTTP 生命周期解耦），再订阅
    bus = start_run_worker(
        query=query,
        mode=body.mode,
        thread_id=thread_id,
        run_id=run_id,
        history_turns=history_turns,
        user_id=str(user.id),
        tenant_id=tenant_id,
    )

    async def event_gen() -> AsyncIterator[str]:
        # tenant / usage 已在 worker Task 内设置；订阅侧仅推帧
        async for chunk in subscribe_run_sse(run_id, bus=bus):
            yield chunk

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
    """SSE 重放已落盘帧（seq > after_seq）；须登录。

    未知/跨用户 run_id → 404；run 仍在流式写入（无收尾帧）→ 409 +
    Retry-After（F-OBS-2），客户端退避重试，沉降后同请求零 diff。
    HITL 恢复段在写窗（hitl.resumed 已落、尚无新收尾帧）→ 409 + Retry-After，
    detail 与首段在飞可区分（task_lg_rag_replay_resume_ux_opt D1）。
    follow=true（D2）→ live-tail：推存量 → 事件表轮询按 seq 推增量 → 见新收尾帧
    收尾；等待语义不写在飞/在写窗闸（不返 409）；总时长上限到点自然结束、禁伪造帧。
    """
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
        events = await load_events_after(
            run_id,
            str(user.id),
            after_seq,
            refuse_in_flight=not body.follow,
        )
    except LgRagRunResumeInProgressError:
        # D1：恢复段在写窗 replay 语义化——该形态既有在飞闸不拦（done{waiting_approval}
        # 挂起帧算收尾 · F-OBS-2 刻意口径），若无本映射则 replay 合法 200 零帧无语义区分；
        # detail 刻意区别于首段在飞 409，客户端退避重试，恢复段沉降后同请求零 diff。
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Resume is writing new events; retry after it settles.",
            headers={"Retry-After": "2"},
        ) from None
    except LgRagRunInFlightError:
        # F-OBS-2：在飞 replay 语义化——run 仍在流式写入时读路径不稳定（web 联调
        # FP-1 实证瞬返 500），前置判定为 409 + Retry-After 让客户端退避重试；
        # 沉降后同请求走原路径零 diff。
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Run is still in flight; retry after it settles.",
            headers={"Retry-After": "2"},
        ) from None
    except LgRagRunNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        ) from None

    if body.follow:
        # D2 follow=true live-tail：初始批不写在飞/在写窗闸（上方 refuse_in_flight=False），
        # 存量推完未收尾则事件表轮询续 tail；上限/轮询/keepalive 全走环境面 helper。
        return StreamingResponse(
            _iter_replay_follow_sse(
                run_id=run_id,
                user_id=str(user.id),
                after_seq=after_seq,
                initial_events=events,
                poll_seconds=_replay_follow_poll_seconds(),
                keepalive_interval_s=_replay_follow_keepalive_interval_s(),
                max_seconds=_replay_follow_max_seconds(),
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "X-Ops-Lg-Rag-Run-Id": run_id,
            },
        )

    async def event_gen() -> AsyncIterator[str]:
        for ev in events:
            yield _format_replay_sse_frame(ev)

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "X-Ops-Lg-Rag-Run-Id": run_id,
        },
    )
