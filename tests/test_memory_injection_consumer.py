"""task_memory_injection_consumer · Phase B ④b 验收（全模式收窄 · 功能休眠）。

HG-PHASE-B-DECISION=approved（2026-10-20 维护者裁定结局④b ·
docs/harness/invokes/by-task/memory-injection-consumer/invoke_20261020_phase_b_decision_4b.md）：
三模式（basic / router / supervisor）记忆注入路径整体收窄——装配面不再读
MEMORY_FACTS_ENABLED / MEMORY_EPISODES_ENABLED、不再调任何 recall、不再注入块；
功能休眠（实现保留），复活对接 docs/tasks/deferred/task_memory_facts_build_4a.md。

本文件验收（红测先行）：
- TC8/FP-5：注入开下三模式 recall（facts 确定性/向量 + episodes）全零调用；
- 注入开/关行为零 diff：spy 记录的 LLM 请求清单与 state.messages 对拍相等
  （对拍 Phase A 基线 invoke_20261019_30_phaseA_spy_matrix.md：九消费点本就零消费，
   收窄后请求面逐字节不变）；
- TC2：默认关零 diff（recall 零调用 ∧ 注入块零出现 ∧ 流程照常）；
- TC5：diff 白名单（tests/ + invoke docs/ + continuity.py + memory README/__init__
  + 01_modules.md；scripts/ alembic/ 及其余 app/ 禁现）。
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.llm.schema import LlmChunk, LlmMessage
from app.ops.lc_evidence_chain.types import ChainResult, EvidenceItem, RetrieveResult
from app.ops.lg_rag.continuity import (
    MEMORY_EPISODES_HEADER,
    MEMORY_FACTS_HEADER,
    MEMORY_PREFERENCES_HEADER,
    assemble_graph_messages,
    inject_memory_facts_block,
    render_memory_episodes_block,
    render_memory_facts_block,
)
from app.ops.lg_rag.graph import ainvoke_basic_agent, ainvoke_router_agent
from app.ops.lg_rag.multi.graph import ainvoke_supervisor_agent
from app.ops.prompts import render
from app.ops.tenant_context import TENANT_A, reset_current_tenant, set_current_tenant

# ---------------------------------------------------------------------------
# 哨兵与 markers：注入块内容唯一可辨；④b 后任何面命中即收窄失守
# ---------------------------------------------------------------------------

FACT_VALUE = "PHASEB-SENTINEL-FACT-8e4a1d"
PREF_VALUE = "PHASEB-SENTINEL-PREF-62bb"
EPISODE_SUMMARY = "PHASEB-SENTINEL-EPISODE-先查日志再重启"

FACT_MARKERS = [MEMORY_FACTS_HEADER, MEMORY_PREFERENCES_HEADER, FACT_VALUE, PREF_VALUE]
EPISODE_MARKERS = [MEMORY_EPISODES_HEADER, EPISODE_SUMMARY]
ALL_MARKERS = FACT_MARKERS + EPISODE_MARKERS

_QUERY = "服务超时怎么排查"  # 避开 nodes.py:45 _ISSUE_NO_RE 规则快路径（#数字 跳过 classify LLM）
_SUBTASK_QUERY = "检索服务超时处置步骤"
_USER = "phaseb-user"
_REWRITE_OUT = "服务超时如何定位并恢复"
_GRADE_REFUSE = '[{"chunk_id": 1, "relevance": "irrelevant", "reason": "首轮不相关"}]'
_GRADE_EXACT = '[{"chunk_id": 1, "relevance": "exact", "reason": "二轮命中"}]'
_ANSWER_OUT = "答案：先查日志再重启"
_AGG_OUT = "## 综合结论\n先查日志再重启。"


# ---------------------------------------------------------------------------
# SpyProvider：记录每次调用的消息清单；script 按序出稿、用尽重复末项
# （承 tests/test_lg_rag_multi.py:_provider 先例——调用次数受拓扑判定影响，
#  不写死条数；次数本身由 calls 记录承担断言）
# ---------------------------------------------------------------------------


@dataclass
class RecordedCall:
    """一次 LLM 调用的快照（发往 provider 的消息清单原样留存）。"""

    spy: str
    method: str
    messages: list[tuple[str, str]]

    @property
    def text(self) -> str:
        return "\n".join(content for _, content in self.messages)


class SpyProvider:
    """fake LLM provider：complete / complete_stream 均记录消息后按 script 出稿。"""

    def __init__(self, tag: str, *outputs: object) -> None:
        self.tag = tag
        self._stream = list(outputs)
        self.calls: list[RecordedCall] = []

    def _scripted(self) -> str:
        if not self._stream:
            return ""
        item = self._stream.pop(0) if len(self._stream) > 1 else self._stream[0]
        if isinstance(item, BaseException):
            raise item
        return str(item)

    def _record(self, method: str, messages: list[LlmMessage]) -> None:
        self.calls.append(
            RecordedCall(
                spy=self.tag,
                method=method,
                messages=[(str(m.role), str(m.content)) for m in messages],
            )
        )

    async def complete(self, messages: list[LlmMessage], model: str | None = None) -> str:
        self._record("complete", messages)
        return self._scripted()

    async def complete_stream(self, messages: list[LlmMessage], model: str | None = None):
        self._record("complete_stream", messages)
        text = self._scripted()
        if text:
            yield LlmChunk(content=text)


def _hits(calls: list[RecordedCall], markers: list[str]) -> list[tuple[int, str, str]]:
    """[(call_index, spy_tag, marker)] — 诊断用全量命中清单。"""

    found: list[tuple[int, str, str]] = []
    for i, call in enumerate(calls):
        for marker in markers:
            if marker in call.text:
                found.append((i, call.spy, marker))
    return found


def _assert_no_markers(calls: list[RecordedCall], markers: list[str], ctx: str) -> None:
    found = _hits(calls, markers)
    assert not found, f"{ctx}: 注入块到达 LLM 请求面（命中清单 {found}）"


def _assembled_text(out: dict) -> str:
    return "\n".join(str(m.content) for m in out["messages"])


def _norm(calls: list[RecordedCall]) -> list[tuple[str, str, list[tuple[str, str]]]]:
    """归一化 LLM 调用清单：spy 名去掉 .on/.off 尾标（同一位点的开/关双拍须可比）。"""

    return [(re.sub(r"\.(on|off)$", "", c.spy), c.method, c.messages) for c in calls]


# ---------------------------------------------------------------------------
# patch 点与 fixture
# ---------------------------------------------------------------------------

_CHAIN_RETRIEVE = "app.ops.lc_evidence_chain.chain.retrieve_evidence"
_CHAIN_GRADER_PROVIDER = "app.ops.lc_evidence_chain.grader.get_llm_provider"
_CHAIN_ANSWER_PROVIDER = "app.ops.lc_evidence_chain.answer.get_llm_provider"
_NODES_PROVIDER = "app.ops.lg_rag.nodes.get_llm_provider"
_NODES_CHAIN = "app.ops.lg_rag.nodes.ainvoke_evidence_answer"
_MULTI_PROVIDER = "app.ops.lg_rag.multi.nodes.get_llm_provider"


@pytest.fixture
def injection_on(monkeypatch: pytest.MonkeyPatch):
    """注入开（facts + episodes）+ 全 recall 通路 stub + tenant ContextVar + tracing 关闭。

    ④b 休眠态下三通路 stub 均**零调用**（TC8/FP-5 核心断言面）；向量通路 stub
    置 AssertionError side_effect——任何触达即显式红（不依赖 await_count 口径）。
    tracing 关闭为对本机 .env（可能带 LANGFUSE 双键）免疫。
    """

    monkeypatch.setenv("MEMORY_FACTS_ENABLED", "true")
    monkeypatch.setenv("MEMORY_EPISODES_ENABLED", "true")
    for key in (
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_SECRET_KEY",
        "OPS_CHAT_TRACER",
        "LG_RAG_REACT_SATISFACTION",
    ):
        monkeypatch.delenv(key, raising=False)
    for target in (
        "app.ops.lg_rag.graph.tracing_enabled",
        "app.ops.lg_rag.nodes.tracing_enabled",
        "app.ops.lg_rag.multi.nodes.tracing_enabled",
        "app.ops.lc_evidence_chain.chain.tracing_enabled",
    ):
        monkeypatch.setattr(target, lambda: False, raising=False)

    facts_recall = AsyncMock(
        return_value=[
            {"key": "project.phaseb_probe", "value": FACT_VALUE, "kind": "fact"},
            {"key": "style.phaseb_probe", "value": PREF_VALUE, "kind": "preference"},
        ]
    )
    monkeypatch.setattr("app.ops.memory.service.recall_active", facts_recall)
    vector_recall = AsyncMock(
        side_effect=AssertionError("④b 休眠：向量召回通路不应被触达")
    )
    monkeypatch.setattr("app.ops.memory.service.recall_with_vector", vector_recall)
    episodes_recall = AsyncMock(
        return_value=[
            {
                "tenant_id": TENANT_A,
                "run_id": "phaseb-run",
                "task_domain": "ops",
                "context_fingerprint": "fp",
                "plan_summary": EPISODE_SUMMARY,
                "tool_sequence": ["logs.read"],
                "outcome": "success",
                "status": "active",
            }
        ]
    )
    monkeypatch.setattr(
        "app.ops.memory.episode_service.recall_success_episodes", episodes_recall
    )
    token = set_current_tenant(TENANT_A)
    yield SimpleNamespace(facts=facts_recall, vector=vector_recall, episodes=episodes_recall)
    reset_current_tenant(token)


def _switches_off(monkeypatch: pytest.MonkeyPatch) -> None:
    """注入关（默认形态）：双开关删除（stub 仍在——关/开两面 recall 都须零调用）。"""

    monkeypatch.delenv("MEMORY_FACTS_ENABLED", raising=False)
    monkeypatch.delenv("MEMORY_EPISODES_ENABLED", raising=False)
    monkeypatch.delenv("MEMORY_FACTS_VECTOR_RECALL_ENABLED", raising=False)


def _assert_dormant(
    injection_on: SimpleNamespace, out: dict, calls: list[RecordedCall], ctx: str
) -> None:
    """④b 休眠三断言：recall 全通路零调用 ∧ state.messages 零注入块 ∧ LLM 请求面零命中。"""

    assert injection_on.facts.await_count == 0, f"{ctx}: facts recall 被调（收窄失守）"
    assert injection_on.vector.await_count == 0, f"{ctx}: 向量 recall 被调（收窄失守）"
    assert injection_on.episodes.await_count == 0, f"{ctx}: episodes recall 被调（收窄失守）"
    leaked = [m for m in ALL_MARKERS if m in _assembled_text(out)]
    assert not leaked, f"{ctx}: 注入块进入 state.messages: {leaked}"
    _assert_no_markers(calls, ALL_MARKERS, ctx)


def _assert_on_off_parity(
    on_out: dict,
    on_calls: list[RecordedCall],
    off_out: dict,
    off_calls: list[RecordedCall],
    ctx: str,
) -> None:
    """注入开/关行为零 diff：LLM 请求清单与装配消息逐字节相等（对拍 Phase A 基线）。"""

    assert _norm(on_calls) == _norm(off_calls), f"{ctx}: 注入开/关 LLM 请求面不等"
    assert _assembled_text(on_out) == _assembled_text(off_out), (
        f"{ctx}: 注入开/关 state.messages 不等"
    )


def _fake_retrieve() -> RetrieveResult:
    return RetrieveResult(
        query=_QUERY,
        evidence=[
            EvidenceItem(
                id=1,
                repo="ops-desk-api",
                source_type="doc",
                source_id="kb-1",
                chunk_index=0,
                content="服务超时先查日志再重启。",
            )
        ],
    )


def _patch_chain(
    monkeypatch: pytest.MonkeyPatch, *, grader: SpyProvider, answer: SpyProvider
) -> None:
    monkeypatch.setattr(_CHAIN_RETRIEVE, AsyncMock(return_value=_fake_retrieve()))
    monkeypatch.setattr(_CHAIN_GRADER_PROVIDER, lambda *a, **k: grader)
    monkeypatch.setattr(_CHAIN_ANSWER_PROVIDER, lambda *a, **k: answer)


def _nodes_call_site(call: RecordedCall) -> str:
    """按 system prompt 归因 lg_rag.nodes 三个 LLM 点（对拍 render 真值）。"""

    system = call.messages[0][1] if call.messages and call.messages[0][0] == "system" else ""
    for prompt_id, site in (
        ("lg_rag.router.system", "router_node.classify"),
        ("lg_rag.rewrite.system", "rewrite_node"),
        ("lg_rag.direct.system", "direct_answer_node"),
    ):
        if render(prompt_id) in system:
            return site
    return "unknown"


def _multi_call_site(call: RecordedCall) -> str:
    """multi 图 LLM 点归因：aggregator system 含 render 真值（isolation 态 wrap_slot 亦含）。"""

    system = call.messages[0][1] if call.messages and call.messages[0][0] == "system" else ""
    if render("lg_rag.aggregator.system") in system:
        return "aggregator_node"
    return "supervisor_node.planner"


# ---------------------------------------------------------------------------
# ④b 场景 runner：同一图形态跑两次（注入开 / 关），产出 spy 记录供对拍
# ---------------------------------------------------------------------------


async def _run_basic_rag(monkeypatch: pytest.MonkeyPatch, tag: str):
    grader = SpyProvider(f"chain.grader.{tag}", _GRADE_EXACT)
    answer = SpyProvider(f"chain.answer.{tag}", _ANSWER_OUT)
    _patch_chain(monkeypatch, grader=grader, answer=answer)
    out = await ainvoke_basic_agent(_QUERY, thread_id=f"phaseb-basic-{tag}", user_id=_USER)
    return out, grader.calls + answer.calls


async def _run_router_rag_rewrite(monkeypatch: pytest.MonkeyPatch, tag: str):
    nodes_spy = SpyProvider(f"lg_rag.nodes.{tag}", '{"route": "rag"}', _REWRITE_OUT)
    grader = SpyProvider(f"chain.grader.{tag}", _GRADE_REFUSE, _GRADE_EXACT)
    answer = SpyProvider(f"chain.answer.{tag}", _ANSWER_OUT)
    _patch_chain(monkeypatch, grader=grader, answer=answer)
    monkeypatch.setattr(_NODES_PROVIDER, lambda *a, **k: nodes_spy)
    out = await ainvoke_router_agent(
        _QUERY, thread_id=f"phaseb-router-rag-{tag}", user_id=_USER
    )
    return out, nodes_spy.calls + grader.calls + answer.calls, nodes_spy.calls


async def _run_router_direct(monkeypatch: pytest.MonkeyPatch, tag: str):
    nodes_spy = SpyProvider(f"lg_rag.nodes.{tag}", '{"route": "direct"}', "直答：先查日志")
    monkeypatch.setattr(_NODES_PROVIDER, lambda *a, **k: nodes_spy)
    monkeypatch.setattr(
        _CHAIN_RETRIEVE,
        AsyncMock(side_effect=AssertionError("direct 路径不应发生检索")),
    )
    out = await ainvoke_router_agent(
        _QUERY, thread_id=f"phaseb-router-direct-{tag}", user_id=_USER
    )
    return out, nodes_spy.calls


async def _run_supervisor(monkeypatch: pytest.MonkeyPatch, tag: str):
    plan = json.dumps(
        {"subtasks": [{"id": "t1", "type": "rag", "input": _SUBTASK_QUERY}]},
        ensure_ascii=False,
    )
    multi_spy = SpyProvider(f"multi.nodes.{tag}", plan, _AGG_OUT)
    inner_router = SpyProvider(f"lg_rag.nodes.inner.{tag}", '{"route": "rag"}')
    chain = AsyncMock(
        return_value=ChainResult(
            query=_SUBTASK_QUERY,
            evidence=[],
            answer="检索答案：先查日志",
            meta={"gate_action": "answer", "kept_count": 1, "hit_count": 1},
        )
    )
    monkeypatch.setattr(_MULTI_PROVIDER, lambda *a, **k: multi_spy)
    monkeypatch.setattr(_NODES_PROVIDER, lambda *a, **k: inner_router)
    monkeypatch.setattr(_NODES_CHAIN, chain)
    out = await ainvoke_supervisor_agent(
        # run_id 常量：supervisor 子任务 id 嵌入 run_id，开/关双拍须同值才可比
        # （隔离由 thread_id 承担）；spy 位点区分仍靠 tag
        _QUERY, thread_id=f"phaseb-supervisor-{tag}", user_id=_USER, run_id="phaseb-run"
    )
    return out, multi_spy.calls + inner_router.calls, multi_spy.calls, inner_router.calls, chain


# ---------------------------------------------------------------------------
# ④b 验收：注入开 × 三模式 → 休眠三断言 + 开/关零 diff 对拍
# ---------------------------------------------------------------------------


async def test_4b_basic_rag_dormant_and_on_off_parity(
    monkeypatch: pytest.MonkeyPatch, injection_on: SimpleNamespace
) -> None:
    """basic(rag) × 注入开：recall 零调用 ∧ 零注入块；开/关 LLM 请求面逐字节相等。"""

    on_out, on_calls = await _run_basic_rag(monkeypatch, "on")
    assert [c.method for c in on_calls] == ["complete", "complete"]  # grader + answer 照常
    _assert_dormant(injection_on, on_out, on_calls, "basic/on")

    _switches_off(monkeypatch)
    off_out, off_calls = await _run_basic_rag(monkeypatch, "off")
    _assert_on_off_parity(on_out, on_calls, off_out, off_calls, "basic")
    _assert_dormant(injection_on, off_out, off_calls, "basic/off")


async def test_4b_router_rag_rewrite_loop_dormant_and_on_off_parity(
    monkeypatch: pytest.MonkeyPatch, injection_on: SimpleNamespace
) -> None:
    """router(rag→rewrite 回环) × 注入开：classify/rewrite + grader×2 + answer 全链路休眠。

    首轮 grader 判 irrelevant → gate refuse → kept 空 → answer 不调 LLM →
    quality low → rewrite 新 query → 二轮 grader 判 exact → kept → answer 调 LLM。
    """

    on_out, on_calls, on_nodes = await _run_router_rag_rewrite(monkeypatch, "on")
    sites = [_nodes_call_site(c) for c in on_nodes]
    assert sites == ["router_node.classify", "rewrite_node"], sites
    for call in on_nodes:
        assert call.messages[-1] == ("user", _QUERY), call.messages
    _assert_dormant(injection_on, on_out, on_calls, "router-rag/on")

    _switches_off(monkeypatch)
    off_out, off_calls, _ = await _run_router_rag_rewrite(monkeypatch, "off")
    _assert_on_off_parity(on_out, on_calls, off_out, off_calls, "router-rag")
    _assert_dormant(injection_on, off_out, off_calls, "router-rag/off")


async def test_4b_router_direct_dormant_and_on_off_parity(
    monkeypatch: pytest.MonkeyPatch, injection_on: SimpleNamespace
) -> None:
    """router(direct) × 注入开：classify + direct_answer 休眠（不触 chain）；开/关零 diff。"""

    on_out, on_calls = await _run_router_direct(monkeypatch, "on")
    sites = [_nodes_call_site(c) for c in on_calls]
    assert sites == ["router_node.classify", "direct_answer_node"], sites
    assert on_calls[1].messages[-1] == ("user", _QUERY)
    _assert_dormant(injection_on, on_out, on_calls, "router-direct/on")

    _switches_off(monkeypatch)
    off_out, off_calls = await _run_router_direct(monkeypatch, "off")
    _assert_on_off_parity(on_out, on_calls, off_out, off_calls, "router-direct")
    _assert_dormant(injection_on, off_out, off_calls, "router-direct/off")


async def test_4b_supervisor_dormant_and_on_off_parity(
    monkeypatch: pytest.MonkeyPatch, injection_on: SimpleNamespace
) -> None:
    """supervisor × 注入开：planner/aggregator/内层 classify 休眠；开/关零 diff。

    Phase A 实证 supervisor 存在内层 rag 工人复装配（episodes recall 2 次）——
    ④b 收窄后外层与内层复装配同走 impl 单点，本测试 episodes 零调用断言同时
    覆盖内层复装配面（若内层仍 recall 即红）。
    """

    on_out, on_calls, on_multi, on_inner, on_chain = await _run_supervisor(monkeypatch, "on")
    sites = [_multi_call_site(c) for c in on_multi]
    assert sites == ["supervisor_node.planner", "aggregator_node"], sites
    assert [c.method for c in on_inner] == ["complete"]
    assert _nodes_call_site(on_inner[0]) == "router_node.classify"
    assert on_inner[0].messages[-1] == ("user", _SUBTASK_QUERY)
    on_chain.assert_awaited_once()
    _assert_dormant(injection_on, on_out, on_calls, "supervisor/on")

    _switches_off(monkeypatch)
    off_out, off_calls, _, _, _ = await _run_supervisor(monkeypatch, "off")
    _assert_on_off_parity(on_out, on_calls, off_out, off_calls, "supervisor")
    _assert_dormant(injection_on, off_out, off_calls, "supervisor/off")


# ---------------------------------------------------------------------------
# TC2：默认关回归（零 diff 语义——recall 零调用 ∧ 注入块零出现 ∧ 流程照常）
# ---------------------------------------------------------------------------


async def test_switches_default_off_zero_recall_zero_injection(
    monkeypatch: pytest.MonkeyPatch, injection_on: SimpleNamespace
) -> None:
    """双开关默认关（删 env）→ recall 零 await ∧ state.messages 无注入块 ∧ 流程照常。"""

    _switches_off(monkeypatch)
    grader = SpyProvider("chain.grader", _GRADE_EXACT)
    answer = SpyProvider("chain.answer", _ANSWER_OUT)
    _patch_chain(monkeypatch, grader=grader, answer=answer)

    out = await ainvoke_basic_agent(_QUERY, thread_id="phaseb-off", user_id=_USER)

    _assert_dormant(injection_on, out, grader.calls + answer.calls, "default-off")
    assert out["messages"][-1].content == _ANSWER_OUT


# ---------------------------------------------------------------------------
# harness 自牙测：断言器对含哨兵的调用必 raise；markers 与渲染真值对齐
# （防空转绿——④b 后注入路径不存在，牙须咬在「若注入发生必被看见」上）
# ---------------------------------------------------------------------------


async def test_spy_assertion_has_teeth() -> None:
    spy = SpyProvider("selfcheck", "ok")
    await spy.complete([LlmMessage(role="user", content=f"内容含 {FACT_VALUE}")])
    assert _hits(spy.calls, FACT_MARKERS), "spy 记录面失效"
    with pytest.raises(AssertionError):
        _assert_no_markers(spy.calls, FACT_MARKERS, "selfcheck")

    clean = SpyProvider("selfcheck", "ok")
    await clean.complete([LlmMessage(role="user", content="普通内容")])
    _assert_no_markers(clean.calls, ALL_MARKERS, "selfcheck-clean")


def test_markers_match_render_truth() -> None:
    """markers 与 render/inject 真值对齐：若注入块真出现，必含 marker 并被装配面看见。"""

    facts_block = render_memory_facts_block(
        [
            {"key": "project.phaseb_probe", "value": FACT_VALUE, "kind": "fact"},
            {"key": "style.phaseb_probe", "value": PREF_VALUE, "kind": "preference"},
        ]
    )
    for marker in FACT_MARKERS:
        assert marker in facts_block, f"render 真值缺 marker: {marker}"
    episode_block = render_memory_episodes_block(
        [
            {
                "tenant_id": TENANT_A,
                "run_id": "phaseb-run",
                "task_domain": "ops",
                "context_fingerprint": "fp",
                "plan_summary": EPISODE_SUMMARY,
                "tool_sequence": ["logs.read"],
                "outcome": "success",
                "status": "active",
            }
        ]
    )
    for marker in EPISODE_MARKERS:
        assert marker in episode_block, f"render 真值缺 marker: {marker}"
    # 注入块一旦进装配产物，state.messages 文本面必可见（休眠断言非空真）
    msgs = inject_memory_facts_block(assemble_graph_messages("q", []), facts_block)
    text = "\n".join(str(m.content) for m in msgs)
    assert FACT_VALUE in text and MEMORY_FACTS_HEADER in text


# ---------------------------------------------------------------------------
# TC5（N2 吸收 · 白名单形态 · Phase B 版）：diff ⊆ tests/ + invoke docs/
# + continuity.py + memory README/__init__ + 01_modules.md；
# scripts/ alembic/ 及其余 app/ 显式禁现（含 untracked，防新文件绕过）
# ---------------------------------------------------------------------------

_BASE = "414270d"
_APP_ALLOWED = {
    "app/ops/lg_rag/continuity.py",
    "app/ops/memory/README.md",
    "app/ops/memory/__init__.py",
    # 切割连带：continuity 不再 import memory，三条 ignore 条目随切割移除
    ".importlinter",
}
_TREE_ALLOWED_PREFIXES = (
    "tests/",
    "docs/harness/invokes/by-task/memory-injection-consumer/",
    "docs/_tech_graph/l1/01_modules.md",
)
# 00/维护者落签面（非 30 产出 · 已在分支提交 29cd456/ed2c150 带 [00] 标记）：
# 闸表裁定、DEF-005 对接文档与其优先级登记——30 禁改，仅登记为既有分支 delta
_UPSTREAM_SIGN_PATHS = {
    "docs/tasks/active/task_memory_injection_consumer.md",
    "docs/tasks/deferred/task_memory_facts_build_4a.md",
    "docs/tasks/PRIORITY_DEFERRED.md",
}
_BANNED_PREFIXES = ("scripts/", "alembic/")


def _allowed(path: str) -> bool:
    return (
        path in _APP_ALLOWED
        or path in _UPSTREAM_SIGN_PATHS
        or path.startswith(_TREE_ALLOWED_PREFIXES)
    )


def _banned(path: str) -> bool:
    if path.startswith(_BANNED_PREFIXES):
        return True
    return path.startswith("app/") and path not in _APP_ALLOWED


def _git(root: Path, *args: str) -> list[str]:
    out = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True
    )
    return [line.strip() for line in out.stdout.splitlines() if line.strip()]


def test_phase_b_diff_whitelist() -> None:
    root = Path(__file__).resolve().parents[1]
    changed: set[str] = set()
    for args in (
        ("diff", "--name-only", _BASE),  # 工作区 vs base（未暂存）
        ("diff", "--name-only", "--cached", _BASE),  # 暂存区 vs base
        ("diff", "--name-only", _BASE, "HEAD"),  # 已提交 delta（含 Phase A a9fde63）
    ):
        changed.update(_git(root, *args))
    untracked = set(_git(root, "ls-files", "--others", "--exclude-standard"))

    violations = sorted(p for p in changed if not _allowed(p))
    assert not violations, f"diff 越白名单: {violations}"
    banned = sorted(p for p in changed | untracked if _banned(p))
    assert not banned, f"禁改面（scripts/ alembic/ 及其余 app/）出现改动: {banned}"
