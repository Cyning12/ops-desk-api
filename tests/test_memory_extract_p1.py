"""memory-facts-p1 · LLM 离线候选抽取红线 + 双开关全关=P0 逐字节（不连真外网）。

红线（SPEC §5 D3 / task V3）：
② 抽取噪声拒写：5 候选 3 应拒 → 拒的查表为零、过的落库（带 source_run_id）
③ LLM 失败 / 非法 JSON → 零写入（表行数不变；非法 JSON 重试 ≤1 = 共 2 次尝试）
④ 热路径零抽取：EXTRACT=true 时装配路径不触发抽取；schedule 点火即返回，
   抽取只在后台钩子里发生
⑥ 两开关全关：装配输出与 P0 逐字节一致；向量开关关 = P0 确定性召回路径
另：invoke / SSE 两入口 run 完成后均有点火钩子；SSE 零新事件类型。

fake provider：进程内桩（BaseProvider.complete 返回罐头 JSON），不连外网。
"""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import AsyncIterator, Iterable
from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage

from app.llm.schema import BaseProvider, LlmChunk, LlmMessage, LlmProviderError
from app.ops.lg_rag.continuity import (
    assemble_graph_messages,
    assemble_graph_messages_with_memory,
    render_memory_facts_block,
)
from app.ops.memory import extract as extract_mod
from app.ops.memory.extract import (
    drain_memory_extraction,
    memory_facts_extract_enabled,
    run_memory_extraction,
    schedule_memory_extraction,
)
from tests.conftest import DB_AVAILABLE

_TENANT = "mfx1-test-tenant"


class FakeProvider(BaseProvider):
    """罐头输出 / 可抛错；记录 complete 调用次数。"""

    def __init__(self, payload: str | None = None, *, error: Exception | None = None):
        self.payload = payload or '{"facts": []}'
        self.error = error
        self.calls = 0

    async def complete(self, messages: Iterable[LlmMessage], model: str | None = None) -> str:
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.payload

    async def complete_stream(
        self, messages: Iterable[LlmMessage], model: str | None = None
    ) -> AsyncIterator[LlmChunk]:
        raise NotImplementedError


def _shape(messages: list[BaseMessage]) -> list[tuple[str, str]]:
    return [(type(m).__name__, str(m.content)) for m in messages]


# ---------------- env 纪律：默认关 / 非法回退 + warning ----------------


def test_extract_env_default_and_invalid_fallback(monkeypatch: pytest.MonkeyPatch, caplog):
    monkeypatch.delenv("MEMORY_FACTS_EXTRACT_ENABLED", raising=False)
    assert memory_facts_extract_enabled() is False
    monkeypatch.setenv("MEMORY_FACTS_EXTRACT_ENABLED", "enable plz")
    with caplog.at_level(logging.WARNING, logger="app.ops.memory.extract"):
        assert memory_facts_extract_enabled() is False
    assert "MEMORY_FACTS_EXTRACT_ENABLED" in caplog.text
    monkeypatch.setenv("MEMORY_FACTS_EXTRACT_ENABLED", "true")
    assert memory_facts_extract_enabled() is True


