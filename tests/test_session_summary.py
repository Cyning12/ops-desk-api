"""session-summary-fallback 守护测试：D1 生成通路 · D2 缓存 · D3 双对拍（上线前提）。

双对拍钉死（SPEC §6-D3 · 两条都过才允许合入）：
- **off 对拍**：SESSION_SUMMARY_ENABLED 未设 / false / 非法值 → 装配输出与
  占位模式**逐字节一致**（非法值 + warning · continuity 三件套先例）；
- **on 态全失败对拍**：强制 LLM 全失败 → 输出与 off 态**逐字节一致** +
  span session_summary_degraded=N（缺标记不算过——「静默降级」与
  「根本没走摘要面」必须可区分 · 变异检验③ oracle）。

缓存面：key 铁律（内容哈希+prompt_version+model）· 生成成功才写 ·
命中零 LLM 调用 · 读写失败不挡主答 · 原文表零写入。
"""
from __future__ import annotations

import asyncio
import logging
import uuid

import pytest
from langchain_core.messages import BaseMessage

from app.llm.model_catalog import resolve_task_model
from app.llm.schema import BaseProvider
from app.ops.lg_rag.continuity import (
    assemble_graph_messages,
    assemble_graph_messages_with_memory,
)
from app.ops.session import summary as session_summary
from tests.conftest import DB_AVAILABLE

_DB_SKIP = pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL unavailable")


def _fixture_turns(n: int = 10) -> list[dict]:
    """默认 10 轮 user 历史 → 压缩出 2 条占位 + 尾部 6 轮全量。"""
    return [{"role": "user", "content": f"q{i}"} for i in range(n)]


def _shape(messages: list[BaseMessage]) -> list[tuple[str, str]]:
    return [(type(m).__name__, str(m.content)) for m in messages]


class _FakeProvider(BaseProvider):
    """计数 fake：complete 记录调用；可配置文本 / 异常 / 延迟。"""

    def __init__(self, text: str = "摘要：历史轮要点", *, error=None, delay=0.0):
        self.calls: list[dict] = []
        self._text = text
        self._error = error
        self._delay = delay

    async def complete(self, messages, model=None):
        self.calls.append({"messages": list(messages), "model": model})
        if self._delay:
            await asyncio.sleep(self._delay)
        if self._error is not None:
            raise self._error
        return self._text


def _patch_face(monkeypatch: pytest.MonkeyPatch, provider: _FakeProvider) -> dict:
    """mock 摘要面 LLM/缓存/span；返回观测 dict（reads/writes/spans 计数）。"""
    obs: dict = {"reads": 0, "writes": 0, "spans": []}
    monkeypatch.setattr(session_summary, "get_llm_provider", lambda: provider)

    async def _read(thread_id, digest):
        obs["reads"] += 1
        return None

    async def _write(**kwargs):
        obs["writes"] += 1

    monkeypatch.setattr(session_summary, "_read_cached_summary", _read)
    monkeypatch.setattr(session_summary, "_write_cached_summary", _write)
    monkeypatch.setattr(
        session_summary,
        "update_current_span_metadata",
        lambda m: obs["spans"].append(m),
    )
    return obs


def _quiet_memory(monkeypatch: pytest.MonkeyPatch) -> None:
    """本面测试只验摘要轨：记忆注入开关显式关闭（.env 可能带 true）。"""
    monkeypatch.delenv("MEMORY_FACTS_ENABLED", raising=False)


# ---------------- D3 · off 三态对拍（逐字节一致 · 上线前提①） ----------------


async def test_off_unset_byte_identical_zero_io(monkeypatch: pytest.MonkeyPatch):
    """未设开关：与占位模式逐字节一致；零 LLM 调用、零缓存读写、零 span。"""
    monkeypatch.delenv("SESSION_SUMMARY_ENABLED", raising=False)
    _quiet_memory(monkeypatch)
    history = _fixture_turns()
    baseline = assemble_graph_messages("本轮问", history)
    provider = _FakeProvider()
    obs = _patch_face(monkeypatch, provider)
    out = await assemble_graph_messages_with_memory(
        "本轮问", history, thread_id="th-sum"
    )
    assert _shape(out) == _shape(baseline)
    assert provider.calls == []
    assert obs == {"reads": 0, "writes": 0, "spans": []}


