"""lg-rag §10.7 · 子任务 running 起步帧桥（freeze lg-rag-sse-v1 扩展）。

背景：``astream(updates)`` 仅在节点结束后才映射 ``subtask.progress``；
``rag_subtask`` 内整段 ``ainvoke_router_agent`` 可静默数分钟。故采用与
``answer_stream`` 同构的 contextvar progress sink：SSE emit 循环挂 sink；
子任务节点入口 ``emit_subtask_running`` ——
    - 有 sink：立即推送 ``(agent_role, payload)``，emit 循环发
      ``subtask.progress`` + ``status=running``（与 delta 同 ``pending_frames`` 竞速）；
    - 无 sink（invoke / 非 SSE）：空操作；
    - sink 异常：打日志，不中断节点（failure_paths）。

禁止新增 event_type；禁止 import app.ops.session / app.ops.chat。
"""
from __future__ import annotations

import contextvars
import logging
from collections.abc import Awaitable, Callable
from typing import Any

logger = logging.getLogger(__name__)

_INPUT_PREVIEW_MAX = 200

# sink(agent_role, payload)：把 running 帧交给 SSE emit 循环
SubtaskProgressSink = Callable[[str, dict[str, Any]], Awaitable[None]]

_subtask_progress_sink: contextvars.ContextVar[SubtaskProgressSink | None] = (
    contextvars.ContextVar("lg_rag_subtask_progress_sink", default=None)
)


def current_subtask_progress_sink() -> SubtaskProgressSink | None:
    """当前上下文的 progress sink；无（invoke / 非 SSE）则 ``None``。"""
    return _subtask_progress_sink.get()


def set_subtask_progress_sink(
    sink: SubtaskProgressSink,
) -> contextvars.Token[SubtaskProgressSink | None]:
    """挂 sink（SSE emit 循环在创建图执行 task 前调用，context 随之传播）。"""
    return _subtask_progress_sink.set(sink)


def reset_subtask_progress_sink(
    handle: contextvars.Token[SubtaskProgressSink | None],
) -> None:
    """摘除 sink（emit 循环 finally 中复位，防泄漏到调用方 context）。"""
    _subtask_progress_sink.reset(handle)


def _truncate_preview(text: str, max_len: int = _INPUT_PREVIEW_MAX) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


async def emit_subtask_running(
    *,
    agent_role: str,
    subtask_id: str,
    type: str,
    input_preview: str = "",
) -> None:
    """子任务入口起步帧：有 sink 则推送 running；无 sink 空操作。

    payload 至少含 ``status=running`` / ``subtask_id`` / ``type``；
    ``input_preview`` 非空时写入截断 ``input``。
    """
    sink = current_subtask_progress_sink()
    if sink is None:
        return
    payload: dict[str, Any] = {
        "status": "running",
        "subtask_id": subtask_id,
        "type": type,
    }
    if input_preview:
        payload["input"] = _truncate_preview(input_preview)
    try:
        await sink(agent_role, payload)
    except Exception as exc:
        logger.warning(
            "lg_rag subtask running 帧投递失败 role=%s id=%s err=%r",
            agent_role,
            subtask_id,
            exc,
        )
