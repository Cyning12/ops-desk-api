"""lg-rag SSE：astream(updates) → T1 事件帧（freeze lg-rag-sse-v1）。

断连语义（T2/T4）：服务端尽量跑完图；不保证客户端收齐；无 cancel。
T4：每帧可选顶层 cursor；事件尽量落盘供 POST /lg-rag/replay。
T5：终答 token 流 —— emit 循环经 contextvar 挂 answer token sink
（answer_stream.complete_answer_streaming 桥），aggregator /
direct_answer 的 LLM chunk → answer {"delta": ...} 多帧；节点 updates
到后发终帧 {"content": <full>, "final": true}（T2 兼容）。
T5.1：persist 后台调度，不阻塞 SSE yield / pending_frames 入队。
§10.6：等待下一 update 期间周期性 SSE comment keepalive（不落盘、不占 seq）。
"""
from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import time
import uuid
from collections.abc import AsyncIterator, Callable
from typing import Any

from langchain_core.messages import AIMessage

from app.ops.lg_rag.answer_stream import (
    reset_answer_token_sink,
    set_answer_token_sink,
)
from app.ops.lg_rag.sse_replay import format_sse_event, make_cursor
from app.ops.lg_rag.thread_store import persist_thread_turns
from app.ops.tracing import flush_traces, tracing_enabled

logger = logging.getLogger(__name__)

_SUBTASK_NODES = frozenset({"rag_subtask", "info_extract", "tool_exec"})
_ROLE_ALIAS = {
    "intent_node": "intent",
    "critic_node": "critic",
}
_PAYLOAD_MAX = 800
_ANSWER_MAX = 32_000
# 终答节点（T5）：updates 帧映射为 answer 终帧（content + final）
_ANSWER_NODES = frozenset({"aggregator", "direct_answer"})
_STREAM_END: Any = object()  # astream 耗尽哨兵（区别于合法 update）
# §10.6：长节点静默保活（SSE comment · 不进 data JSON / 不落盘）
_KEEPALIVE_INTERVAL_S = 30.0
_KEEPALIVE_FRAME = ": keepalive\n\n"

def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def _sse_frame(event: dict[str, Any]) -> str:
    """SSE 帧外形对齐既有 chat 格式（event + data JSON）；不新增 event_type。"""
    return (
        f"event: {event['event_type']}\n"
        f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    )


def _summarize_payload(node_output: Any) -> dict[str, Any]:
    """节点输出摘要：避免把整段 state dump 进 SSE。"""
    if not isinstance(node_output, dict):
        return {"summary": _truncate(repr(node_output), _PAYLOAD_MAX)}
    out: dict[str, Any] = {}
    for key in (
        "intent",
        "allowed_capability_ids",
        "subtasks",
        "route",
        "retry_count",
        "critic_verdict",
        "rebinding_count",
    ):
        if key in node_output:
            raw = node_output[key]
            try:
                s = json.dumps(raw, ensure_ascii=False, default=str)
            except TypeError:
                s = repr(raw)
            out[key] = json.loads(s) if len(s) <= _PAYLOAD_MAX else _truncate(s, _PAYLOAD_MAX)
    if "subtask_results" in node_output:
        results = node_output.get("subtask_results") or []
        # updates 模式通常追加一条
        last = results[-1] if isinstance(results, list) and results else results
        try:
            s = json.dumps(last, ensure_ascii=False, default=str)
        except TypeError:
            s = repr(last)
        out["subtask_result"] = (
            json.loads(s) if len(s) <= _PAYLOAD_MAX else _truncate(s, _PAYLOAD_MAX)
        )
    if "messages" in node_output:
        answer = _extract_ai_text(node_output["messages"])
        if answer:
            out["answer_preview"] = _truncate(answer, min(200, _PAYLOAD_MAX))
    if not out:
        out["keys"] = sorted(node_output.keys())[:20]
    return out


def _extract_ai_text(messages: Any) -> str:
    for msg in reversed(messages or []):
        if isinstance(msg, AIMessage):
            content = msg.content
            return content if isinstance(content, str) else str(content)
        if getattr(msg, "type", None) == "ai":
            content = getattr(msg, "content", "")
            return content if isinstance(content, str) else str(content)
    return ""