@pytest.mark.parametrize("value", ["false", "0", "no", "off"])
async def test_off_falsy_byte_identical(monkeypatch: pytest.MonkeyPatch, value: str):
    monkeypatch.setenv("SESSION_SUMMARY_ENABLED", value)
    _quiet_memory(monkeypatch)
    history = _fixture_turns()
    baseline = assemble_graph_messages("q-now", history)
    provider = _FakeProvider()
    obs = _patch_face(monkeypatch, provider)
    out = await assemble_graph_messages_with_memory(
        "q-now", history, thread_id="th-sum"
    )
    assert _shape(out) == _shape(baseline)
    assert provider.calls == [] and obs["reads"] == 0 and obs["writes"] == 0


async def test_off_invalid_value_byte_identical_and_warns(
    monkeypatch: pytest.MonkeyPatch, caplog
):
    """非法值回退 false + warning（continuity 三件套逐字复刻）· 输出逐字节一致。"""
    monkeypatch.setenv("SESSION_SUMMARY_ENABLED", "enable plz")
    _quiet_memory(monkeypatch)
    history = _fixture_turns()
    baseline = assemble_graph_messages("q-now", history)
    provider = _FakeProvider()
    _patch_face(monkeypatch, provider)
    with caplog.at_level(logging.WARNING, logger="app.ops.lg_rag.continuity"):
        out = await assemble_graph_messages_with_memory(
            "q-now", history, thread_id="th-sum"
        )
    assert _shape(out) == _shape(baseline)
    assert "SESSION_SUMMARY_ENABLED" in caplog.text
    assert provider.calls == []


async def test_switch_env_reread_immediate(monkeypatch: pytest.MonkeyPatch):
    """env 重读即时生效（进程内无缓存态）：off → on → off 同一进程内切换。"""
    _quiet_memory(monkeypatch)
    history = _fixture_turns()
    baseline = assemble_graph_messages("q", history)
    provider = _FakeProvider(text="切换期摘要")
    _patch_face(monkeypatch, provider)

    monkeypatch.delenv("SESSION_SUMMARY_ENABLED", raising=False)
    out_off = await assemble_graph_messages_with_memory("q", history, thread_id="t1")
    assert _shape(out_off) == _shape(baseline)
    assert provider.calls == []

    monkeypatch.setenv("SESSION_SUMMARY_ENABLED", "true")
    out_on = await assemble_graph_messages_with_memory("q", history, thread_id="t1")
    assert _shape(out_on) != _shape(baseline)
    assert provider.calls  # on 态即时生效，无需重启

    monkeypatch.delenv("SESSION_SUMMARY_ENABLED", raising=False)
    out_off2 = await assemble_graph_messages_with_memory("q", history, thread_id="t1")
    assert _shape(out_off2) == _shape(baseline)


# ---------------- D3 · on 态全失败对拍（逐字节一致 · 上线前提②） ----------------


async def test_on_all_llm_failures_byte_identical_with_degraded_span(
    monkeypatch: pytest.MonkeyPatch,
):
    """强制 LLM 全失败：输出与 off 态逐字节一致 + span session_summary_degraded=N。

    「走了摘要面但全降级」与「根本没走摘要面」经 provider 调用计数 +
    span 标记区分（变异检验③ oracle）。
    """
    monkeypatch.setenv("SESSION_SUMMARY_ENABLED", "true")
    _quiet_memory(monkeypatch)
    history = _fixture_turns()
    baseline = assemble_graph_messages("q-now", history)
    provider = _FakeProvider(error=RuntimeError("llm down"))
    obs = _patch_face(monkeypatch, provider)
    out = await assemble_graph_messages_with_memory(
        "q-now", history, thread_id="th-sum"
    )
    assert _shape(out) == _shape(baseline)  # 与 off 态逐字节一致
    assert len(provider.calls) == 2  # 确实走了摘要面（两占位 chunk 各一次）
    assert obs["writes"] == 0  # 失败不写缓存（生成成功才写）
    assert obs["spans"] == [
        {
            "session_summary_generated": 0,
            "session_summary_cache_hits": 0,
            "session_summary_degraded": 2,
        }
    ]


