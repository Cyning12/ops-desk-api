"""Integration tests for the chat WebSocket endpoint.

WebSocket tests use starlette's synchronous TestClient, driven from async
tests via ``asyncio.to_thread``. The app runs in the TestClient's own event
loop; the ``_reset_engine`` fixture in conftest disposes pooled connections
between tests.
"""

from __future__ import annotations

import asyncio
import json

import pytest
from sqlalchemy import select

from app.db.models import OpsRun
from app.db.session import AsyncSessionLocal, engine
from app.llm.providers.base import BaseProviderImpl
from app.llm.schema import LlmChunk
from app.ops.rag.retrieve import RetrievedChunk
from tests.conftest import DB_AVAILABLE


class FakeProvider(BaseProviderImpl):
    def __init__(self, chunks: list[LlmChunk]) -> None:
        self._chunks = chunks

    async def complete_stream(self, messages, model=None):
        for chunk in self._chunks:
            yield chunk


class SlowProvider(BaseProviderImpl):
    """Yields many chunks slowly so a cancel can land mid-run."""

    def __init__(self, chunks: int = 50, delay: float = 0.05) -> None:
        self._chunks = chunks
        self._delay = delay

    async def complete_stream(self, messages, model=None):
        for i in range(self._chunks):
            await asyncio.sleep(self._delay)
            yield LlmChunk(content=f"chunk-{i} ")


@pytest.fixture
def fake_provider(monkeypatch):
    def _make(chunks: list[LlmChunk]):
        monkeypatch.setattr(
            "app.ops.chat.nodes.get_llm_provider",
            lambda: FakeProvider(chunks),
        )

    return _make


@pytest.fixture
def slow_provider(monkeypatch):
    monkeypatch.setattr(
        "app.ops.chat.nodes.get_llm_provider",
        lambda: SlowProvider(),
    )


class _StubEmbedder:
    """确定性查询向量（检索链打桩 · test-baseline-reds D1）：不触外网/本机模型。"""

    name = "stub-embedder"

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * 1024 for _ in texts]


class _StubGraderProvider:
    """grader 打桩：恒评 exact（chunk_id 与 _STUB_CHUNK 对齐）→ 闸放行 answer。"""

    async def complete(self, messages, model=None) -> str:
        return json.dumps([{"chunk_id": 1, "relevance": "exact", "reason": "stub: 打桩恒放行"}])


_STUB_CHUNK = RetrievedChunk(
    id=1,
    repo="acme/ops-desk",
    source_type="doc",
    source_id="docs/demo.md",
    chunk_index=0,
    content="Title: Demo\n打桩语料：与 query 直接相关的证据块。",
    metadata={},
    images=[],
)


@pytest.fixture
def stub_rag_chain(monkeypatch):
    """检索链外部依赖打桩确定化（test-baseline-reds D1 · 钉死契约：最小面）。

    现行拓扑 general/overview → retrieve→grade→gate（R-3），三处外部依赖
    全部换确定性桩，事件序列与外部世界无关：
    - ``_get_embedder``：不打 SiliconFlow /embeddings（httpx 外网 + 宿主代理 env）
    - ``hybrid_recall``：不查 ops_knowledge_chunks（测试库语料为空也无妨）
    - grader 侧 ``get_llm_provider``：不调评级 LLM（恒 exact → gate=answer）
    - ``rerank_enabled`` 恒 False：宿主 .env 可能开 RAG_RERANK_ENABLED=true，
      开了会走 SiliconFlow /rerank 真 HTTP，低分被地板滤空 → refuse（实测踩到）
    answer 节点 provider 在 nodes 命名空间，由 fake_provider/slow_provider 各自打。
    """

    async def _fake_recall(session, query, qvec, *, k_each=10, top_n=5, query_sparse=None):
        return [_STUB_CHUNK]

    monkeypatch.setattr("app.ops.chat.rag_nodes._get_embedder", lambda: _StubEmbedder())
    monkeypatch.setattr("app.ops.chat.rag_nodes.hybrid_recall", _fake_recall)
    monkeypatch.setattr(
        "app.ops.chat.rag_nodes.get_llm_provider", lambda *a, **k: _StubGraderProvider()
    )
    monkeypatch.setattr("app.ops.chat.rag_nodes.rerank_enabled", lambda: False)


@pytest.fixture
async def _portal_engine(seeded_maintainer):
    """Drop pytest-loop connections so the TestClient portal loop gets fresh ones.

    ``seeded_maintainer`` runs on the pytest-asyncio loop and leaves pooled
    asyncpg connections bound to that loop; the WS app runs on the
    TestClient's portal loop and cannot reuse them. Disposing before and
    after the test keeps each loop on its own connections.
    """
    await engine.dispose()
    yield
    await engine.dispose()


def _ws_collect(payloads: list[dict | str], stop_on: tuple[str, ...]) -> list[dict]:
    """Connect, send payloads in order, collect events until a stop type."""
    from starlette.testclient import TestClient

    from app.main import app

    events: list[dict] = []
    with TestClient(app) as tc, tc.websocket_connect("/api/ops/chat/ws") as ws:
        for payload in payloads:
            ws.send_text(payload if isinstance(payload, str) else json.dumps(payload))
            # After sending a cancel, keep reading; for other payloads we
            # read in the loop below.
        while True:
            event = ws.receive_json()
            events.append(event)
            if event["event_type"] in stop_on:
                break
    return events


