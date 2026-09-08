"""lg-rag §10.7 · 子任务 progress 桥（running / step · freeze lg-rag-sse-v1）。

背景：``astream(updates)`` 仅在节点结束后才映射 ``subtask.progress``；
``rag_subtask`` 内 router / evidence 可静默数分钟。故采用与
``answer_stream`` 同构的 contextvar progress sink：SSE emit 循环挂 sink；
- ``emit_subtask_running``：入口起步帧 ``status=running``；
- ``emit_subtask_step``：中途里程碑 ``status=step`` + ``step`` + 可选 ``detail``；
- 两帧均带可选 ``message``（``subtask_message`` 确定性模板，纯同步，
  生成失败打日志降级、帧仍发）；
- 无 sink（invoke / 非 SSE）：空操作；sink 异常打日志不中断节点。

禁止新增 event_type；禁止 import app.ops.session / app.ops.chat。
"""
from __future__ import annotations

import contextvars
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from app.ops.lg_rag.subtask_message import (
    build_subtask_running_message,
    build_subtask_step_message,
)

logger = logging.getLogger(__name__)

_INPUT_PREVIEW_MAX = 200
_DETAIL_MAX = 400

# sink(agent_role, payload)：把 progress 帧交给 SSE emit 循环
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


def _truncate_detail(detail: dict[str, Any] | None) -> dict[str, Any] | None:
    if not detail:
        return None
    try:
        raw = json.dumps(detail, ensure_ascii=False, default=str)
    except TypeError:
        raw = repr(detail)
    if len(raw) <= _DETAIL_MAX:
        return detail
    return {"summary": _truncate_preview(raw, _DETAIL_MAX)}


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
    try:  # message 生成失败仅降级（帧仍发），不中断节点
        payload["message"] = build_subtask_running_message(
            type=type, input_preview=input_preview
        )
    except Exception as exc:
        logger.warning(
            "lg_rag running message 生成失败 id=%s err=%r", subtask_id, exc
        )
    try:
        await sink(agent_role, payload)
    except Exception as exc:
        logger.warning(
            "lg_rag subtask running 帧投递失败 role=%s id=%s err=%r",
            agent_role,
            subtask_id,
            exc,
        )


async def emit_subtask_step(
    *,
    agent_role: str,
    subtask_id: str,
    type: str,
    step: str,
    detail: dict[str, Any] | None = None,
) -> None:
    """子任务中途里程碑：有 sink 则推送 ``status=step``；无 sink 空操作。

    payload：``status`` / ``subtask_id`` / ``type`` / ``step``；
    ``detail`` 可选（截断，不塞全文 evidence）。
    """
    sink = current_subtask_progress_sink()
    if sink is None:
        return
    payload: dict[str, Any] = {
        "status": "step",
        "subtask_id": subtask_id,
        "type": type,
        "step": step,
    }
    truncated = _truncate_detail(detail)
    if truncated is not None:
        payload["detail"] = truncated
    try:  # message 生成失败仅降级（帧仍发），不中断节点
        payload["message"] = build_subtask_step_message(step=step, detail=detail)
    except Exception as exc:
        logger.warning(
            "lg_rag step message 生成失败 id=%s step=%s err=%r",
            subtask_id,
            step,
            exc,
        )
    try:
        await sink(agent_role, payload)
    except Exception as exc:
        logger.warning(
            "lg_rag subtask step 帧投递失败 role=%s id=%s step=%s err=%r",
            agent_role,
            subtask_id,
            step,
            exc,
        )
