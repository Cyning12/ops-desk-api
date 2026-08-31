"""lg-rag SSE：astream(updates) → T1 事件帧（freeze lg-rag-sse-v1）。

断连语义（T2）：服务端尽量跑完图；不保证客户端收齐；无 cancel/replay（T4）。
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from collections.abc import AsyncIterator, Callable
from typing import Any

from langchain_core.messages import AIMessage

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
    """返回 (event_type, agent_role, payload)。"""
    role = _agent_role(node_name)
    if node_name in _SUBTASK_NODES:
        return "subtask.progress", role, _summarize_payload(node_output)
    if node_name == "aggregator":
        answer = ""
        if isinstance(node_output, dict):
            answer = _extract_ai_text(node_output.get("messages"))
        return (
            "answer",
            "aggregator",
            {"content": _truncate(answer, _ANSWER_MAX)},
        )
    return "node.progress", role, _summarize_payload(node_output)


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
    from app.ops.lg_rag.graph import astream_basic_agent, astream_router_agent
    from app.ops.lg_rag.multi.graph import astream_supervisor_agent

    rid = run_id or uuid.uuid4().hex
    started = time.perf_counter()
    seq = 0
    last_answer = ""

    def emit(event_type: str, agent_role: str, payload: dict[str, Any]) -> str:
        nonlocal seq
        seq += 1
        return _sse_frame(
            {
                "run_id": rid,
                "seq": seq,
                "ts_ms": int((time.perf_counter() - started) * 1000),
                "agent_role": agent_role,
                "event_type": event_type,
                "payload": payload,
            }
        )

    yield emit(
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
    try:
        async for update in astream_fn(
            query, thread_id=thread_id, history_turns=history_turns or []
        ):
            if not isinstance(update, dict):
                continue
            for node_name, node_output in update.items():
                event_type, role, payload = map_node_update(node_name, node_output)
                if event_type == "answer":
                    saw_answer = True
                    content = payload.get("content")
                    if isinstance(content, str) and content:
                        last_answer = content
                yield emit(event_type, role, payload)
        # router/basic 可能无 aggregator：用末帧预览不够时仍发 done；
        # 若全程无 answer，补一帧空 answer 便于客户端统一收口（可选）
        if not saw_answer and mode != "supervisor":
            # basic/router：最后进度里可能已有 answer_preview；仍发空 answer 占位
            yield emit("answer", "system", {"content": "", "note": "no_aggregator"})
        yield emit(
            "done",
            "system",
            {
                "run_id": rid,
                "thread_id": thread_id,
                "latency_ms": int((time.perf_counter() - started) * 1000),
            },
        )
        if user_id:
            try:
                await persist_thread_turns(thread_id, user_id, query, last_answer)
            except Exception:
                logger.exception(
                    "lg-rag persist after done failed thread_id=%s", thread_id
                )
    except Exception as exc:
        logger.exception("lg-rag stream failed run_id=%s", rid)
        yield emit(
            "error",
            "system",
            {
                "stage": "lg_rag.stream",
                "message": "旁路流式调用失败",
                "retryable": True,
                "detail": _truncate(repr(exc), 200),
            },
        )
    finally:
        if tracing_enabled():
            flush_traces()