async def test_on_but_missing_thread_id_keeps_placeholders(
    monkeypatch: pytest.MonkeyPatch, caplog
):
    """开关 on 但无 thread_id（身份缺失）→ 保留占位 + warning，零 LLM 调用。"""
    monkeypatch.setenv("SESSION_SUMMARY_ENABLED", "true")
    _quiet_memory(monkeypatch)
    history = _fixture_turns()
    baseline = assemble_graph_messages("q", history)
    provider = _FakeProvider()
    _patch_face(monkeypatch, provider)
    with caplog.at_level(logging.WARNING, logger="app.ops.lg_rag.continuity"):
        out = await assemble_graph_messages_with_memory("q", history)
    assert _shape(out) == _shape(baseline)
    assert provider.calls == []
    assert "thread_id missing" in caplog.text


async def test_prompt_asset_failure_degrades_wholesale(monkeypatch: pytest.MonkeyPatch):
    """prompt 资产事故 → 摘要面整体降级占位（不炸请求 · 零 LLM 调用）。"""
    monkeypatch.setenv("SESSION_SUMMARY_ENABLED", "true")
    _quiet_memory(monkeypatch)
    history = _fixture_turns()
    baseline = assemble_graph_messages("q", history)
    provider = _FakeProvider()
    obs = _patch_face(monkeypatch, provider)

    def _boom():
        raise RuntimeError("asset gone")

    monkeypatch.setattr(session_summary, "_resolve_prompt", _boom)
    out = await assemble_graph_messages_with_memory("q", history, thread_id="th-sum")
    assert _shape(out) == _shape(baseline)
    assert provider.calls == []
    assert obs["spans"] == [{"session_summary_degraded": 2}]


# ---------------- D1 · 生成通路（on 态正常路径） ----------------


async def test_on_replaces_placeholders_with_three_markers(
    monkeypatch: pytest.MonkeyPatch,
):
    """占位 chunk 被真摘要条替换：版本 v1 + 来源 模型:<model> + 有损声明三标记；

    结构零改动（条数 / 顺序 / 尾部全量轮 / 本轮 query 逐字节不变）。
    """
    monkeypatch.setenv("SESSION_SUMMARY_ENABLED", "true")
    _quiet_memory(monkeypatch)
    history = _fixture_turns()
    baseline = assemble_graph_messages("q-now", history)
    provider = _FakeProvider(text="前两轮讨论了部署窗口与回退方案")
    obs = _patch_face(monkeypatch, provider)
    out = await assemble_graph_messages_with_memory(
        "q-now", history, thread_id="th-sum"
    )
    assert len(out) == len(baseline)  # 条数不变
    for msg in out[:2]:  # 两条占位均被替换
        content = str(msg.content)
        assert content.startswith("[历史摘要 · v1 · 2 轮 · 模型:")  # 版本+来源
        assert "有损压缩" in content  # 有损声明
        assert "前两轮讨论了部署窗口与回退方案" in content
        assert "roles=" not in content  # 占位格式零残留
    assert _shape(out[2:]) == _shape(baseline[2:])  # 尾部与本轮 query 不动
    assert obs["writes"] == 2  # 生成成功才写缓存
    assert obs["spans"][-1]["session_summary_generated"] == 2
    assert obs["spans"][-1]["session_summary_degraded"] == 0


