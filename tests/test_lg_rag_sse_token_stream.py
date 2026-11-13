"""T5 · lg-rag SSE token 流：answer 多帧 delta + 终帧 final（mock · 不连真 LLM）。

覆盖（task_lg_rag_sse_token_stream 验收）：
- delta 帧序 + 拼接 == 终帧 content（mock 断言）
- delta 与 node.progress/subtask.progress 并存、全程 seq 单调不串台
- 终帧 {"content", "final": true} T2 兼容外形
- token 流异常/不支持 → 降级整段 answer（T2 行为）
- delta/终帧落盘 ops_lg_rag_run_events（persist_run_event 调用断言）
- replay 逐帧重放含 delta；basic 占位帧不变；401/404 不变
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from langchain_core.messages import AIMessage

from app.llm.schema import BaseProvider, LlmChunk, LlmMessage
from app.ops.lg_rag.answer_stream import (
    complete_answer_streaming,
    current_answer_token_sink,
    reset_answer_token_sink,
    set_answer_token_sink,
)
from app.ops.lg_rag.sse_replay import format_sse_event


@pytest.fixture(autouse=True)
def _no_pg_checkpointer_by_default(monkeypatch):
    """测试**不该**从 `.env` 继承「生产式」配置（同 test_lg_rag_sse_stream）。

    ``LG_RAG_HTTP_CHECKPOINTER=postgres`` 会让 supervisor 模式的 SSE 真去开
    PG saver（连库 + 建表）⇒ 测试依赖外部环境、变慢，对照断言还会被翻掉。
    P0' T3 后必须显式置空值（delenv 会吃到「unset=默认开」）。
    """
    monkeypatch.setenv("LG_RAG_HTTP_CHECKPOINTER", "")


_STREAM = "/api/ops/lg-rag/stream"
_REPLAY = "/api/ops/lg-rag/replay"


class _FakeProvider(BaseProvider):
    """可控 mock provider：complete_stream 吐固定 chunk，可选中途抛错。"""

    def __init__(
        self,
        chunks: list[str] | None = None,
        full: str = "",
        stream_exc: Exception | None = None,
    ) -> None:
        self._chunks = chunks or []
        self._full = full
        self._stream_exc = stream_exc
        self.complete_calls = 0

    async def complete(self, messages: Any, model: str | None = None) -> str:
        self.complete_calls += 1
        return self._full

    async def complete_stream(
        self, messages: Any, model: str | None = None
    ) -> AsyncIterator[LlmChunk]:
        for text in self._chunks:
            yield LlmChunk(content=text)
        if self._stream_exc is not None:
            raise self._stream_exc


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


def _msgs(text: str) -> list[LlmMessage]:
    return [LlmMessage(role="user", content=text)]


# ---------------------------------------------------------------------------
# 纯桥：complete_answer_streaming
# ---------------------------------------------------------------------------


async def test_bridge_no_sink_uses_complete() -> None:
    """无 sink（invoke / 非 SSE 路径）→ 整段 complete，行为与 T2 一致。"""
    provider = _FakeProvider(full="整段")
    assert current_answer_token_sink() is None
    out = await complete_answer_streaming(provider, _msgs("q"), node="aggregator")
    assert out == "整段"
    assert provider.complete_calls == 1


async def test_bridge_with_sink_pushes_chunks() -> None:
    """有 sink → complete_stream 逐 chunk 推 (node, chunk)；返回拼接全文。"""
    provider = _FakeProvider(chunks=["最终", "答案"], full="不应调用")
    got: list[tuple[str, str]] = []

    async def sink(role: str, chunk: str) -> None:
        got.append((role, chunk))

    handle = set_answer_token_sink(sink)
    try:
        out = await complete_answer_streaming(provider, _msgs("q"), node="aggregator")
    finally:
        reset_answer_token_sink(handle)
    assert out == "最终答案"
    assert got == [("aggregator", "最终"), ("aggregator", "答案")]
    assert provider.complete_calls == 0
    assert current_answer_token_sink() is None


async def test_bridge_stream_error_degrades_to_complete() -> None:
    """流式中途异常：已推 delta 保留，降级 complete 取整段返回 + 日志。"""
    provider = _FakeProvider(
        chunks=["半截"], full="整段兜底", stream_exc=RuntimeError("stream boom")
    )
    got: list[str] = []

    async def sink(_role: str, chunk: str) -> None:
        got.append(chunk)

    handle = set_answer_token_sink(sink)
    try:
        out = await complete_answer_streaming(provider, _msgs("q"), node="aggregator")
    finally:
        reset_answer_token_sink(handle)
    assert got == ["半截"]  # 已发 delta 保留
    assert out == "整段兜底"  # 终帧 content 全量替换语义兜底
    assert provider.complete_calls == 1


# ---------------------------------------------------------------------------
# HTTP：delta 帧序 / 拼接 / 并存 / 降级
# ---------------------------------------------------------------------------


async def test_stream_delta_frames_order_and_join(
    client: AsyncClient, override_auth_maintainer
) -> None:
    """aggregator token → answer delta 多帧；拼接 == 终帧 content；落盘含 delta。"""

    async def _fake_stream(
        query: str, *, thread_id: str = "t", checkpointer: Any = None, **_kw: Any
    ) -> AsyncIterator[dict[str, Any]]:
        provider = _FakeProvider(chunks=["最终", "答案", "。"])
        full = await complete_answer_streaming(provider, _msgs(query), node="aggregator")
        yield {"supervisor": {"subtasks": [{"id": "t1", "type": "rag", "input": query}]}}
        yield {"aggregator": {"messages": [AIMessage(content=full)]}}

    with (
        patch(
            "app.ops.lg_rag.multi.graph.astream_supervisor_agent",
            new=_fake_stream,
        ),
        patch(
            "app.ops.lg_rag.sse_stream.persist_thread_turns",
            new_callable=AsyncMock,
        ),
        patch(
            "app.ops.lg_rag.event_store.persist_run_event",
            new_callable=AsyncMock,
        ) as mock_persist,
    ):
        response = await client.post(_STREAM, json={"query": "复合问", "thread_id": "th-t5-1"})
    assert response.status_code == 200
    events = _parse_sse(response.text)
    assert events[0]["event_type"] == "run.start"
    assert events[-1]["event_type"] == "done"
    # 全程 seq 单调
    seqs = [e["seq"] for e in events]
    assert seqs == list(range(1, len(events) + 1))

    answer_events = [e for e in events if e["event_type"] == "answer"]
    deltas = [e for e in answer_events if "delta" in e["payload"]]
    finals = [e for e in answer_events if e["payload"].get("final") is True]
    assert [e["payload"]["delta"] for e in deltas] == ["最终", "答案", "。"]
    assert len(finals) == 1
    final = finals[0]
    assert final["payload"]["content"] == "最终答案。"
    assert "".join(e["payload"]["delta"] for e in deltas) == final["payload"]["content"]
    assert final["agent_role"] == "aggregator"
    # delta 全部先于终帧；done 之后不再有 answer
    assert max(e["seq"] for e in deltas) < final["seq"] < events[-1]["seq"]
    # 终帧 T2 兼容：content 为整段字符串
    assert isinstance(final["payload"]["content"], str)

    # 落盘：delta 与终帧同入 ops_lg_rag_run_events（persist_run_event 调用）
    persisted = [c.kwargs for c in mock_persist.await_args_list]
    persisted_answers = [p for p in persisted if p["event_type"] == "answer"]
    assert [p["payload"] for p in persisted_answers] == [
        {"delta": "最终"},
        {"delta": "答案"},
        {"delta": "。"},
        {"content": "最终答案。", "final": True},
    ]
    assert [p["seq"] for p in persisted] == sorted(p["seq"] for p in persisted)


async def test_stream_delta_progress_coexist_no_interleave(
    client: AsyncClient, override_auth_maintainer
) -> None:
    """delta 与 node.progress/subtask.progress 并存：帧序与 seq 单调不串台。"""

    async def _fake_stream(
        query: str, *, thread_id: str = "t", checkpointer: Any = None, **_kw: Any
    ) -> AsyncIterator[dict[str, Any]]:
        sink = current_answer_token_sink()
        assert sink is not None  # emit 循环已挂 sink
        yield {"supervisor": {"subtasks": [{"id": "t1", "type": "rag", "input": query}]}}
        await sink("aggregator", "你好")
        yield {"rag_subtask": {"subtask_results": [{"id": "t1", "output": "hit"}]}}
        await sink("aggregator", "世界")
        yield {"aggregator": {"messages": [AIMessage(content="你好世界")]}}

    with (
        patch(
            "app.ops.lg_rag.multi.graph.astream_supervisor_agent",
            new=_fake_stream,
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
        response = await client.post(_STREAM, json={"query": "q", "thread_id": "th-t5-2"})
    assert response.status_code == 200
    events = _parse_sse(response.text)
    seqs = [e["seq"] for e in events]
    assert seqs == sorted(seqs) and len(set(seqs)) == len(seqs)
    types = [e["event_type"] for e in events]
    assert types == [
        "run.start",
        "node.progress",
        "answer",
        "subtask.progress",
        "answer",
        "answer",
        "done",
    ]
    assert events[2]["payload"] == {"delta": "你好"}
    assert events[4]["payload"] == {"delta": "世界"}
    assert events[5]["payload"] == {"content": "你好世界", "final": True}
    # done 后不再有 answer（types 末位即 done）
    assert types[-1] == "done"


async def test_stream_degrades_to_full_answer_when_stream_fails(
    client: AsyncClient, override_auth_maintainer
) -> None:
    """provider 流式不可用 → 降级整段 answer（T2 行为）：无 delta，仅终帧。"""

    async def _fake_stream(
        query: str, *, thread_id: str = "t", checkpointer: Any = None, **_kw: Any
    ) -> AsyncIterator[dict[str, Any]]:
        provider = _FakeProvider(full="整段兜底答", stream_exc=RuntimeError("no stream"))
        full = await complete_answer_streaming(provider, _msgs(query), node="aggregator")
        yield {"aggregator": {"messages": [AIMessage(content=full)]}}

    with (
        patch(
            "app.ops.lg_rag.multi.graph.astream_supervisor_agent",
            new=_fake_stream,
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
        response = await client.post(_STREAM, json={"query": "q", "thread_id": "th-t5-3"})
    assert response.status_code == 200
    events = _parse_sse(response.text)
    answer_events = [e for e in events if e["event_type"] == "answer"]
    assert len(answer_events) == 1
    assert answer_events[0]["payload"] == {"content": "整段兜底答", "final": True}
    assert events[-1]["event_type"] == "done"


async def test_stream_router_direct_answer_same_protocol(
    client: AsyncClient, override_auth_maintainer
) -> None:
    """router direct_answer：同 provider 流式可得 → 与 aggregator 同协议。"""

    async def _fake_router(
        query: str, *, thread_id: str = "t", checkpointer: Any = None, **_kw: Any
    ) -> AsyncIterator[dict[str, Any]]:
        provider = _FakeProvider(chunks=["你", "好"])
        full = await complete_answer_streaming(provider, _msgs(query), node="direct_answer")
        yield {"router": {"route": "direct"}}
        yield {"direct_answer": {"messages": [AIMessage(content=full)]}}

    with (
        patch(
            "app.ops.lg_rag.graph.astream_router_agent",
            new=_fake_router,
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
            _STREAM, json={"query": "闲聊", "mode": "router", "thread_id": "th-t5-4"}
        )
    assert response.status_code == 200
    events = _parse_sse(response.text)
    answer_events = [e for e in events if e["event_type"] == "answer"]
    deltas = [e["payload"]["delta"] for e in answer_events if "delta" in e["payload"]]
    finals = [e for e in answer_events if e["payload"].get("final") is True]
    assert deltas == ["你", "好"]
    assert len(finals) == 1
    assert finals[0]["payload"]["content"] == "你好"
    assert finals[0]["agent_role"] == "direct_answer"
    # 有真终帧 → 不再补占位空 answer
    assert all(e["payload"].get("note") != "no_aggregator" for e in answer_events)
    assert events[-1]["event_type"] == "done"


async def test_stream_basic_placeholder_unchanged(
    client: AsyncClient, override_auth_maintainer
) -> None:
    """basic 无独立终答 LLM → 占位空 answer 帧行为不变（无 final 标记）。"""

    async def _fake_basic(
        query: str, *, thread_id: str = "t", checkpointer: Any = None, **_kw: Any
    ) -> AsyncIterator[dict[str, Any]]:
        yield {"rag": {"messages": [AIMessage(content="检索答")]}}

    with (
        patch(
            "app.ops.lg_rag.graph.astream_basic_agent",
            new=_fake_basic,
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
            _STREAM, json={"query": "q", "mode": "basic", "thread_id": "th-t5-5"}
        )
    assert response.status_code == 200
    events = _parse_sse(response.text)
    answer_events = [e for e in events if e["event_type"] == "answer"]
    assert len(answer_events) == 1
    assert answer_events[0]["payload"] == {"content": "", "note": "no_aggregator"}
    assert "final" not in answer_events[0]["payload"]


async def test_map_node_update_final_frames() -> None:
    """终帧外形：aggregator / direct_answer → answer {content, final:true}。"""
    from app.ops.lg_rag.sse_stream import map_node_update

    et, role, payload = map_node_update("aggregator", {"messages": [AIMessage(content="答")]})
    assert (et, role) == ("answer", "aggregator")
    assert payload == {"content": "答", "final": True}

    et, role, payload = map_node_update("direct_answer", {"messages": [AIMessage(content="直答")]})
    assert (et, role) == ("answer", "direct_answer")
    assert payload == {"content": "直答", "final": True}

    # 非终答节点不变
    et, role, _payload = map_node_update("supervisor", {"subtasks": []})
    assert et == "node.progress"
    assert role == "supervisor"


# ---------------------------------------------------------------------------
# replay / 鉴权
# ---------------------------------------------------------------------------


async def test_replay_includes_delta_frames(client: AsyncClient, override_auth_maintainer) -> None:
    """replay 逐帧重放含 delta 帧，形状与 live 一致。"""
    stored = [
        format_sse_event(
            {
                "run_id": "run-t5",
                "seq": 2,
                "ts_ms": 20,
                "agent_role": "aggregator",
                "event_type": "answer",
                "payload": {"delta": "你"},
            }
        ),
        format_sse_event(
            {
                "run_id": "run-t5",
                "seq": 3,
                "ts_ms": 30,
                "agent_role": "aggregator",
                "event_type": "answer",
                "payload": {"delta": "好"},
            }
        ),
        format_sse_event(
            {
                "run_id": "run-t5",
                "seq": 4,
                "ts_ms": 40,
                "agent_role": "aggregator",
                "event_type": "answer",
                "payload": {"content": "你好", "final": True},
            }
        ),
        format_sse_event(
            {
                "run_id": "run-t5",
                "seq": 5,
                "ts_ms": 50,
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
    ):
        response = await client.post(_REPLAY, json={"run_id": "run-t5", "after_seq": 1})
    assert response.status_code == 200
    events = _parse_sse(response.text)
    assert [e["seq"] for e in events] == [2, 3, 4, 5]
    assert [e["payload"] for e in events[:3]] == [
        {"delta": "你"},
        {"delta": "好"},
        {"content": "你好", "final": True},
    ]
    for ev in events:
        assert ev["cursor"] == f"{ev['run_id']}:{ev['seq']}"


async def test_stream_requires_auth_unchanged(client: AsyncClient) -> None:
    """未登录 401 不变。"""
    response = await client.post(_STREAM, json={"query": "你好"})
    assert response.status_code == 401


async def test_replay_unknown_run_404_unchanged(
    client: AsyncClient, override_auth_maintainer
) -> None:
    """未知/跨用户 run_id 404 不变。"""
    from app.ops.lg_rag.event_store import LgRagRunNotFoundError

    with patch(
        "app.ops.lg_rag.router.load_events_after",
        new_callable=AsyncMock,
        side_effect=LgRagRunNotFoundError,
    ):
        response = await client.post(_REPLAY, json={"run_id": "missing", "after_seq": 0})
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# T5.1：persist 不阻塞 delta yield
# ---------------------------------------------------------------------------


async def test_delta_yields_before_persist_completes() -> None:
    """T5.1：persist 被卡住时，delta 仍须先入 SSE（节点 updates 前可见）。

    若 emit 仍 await persist 再 put_nowait，本测会在 wait_for 超时失败。
    """
    import asyncio

    from app.ops.lg_rag.sse_stream import iter_lg_rag_sse

    persist_release = asyncio.Event()
    delta_seen = asyncio.Event()
    persist_calls = 0

    async def _blocked_persist(**_kw: Any) -> None:
        nonlocal persist_calls
        persist_calls += 1
        await persist_release.wait()

    async def _fake_stream(
        query: str, *, thread_id: str = "t", checkpointer: Any = None, **_kw: Any
    ) -> AsyncIterator[dict[str, Any]]:
        sink = current_answer_token_sink()
        assert sink is not None
        await sink("aggregator", "先到")
        # 消费者须在节点 updates 前见到 delta
        await asyncio.wait_for(delta_seen.wait(), timeout=2.0)
        persist_release.set()  # 放行后台 persist，避免 done 前 _drain_persist 死锁
        yield {"aggregator": {"messages": [AIMessage(content="先到")]}}

    with (
        patch(
            "app.ops.lg_rag.event_store.persist_run_event",
            new=_blocked_persist,
        ),
        patch(
            "app.ops.lg_rag.sse_stream.persist_thread_turns",
            new_callable=AsyncMock,
        ),
    ):
        agen = iter_lg_rag_sse(
            query="q",
            mode="supervisor",
            thread_id="th-t51",
            run_id="run-t51",
            astream_fn=_fake_stream,
            user_id="user-t51",
        )
        saw_delta = False
        async for raw in agen:
            for block in raw.split("\n\n"):
                block = block.strip()
                if not block:
                    continue
                data_line = None
                for line in block.split("\n"):
                    if line.startswith("data: "):
                        data_line = line[len("data: ") :]
                if not data_line:
                    continue
                ev = json.loads(data_line)
                if ev.get("event_type") == "answer" and "delta" in ev.get("payload", {}):
                    assert ev["payload"]["delta"] == "先到"
                    saw_delta = True
                    delta_seen.set()
        assert saw_delta

    assert persist_calls >= 1


async def test_slow_chunks_visible_before_aggregator_update() -> None:
    """T5.1：慢 chunk 下多枚 delta 均在终帧 final 之前出现在消费者时间线。"""
    import asyncio

    from app.ops.lg_rag.sse_stream import iter_lg_rag_sse

    consumer: list[str] = []

    async def _fake_stream(
        query: str, *, thread_id: str = "t", checkpointer: Any = None, **_kw: Any
    ) -> AsyncIterator[dict[str, Any]]:
        sink = current_answer_token_sink()
        assert sink is not None
        await sink("aggregator", "一")
        await asyncio.sleep(0.02)
        await sink("aggregator", "二")
        yield {"aggregator": {"messages": [AIMessage(content="一二")]}}

    with (
        patch(
            "app.ops.lg_rag.event_store.persist_run_event",
            new_callable=AsyncMock,
        ),
        patch(
            "app.ops.lg_rag.sse_stream.persist_thread_turns",
            new_callable=AsyncMock,
        ),
    ):
        agen = iter_lg_rag_sse(
            query="q",
            mode="supervisor",
            thread_id="th-t51b",
            astream_fn=_fake_stream,
            user_id="user-t51b",
        )
        async for raw in agen:
            for block in raw.split("\n\n"):
                block = block.strip()
                if not block:
                    continue
                data_line = None
                for line in block.split("\n"):
                    if line.startswith("data: "):
                        data_line = line[len("data: ") :]
                if not data_line:
                    continue
                ev = json.loads(data_line)
                if ev.get("event_type") == "answer" and "delta" in ev.get("payload", {}):
                    consumer.append(f"delta:{ev['payload']['delta']}")
                if ev.get("event_type") == "answer" and ev.get("payload", {}).get("final"):
                    consumer.append("final")

    assert consumer == ["delta:一", "delta:二", "final"]
