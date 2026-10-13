"""T4 · lg-rag SSE resume / replay（纯函数 + mock；不连真 LLM）。"""
from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from langchain_core.messages import AIMessage

from tests.conftest import DB_AVAILABLE

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


# ---------------------------------------------------------------------------
# F-OBS-2 · 在飞 replay 语义化（409 + Retry-After，不再 500）
# ---------------------------------------------------------------------------

_DB_REQUIRED = pytest.mark.skipif(
    not DB_AVAILABLE, reason="需要本地 PG（opsdesk_test）真跑事件表"
)


async def test_replay_in_flight_run_409_with_retry_after(
    client: AsyncClient, override_auth_maintainer
) -> None:
    """run 在飞（帧在写、未收尾）时 replay → 409 + Retry-After（正整数秒），不再 500。

    web 联调 FP-1 实证：在飞 replay 瞬返 500（run 640d68970a564fbb8459d8d40cb1c5f6），
    沉降后 200。语义化后客户端收到 409 退避重试；沉降后路径零 diff。
    修复前 RED 签名：event_store 尚无 LgRagRunInFlightError（AttributeError），
    修复后若漏映射则该异常冒穿路由成裸 500。
    """
    from app.ops.lg_rag import event_store

    with patch(
        "app.ops.lg_rag.router.load_events_after",
        new_callable=AsyncMock,
        side_effect=event_store.LgRagRunInFlightError,
    ):
        response = await client.post(
            _REPLAY, json={"run_id": "run-live", "after_seq": 0}
        )
    assert response.status_code == 409
    retry_after = response.headers.get("Retry-After")
    assert retry_after is not None, "409 必须带 Retry-After 供客户端退避"
    assert retry_after.isdigit() and int(retry_after) > 0


async def _persist_frame(
    run_id: str, seq: int, user_id: str, event_type: str, payload: dict
) -> None:
    from app.ops.lg_rag import event_store

    await event_store.persist_run_event(
        run_id=run_id,
        seq=seq,
        user_id=user_id,
        thread_id=f"th-{run_id}",
        ts_ms=seq * 10,
        agent_role="system",
        event_type=event_type,
        payload=payload,
    )


@_DB_REQUIRED
async def test_load_events_refuses_in_flight_run(seeded_maintainer) -> None:
    """在飞（有帧、无 done/error 收尾帧）→ refuse_in_flight=True 抛 LgRagRunInFlightError。

    同用例对照（默认形态 refuse_in_flight 缺省 False 照常返回在飞帧）同时实证：
    读取路径本身在真 PG 下不抛——live 500 的具体异常类型仓内不可复现，
    语义化前置判定使该异常面整体不再触达（裁定留痕见 30 invoke）。
    修复前 RED 签名：TypeError（load_events_after 尚无 refuse_in_flight 形参）。
    """
    import uuid

    from app.ops.lg_rag import event_store

    user_id = str(seeded_maintainer["user"].id)
    run_id = f"inflight-{uuid.uuid4().hex[:8]}"
    await _persist_frame(run_id, 1, user_id, "run.start", {"status": "started"})
    await _persist_frame(run_id, 2, user_id, "subtask", {"subtask_id": "s1"})

    with pytest.raises(event_store.LgRagRunInFlightError):
        await event_store.load_events_after(run_id, user_id, 0, refuse_in_flight=True)

    events = await event_store.load_events_after(run_id, user_id, 0)
    assert [e["seq"] for e in events] == [1, 2]


@_DB_REQUIRED
async def test_load_events_waiting_approval_replays_normally(seeded_maintainer) -> None:
    """挂起待恢复（done{waiting_approval}）不算在飞：其 replay 是既有合法操作，必须零 diff。

    判定面红线：waiting_approval 对 run_is_terminal 是「非终态」，但对 replay 闸
    是「已收尾」——若复用 run_is_terminal 会把挂起 run 的合法 replay 误拦成 409。
    """
    import uuid

    from app.ops.lg_rag import event_store

    user_id = str(seeded_maintainer["user"].id)
    run_id = f"suspended-{uuid.uuid4().hex[:8]}"
    await _persist_frame(run_id, 1, user_id, "run.start", {"status": "started"})
    await _persist_frame(run_id, 2, user_id, "done", {"status": "waiting_approval"})

    events = await event_store.load_events_after(run_id, user_id, 0, refuse_in_flight=True)
    assert [e["seq"] for e in events] == [1, 2]


@_DB_REQUIRED
async def test_load_events_terminal_run_passes_refusal_gate(seeded_maintainer) -> None:
    """已沉降 run（done{completed}）→ refuse_in_flight=True 照常返回（TC3 零 diff 存储层锚点）。"""
    import uuid

    from app.ops.lg_rag import event_store

    user_id = str(seeded_maintainer["user"].id)
    run_id = f"settled-{uuid.uuid4().hex[:8]}"
    await _persist_frame(run_id, 1, user_id, "run.start", {"status": "started"})
    await _persist_frame(run_id, 2, user_id, "done", {"status": "completed"})

    events = await event_store.load_events_after(run_id, user_id, 0, refuse_in_flight=True)
    assert [e["seq"] for e in events] == [1, 2]
