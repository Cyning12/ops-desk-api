"""T4 · lg-rag SSE resume / replay（纯函数 + mock；不连真 LLM）。"""
from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from langchain_core.messages import AIMessage

from app.ops.lg_rag.event_store import LgRagRunNotFoundError
from app.ops.lg_rag.sse_replay import (
    InvalidCursorError,
    format_sse_event,
    make_cursor,
    parse_cursor,
    replay_events,
    resolve_replay_target,
)

_STREAM = "/api/ops/lg-rag/stream"
_REPLAY = "/api/ops/lg-rag/replay"


def _parse_sse(body: str) -> list[dict]:
    events: list[dict] = []
    for block in body.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        data_line = None
        for line in block.split("\n"):
            if line.startswith("data: "):
                data_line = line[len("data: ") :]
        if data_line:
            events.append(json.loads(data_line))
    return events


def test_make_and_parse_cursor() -> None:
    assert make_cursor("abc", 3) == "abc:3"
    assert parse_cursor("abc:3") == ("abc", 3)
    assert parse_cursor("run:with:colons:9") == ("run:with:colons", 9)


def test_parse_cursor_invalid() -> None:
    with pytest.raises(InvalidCursorError):
        parse_cursor("")
    with pytest.raises(InvalidCursorError):
        parse_cursor("noseq")
    with pytest.raises(InvalidCursorError):
        parse_cursor(":1")
    with pytest.raises(InvalidCursorError):
        parse_cursor("r:x")


def test_resolve_replay_target_forms() -> None:
    assert resolve_replay_target(cursor="r1:2") == ("r1", 2)
    assert resolve_replay_target(run_id="r1", after_seq=0) == ("r1", 0)
    with pytest.raises(InvalidCursorError):
        resolve_replay_target()
    with pytest.raises(InvalidCursorError):
        resolve_replay_target(run_id="r1")


def test_replay_events_strict_gt() -> None:
    events = [
        {"run_id": "r", "seq": 1, "event_type": "run.start", "payload": {}},
        {"run_id": "r", "seq": 2, "event_type": "answer", "payload": {"content": "a"}},
        {"run_id": "r", "seq": 3, "event_type": "done", "payload": {}},
    ]
    assert [e["seq"] for e in replay_events(events, after_seq=1)] == [2, 3]
    assert [e["seq"] for e in replay_events(events, after_seq=2)] == [3]
    assert replay_events(events, after_seq=3) == []
    # 重复同一 after_seq 不重发已收区间
    again = replay_events(events, after_seq=1)
    assert [e["seq"] for e in again] == [2, 3]


def test_format_sse_event_has_cursor() -> None:
    ev = format_sse_event(
        {
            "run_id": "rid",
            "seq": 4,
            "ts_ms": 10,
            "agent_role": "system",
            "event_type": "done",
            "payload": {},
        }
    )
    assert ev["cursor"] == "rid:4"
    assert ev["event_type"] == "done"


async def _fake_supervisor_stream(
    query: str, *, thread_id: str = "t", checkpointer: Any = None, **_kwargs
) -> AsyncIterator[dict[str, Any]]:
    yield {"aggregator": {"messages": [AIMessage(content=f"答:{query}")]}}


async def test_stream_frames_include_cursor(
    client: AsyncClient, override_auth_maintainer
) -> None:
    with (
        patch(
            "app.ops.lg_rag.multi.graph.astream_supervisor_agent",
            new=_fake_supervisor_stream,
        ),
        patch(
            "app.ops.lg_rag.sse_stream.persist_thread_turns",
            new_callable=AsyncMock,
        ),
        patch(
            "app.ops.lg_rag.event_store.persist_run_event",
            new_callable=AsyncMock,
        ),
    ):
        response = await client.post(
            _STREAM,
            json={"query": "续看", "thread_id": "th-resume-1"},
        )
    assert response.status_code == 200
    events = _parse_sse(response.text)
    assert events
    for ev in events:
        assert ev["cursor"] == f"{ev['run_id']}:{ev['seq']}"
    assert events[0]["event_type"] == "run.start"
    assert events[-1]["event_type"] == "done"


async def test_replay_requires_auth(client: AsyncClient) -> None:
    response = await client.post(_REPLAY, json={"run_id": "r", "after_seq": 0})
    assert response.status_code == 401


async def test_replay_invalid_cursor_422(
    client: AsyncClient, override_auth_maintainer
) -> None:
    response = await client.post(_REPLAY, json={"cursor": "bad"})
    assert response.status_code == 422


async def test_replay_unknown_run_404(
    client: AsyncClient, override_auth_maintainer
) -> None:
    with patch(
        "app.ops.lg_rag.router.load_events_after",
        new_callable=AsyncMock,
        side_effect=LgRagRunNotFoundError,
    ):
        response = await client.post(
            _REPLAY, json={"run_id": "missing", "after_seq": 0}
        )
    assert response.status_code == 404


async def test_replay_after_seq_sse_shape(
    client: AsyncClient, override_auth_maintainer
) -> None:
    stored = [
        format_sse_event(
            {
                "run_id": "run-x",
                "seq": 2,
                "ts_ms": 20,
                "agent_role": "aggregator",
                "event_type": "answer",
                "payload": {"content": "hi"},
            }
        ),
        format_sse_event(
            {
                "run_id": "run-x",
                "seq": 3,
                "ts_ms": 30,
                "agent_role": "system",
                "event_type": "done",
                "payload": {},
            }
        ),
    ]
    with patch(
        "app.ops.lg_rag.router.load_events_after",
        new_callable=AsyncMock,
        return_value=stored,
    ) as mock_load:
        response = await client.post(
            _REPLAY, json={"run_id": "run-x", "after_seq": 1}
        )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    mock_load.assert_awaited_once()
    events = _parse_sse(response.text)
    assert [e["seq"] for e in events] == [2, 3]
    assert events[0]["cursor"] == "run-x:2"
    assert events[0]["payload"]["content"] == "hi"

    # 同一 after_seq 再次请求：mock 仍只返回 > after_seq（契约）
    with patch(
        "app.ops.lg_rag.router.load_events_after",
        new_callable=AsyncMock,
        return_value=stored,
    ):
        again = await client.post(_REPLAY, json={"cursor": "run-x:1"})
    assert [e["seq"] for e in _parse_sse(again.text)] == [2, 3]
