"""lg-rag SSE cursor / replay 纯函数（T4 · 不依赖 chat/session）。"""

from __future__ import annotations

from typing import Any


class InvalidCursorError(ValueError):
    """cursor / after_seq 格式非法；HTTP 映射 422。"""


def make_cursor(run_id: str, seq: int) -> str:
    """``cursor = "{run_id}:{seq}"``。"""
    return f"{run_id}:{seq}"


def parse_cursor(cursor: str) -> tuple[str, int]:
    """解析 cursor → ``(run_id, after_seq)``；非法抛 ``InvalidCursorError``。"""
    if not isinstance(cursor, str) or not cursor.strip():
        raise InvalidCursorError("cursor required")
    raw = cursor.strip()
    if ":" not in raw:
        raise InvalidCursorError("cursor must be run_id:seq")
    run_id, seq_part = raw.rsplit(":", 1)
    if not run_id:
        raise InvalidCursorError("cursor run_id empty")
    try:
        seq = int(seq_part)
    except ValueError as exc:
        raise InvalidCursorError("cursor seq must be int") from exc
    if seq < 0:
        raise InvalidCursorError("cursor seq must be >= 0")
    return run_id, seq


def resolve_replay_target(
    *,
    run_id: str | None = None,
    after_seq: int | None = None,
    cursor: str | None = None,
) -> tuple[str, int]:
    """body ``{cursor}`` 或 ``{run_id, after_seq}`` → ``(run_id, after_seq)``。"""
    if cursor is not None and str(cursor).strip():
        return parse_cursor(str(cursor))
    if run_id is not None and after_seq is not None:
        rid = str(run_id).strip()
        if not rid:
            raise InvalidCursorError("run_id empty")
        if not isinstance(after_seq, int) or isinstance(after_seq, bool):
            raise InvalidCursorError("after_seq must be int")
        if after_seq < 0:
            raise InvalidCursorError("after_seq must be >= 0")
        return rid, after_seq
    raise InvalidCursorError("require cursor or (run_id, after_seq)")


def replay_events(
    events: list[dict[str, Any]],
    *,
    after_seq: int = 0,
) -> list[dict[str, Any]]:
    """过滤 ``seq > after_seq``；客户端对同 run_id+seq 去重。"""
    out: list[dict[str, Any]] = []
    for ev in events:
        seq = int(ev.get("seq") or 0)
        if seq > after_seq:
            out.append(ev)
    return out


def format_sse_event(event: dict[str, Any]) -> dict[str, Any]:
    """live / replay 共用 data 形状（含可选顶层 cursor）。"""
    run_id = str(event.get("run_id") or "")
    seq = int(event.get("seq") or 0)
    return {
        "run_id": run_id,
        "seq": seq,
        "ts_ms": event.get("ts_ms"),
        "agent_role": event.get("agent_role"),
        "event_type": event.get("event_type"),
        "payload": event.get("payload", {}),
        "cursor": make_cursor(run_id, seq) if run_id else None,
    }