def _agent_role(node_name: str) -> str:
    return _ROLE_ALIAS.get(node_name, node_name)


def map_node_update(node_name: str, node_output: Any) -> tuple[str, str, dict[str, Any]]:
    """返回 (event_type, agent_role, payload)。

    T5：aggregator / direct_answer 的 updates 帧 → ``answer`` 终帧
    ``{"content": <full>, "final": true}``（T2 兼容：旧客户端仅看
    ``content`` 行为不变）；token delta 帧不经本函数（sink 直发）。
    """
    role = _agent_role(node_name)
    if node_name in _SUBTASK_NODES:
        return "subtask.progress", role, _summarize_payload(node_output)
    if node_name in _ANSWER_NODES:
        answer = ""
        if isinstance(node_output, dict):
            answer = _extract_ai_text(node_output.get("messages"))
        return (
            "answer",
            role,
            {"content": _truncate(answer, _ANSWER_MAX), "final": True},
        )
    return "node.progress", role, _summarize_payload(node_output)


async def _anext_or_end(agen: AsyncIterator[dict[str, Any]]) -> Any:
    """``__anext__`` 包装：耗尽返回 ``_STREAM_END``；其余异常照常上抛。"""
    try:
        return await agen.__anext__()
    except StopAsyncIteration:
        return _STREAM_END


