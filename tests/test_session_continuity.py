"""H3 · Chat Session 连续性（纯函数 + mock）。"""

from __future__ import annotations

from app.ops.session.continuity import compress_window
from app.ops.session.sse_replay import (
    format_sse_replay_payload,
    replay_cursor_from_event,
    replay_events,
)


def test_compress_window_keeps_tail_full():
    turns = [
        {"role": "user", "content": f"q{i}"}
        for i in range(10)
    ]
    out = compress_window(turns, max_full_turns=4, group_size=2)
    assert len(out) == 7  # 3 summary groups + 4 tail
    assert out[-1]["content"] == "q9"
    assert out[0]["role"] == "system"
    assert "历史摘要" in out[0]["content"]


def test_compress_window_small_noop():
    turns = [{"role": "user", "content": "hi"}]
    assert compress_window(turns, max_full_turns=6) == turns


def test_replay_events_after_seq():
    events = [
        {"run_id": "r1", "seq": 1, "event_type": "run.start", "payload": {}},
        {"run_id": "r1", "seq": 2, "event_type": "answer", "payload": {"content": "a"}},
        {"run_id": "r1", "seq": 3, "event_type": "done", "payload": {}},
    ]
    replay = replay_events(events, after_seq=1)
    assert [e["seq"] for e in replay] == [2, 3]


def test_replay_cursor_and_payload():
    ev = {"run_id": "abc", "seq": 5, "event_type": "answer", "payload": {"content": "x"}}
    assert replay_cursor_from_event(ev) == "abc:5"
    payload = format_sse_replay_payload(ev)
    assert payload["cursor"] == "abc:5"
    assert payload["event_type"] == "answer"
