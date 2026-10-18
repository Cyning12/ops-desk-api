"""T3 · lg-rag Session 连续性（纯函数 + mock DB；不连真 LLM；不测 replay）。"""

from __future__ import annotations

import ast
import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.ops.lg_rag.continuity import assemble_graph_messages, compress_window
from app.ops.lg_rag.thread_store import LgRagThreadForbiddenError

_STREAM = "/api/ops/lg-rag/stream"
_INVOKE = "/api/ops/lg-rag/invoke"
_LG_RAG_DIR = Path(__file__).resolve().parents[1] / "app" / "ops" / "lg_rag"


def test_lg_rag_package_does_not_import_chat_or_session() -> None:
    forbidden = ("app.ops.chat", "app.ops.session")
    for path in sorted(_LG_RAG_DIR.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not any(
                    node.module == f or node.module.startswith(f + ".") for f in forbidden
                ), f"{path.name} imports {node.module}"
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not any(
                        alias.name == f or alias.name.startswith(f + ".") for f in forbidden
                    ), f"{path.name} imports {alias.name}"


def _turns(*pairs: tuple[str, str]) -> list[dict]:
    return [{"role": role, "content": content} for role, content in pairs]


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


async def _fake_supervisor_stream(
    query: str, *, thread_id: str = "t", checkpointer: Any = None, **_kwargs
) -> AsyncIterator[dict[str, Any]]:
    yield {"aggregator": {"messages": [AIMessage(content=f"答:{query}")]}}


def test_compress_window_defaults_and_groups_head() -> None:
    turns = [{"role": "user", "content": f"q{i}"} for i in range(10)]
    out = compress_window(turns)
    # 默认 max_full_turns=6 → 头 4 条按 group_size=2 成 2 条摘要 + 尾 6
    assert len(out) == 8
    assert out[-1]["content"] == "q9"
    assert out[0]["role"] == "system"
    assert "历史摘要" in out[0]["content"]
    assert all(t["content"].startswith("q") for t in out[-6:])


def test_compress_window_short_noop() -> None:
    turns = _turns(("user", "hi"), ("assistant", "yo"))
    assert compress_window(turns, max_full_turns=6, group_size=2) == turns


def test_compress_window_failure_truncates_tail() -> None:
    turns: list[Any] = [{"role": "user", "content": str(i)} for i in range(10)]
    turns[0] = None
    out = compress_window(turns, max_full_turns=4, group_size=2)
    assert out == turns[-4:]


def test_assemble_same_thread_includes_previous_turn() -> None:
    history = _turns(("user", "上一问"), ("assistant", "上一答"))
    msgs = assemble_graph_messages("本轮问", history)
    texts = [m.content for m in msgs]
    assert "上一问" in texts
    assert "上一答" in texts
    assert texts[-1] == "本轮问"
    assert isinstance(msgs[-1], HumanMessage)
    assert any(isinstance(m, AIMessage) for m in msgs)


def test_assemble_different_thread_no_cross_history() -> None:
    other = assemble_graph_messages("b-问", _turns(("user", "a-问"), ("assistant", "a-答")))
    empty = assemble_graph_messages("b-问", [])
    assert [m.content for m in empty] == ["b-问"]
    assert "a-问" not in [m.content for m in empty]
    assert isinstance(other[0], HumanMessage)


def test_assemble_compressed_head_is_system() -> None:
    history = [{"role": "user", "content": f"q{i}"} for i in range(8)]
    msgs = assemble_graph_messages("now", history, max_full_turns=4, group_size=2)
    assert isinstance(msgs[0], SystemMessage)
    assert msgs[-1].content == "now"


async def test_ainvoke_injects_history_plus_query() -> None:
    captured: dict[str, Any] = {}

    class _FakeGraph:
        async def ainvoke(self, state: dict[str, Any], config: Any) -> dict[str, Any]:
            captured["messages"] = state["messages"]
            return state

    from app.ops.lg_rag.graph import _ainvoke_with_tracing

    await _ainvoke_with_tracing(
        _FakeGraph(),
        "q2",
        thread_id="th-1",
        history_turns=_turns(("user", "q1"), ("assistant", "a1")),
    )
    texts = [m.content for m in captured["messages"]]
    assert texts == ["q1", "a1", "q2"]


async def test_stream_requires_auth(client: AsyncClient) -> None:
    response = await client.post(_STREAM, json={"query": "续问"})
    assert response.status_code == 401


async def test_stream_missing_thread_id_returns_header(
    client: AsyncClient, override_auth_maintainer
) -> None:
    with (
        patch(
            "app.ops.lg_rag.router.resolve_thread_for_user",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "app.ops.lg_rag.router.load_thread_turns",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "app.ops.lg_rag.multi.graph.astream_supervisor_agent",
            new=_fake_supervisor_stream,
        ),
        patch(
            "app.ops.lg_rag.sse_stream.persist_thread_turns",
            new=AsyncMock(),
        ),
    ):
        response = await client.post(_STREAM, json={"query": "你好"})
    assert response.status_code == 200
    tid = response.headers.get("X-Ops-Lg-Rag-Thread-Id")
    assert tid
    assert len(tid) <= 255
    events = _parse_sse(response.text)
    assert events[0]["event_type"] == "run.start"
    assert events[0]["payload"]["thread_id"] == tid
    assert events[-1]["event_type"] == "done"


async def test_stream_thread_id_too_long_422(client: AsyncClient, override_auth_maintainer) -> None:
    response = await client.post(_STREAM, json={"query": "q", "thread_id": "t" * 256})
    assert response.status_code == 422


async def test_stream_cross_user_thread_404(client: AsyncClient, override_auth_maintainer) -> None:
    with patch(
        "app.ops.lg_rag.router.resolve_thread_for_user",
        new=AsyncMock(side_effect=LgRagThreadForbiddenError()),
    ):
        response = await client.post(_STREAM, json={"query": "q", "thread_id": "other-user-thread"})
    assert response.status_code == 404
    assert "other-user" not in response.text.lower()


async def test_invoke_cross_user_thread_404(client: AsyncClient, override_auth_maintainer) -> None:
    with patch(
        "app.ops.lg_rag.router.resolve_thread_for_user",
        new=AsyncMock(side_effect=LgRagThreadForbiddenError()),
    ):
        response = await client.post(_INVOKE, json={"query": "q", "thread_id": "other-user-thread"})
    assert response.status_code == 404


async def test_stream_same_thread_passes_previous_turns(
    client: AsyncClient, override_auth_maintainer
) -> None:
    captured: dict[str, Any] = {}
    history = _turns(("user", "上一问"), ("assistant", "上一答"))

    async def _capture_stream(
        query: str, *, thread_id: str = "t", history_turns=None, **_kwargs
    ) -> AsyncIterator[dict[str, Any]]:
        captured["query"] = query
        captured["thread_id"] = thread_id
        captured["history_turns"] = list(history_turns or [])
        yield {"aggregator": {"messages": [AIMessage(content="本轮答")]}}

    with (
        patch(
            "app.ops.lg_rag.router.resolve_thread_for_user",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "app.ops.lg_rag.router.load_thread_turns",
            new=AsyncMock(return_value=history),
        ),
        patch(
            "app.ops.lg_rag.multi.graph.astream_supervisor_agent",
            new=_capture_stream,
        ),
        patch(
            "app.ops.lg_rag.sse_stream.persist_thread_turns",
            new=AsyncMock(),
        ),
    ):
        response = await client.post(
            _STREAM,
            json={"query": "本轮问", "thread_id": "th-cont-1"},
        )
    assert response.status_code == 200
    assert captured["query"] == "本轮问"
    assert captured["thread_id"] == "th-cont-1"
    assert captured["history_turns"] == history
    assembled = assemble_graph_messages(captured["query"], captured["history_turns"])
    texts = [m.content for m in assembled]
    assert texts[:2] == ["上一问", "上一答"]
    assert texts[-1] == "本轮问"


async def test_stream_other_thread_does_not_get_history(
    client: AsyncClient, override_auth_maintainer
) -> None:
    captured: dict[str, Any] = {}

    async def _capture_stream(
        query: str, *, thread_id: str = "t", history_turns=None, **_kwargs
    ) -> AsyncIterator[dict[str, Any]]:
        captured[thread_id] = list(history_turns or [])
        yield {"aggregator": {"messages": [AIMessage(content="x")]}}

    with (
        patch(
            "app.ops.lg_rag.router.resolve_thread_for_user",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "app.ops.lg_rag.router.load_thread_turns",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "app.ops.lg_rag.multi.graph.astream_supervisor_agent",
            new=_capture_stream,
        ),
        patch(
            "app.ops.lg_rag.sse_stream.persist_thread_turns",
            new=AsyncMock(),
        ),
    ):
        response = await client.post(_STREAM, json={"query": "b", "thread_id": "th-b"})
    assert response.status_code == 200
    assert captured["th-b"] == []
