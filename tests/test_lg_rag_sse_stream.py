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
    query: str, *, thread_id: str = "t", checkpointer: Any = None
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


async def test_map_node_update_helpers() -> None:
    from app.ops.lg_rag.sse_stream import map_node_update

    et, role, payload = map_node_update(
        "rag_subtask", {"subtask_results": [{"id": "t1", "output": "x"}]}
    )
    assert et == "subtask.progress"
    assert role == "rag_subtask"
    assert "subtask_result" in payload

    et, role, payload = map_node_update(
        "aggregator", {"messages": [AIMessage(content="答")]}
    )
    assert et == "answer"
    assert payload["content"] == "答"
