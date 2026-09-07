"""lg-rag SSE stream：鉴权、校验、事件序（mock astream）。"""
from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import patch

from httpx import AsyncClient
from langchain_core.messages import AIMessage

_PATH = "/api/ops/lg-rag/stream"


async def _fake_supervisor_stream(
    query: str, *, thread_id: str = "t", checkpointer: Any = None, **_kwargs
) -> AsyncIterator[dict[str, Any]]:
    yield {"intent_node": {"intent": {"domain": "kb", "needs_tool": False}}}
    yield {"strategy_builder": {"allowed_capability_ids": []}}
    yield {"supervisor": {"subtasks": [{"id": "t1", "type": "rag", "input": query}]}}
    yield {
        "rag_subtask": {
            "subtask_results": [{"id": "t1", "type": "rag", "output": "hit"}]
        }
    }
    yield {"aggregator": {"messages": [AIMessage(content="最终答案")]}}
    yield {"critic_node": {"critic_verdict": "pass"}}


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


async def test_stream_requires_auth(client: AsyncClient) -> None:
    response = await client.post(_PATH, json={"query": "你好"})
    assert response.status_code == 401


async def test_stream_empty_query_422(
    client: AsyncClient, override_auth_maintainer
) -> None:
    response = await client.post(_PATH, json={"query": ""})
    assert response.status_code == 422


async def test_stream_invalid_mode_422(
    client: AsyncClient, override_auth_maintainer
) -> None:
    response = await client.post(_PATH, json={"query": "q", "mode": "chat"})
    assert response.status_code == 422


async def test_stream_supervisor_event_order(
    client: AsyncClient, override_auth_maintainer
) -> None:
    with patch(
        "app.ops.lg_rag.multi.graph.astream_supervisor_agent",
        new=_fake_supervisor_stream,
    ):
        response = await client.post(
            _PATH,
            json={"query": "复合问", "thread_id": "th-sse-1"},
        )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    events = _parse_sse(response.text)
    types = [e["event_type"] for e in events]
    assert types[0] == "run.start"
    assert "node.progress" in types
    assert "subtask.progress" in types
    assert "answer" in types
    assert types[-1] == "done"
    answer = next(e for e in events if e["event_type"] == "answer")
    assert answer["payload"]["content"] == "最终答案"
    assert answer["agent_role"] == "aggregator"
    start = events[0]
    assert start["payload"]["thread_id"] == "th-sse-1"
    assert start["payload"]["mode"] == "supervisor"
    assert events[0]["seq"] == 1
    assert events[-1]["seq"] == len(events)
    for ev in events:
        assert ev.get("cursor") == f"{ev['run_id']}:{ev['seq']}"


async def test_map_node_update_helpers() -> None:
    from app.ops.lg_rag.sse_stream import map_node_update

    et, role, payload = map_node_update(
        "rag_subtask", {"subtask_results": [{"id": "t1", "output": "x"}]}
    )
    assert et == "subtask.progress"
    assert role == "rag_subtask"
    assert "subtask_result" in payload
    assert payload["status"] == "done"

    et, role, payload = map_node_update(
        "aggregator", {"messages": [AIMessage(content="答")]}
    )
    assert et == "answer"
    assert payload["content"] == "答"


async def test_subtask_running_before_slow_node_update() -> None:
    """§10.7：慢 rag_subtask 节点内 sleep 时，running 帧须先于 updates 完成帧可见。"""
    import asyncio
    from unittest.mock import AsyncMock, patch

    from app.ops.lg_rag.progress_stream import emit_subtask_running
    from app.ops.lg_rag.sse_stream import iter_lg_rag_sse

    async def _slow_rag_astream(
        query: str, *, thread_id: str = "t", **_kwargs: Any
    ) -> AsyncIterator[dict[str, Any]]:
        # 模拟节点入口：重活前 emit running，再 sleep（节点未结束）
        await emit_subtask_running(
            agent_role="rag_subtask",
            subtask_id="t1",
            type="rag",
            input_preview=query,
        )
        await asyncio.sleep(0.05)
        yield {
            "rag_subtask": {
                "subtask_results": [{"id": "t1", "type": "rag", "output": "hit"}]
            }
        }

    timeline: list[str] = []
    with (
        patch(
            "app.ops.lg_rag.event_store.persist_run_event",
            new_callable=AsyncMock,
        ) as persist_mock,
        patch(
            "app.ops.lg_rag.sse_stream.persist_thread_turns",
            new_callable=AsyncMock,
        ),
    ):
        async for raw in iter_lg_rag_sse(
            query="慢子任务",
            mode="supervisor",
            thread_id="th-sub-live",
            user_id="u-sub-live",
            astream_fn=_slow_rag_astream,
        ):
            for block in raw.split("\n\n"):
                block = block.strip()
                if not block or not block.startswith("event:"):
                    continue
                data_line = None
                for line in block.split("\n"):
                    if line.startswith("data: "):
                        data_line = line[len("data: ") :]
                if not data_line:
                    continue
                ev = json.loads(data_line)
                if ev.get("event_type") != "subtask.progress":
                    continue
                status = (ev.get("payload") or {}).get("status")
                if status == "running":
                    timeline.append("running")
                elif status == "done":
                    timeline.append("done")

    assert timeline == ["running", "done"]
    # running 帧落盘占 seq
    running_persists = [
        c
        for c in persist_mock.await_args_list
        if c.kwargs.get("event_type") == "subtask.progress"
        and (c.kwargs.get("payload") or {}).get("status") == "running"
    ]
    assert running_persists, "running 帧须走 emit→persist"
    assert running_persists[0].kwargs["payload"]["subtask_id"] == "t1"
    assert running_persists[0].kwargs["payload"]["type"] == "rag"


async def test_keepalive_comment_before_slow_update() -> None:
    """§10.6：慢 __anext__ 期间须先 yield comment keepalive（不占 seq / 非 data 帧）。"""
    import asyncio
    from unittest.mock import AsyncMock, patch

    from app.ops.lg_rag.sse_stream import _KEEPALIVE_FRAME, iter_lg_rag_sse

    async def _slow_astream(
        query: str, *, thread_id: str = "t", **_kwargs: Any
    ) -> AsyncIterator[dict[str, Any]]:
        await asyncio.sleep(0.12)
        yield {"intent_node": {"intent": {"domain": "kb"}}}

    frames: list[str] = []
    with (
        patch("app.ops.lg_rag.sse_stream._KEEPALIVE_INTERVAL_S", 0.04),
        patch(
            "app.ops.lg_rag.event_store.persist_run_event",
            new_callable=AsyncMock,
        ) as persist_mock,
    ):
        async for frame in iter_lg_rag_sse(
            query="慢节点",
            mode="supervisor",
            thread_id="th-ka-1",
            user_id="u-ka",
            astream_fn=_slow_astream,
        ):
            frames.append(frame)

    assert any(f == _KEEPALIVE_FRAME for f in frames)
    first_keepalive = next(i for i, f in enumerate(frames) if f == _KEEPALIVE_FRAME)
    first_data = next(i for i, f in enumerate(frames) if f.startswith("event:"))
    # run.start 先于 keepalive；慢 update 的 keepalive 在节点 data 帧之前
    assert first_data < first_keepalive
    data_after_ka = [f for f in frames[first_keepalive:] if f.startswith("event:")]
    assert data_after_ka, "keepalive 之后仍应有业务帧"
    # comment 不落盘
    for call in persist_mock.await_args_list:
        kwargs = call.kwargs
        assert kwargs.get("event_type") != "keepalive"
        payload = kwargs.get("payload") or {}
        assert "keepalive" not in str(payload).lower()
