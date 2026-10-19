"""task_memory_injection_consumer · Phase A 实证矩阵（观测-only · 零生产码改动）。

SpyProvider 逐次记录三模式（basic / router / supervisor）下各节点发往 LLM 的
消息清单，断言注入块（facts / preferences / episodes）是否到达 LLM 请求面。
结论表落 docs/harness/invokes/by-task/memory-injection-consumer/，
作为 HG-PHASE-B-DECISION 裁定的唯一依据。

锚点（行号基于 base 414270d 校正）：
- 装配面：app/ops/lg_rag/continuity.py assemble_graph_messages_with_memory :559
  （facts 开关 :144 / episodes 开关 :215，os.getenv 运行时读、默认 false；
   facts skip 条件 :458 tenant/user 缺一即跳；episodes skip 条件 :500 tenant 缺即跳）
- 入口：app/ops/lg_rag/graph.py:218 ainvoke_basic_agent / :255 ainvoke_router_agent；
  app/ops/lg_rag/multi/graph.py:108 ainvoke_supervisor_agent
- LLM 消费点：
  - app/ops/lg_rag/nodes.py:85 router_node(classify) / :214 rewrite_node / :258 direct_answer_node
  - app/ops/lg_rag/multi/nodes.py:1164 supervisor_node(planner) / :2110 aggregator_node
    （critic / strategy_builder / observe 默认路径为规则实现，无 LLM ——
     test_lg_rag_multi.py:140 注释同证；observe 的 _satisfied_by_model 受
     LG_RAG_REACT_SATISFACTION!=1 默认短路）
  - app/ops/lc_evidence_chain/grader.py:28 grade_chunk(LLM) / answer.py:153 answer_question
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
)
from app.ops.lg_rag.graph import ainvoke_basic_agent, ainvoke_router_agent
from app.ops.lg_rag.multi.graph import ainvoke_supervisor_agent
from app.ops.prompts import render
from app.ops.tenant_context import TENANT_A, reset_current_tenant, set_current_tenant

# ---------------------------------------------------------------------------
# 哨兵与 markers：注入块内容唯一可辨，命中 LLM 请求面即「消费」
# ---------------------------------------------------------------------------

FACT_VALUE = "PHASEA-SENTINEL-FACT-7f3d2c"
PREF_VALUE = "PHASEA-SENTINEL-PREF-51aa"
EPISODE_SUMMARY = "PHASEA-SENTINEL-EPISODE-先查日志再重启"

FACT_MARKERS = [MEMORY_FACTS_HEADER, MEMORY_PREFERENCES_HEADER, FACT_VALUE, PREF_VALUE]
EPISODE_MARKERS = [MEMORY_EPISODES_HEADER, EPISODE_SUMMARY]
ALL_MARKERS = FACT_MARKERS + EPISODE_MARKERS

_QUERY = "服务超时怎么排查"  # 避开 nodes.py:45 _ISSUE_NO_RE 规则快路径（#数字 跳过 classify LLM）
_SUBTASK_QUERY = "检索服务超时处置步骤"
_USER = "phasea-user"
_REWRITE_OUT = "服务超时如何定位并恢复"
_GRADE_REFUSE = '[{"chunk_id": 1, "relevance": "irrelevant", "reason": "首轮不相关"}]'
_GRADE_EXACT = '[{"chunk_id": 1, "relevance": "exact", "reason": "二轮命中"}]'
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


def _assert_assembled(out: dict) -> None:
    """装配面前提：注入块确实存在于图状态消息（否则「零消费」断言无意义）。"""

    assembled = _assembled_text(out)
    missing = [marker for marker in ALL_MARKERS if marker not in assembled]
    assert not missing, f"装配面缺注入块 markers: {missing}"


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
    """注入开（facts + episodes）+ 双 recall mock + tenant ContextVar + tracing 关闭。

    tracing 关闭是为对本机 .env（可能带 LANGFUSE 双键）免疫：trace_span 全 no-op，
    矩阵观测面只剩 provider 消息清单。
    """

    monkeypatch.setenv("MEMORY_FACTS_ENABLED", "true")
    monkeypatch.setenv("MEMORY_EPISODES_ENABLED", "true")
    for key in (
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_SECRET_KEY",
        "OPS_CHAT_TRACER",
        "LG_RAG_REACT_SATISFACTION",
        # continuity.py:464 向量召回分流：本机 .env 置 true 会绕过 recall_active
        # mock 走 recall_with_vector（DB 依赖）→ facts 块缺席；观测面钉确定性通路
        "MEMORY_FACTS_VECTOR_RECALL_ENABLED",
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
            {"key": "project.phasea_probe", "value": FACT_VALUE, "kind": "fact"},
            {"key": "style.phasea_probe", "value": PREF_VALUE, "kind": "preference"},
        ]
    )
    monkeypatch.setattr("app.ops.memory.service.recall_active", facts_recall)
    episodes_recall = AsyncMock(
        return_value=[
            {
                "tenant_id": TENANT_A,
                "run_id": "phasea-run",
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
    yield SimpleNamespace(facts=facts_recall, episodes=episodes_recall)
    reset_current_tenant(token)


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
# 实证矩阵：注入开 × 三模式
# ---------------------------------------------------------------------------


async def test_matrix_basic_rag_zero_consumption(
    monkeypatch: pytest.MonkeyPatch, injection_on: SimpleNamespace
) -> None:
    """basic(rag) × 注入开：装配块进 state.messages；grader/answer 两消费点零命中。"""

    grader = SpyProvider("chain.grader", _GRADE_EXACT)
    answer = SpyProvider("chain.answer", "答案：先查日志再重启")
    _patch_chain(monkeypatch, grader=grader, answer=answer)

    out = await ainvoke_basic_agent(_QUERY, thread_id="phasea-basic", user_id=_USER)

    _assert_assembled(out)
    assert [c.method for c in grader.calls] == ["complete"]
    assert [c.method for c in answer.calls] == ["complete"]
    _assert_no_markers(grader.calls + answer.calls, ALL_MARKERS, "basic/grader+answer")
    # 装配面单点：facts / episodes 各恰好 recall 一次
    assert injection_on.facts.await_count == 1
    assert injection_on.episodes.await_count == 1


async def test_matrix_router_rag_rewrite_loop_zero_consumption(
    monkeypatch: pytest.MonkeyPatch, injection_on: SimpleNamespace
) -> None:
    """router(rag→rewrite 回环) × 注入开：classify/rewrite + grader×2 + answer 全零命中。

    首轮 grader 判 irrelevant → gate refuse → kept 空 → answer 不调 LLM →
    quality low → rewrite 新 query → 二轮 grader 判 exact → kept → answer 调 LLM。
    """

    nodes_spy = SpyProvider("lg_rag.nodes", '{"route": "rag"}', _REWRITE_OUT)
    grader = SpyProvider("chain.grader", _GRADE_REFUSE, _GRADE_EXACT)
    answer = SpyProvider("chain.answer", "答案：先查日志再重启")
    _patch_chain(monkeypatch, grader=grader, answer=answer)
    monkeypatch.setattr(_NODES_PROVIDER, lambda *a, **k: nodes_spy)

    out = await ainvoke_router_agent(_QUERY, thread_id="phasea-router-rag", user_id=_USER)

    sites = [_nodes_call_site(c) for c in nodes_spy.calls]
    assert sites == ["router_node.classify", "rewrite_node"], sites
    # classify / rewrite 的 user 消息 = 原始 query（nodes.py:94 / :217），无注入块
    for call in nodes_spy.calls:
        assert call.messages[-1] == ("user", _QUERY), call.messages
    assert [c.method for c in grader.calls] == ["complete", "complete"]
    assert [c.method for c in answer.calls] == ["complete"]
    _assert_no_markers(
        nodes_spy.calls + grader.calls + answer.calls, ALL_MARKERS, "router-rag-rewrite"
    )
    _assert_assembled(out)
    assert injection_on.facts.await_count == 1
    assert injection_on.episodes.await_count == 1


async def test_matrix_router_direct_zero_consumption(
    monkeypatch: pytest.MonkeyPatch, injection_on: SimpleNamespace
) -> None:
    """router(direct) × 注入开：classify + direct_answer 两消费点零命中（不触 chain）。"""

    nodes_spy = SpyProvider("lg_rag.nodes", '{"route": "direct"}', "直答：先查日志")
    monkeypatch.setattr(_NODES_PROVIDER, lambda *a, **k: nodes_spy)
    monkeypatch.setattr(
        _CHAIN_RETRIEVE,
        AsyncMock(side_effect=AssertionError("direct 路径不应发生检索")),
    )

    out = await ainvoke_router_agent(_QUERY, thread_id="phasea-router-direct", user_id=_USER)

    sites = [_nodes_call_site(c) for c in nodes_spy.calls]
    assert sites == ["router_node.classify", "direct_answer_node"], sites
    # direct_answer 的 user 消息 = _last_user_text(state.messages)（nodes.py:255/:262），
    # 即纯 query 文本而非整包 state.messages —— 注入块（SystemMessage）不进 LLM 请求
    assert nodes_spy.calls[1].messages[-1] == ("user", _QUERY)
    _assert_no_markers(nodes_spy.calls, ALL_MARKERS, "router-direct")
    _assert_assembled(out)


async def test_matrix_supervisor_zero_consumption(
    monkeypatch: pytest.MonkeyPatch, injection_on: SimpleNamespace
) -> None:
    """supervisor × 注入开：planner/aggregator/内层 classify 三消费点零命中。

    wiring 观测（钉死当前形态，供 Phase B 裁定）：
    - 外层入口装配一次（facts + episodes）；
    - 内层 rag 工人经 astream_router_agent 复跑装配——user_id 未传致 facts
      跳过（continuity.py:458），tenant ContextVar 仍在致 episodes 再 recall
      一次（continuity.py:500 不命中 skip）；
    - 内层 classify 的 user 消息 = 子任务 input；aggregator 的 user 消息 =
      原始 query + 子任务结果 JSON——均不含注入块。
    """

    plan = json.dumps(
        {"subtasks": [{"id": "t1", "type": "rag", "input": _SUBTASK_QUERY}]},
        ensure_ascii=False,
    )
    multi_spy = SpyProvider("multi.nodes", plan, _AGG_OUT)
    inner_router = SpyProvider("lg_rag.nodes.inner", '{"route": "rag"}')
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
        _QUERY, thread_id="phasea-supervisor", user_id=_USER, run_id="phasea-run"
    )

    sites = [_multi_call_site(c) for c in multi_spy.calls]
    assert sites == ["supervisor_node.planner", "aggregator_node"], sites
    assert [c.method for c in inner_router.calls] == ["complete"]
    assert _nodes_call_site(inner_router.calls[0]) == "router_node.classify"
    assert inner_router.calls[0].messages[-1] == ("user", _SUBTASK_QUERY)
    chain.assert_awaited_once()
    assert chain.await_args_list[0].args[0] == _SUBTASK_QUERY
    _assert_no_markers(multi_spy.calls + inner_router.calls, ALL_MARKERS, "supervisor")
    _assert_assembled(out)
    # wiring 实证：facts 1 次（外层） vs episodes 2 次（外层 + 内层工人复装配）
    assert injection_on.facts.await_count == 1
    assert injection_on.episodes.await_count == 2


# ---------------------------------------------------------------------------
# TC2：默认关回归（零 diff 语义——recall 零调用 ∧ 注入块零出现）
# ---------------------------------------------------------------------------


async def test_switches_default_off_zero_recall_zero_injection(
    monkeypatch: pytest.MonkeyPatch, injection_on: SimpleNamespace
) -> None:
    """双开关默认关（删 env）→ recall 零 await ∧ state.messages 无注入块 ∧ 流程照常。"""

    monkeypatch.delenv("MEMORY_FACTS_ENABLED", raising=False)
    monkeypatch.delenv("MEMORY_EPISODES_ENABLED", raising=False)
    grader = SpyProvider("chain.grader", _GRADE_EXACT)
    answer = SpyProvider("chain.answer", "答案：先查日志再重启")
    _patch_chain(monkeypatch, grader=grader, answer=answer)

    out = await ainvoke_basic_agent(_QUERY, thread_id="phasea-off", user_id=_USER)

    assert injection_on.facts.await_count == 0
    assert injection_on.episodes.await_count == 0
    assembled = _assembled_text(out)
    leaked = [marker for marker in ALL_MARKERS if marker in assembled]
    assert not leaked, f"默认关下注入块泄漏: {leaked}"
    assert out["messages"][-1].content == "答案：先查日志再重启"


# ---------------------------------------------------------------------------
# harness 自牙测：断言器对含哨兵的调用必 raise（防空转绿）
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


# ---------------------------------------------------------------------------
# TC5（N2 吸收 · 白名单形态）：diff ⊆ tests/ + invoke docs/；
# app/ | scripts/ | alembic/ 显式禁现（含 untracked，防新文件绕过）
# ---------------------------------------------------------------------------

_BASE = "414270d"
_ALLOWED = re.compile(r"^(tests/|docs/harness/invokes/by-task/memory-injection-consumer/)")
_BANNED = re.compile(r"^(app/|scripts/|alembic/)")


def _git(root: Path, *args: str) -> list[str]:
    out = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True
    )
    return [line.strip() for line in out.stdout.splitlines() if line.strip()]


def test_phase_a_diff_whitelist() -> None:
    root = Path(__file__).resolve().parents[1]
    changed: set[str] = set()
    for args in (
        ("diff", "--name-only", _BASE),  # 工作区 vs base（未暂存）
        ("diff", "--name-only", "--cached", _BASE),  # 暂存区 vs base
        ("diff", "--name-only", _BASE, "HEAD"),  # 已提交 delta
    ):
        changed.update(_git(root, *args))
    untracked = set(_git(root, "ls-files", "--others", "--exclude-standard"))

    violations = sorted(p for p in changed if not _ALLOWED.match(p))
    assert not violations, f"diff 越白名单（仅允许 tests/ 与 invoke docs/）: {violations}"
    banned = sorted(p for p in changed | untracked if _BANNED.match(p))
    assert not banned, f"禁改面（app/ scripts/ alembic/）出现改动: {banned}"