def _ws_message_then_cancel(message: str) -> list[dict]:
    """Send a message, cancel while the answer node is still generating."""
    from starlette.testclient import TestClient

    from app.main import app

    events: list[dict] = []
    with TestClient(app) as tc, tc.websocket_connect("/api/ops/chat/ws") as ws:
        ws.send_text(json.dumps({"type": "message", "message": message}))
        run_id = None
        while True:
            event = ws.receive_json()
            events.append(event)
            if event["event_type"] == "run.start":
                run_id = event["run_id"]
                # The SlowProvider answer node takes ~2.5s to surface its
                # buffered events; cancelling now lands mid-generation.
                ws.send_text(json.dumps({"type": "cancel", "run_id": run_id}))
                break
        while True:
            event = ws.receive_json()
            events.append(event)
            if event["event_type"] in ("run.cancelled", "done", "error"):
                break
    return events


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_ws_disabled_when_switch_off(monkeypatch, _portal_engine) -> None:
    """OPS_CHAT_WS_ENABLED=false: handshake is refused with close code 1008."""
    monkeypatch.setattr("app.ops.chat.ws.settings.ops_chat_ws_enabled", False)

    def _scenario() -> int | None:
        from starlette.testclient import TestClient
        from starlette.websockets import WebSocketDisconnect

        from app.main import app

        with TestClient(app) as tc:
            try:
                with tc.websocket_connect("/api/ops/chat/ws"):
                    pass
            except WebSocketDisconnect as exc:
                return exc.code
        return None

    code = await asyncio.to_thread(_scenario)
    assert code == 1008


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_ws_message_streams_events(fake_provider, stub_rag_chain, _portal_engine) -> None:
    """A message produces the same event sequence as the SSE stream.

    断言对齐**现行图拓扑**（test-baseline-reds D1）：general 意图走 R-3 检索链
    retrieve→grade→gate，必多两个 tool_result；检索链由 stub_rag_chain 打桩确定化。
    若断言改回 2026-07-18 旧期望（无 tool_result）应对现行拓扑真挂。
    """
    fake_provider([LlmChunk(content="Hello"), LlmChunk(content="!")])

    events = await asyncio.to_thread(
        _ws_collect,
        [{"type": "message", "message": "hi"}],
        ("done", "error"),
    )

    event_types = [e["event_type"] for e in events]
    assert event_types == [
        "run.start",
        "thinking",  # intent
        "tool_result",  # retrieve（stubbed hybrid_recall 命中 1 块）
        "tool_result",  # grade（stubbed grader 恒 exact → gate=answer）
        "thinking",  # answer 准备
        "answer",
        "answer",
        "done",
    ]
    answer_event = next(e for e in events if e["event_type"] == "answer")
    assert answer_event["agent_role"] == "answer"
    assert answer_event["payload"]["content"] == "Hello"
    assert events[-1]["payload"]["model"]


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_ws_invalid_json_returns_error(_portal_engine) -> None:
    """Malformed JSON yields a ws.protocol error and keeps the connection open."""
    events = await asyncio.to_thread(
        _ws_collect,
        ["not json at all"],
        ("error",),
    )
    assert events[0]["event_type"] == "error"
    assert events[0]["payload"]["stage"] == "ws.protocol"


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_ws_cancel_without_active_run(_portal_engine) -> None:
    """Cancelling with no active run returns a ws.cancel error."""
    events = await asyncio.to_thread(
        _ws_collect,
        [{"type": "cancel", "run_id": "00000000-0000-0000-0000-000000000099"}],
        ("error",),
    )
    assert events[0]["event_type"] == "error"
    assert events[0]["payload"]["stage"] == "ws.cancel"


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_ws_cancel_active_run(slow_provider, stub_rag_chain, _portal_engine) -> None:
    """Cancelling mid-generation emits run.cancelled and marks the run cancelled.

    stub_rag_chain：cancel 竞态断言只关心 answer 节点慢生成；检索链打桩快速通过，
    不触外网/语料表（test-baseline-reds D1）。
    """
    events = await asyncio.to_thread(_ws_message_then_cancel, "tell me a story")

    event_types = [e["event_type"] for e in events]
    assert event_types[0] == "run.start"
    assert event_types[-1] == "run.cancelled"
    # Cancel interrupted the answer node before its buffered events surfaced.
    assert "answer" not in event_types
    assert "done" not in event_types

    run_id = events[0]["run_id"]
    await engine.dispose()
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(OpsRun).where(OpsRun.id == run_id))
        run = result.scalar_one_or_none()
    assert run is not None
    assert run.status == "cancelled"


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_ws_second_message_while_active_rejected(
    slow_provider, stub_rag_chain, _portal_engine
) -> None:
    """A second message during an active run returns an error, not a new run.

    stub_rag_chain：首个 run 须稳定停在 answer 慢生成段，并发拒语义才确定
    （检索链打桩 · test-baseline-reds D1）。
    """
    from starlette.testclient import TestClient

    from app.main import app

    def _scenario() -> list[dict]:
        events: list[dict] = []
        with TestClient(app) as tc, tc.websocket_connect("/api/ops/chat/ws") as ws:
            ws.send_text(json.dumps({"type": "message", "message": "first"}))
            # Wait only for run.start: the SlowProvider answer node is still
            # generating (~2.5s), so the run is definitely active.
            while True:
                event = ws.receive_json()
                events.append(event)
                if event["event_type"] == "run.start":
                    break
            ws.send_text(json.dumps({"type": "message", "message": "second"}))
            while True:
                event = ws.receive_json()
                events.append(event)
                if event["event_type"] == "error":
                    break
            ws.send_text(json.dumps({"type": "cancel", "run_id": events[0]["run_id"]}))
            while True:
                event = ws.receive_json()
                events.append(event)
                if event["event_type"] in ("run.cancelled", "done", "error"):
                    break
        return events

    events = await asyncio.to_thread(_scenario)
    reject = next(e for e in events if e["event_type"] == "error")
    assert reject["payload"]["message"] == "run already active"
    assert events[-1]["event_type"] == "run.cancelled"