async def test_on_short_history_no_placeholders_byte_identical(
    monkeypatch: pytest.MonkeyPatch,
):
    """on 态短窗（≤6 轮永不压缩 · 零占位）→ 与 off 逐字节一致且零 LLM 调用。"""
    monkeypatch.setenv("SESSION_SUMMARY_ENABLED", "true")
    _quiet_memory(monkeypatch)
    history = _fixture_turns(4)
    baseline = assemble_graph_messages("q", history)
    provider = _FakeProvider()
    obs = _patch_face(monkeypatch, provider)
    out = await assemble_graph_messages_with_memory("q", history, thread_id="th-sum")
    assert _shape(out) == _shape(baseline)
    assert provider.calls == [] and obs["reads"] == 0 and obs["writes"] == 0


async def test_partial_failure_only_failed_chunk_degrades(
    monkeypatch: pytest.MonkeyPatch,
):
    """单 chunk 粒度降级：第一 chunk 失败保留占位，第二 chunk 正常摘要。"""
    monkeypatch.setenv("SESSION_SUMMARY_ENABLED", "true")
    _quiet_memory(monkeypatch)
    history = _fixture_turns()
    baseline = assemble_graph_messages("q", history)

    class _FlakyProvider(_FakeProvider):
        async def complete(self, messages, model=None):
            self.calls.append({"messages": list(messages), "model": model})
            if len(self.calls) == 1:
                raise RuntimeError("boom")
            return self._text

    provider = _FlakyProvider(text="第二段摘要")
    obs = _patch_face(monkeypatch, provider)
    out = await assemble_graph_messages_with_memory("q", history, thread_id="th-sum")
    assert _shape([out[0]]) == _shape([baseline[0]])  # 失败 chunk 占位保留
    assert "第二段摘要" in str(out[1].content)  # 成功 chunk 真摘要
    assert obs["spans"][-1]["session_summary_degraded"] == 1
    assert obs["spans"][-1]["session_summary_generated"] == 1


async def test_chunk_timeout_degrades_and_does_not_block(monkeypatch: pytest.MonkeyPatch):
    """单次调用超时 → 该 chunk 降级占位 + span 标记；主答零阻塞（按时返回）。"""
    monkeypatch.setenv("SESSION_SUMMARY_ENABLED", "true")
    _quiet_memory(monkeypatch)
    monkeypatch.setattr(session_summary, "SUMMARY_TIMEOUT_S", 0.05)
    history = _fixture_turns()
    baseline = assemble_graph_messages("q", history)
    provider = _FakeProvider(delay=5.0)
    obs = _patch_face(monkeypatch, provider)
    out = await assemble_graph_messages_with_memory("q", history, thread_id="th-sum")
    assert _shape(out) == _shape(baseline)
    assert obs["spans"][-1]["session_summary_degraded"] == 2
    assert obs["writes"] == 0


# ---------------- D1 · summary 档路由与 usage 归因 ----------------


