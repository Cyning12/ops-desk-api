"""SSE event formatting utilities."""
import json
import time


def make_sse_event(run_id: str, seq: int, started_at: float, event_type: str, agent_role: str, payload: dict) -> str:
    """Format a single SSE message."""
    data = {
        "run_id": run_id,
        "seq": seq,
        "ts_ms": int((time.perf_counter() - started_at) * 1000),
        "agent_role": agent_role,
        "event_type": event_type,
        "payload": payload,
    }
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