async def iter_lg_rag_sse(
    *,
    query: str,
    mode: str,
    thread_id: str,
    run_id: str | None = None,
    astream_fn: Callable[..., AsyncIterator[dict[str, Any]]] | None = None,
    history_turns: list[dict] | None = None,
    user_id: str | None = None,
) -> AsyncIterator[str]:
    """产出 SSE 字符串帧；异常时发 error 帧后结束。"""
    from app.ops.lg_rag.event_store import persist_run_event
    from app.ops.lg_rag.graph import astream_basic_agent, astream_router_agent
    from app.ops.lg_rag.multi.graph import astream_supervisor_agent

    rid = run_id or uuid.uuid4().hex
    started = time.perf_counter()
    seq = 0
    last_answer = ""
    # T5.1：落盘与 SSE yield 解耦——persist 失败仍不阻断已发帧（T4）；
    # 禁止 await persist 串在入队/yield 前（否则每 chunk 被 DB commit 卡节奏）。
    persist_tasks: set[asyncio.Task[None]] = set()

    async def emit(event_type: str, agent_role: str, payload: dict[str, Any]) -> str:
        nonlocal seq
        seq += 1
        event = format_sse_event(
            {
                "run_id": rid,
                "seq": seq,
                "ts_ms": int((time.perf_counter() - started) * 1000),
                "agent_role": agent_role,
                "event_type": event_type,
                "payload": payload,
            }
        )
        # format_sse_event 已写 cursor；兜底保证字段存在
        if not event.get("cursor"):
            event["cursor"] = make_cursor(rid, seq)
        frame = _sse_frame(event)
        if user_id:
            # 闭包钉死本帧字段，避免后续 seq 递增污染后台任务
            p_run_id = rid
            p_seq = seq
            p_user_id = user_id
            p_thread_id = thread_id
            p_ts_ms = int(event.get("ts_ms") or 0)
            p_agent_role = agent_role
            p_event_type = event_type
            p_payload = payload

            async def _persist_one() -> None:
                try:
                    await persist_run_event(
                        run_id=p_run_id,
                        seq=p_seq,
                        user_id=p_user_id,
                        thread_id=p_thread_id,
                        ts_ms=p_ts_ms,
                        agent_role=p_agent_role,
                        event_type=p_event_type,
                        payload=p_payload,
                    )
                except Exception:
                    logger.exception(
                        "lg-rag event persist failed run_id=%s seq=%s",
                        p_run_id,
                        p_seq,
                    )

            task = asyncio.create_task(_persist_one())
            persist_tasks.add(task)
            task.add_done_callback(persist_tasks.discard)
        return frame

    async def _drain_persist() -> None:
        if persist_tasks:
            await asyncio.gather(*tuple(persist_tasks), return_exceptions=True)

    yield await emit(
        "run.start",
        "system",
        {"run_id": rid, "thread_id": thread_id, "mode": mode},
    )

    if astream_fn is None:
        if mode == "basic":
            astream_fn = astream_basic_agent
        elif mode == "router":
            astream_fn = astream_router_agent
        else:
            astream_fn = astream_supervisor_agent

    saw_answer = False
    # T5 token sink：终答节点 LLM chunk 在此入队；sink 跑在图执行 task 的
    # context（不能 yield），帧经队列交回主循环吐出。emit 内 seq 单调 +
    # 尽量落盘（T5.1 后台），delta 帧与进度帧共享同一 seq 序列，不串台。
    pending_frames: asyncio.Queue[str] = asyncio.Queue()

    async def _answer_token_sink(role: str, chunk: str) -> None:
        frame = await emit("answer", role, {"delta": chunk})
        pending_frames.put_nowait(frame)

    sink_handle = set_answer_token_sink(_answer_token_sink)
    try:
        agen = astream_fn(
            query, thread_id=thread_id, history_turns=history_turns or []
        )
        while True:
            next_task = asyncio.ensure_future(_anext_or_end(agen))
            try:
                # 图执行期间 delta 帧先入队；与下一 update 竞速，先到先吐，
                # 保证长终答调用中 token 实时上屏（不等节点 updates）。
                # §10.6：等待超时则发 comment keepalive，重置客户端 idle。
                while not next_task.done():
                    get_task = asyncio.ensure_future(pending_frames.get())
                    done, _ = await asyncio.wait(
                        {next_task, get_task},
                        timeout=_KEEPALIVE_INTERVAL_S,
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                    if get_task in done:
                        yield get_task.result()
                        continue
                    get_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await get_task
                    if next_task.done():
                        break
                    yield _KEEPALIVE_FRAME
                # update 边界：先吐净残留 delta（sink 早于节点返回，seq 已单调）
                while not pending_frames.empty():
                    yield pending_frames.get_nowait()
                update = next_task.result()
            finally:
                # 生成器被 close（断连）或异常时取消挂起的 anext，防 task 泄漏
                if not next_task.done():
                    next_task.cancel()
            if update is _STREAM_END:
                break
            if not isinstance(update, dict):
                continue
            for node_name, node_output in update.items():
                event_type, role, payload = map_node_update(node_name, node_output)
                if event_type == "answer":
                    saw_answer = True
                    content = payload.get("content")
                    if isinstance(content, str) and content:
                        last_answer = content
                yield await emit(event_type, role, payload)
        # router/basic 可能无 aggregator：用末帧预览不够时仍发 done；
        # 若全程无 answer，补一帧空 answer 便于客户端统一收口（可选）
        if not saw_answer and mode != "supervisor":
            # basic/router：最后进度里可能已有 answer_preview；仍发空 answer 占位
            yield await emit("answer", "system", {"content": "", "note": "no_aggregator"})
        yield await emit(
            "done",
            "system",
            {
                "run_id": rid,
                "thread_id": thread_id,
                "latency_ms": int((time.perf_counter() - started) * 1000),
            },
        )
        await _drain_persist()
        if user_id:
            try:
                await persist_thread_turns(thread_id, user_id, query, last_answer)
            except Exception:
                logger.exception(
                    "lg-rag persist after done failed thread_id=%s", thread_id
                )
    except Exception as exc:
        # delta 途中图异常：已发 delta 保留（sink 已入队/落盘调度），先吐净残留再发
        # error 帧；不补 final 帧（failure_paths）。
        while not pending_frames.empty():
            yield pending_frames.get_nowait()
        logger.exception("lg-rag stream failed run_id=%s", rid)
        yield await emit(
            "error",
            "system",
            {
                "stage": "lg_rag.stream",
                "message": "旁路流式调用失败",
                "retryable": True,
                "detail": _truncate(repr(exc), 200),
            },
        )
        await _drain_persist()
    finally:
        reset_answer_token_sink(sink_handle)
        await _drain_persist()
        if tracing_enabled():
            flush_traces()