class TestSummaryTierRouting:
    """summary 档（T2）：默认 None 不落档沿用现网默认 · env 覆盖 · 非法回退。"""

    def test_summary_tier_default_none(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("OPS_LLM_TIER_SUMMARY_MODEL", raising=False)
        model, source = resolve_task_model("summary")
        assert model is None and source == "default"

    def test_summary_tier_env_override(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv(
            "OPS_LLM_TIER_SUMMARY_MODEL", "deepseek-ai/DeepSeek-V4-Flash"
        )
        model, source = resolve_task_model("summary")
        assert model == "deepseek-ai/DeepSeek-V4-Flash" and source == "env_tier"

    def test_summary_tier_invalid_env_falls_back_with_warning(
        self, monkeypatch: pytest.MonkeyPatch, caplog
    ):
        monkeypatch.setenv("OPS_LLM_TIER_SUMMARY_MODEL", "no/such-model-anywhere")
        with caplog.at_level(logging.WARNING, logger="app.llm.model_catalog"):
            model, source = resolve_task_model("summary")
        assert model is None and source == "default"
        assert "OPS_LLM_TIER_SUMMARY_MODEL" in caplog.text


async def test_summary_tier_env_model_passed_to_provider(monkeypatch: pytest.MonkeyPatch):
    """OPS_LLM_TIER_SUMMARY_MODEL 覆盖生效：provider 收到档模型。"""
    monkeypatch.setenv("SESSION_SUMMARY_ENABLED", "true")
    monkeypatch.setenv("OPS_LLM_TIER_SUMMARY_MODEL", "Qwen/Qwen3.6-27B")
    _quiet_memory(monkeypatch)
    provider = _FakeProvider()
    _patch_face(monkeypatch, provider)
    await assemble_graph_messages_with_memory("q", _fixture_turns(), thread_id="th-sum")
    assert provider.calls
    assert all(c["model"] == "Qwen/Qwen3.6-27B" for c in provider.calls)


async def test_usage_run_context_attribution(monkeypatch: pytest.MonkeyPatch):
    """摘要调用注入 use_run_context(task_type=summary · surface=lg_rag）。"""
    from app.llm.usage import current_run_context

    seen: dict = {}

    class _CtxProvider(_FakeProvider):
        async def complete(self, messages, model=None):
            ctx = current_run_context()
            seen["task_type"] = ctx.task_type
            seen["surface"] = ctx.surface
            return await super().complete(messages, model=model)

    monkeypatch.setenv("SESSION_SUMMARY_ENABLED", "true")
    _quiet_memory(monkeypatch)
    _patch_face(monkeypatch, _CtxProvider())
    await assemble_graph_messages_with_memory("q", _fixture_turns(), thread_id="th-sum")
    assert seen == {"task_type": "summary", "surface": "lg_rag"}


# ---------------- D1 · prompt 资产（锚点断言 + loader 显式炸） ----------------


def test_summary_prompt_asset_anchors():
    """v1 资产存在 · 锚点断言守「摘要」「不得新增」级语义（非全文快照）。"""
    from app.ops.prompts import get_template, render

    tmpl = get_template("session.summary.system")
    assert tmpl.version == "v1"
    body = render("session.summary.system")
    assert "摘要" in body
    assert "不得新增" in body


def test_loader_missing_summary_asset_raises(tmp_path, monkeypatch):
    """loader 缺文件显式炸（不静默降级为空模板 · loader 纪律沿用）。"""
    from app.ops.prompts import loader
    from app.ops.prompts.loader import PromptAssetError

    monkeypatch.setattr(loader, "_ASSETS_DIR", tmp_path)
    loader.clear_asset_cache()
    try:
        with pytest.raises(PromptAssetError, match="session.summary.system"):
            loader.load_asset("session.summary.system")
    finally:
        loader.clear_asset_cache()


# ---------------- D2 · 缓存表结构（ORM 级 · 无 DB） ----------------


def test_ops_session_summaries_table_structure():
    """列 / 唯一约束 (thread_id, chunk_hash) / FK CASCADE 结构断言。"""
    from sqlalchemy import UniqueConstraint

    from app.db.models import OpsSessionSummary

    table = OpsSessionSummary.__table__
    assert table.name == "ops_session_summaries"
    cols = {c.name for c in table.columns}
    assert {
        "id",
        "thread_id",
        "chunk_hash",
        "summary",
        "prompt_version",
        "model",
        "turn_count",
        "source",
        "created_at",
    } <= cols
    uniques = [c for c in table.constraints if isinstance(c, UniqueConstraint)]
    assert any(
        {col.name for col in u.columns} == {"thread_id", "chunk_hash"} for u in uniques
    )
    fks = table.c.thread_id.foreign_keys
    assert len(fks) == 1
    fk = next(iter(fks))
    assert fk.column.table.name == "ops_lg_rag_threads"
    assert fk.ondelete == "CASCADE"


def test_chunk_hash_key_discipline():
    """key 铁律（纯函数面）：内容 / prompt_version / model 任一变化 → hash 变。"""
    chunk = [{"role": "user", "content": "a"}]
    base = session_summary.chunk_content_hash("v1", "m-1", chunk)
    assert base != session_summary.chunk_content_hash(
        "v1", "m-1", [{"role": "user", "content": "b"}]
    )
    assert base != session_summary.chunk_content_hash("v2", "m-1", chunk)
    assert base != session_summary.chunk_content_hash("v1", "m-2", chunk)
    # 同参数稳定（命中前提）
    assert base == session_summary.chunk_content_hash("v1", "m-1", list(chunk))


# ---------------- D2 · 缓存读写（真 DB · _DB_SKIP） ----------------


@_DB_SKIP
class TestSessionSummaryCacheDB:
    """缓存面真库行为：命中零 LLM · key 铁律 miss · 写失败不挡主答 · 原文零写入。"""

    @pytest.fixture
    async def thread_id(self):
        from sqlalchemy import delete

        from app.db.models import OpsLgRagThread, OpsUser
        from app.db.session import AsyncSessionLocal

        username = f"sum-{uuid.uuid4().hex[:8]}"
        tid = f"sum-th-{uuid.uuid4().hex[:8]}"
        async with AsyncSessionLocal() as db:
            user = OpsUser(username=username, role="viewer")
            db.add(user)
            await db.flush()
            db.add(OpsLgRagThread(id=tid, user_id=str(user.id)))
            await db.commit()
        yield tid
        async with AsyncSessionLocal() as db:
            # 删 user → CASCADE thread → CASCADE summaries（顺带验 FK 链）
            await db.execute(delete(OpsUser).where(OpsUser.username == username))
            await db.commit()

    @staticmethod
    async def _rows(thread_id: str):
        from sqlalchemy import select

        from app.db.models import OpsSessionSummary
        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(OpsSessionSummary).where(
                    OpsSessionSummary.thread_id == thread_id
                )
            )
            return list(result.scalars().all())

    def _wire(self, monkeypatch: pytest.MonkeyPatch, provider: _FakeProvider):
        monkeypatch.setenv("SESSION_SUMMARY_ENABLED", "true")
        monkeypatch.delenv("OPS_LLM_TIER_SUMMARY_MODEL", raising=False)
        _quiet_memory(monkeypatch)
        monkeypatch.setattr(session_summary, "get_llm_provider", lambda: provider)
        monkeypatch.setattr(
            session_summary, "update_current_span_metadata", lambda m: None
        )

    async def test_generate_then_cache_hit_zero_llm(
        self, monkeypatch: pytest.MonkeyPatch, thread_id: str
    ):
        """生成成功才写 + 命中后零 LLM 调用；版本/来源/轮数落库可查。"""
        history = _fixture_turns()
        p1 = _FakeProvider(text="缓存摘要正文")
        self._wire(monkeypatch, p1)
        out1 = await assemble_graph_messages_with_memory("q", history, thread_id=thread_id)
        assert len(p1.calls) == 2
        assert "缓存摘要正文" in str(out1[0].content)

        p2 = _FakeProvider(text="不应出现")
        monkeypatch.setattr(session_summary, "get_llm_provider", lambda: p2)
        out2 = await assemble_graph_messages_with_memory("q", history, thread_id=thread_id)
        assert p2.calls == []  # 命中零 LLM 调用
        assert _shape(out2) == _shape(out1)

        rows = await self._rows(thread_id)
        assert len(rows) == 2
        assert all(r.prompt_version == "v1" for r in rows)
        assert all(r.source == "llm" for r in rows)
        assert all(r.turn_count == 2 for r in rows)
        assert all(r.model for r in rows)

    async def test_same_position_different_content_misses(
        self, monkeypatch: pytest.MonkeyPatch, thread_id: str
    ):
        """key 铁律：同 thread 同序号**不同内容** → 该 chunk miss 重生成；

        未变 chunk 仍命中（窗口滑动缓存污染防线 · 变异检验② oracle 对照）。
        """
        history_a = _fixture_turns()
        p1 = _FakeProvider(text="首版摘要")
        self._wire(monkeypatch, p1)
        out1 = await assemble_graph_messages_with_memory("q", history_a, thread_id=thread_id)
        assert len(p1.calls) == 2

        history_b = [dict(t) for t in history_a]
        history_b[0] = {"role": "user", "content": "q0-已改"}  # chunk0 内容变
        p2 = _FakeProvider(text="新摘要")
        monkeypatch.setattr(session_summary, "get_llm_provider", lambda: p2)
        out2 = await assemble_graph_messages_with_memory("q", history_b, thread_id=thread_id)
        assert len(p2.calls) == 1  # 仅变化 chunk 重生成
        assert "新摘要" in str(out2[0].content)
        assert str(out2[1].content) == str(out1[1].content)  # 未变 chunk 命中缓存

    async def test_prompt_version_bump_misses(
        self, monkeypatch: pytest.MonkeyPatch, thread_id: str
    ):
        """改 prompt 必 bump version（assets README 纪律）→ key 变自然 miss。"""
        history = _fixture_turns()
        p1 = _FakeProvider()
        self._wire(monkeypatch, p1)
        await assemble_graph_messages_with_memory("q", history, thread_id=thread_id)
        assert len(p1.calls) == 2

        monkeypatch.setattr(
            session_summary, "_resolve_prompt", lambda: ("sys", "v2")
        )
        p2 = _FakeProvider()
        monkeypatch.setattr(session_summary, "get_llm_provider", lambda: p2)
        await assemble_graph_messages_with_memory("q", history, thread_id=thread_id)
        assert len(p2.calls) == 2  # 全 miss 重生成

    async def test_model_change_misses(
        self, monkeypatch: pytest.MonkeyPatch, thread_id: str
    ):
        """换模型（档 env 覆盖）→ key 变自然 miss。"""
        history = _fixture_turns()
        p1 = _FakeProvider()
        self._wire(monkeypatch, p1)
        await assemble_graph_messages_with_memory("q", history, thread_id=thread_id)
        assert len(p1.calls) == 2

        monkeypatch.setenv("OPS_LLM_TIER_SUMMARY_MODEL", "Qwen/Qwen3.6-27B")
        p2 = _FakeProvider()
        monkeypatch.setattr(session_summary, "get_llm_provider", lambda: p2)
        out2 = await assemble_graph_messages_with_memory("q", history, thread_id=thread_id)
        assert len(p2.calls) == 2
        assert "模型:Qwen/Qwen3.6-27B" in str(out2[0].content)

    async def test_cache_io_failure_still_returns_summary(
        self, monkeypatch: pytest.MonkeyPatch, thread_id: str, caplog
    ):
        """缓存读失败视同 miss · 写失败 log + 本次仍用摘要（不挡主答）。"""
        history = _fixture_turns()
        provider = _FakeProvider(text="降级期摘要")
        self._wire(monkeypatch, provider)

        class _BrokenSession:
            async def __aenter__(self):
                raise RuntimeError("db down")

            async def __aexit__(self, *args):
                pass

        monkeypatch.setattr(
            "app.db.session.AsyncSessionLocal", lambda: _BrokenSession()
        )
        with caplog.at_level(logging.WARNING, logger="app.ops.session.summary"):
            out = await assemble_graph_messages_with_memory(
                "q", history, thread_id=thread_id
            )
        assert "降级期摘要" in str(out[0].content)  # 本次仍用生成的摘要
        assert provider.calls  # 读失败视同 miss → 走生成链
        assert "cache read failed" in caplog.text
        assert "cache write failed" in caplog.text

    async def test_original_tables_untouched(
        self, monkeypatch: pytest.MonkeyPatch, thread_id: str
    ):
        """原文 SoT 零污染：摘要通路前后 ops_lg_rag_turns / ops_runs 行数不变。"""
        from sqlalchemy import func, select

        from app.db.models import OpsLgRagTurn, OpsRun
        from app.db.session import AsyncSessionLocal

        async def _counts():
            async with AsyncSessionLocal() as db:
                turns = (
                    await db.execute(select(func.count()).select_from(OpsLgRagTurn))
                ).scalar_one()
                runs = (
                    await db.execute(select(func.count()).select_from(OpsRun))
                ).scalar_one()
            return turns, runs

        before = await _counts()
        provider = _FakeProvider()
        self._wire(monkeypatch, provider)
        await assemble_graph_messages_with_memory("q", _fixture_turns(), thread_id=thread_id)
        assert await _counts() == before
        assert await self._rows(thread_id)  # 摘要只进独立表

    async def test_duplicate_write_same_key_tolerated(self, thread_id: str):
        """并发同 key 双生成：唯一约束先写赢，后者冲突容忍（不炸）。"""
        chunk = [{"role": "user", "content": "a"}]
        digest = session_summary.chunk_content_hash("v1", "m-1", chunk)
        kwargs = {
            "thread_id": thread_id,
            "digest": digest,
            "summary_text": "s",
            "prompt_version": "v1",
            "model": "m-1",
            "turn_count": 1,
        }
        await session_summary._write_cached_summary(**kwargs)
        await session_summary._write_cached_summary(**kwargs)  # 冲突容忍
        assert len(await self._rows(thread_id)) == 1

    async def test_fk_cascade_on_thread_delete(self, thread_id: str):
        """删 thread → 摘要行 CASCADE 跟随（随 thread 清理 · C1 裁决）。"""
        provider = _FakeProvider()
        monkeypatch = pytest.MonkeyPatch()
        try:
            self._wire(monkeypatch, provider)
            await assemble_graph_messages_with_memory(
                "q", _fixture_turns(), thread_id=thread_id
            )
        finally:
            monkeypatch.undo()
        assert len(await self._rows(thread_id)) == 2

        from sqlalchemy import delete

        from app.db.models import OpsLgRagThread
        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(OpsLgRagThread).where(OpsLgRagThread.id == thread_id)
            )
            await db.commit()
        assert await self._rows(thread_id) == []

    async def test_usage_row_attribution_summary_tier(
        self, monkeypatch: pytest.MonkeyPatch, thread_id: str
    ):
        """真 provider 包装层 + fake usage 末帧 → ops_llm_usage 落行
        task_type=summary / surface=lg_rag（归因继承零改造）。"""
        import httpx
        from sqlalchemy import select

        from app.db.models import OpsLlmUsage
        from app.db.session import AsyncSessionLocal
        from app.llm import usage as llm_usage
        from app.llm.providers.siliconflow import SiliconFlowProvider

        usage = (
            '{"prompt_tokens": 7, "completion_tokens": 3,'
            ' "prompt_cache_hit_tokens": 0}'
        )
        lines = [
            'data: {"choices":[{"delta":{"content":"归因摘要"}}]}',
            'data: {"choices":[],"usage":' + usage + '}',
            "data: [DONE]",
        ]

        class _FakeResp:
            status_code = 200

            async def aread(self):
                return b""

            async def aiter_lines(self):
                for line in lines:
                    yield line

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

        class _FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            def stream(self, *args, **kwargs):
                return _FakeResp()

        monkeypatch.setattr(
            httpx, "AsyncClient", lambda *a, **k: _FakeClient()
        )
        provider = SiliconFlowProvider(api_key="test-key")
        self._wire(monkeypatch, provider)
        run_id = uuid.uuid4().hex
        with llm_usage.use_run_context(run_id=run_id, surface="lg_rag"):
            out = await assemble_graph_messages_with_memory(
                "q", _fixture_turns(), thread_id=thread_id
            )
        assert "归因摘要" in str(out[0].content)

        async with AsyncSessionLocal() as db:
            rows = list(
                (
                    await db.execute(
                        select(OpsLlmUsage).where(OpsLlmUsage.run_id == run_id)
                    )
                )
                .scalars()
                .all()
            )
        assert len(rows) == 2  # 两占位 chunk 各一次调用
        assert all(r.task_type == "summary" for r in rows)
        assert all(r.surface == "lg_rag" for r in rows)
        assert all(r.prompt_tokens == 7 for r in rows)
