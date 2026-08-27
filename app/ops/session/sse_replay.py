"""SSE 断线 replay 契约（seq/cursor · mock 友好）。"""

from __future__ import annotations

from typing import Any


def replay_cursor_from_event(event: dict) -> str:
    """从事件生成 replay cursor（``run_id:seq``）。"""
    run_id = str(event.get("run_id") or "")
    seq = int(event.get("seq") or 0)
    return f"{run_id}:{seq}"


def replay_events(
    events: list[dict],
    *,
    after_seq: int = 0,
) -> list[dict]:
    """过滤 ``seq > after_seq`` 的事件，供 SSE replay 重放。"""
    out: list[dict] = []
    for ev in events:
        seq = int(ev.get("seq") or 0)
        if seq > after_seq:
            out.append(ev)
    return out


def format_sse_replay_payload(event: dict) -> dict[str, Any]:
    """Replay 响应形状（与 ``make_sse_event`` data 一致）。"""
    return {
        "run_id": event.get("run_id"),
        "seq": event.get("seq"),
        "ts_ms": event.get("ts_ms"),
        "agent_role": event.get("agent_role"),
        "event_type": event.get("event_type"),
        "payload": event.get("payload", {}),
        "cursor": replay_cursor_from_event(event),
    }