async def test_extract_disabled_is_noop_without_llm(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("MEMORY_FACTS_EXTRACT_ENABLED", raising=False)
    provider = FakeProvider()
    assert await run_memory_extraction(
        tenant_id=_TENANT,
        user_id="u-1",
        run_id="r-1",
        query="q",
        answer="a",
        _provider=provider,
    ) == (0, 0)
    assert provider.calls == 0  # 开关关 = 零 LLM 调用


# ---------------- ④ 热路径零抽取 ----------------


async def test_assemble_path_triggers_no_extraction(monkeypatch: pytest.MonkeyPatch):
    """EXTRACT=true 时，装配/请求函数内零抽取调用、零后台任务（等价 span 断言）。"""
    monkeypatch.setenv("MEMORY_FACTS_EXTRACT_ENABLED", "true")
    spy = AsyncMock(side_effect=AssertionError("hot path must not extract"))
    monkeypatch.setattr(extract_mod, "run_memory_extraction", spy)
    extract_mod._extract_tasks.clear()

    history = [{"role": "user", "content": f"q{i}"} for i in range(10)]
    out = await assemble_graph_messages_with_memory("本轮问", history, tenant_id="t", user_id="u")
    assert _shape(out) == _shape(assemble_graph_messages("本轮问", history))
    assert spy.await_count == 0
    assert not extract_mod._extract_tasks  # 装配路径不点火


async def test_schedule_defers_extraction_to_background(monkeypatch: pytest.MonkeyPatch):
    """点火即返回（调用栈内零 LLM）；抽取只发生在后台 task。"""
    monkeypatch.setenv("MEMORY_FACTS_EXTRACT_ENABLED", "true")
    provider = FakeProvider('{"facts": []}')
    monkeypatch.setattr(
        "app.ops.structured_output.complete.get_llm_provider", lambda *a, **k: provider
    )
    task = schedule_memory_extraction(
        tenant_id=_TENANT, user_id="u-1", run_id="r-bg", source_turn=1, query="q", answer="a"
    )
    assert task is not None
    assert provider.calls == 0  # 热路径零抽取调用
    await drain_memory_extraction()
    assert provider.calls == 1  # 每 run 至多 1 次抽取调用，且只在后台钩子


async def test_schedule_skips_without_identity(monkeypatch: pytest.MonkeyPatch, caplog):
    monkeypatch.setenv("MEMORY_FACTS_EXTRACT_ENABLED", "true")
    with caplog.at_level(logging.WARNING, logger="app.ops.memory.extract"):
        assert (
            schedule_memory_extraction(
                tenant_id="", user_id="u-1", run_id="r", query="q", answer="a"
            )
            is None
        )
    assert "skip extraction" in caplog.text


# ---------------- ⑥ 两开关全关 = P0 逐字节 ----------------


@pytest.mark.parametrize(
    "vec,ext",
    [("false", "false"), ("0", "off"), ("garbage", "enable plz")],
)
async def test_both_switches_off_byte_identical(
    monkeypatch: pytest.MonkeyPatch, vec: str, ext: str
):
    """两开关全关（含非法值回退）：装配输出与 P0 现网逐字节一致（复用 P0 回归结构）。"""
    monkeypatch.setenv("MEMORY_FACTS_ENABLED", "false")
    monkeypatch.setenv("MEMORY_FACTS_VECTOR_RECALL_ENABLED", vec)
    monkeypatch.setenv("MEMORY_FACTS_EXTRACT_ENABLED", ext)
    history = [{"role": "user", "content": f"q{i}"} for i in range(10)]
    baseline = assemble_graph_messages("本轮问", history)
    out = await assemble_graph_messages_with_memory(
        "本轮问", history, tenant_id="ops-desk-pilot", user_id="u-1"
    )
    assert _shape(out) == _shape(baseline)


async def test_vector_switch_off_uses_p0_deterministic_path(
    monkeypatch: pytest.MonkeyPatch,
):
    """MEMORY_FACTS_ENABLED=true 且向量开关关：召回 = P0 确定性路径，向量通路零触达。"""
    monkeypatch.setenv("MEMORY_FACTS_ENABLED", "true")
    monkeypatch.delenv("MEMORY_FACTS_VECTOR_RECALL_ENABLED", raising=False)
    facts = [{"key": "project.primary_repo", "value": "cyning/ops-desk"}]
    det = AsyncMock(return_value=facts)
    vec = AsyncMock(side_effect=AssertionError("vector path must stay untouched"))
    monkeypatch.setattr("app.ops.memory.service.recall_active", det)
    monkeypatch.setattr("app.ops.memory.service.recall_with_vector", vec)

    def _no_embedder():
        raise AssertionError("embedder must not be resolved when vector recall off")

    monkeypatch.setattr("app.ops.rag.embedder.get_query_embedder", _no_embedder)
    out = await assemble_graph_messages_with_memory(
        "q", [], tenant_id="ops-desk-pilot", user_id="u-1"
    )
    assert det.await_count == 1
    assert vec.await_count == 0
    blocks = [str(m.content) for m in out if isinstance(m, SystemMessage)]
    assert render_memory_facts_block(facts) in blocks  # P0 注入块语义逐字节


# ---------------- 入口接线：invoke / SSE run 完成后点火 ----------------


async def test_invoke_schedules_extraction_after_run(
    monkeypatch: pytest.MonkeyPatch, client, override_auth_viewer
):
    monkeypatch.setenv("MEMORY_FACTS_EXTRACT_ENABLED", "true")
    from app.ops.lg_rag import router as lg_router

    monkeypatch.setattr(
        lg_router,
        "_dispatch",
        AsyncMock(return_value={"messages": [AIMessage(content="最终答案")]}),
    )
    monkeypatch.setattr(lg_router, "_prepare_thread", AsyncMock(return_value=[]))
    monkeypatch.setattr(lg_router, "persist_thread_turns", AsyncMock())
    sched = MagicMock(return_value=None)
    monkeypatch.setattr(lg_router, "schedule_memory_extraction", sched)

    resp = await client.post("/api/ops/lg-rag/invoke", json={"query": "hello"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["ok"] is True
    assert sched.call_count == 1
    kwargs = sched.call_args.kwargs
    assert kwargs["query"] == "hello"
    assert kwargs["answer"] == "最终答案"
    assert kwargs["run_id"]  # 溯源 run_id 必带
    assert kwargs["user_id"] == "00000000-0000-0000-0000-000000000002"


async def test_sse_schedules_extraction_after_done(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MEMORY_FACTS_EXTRACT_ENABLED", "true")
    from app.ops.lg_rag import sse_stream
    from app.ops.tenant_context import reset_current_tenant, set_current_tenant

    async def fake_astream(query, *, thread_id, history_turns, **kw):
        yield {"aggregator": {"messages": [AIMessage(content="最终答案")]}}

    monkeypatch.setattr("app.ops.lg_rag.event_store.persist_run_event", AsyncMock())
    monkeypatch.setattr(sse_stream, "persist_thread_turns", AsyncMock())
    sched = MagicMock(return_value=None)
    monkeypatch.setattr(sse_stream, "schedule_memory_extraction", sched)

    token = set_current_tenant("mf-tenant-x")
    try:
        frames = [
            f
            async for f in sse_stream._iter_lg_rag_sse_core(
                query="q",
                mode="basic",
                thread_id="t-1",
                run_id="r-1",
                astream_fn=fake_astream,
                history_turns=[],
                user_id="u-1",
            )
        ]
    finally:
        reset_current_tenant(token)
    assert sched.call_count == 1
    kwargs = sched.call_args.kwargs
    assert kwargs["run_id"] == "r-1"
    assert kwargs["user_id"] == "u-1"
    assert kwargs["answer"] == "最终答案"
    assert kwargs["tenant_id"] == "mf-tenant-x"
    # SSE 零改事件类型：帧集合 ⊆ P0 既有事件类型
    event_types = {
        line.removeprefix("event: ")
        for f in frames
        for line in f.splitlines()
        if line.startswith("event: ")
    }
    assert event_types <= {
        "run.start",
        "answer",
        "done",
        "error",
        "hitl.waiting",
        "subtask.progress",
    }


# ---------------- ②③ 抽取过闸与失败语义（真 PG） ----------------


_DB_SKIP = pytest.mark.skipif(
    not DB_AVAILABLE, reason="需要 PostgreSQL（conftest 会准备 opsdesk_test）"
)


@pytest.fixture
async def _clean_db():
    from sqlalchemy import text

    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session, session.begin():
        await session.execute(
            text("DELETE FROM ops_memory_facts WHERE tenant_id LIKE 'mfx1-test-%'")
        )
    yield
    async with AsyncSessionLocal() as session, session.begin():
        await session.execute(
            text("DELETE FROM ops_memory_facts WHERE tenant_id LIKE 'mfx1-test-%'")
        )


async def _rows(tenant_id: str = _TENANT) -> list:
    from sqlalchemy import text

    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        rows = await session.execute(
            text(
                "SELECT key, value, source_run_id, source_turn "
                "FROM ops_memory_facts WHERE tenant_id = :t"
            ),
            {"t": tenant_id},
        )
        return list(rows.all())


@_DB_SKIP
async def test_extract_noise_candidates_rejected_table_zero(
    monkeypatch: pytest.MonkeyPatch, _clean_db, caplog
):
    """5 候选 3 应拒（易失前缀/非法 key/空值）→ 拒的查表为零、过闸 2 条落库带溯源。"""
    monkeypatch.setenv("MEMORY_FACTS_EXTRACT_ENABLED", "true")
    payload = json.dumps(
        {
            "facts": [
                {"key": "project.primary_repo", "value": "cyning/ops-desk"},
                {"key": "user.display_tz", "value": "Asia/Shanghai"},
                {"key": "tmp.note", "value": "一次性"},
                {"key": "Bad Key", "value": "非法"},
                {"key": "project.empty", "value": "  "},
            ]
        },
        ensure_ascii=False,
    )
    provider = FakeProvider(payload)
    run_id = "run-ext-" + uuid.uuid4().hex[:8]
    user = "u-ext"
    with caplog.at_level(logging.INFO, logger="app.ops.memory.extract"):
        candidates, written = await run_memory_extraction(
            tenant_id=_TENANT,
            user_id=user,
            run_id=run_id,
            source_turn=3,
            query="我主要在 ops-desk-api 仓干活，时区 Asia/Shanghai",
            answer="好的，已了解",
            _provider=provider,
        )
    assert (candidates, written) == (5, 2)
    assert provider.calls == 1  # 每 run 至多 1 次抽取调用
    assert "memory_extract_candidates=5 written=2" in caplog.text  # span/log 计数

    rows = await _rows()
    by_key = {r.key: r for r in rows}
    assert set(by_key) == {"project.primary_repo", "user.display_tz"}
    # 拒的查表为零（不是"存了不召回"）
    assert "tmp.note" not in by_key and "Bad Key" not in by_key
    assert "project.empty" not in by_key
    # 抽取写入必带 source_run_id + source_turn（revoke_by_source 可一键全撤）
    for row in rows:
        assert row.source_run_id == run_id
        assert row.source_turn == 3


@_DB_SKIP
async def test_extract_invalid_json_zero_writes(monkeypatch: pytest.MonkeyPatch, _clean_db, caplog):
    """非法 JSON → 零写入；管道内重试 ≤1（总尝试 = 2）后放弃。"""
    monkeypatch.setenv("MEMORY_FACTS_EXTRACT_ENABLED", "true")
    provider = FakeProvider("这不是 JSON {{{")
    before = len(await _rows())
    with caplog.at_level(logging.WARNING, logger="app.ops.memory.extract"):
        candidates, written = await run_memory_extraction(
            tenant_id=_TENANT,
            user_id="u-bad",
            run_id="run-bad-" + uuid.uuid4().hex[:6],
            query="q",
            answer="a",
            _provider=provider,
        )
    assert (candidates, written) == (0, 0)
    assert provider.calls == 2  # 首次 + correction 重试 1 次
    assert len(await _rows()) == before  # 表行数不变
    assert "zero writes" in caplog.text


@_DB_SKIP
async def test_extract_provider_error_zero_writes(monkeypatch: pytest.MonkeyPatch, _clean_db):
    """LLM 抛错 → 零写入（不重试风暴：异常路径 0 重试）。"""
    monkeypatch.setenv("MEMORY_FACTS_EXTRACT_ENABLED", "true")
    provider = FakeProvider(error=LlmProviderError("llm down", retryable=True))
    before = len(await _rows())
    candidates, written = await run_memory_extraction(
        tenant_id=_TENANT,
        user_id="u-err",
        run_id="run-err-" + uuid.uuid4().hex[:6],
        query="q",
        answer="a",
        _provider=provider,
    )
    assert (candidates, written) == (0, 0)
    assert provider.calls == 1
    assert len(await _rows()) == before


# ---------------- memory-preference-profile · 显式-only 落点（物理拒收推断型） ----------------


def test_extraction_schema_has_no_kind_field():
    """schema 无 kind 字段：结构化输出层面**物理产不出** preference。"""
    from app.ops.memory.extract import ExtractedFactItem, MemoryFactExtraction

    assert set(ExtractedFactItem.model_fields) == {"key", "value"}
    assert set(MemoryFactExtraction.model_fields) == {"facts"}


async def test_extract_constructed_candidates_are_fact_kind(
    monkeypatch: pytest.MonkeyPatch,
):
    """构造点钉死：抽取候选 FactCandidate.kind 恒为 fact（变异检验 ③ 落点）。"""
    monkeypatch.setenv("MEMORY_FACTS_EXTRACT_ENABLED", "true")
    payload = json.dumps(
        {"facts": [{"key": "project.primary_repo", "value": "cyning/ops-desk"}]},
        ensure_ascii=False,
    )
    provider = FakeProvider(payload)
    recorded = []

    async def fake_write(candidate, **kwargs):  # 截获构造点产物，不落库
        recorded.append(candidate)
        return MagicMock()

    monkeypatch.setattr(extract_mod, "write_fact", fake_write)
    candidates, written = await run_memory_extraction(
        tenant_id=_TENANT,
        user_id="u-kind",
        run_id="run-kind-" + uuid.uuid4().hex[:6],
        query="我主要在 ops-desk-api 仓干活",
        answer="好的",
        _provider=provider,
    )
    assert (candidates, written) == (1, 1)
    assert len(recorded) == 1
    assert recorded[0].kind == "fact"  # 构造点未传 kind → 默认 fact
